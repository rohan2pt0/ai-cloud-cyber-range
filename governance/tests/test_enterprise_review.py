"""The enterprise review is standing, not asked for each time (principle `enterprise-grade`, AGENTS.md section 7), and the hosted apps carry
their own security headers so the page's policy and the host's can never drift apart."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HEADERS = (ROOT / "website" / "_headers").read_text("utf-8")


def rules():
    out, cur = {}, None
    for line in HEADERS.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            cur = out.setdefault(line.strip(), [])
        elif cur is not None:
            cur.append(line.strip())
    return out


def test_the_hosted_apps_have_their_own_header_rules():
    r = rules()
    for path in ("/app/*", "/vantage/*", "/command/*"):
        assert any("frame-ancestors 'none'" in h for h in r[path]), f"{path}: nobody may frame an app that holds a person's data"
    for path in ("/app/*", "/vantage/*"):
        # both sign in through another site's window (OneDrive): the global same-origin rule is detached for a popup-friendly one
        assert "! Cross-Origin-Opener-Policy" in r[path] and "Cross-Origin-Opener-Policy: same-origin-allow-popups" in r[path]
        assert not any("script-src" in h for h in r[path]), "the single-file apps carry inline code: a script-src would break them"
    assert not any("unsafe-inline" in h and "script-src" in h for h in r["/command/*"]), "the door allows no inline script"


def test_the_doors_policy_in_the_page_and_in_the_host_is_the_same_policy():
    meta = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', (ROOT / "guiding-map" / "command" / "index.html").read_text("utf-8")).group(1)
    host = next(h for h in rules()["/command/*"] if h.startswith("Content-Security-Policy:")).split(": ", 1)[1]
    norm = lambda s: sorted(x.strip() for x in s.split(";") if x.strip() and not x.strip().startswith("frame-ancestors"))  # noqa: E731
    assert norm(meta) == norm(host), "the page's own policy and the host's must not drift"


def test_the_review_is_a_core_principle_and_the_first_step_of_every_session():
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    assert princ["enterprise-grade"]["core"] is True
    agents = (ROOT / "AGENTS.md").read_text("utf-8")
    sec = agents.split("## 7. Enterprise grade")[1]
    for lens in ("Single points of failure", "Friction", "UI and UX", "Security and privacy", "Operate"):
        assert lens in sec, lens
    for rule in ("Do not subscribe to pull-request events", "ONE check-in", "about 60%"):
        assert rule in sec, f"the room-saving rule is missing: {rule}"
    q = {i["id"]: i for i in json.loads((ROOT / "governance" / "queue.json").read_text("utf-8"))["items"]}
    assert q["enterprise-sweep-components"]["state"] == "open" and q["enterprise-sweep-components"]["due"], "the first full sweep is an open, dated ask"
