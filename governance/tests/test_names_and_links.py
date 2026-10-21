"""Names, not ports, and links that never break (doc 99): the site's address is your domain only once it is live; going
live is refused until the domain really serves the site; brand.env keeps its comments; the link checker finds a missing
page, a missing anchor and a link to a domain that is not live, and follows the site's base folder; links to repository
files leave the docs for GitHub; a person is shown a name, never localhost:PORT, once names are on."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


cfg = load("config", "governance/config.py")
web = load("securax_website", "governance/website.py")
lc = load("securax_linkcheck", "tools/linkcheck.py")
addr = load("securax_addr_t", "governance/addr.py")
hook = load("securax_repo_links", "docs/hooks/repo_links.py")


def test_the_site_address_is_the_domain_only_once_it_is_live():
    base = {"SITE_DOMAIN": "example.org", "REPO_SLUG": "Owner/repo"}
    assert cfg.site_url({**base, "SITE_LIVE": "no"}) == "https://owner.github.io/repo/"
    assert cfg.site_url({**base, "SITE_LIVE": "yes"}) == "https://example.org/"
    assert cfg.site_url({"REPO_SLUG": "owner/owner.github.io"}) == "https://owner.github.io/"
    assert cfg.site_url({}) == ""


def test_going_live_is_refused_until_the_domain_serves_the_site(tmp_path, monkeypatch):
    brand = tmp_path / "brand.env"
    brand.write_text("# keep me\nSITE_DOMAIN=example.org\nSITE_LIVE=no\n")
    vals = {"SITE_DOMAIN": "example.org", "REPO_SLUG": "o/r", "SITE_URL": "https://o.github.io/r/"}
    out = []
    monkeypatch.setattr(web, "resolves", lambda n: set())
    assert web.go_live(vals, out.append, brand) == 1 and "SITE_LIVE=no" in brand.read_text()
    monkeypatch.setattr(web, "resolves", lambda n: {"185.199.108.153"})
    monkeypatch.setattr(web, "answers", lambda u: (False, "HTTP 404"))
    assert web.go_live(vals, out.append, brand) == 1 and "SITE_LIVE=no" in brand.read_text()
    monkeypatch.setattr(web, "answers", lambda u: (True, "HTTP 200"))
    assert web.go_live(vals, out.append, brand) == 0
    assert brand.read_text() == "# keep me\nSITE_DOMAIN=example.org\nSITE_LIVE=yes\n"     # one line changed, comments kept
    assert any("185.199.108.153" in r for r in web.records("example.org", vals)) and web.records("docs.example.org", vals) == ["CNAME docs.example.org   o.github.io."]


def test_the_link_checker_finds_what_a_visitor_would_hit(tmp_path):
    site = tmp_path / "site"
    (site / "docs" / "a").mkdir(parents=True)
    (site / "index.html").write_text('<a href="docs/">d</a><a href="docs/a/#top">t</a><a href="https://example.org/x">x</a>'
                                     '<a href="/r/docs/a/">based</a><a href="missing.html">m</a><a href="docs/a/#nope">n</a>')
    (site / "docs" / "index.html").write_text('<link rel="preconnect" href="https://fonts.example.invalid"><img src="../gone.png">')
    (site / "docs" / "a" / "index.html").write_text('<h1 id="top">A</h1>')
    vals = {"SITE_DOMAIN": "example.org", "SITE_URL": "https://o.github.io/r/"}
    broken, external, n = lc.check_site(site, vals)
    text = "\n".join(broken)
    assert "missing.html does not exist" in text and "../gone.png does not exist" in text and "no anchor #nope" in text
    assert "example.org is not live yet" in text
    assert not any("based" in b or "docs/a/#top" in b or "docs/ " in b for b in broken) and len(broken) == 4, text
    broken, _, _ = lc.check_site(site, {**vals, "SITE_URL": "https://example.org/"})
    assert not any("not live" in b for b in broken)                    # once live, links to it are fine


def test_links_to_repository_files_leave_the_docs_for_github():
    config = {"repo_url": "https://github.com/o/r", "edit_uri": "edit/main/docs/"}
    md = "[c](../../CHANGELOG.md) [d](../index.md) [g](../../governance) [x](../../no-such-file.md) [w](https://e.org)\n```\n[k](../../CHANGELOG.md)\n```"
    out = hook.rewrite(md, "docs/securax", "docs/securax", str(ROOT), config)
    assert "(https://github.com/o/r/blob/main/CHANGELOG.md)" in out and "(https://github.com/o/r/tree/main/governance)" in out
    assert "(../index.md)" in out and "(../../no-such-file.md)" in out and "(https://e.org)" in out   # unknown stays: strict fails
    assert "```\n[k](../../CHANGELOG.md)\n```" in out                                                    # code is never touched
    inc = hook.rewrite("[v](docs/securax/21-VERSIONING-AND-RELEASES.md)", "", "docs/reference", str(ROOT), config)
    assert inc == "[v](../securax/21-VERSIONING-AND-RELEASES.md)"                                        # an included file's link


def test_a_person_is_shown_a_name_once_names_are_on(monkeypatch):
    monkeypatch.delenv("SECURAX_DOMAIN", raising=False)
    assert addr.web_url("hub", 8088, "/x", env={}) == "http://localhost:8088/x"
    on = {"COMPOSE_FILE": "docker-compose.yml:tls.yml"}
    assert addr.web_url("hub", 8088, "/x", env=on) == "https://hub.securax.localhost/x"
    assert addr.web_url("chat", 3000, env={**on, "SECURAX_DOMAIN": "home.example.org"}) == "https://chat.home.example.org/"
    fitness = load("securax_fitness_t", "lifecycle/fitness.py")      # by path: another test may own the name 'lifecycle'
    assert fitness.raw_addresses() == [], "use web_url() / governance/addr.py instead of a raw localhost:PORT"


def test_the_readme_links_only_to_what_exists_and_is_live():
    assert lc.check_readme(cfg.values()) == []
