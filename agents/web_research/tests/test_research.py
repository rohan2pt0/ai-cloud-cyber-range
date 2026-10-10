"""Autonomous web-research agent — the rails must hold. All offline (injected I/O)."""
from agents.web_research import research, safety
from agents.web_research.researcher import extract_text


# ---- SSRF / target safety --------------------------------------------------------------------
def test_ssrf_blocks_internal_and_metadata():
    for bad in [
        "http://localhost/admin", "http://127.0.0.1:8080/v1", "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/", "http://192.168.1.1/", "http://metadata.google.internal/",
        "http://gateway/healthz", "file:///etc/passwd", "ftp://host/x",
    ]:
        ok, _ = safety.is_safe_target(bad)
        assert not ok, bad


def test_ssrf_allows_public_fqdn():
    ok, _ = safety.is_safe_target("https://www.irdai.gov.in/term-insurance")
    assert ok


# ---- allowlist / denylist --------------------------------------------------------------------
def test_allowlist_fail_closed_when_empty():
    ok, _ = safety.domain_allowed("https://example.com/x", [], [])
    assert not ok


def test_allowlist_matches_subdomains_only():
    assert safety.domain_allowed("https://news.livemint.com/a", ["livemint.com"], [])[0]
    assert not safety.domain_allowed("https://evil.com/a", ["livemint.com"], [])[0]


def test_denylist_overrides_open():
    assert not safety.domain_allowed("https://facebook.com/x", ["*"], ["facebook.com"])[0]
    assert safety.domain_allowed("https://good.com/x", ["*"], ["facebook.com"])[0]


# ---- state-changing -> HITL ------------------------------------------------------------------
def test_state_changing_detection():
    assert safety.is_state_changing("POST", "https://x.com/a")
    assert safety.is_state_changing("GET", "https://x.com/checkout")
    assert safety.is_state_changing("GET", "https://x.com/login?next=/")
    assert not safety.is_state_changing("GET", "https://x.com/articles/term-insurance")


# ---- robots.txt ------------------------------------------------------------------------------
def test_robots_disallow_respected():
    robots = "User-agent: *\nDisallow: /private\nAllow: /private/ok"
    assert not safety.robots_allows(robots, "/private/data")
    assert safety.robots_allows(robots, "/private/ok/page")  # longer Allow wins
    assert safety.robots_allows(robots, "/public")
    assert safety.robots_allows("", "/anything")             # no robots -> allowed


# ---- extraction ------------------------------------------------------------------------------
def test_extract_strips_scripts_and_gets_title():
    html = "<html><head><title>Hi</title></head><body><script>steal()</script><p>Real text here</p></body></html>"
    title, text = extract_text(html)
    assert title == "Hi"
    assert "Real text here" in text and "steal" not in text


# ---- end-to-end with injected search/fetch/llm (NO network) ----------------------------------
def _fake_search(mapping):
    return lambda q, k: mapping.get(q, mapping.get("*", []))


def _fake_fetch(pages):
    def f(url):
        if url not in pages:
            return 404, "", url
        return 200, pages[url], url
    return f


def test_end_to_end_cites_only_fetched_sources():
    pages = {
        "https://irdai.gov.in/a": "<title>IRDAI</title><p>Term cover guidance.</p>",
        "https://livemint.com/b": "<title>Mint</title><p>Best term plans 2026.</p>",
    }
    captured = {}

    def fake_llm(messages):
        captured["system"] = messages[0]["content"]
        captured["user"] = messages[-1]["content"]
        return "Term insurance basics [1]; market view [2]. Confidence & gaps: medium."

    res = research(
        "best term insurance india",
        allow=["irdai.gov.in", "livemint.com"],
        search=_fake_search({"*": list(pages)}),
        fetch=_fake_fetch(pages),
        llm=fake_llm,
        max_pages=8,
    )
    assert len(res.sources) == 2
    assert "[1]" in res.report and "[2]" in res.report
    # the untrusted-content contract must be in the system prompt
    assert "untrusted" in captured["system"].lower() and "never" in captured["system"].lower()


def test_offlist_and_ssrf_urls_are_skipped_not_fetched():
    pages = {"https://ok.com/x": "<p>fine</p>"}
    fetched = []

    def tracking_fetch(url):
        fetched.append(url)
        return _fake_fetch(pages)(url)

    res = research(
        "x",
        allow=["ok.com"],
        search=_fake_search({"*": [
            "https://ok.com/x", "https://evil.com/y", "http://169.254.169.254/meta", "http://localhost/z",
        ]}),
        fetch=tracking_fetch, llm=None, max_pages=8,
    )
    assert fetched == ["https://ok.com/x"]           # only the safe, allowlisted URL was fetched
    assert any("evil.com" in s for s in res.skipped)
    assert any("169.254" in s for s in res.skipped)


def test_state_changing_links_become_pending_actions_not_fetched():
    fetched = []

    def tracking_fetch(url):
        fetched.append(url)
        return 200, "<p>x</p>", url

    res = research(
        "buy something",
        allow=["shop.com"],
        search=_fake_search({"*": ["https://shop.com/checkout", "https://shop.com/review/item"]}),
        fetch=tracking_fetch, llm=None, max_pages=8,
    )
    assert "https://shop.com/checkout" not in fetched           # never auto-fetched
    assert any(a.url == "https://shop.com/checkout" for a in res.pending_actions)
    assert fetched == ["https://shop.com/review/item"]          # the read-only one is fine


def test_page_budget_caps_fetches():
    pages = {f"https://ok.com/{i}": "<p>t</p>" for i in range(20)}
    res = research(
        "x", allow=["ok.com"],
        search=_fake_search({"*": list(pages)}),
        fetch=_fake_fetch(pages), llm=None, max_pages=3,
    )
    assert len(res.sources) == 3


def test_redirect_to_internal_is_blocked():
    def redirecting_fetch(url):
        # page redirects to a metadata endpoint
        return 200, "<p>ok</p>", "http://169.254.169.254/latest/"

    res = research(
        "x", allow=["ok.com"],
        search=_fake_search({"*": ["https://ok.com/x"]}),
        fetch=redirecting_fetch, llm=None, max_pages=8,
    )
    assert not res.sources
    assert any("redirect blocked" in s for s in res.skipped)


def test_no_sources_never_fabricates():
    res = research(
        "x", allow=["ok.com"],
        search=_fake_search({"*": ["https://blocked.com/x"]}),
        fetch=_fake_fetch({}), llm=lambda m: "should not be called with no sources", max_pages=8,
    )
    assert not res.sources
    assert "fabricat" in res.report.lower() or "No sources" in res.report
