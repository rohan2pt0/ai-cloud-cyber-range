"""OS kit (doc 95): every edition is valid and its built app is current; a new app is one command and one JSON file; the
builder refuses broken editions in plain words, never overwrites a folder it did not build, and cannot be tricked into
writing markup or script into the page through an edition's text."""
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("oskit", ROOT / "governance" / "oskit.py")
ok = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ok)


def test_every_edition_is_valid_and_every_app_is_current():
    assert ok.check() == [], "run ./securax os build --all"
    assert "vantage" in ok.editions() and (ROOT / "guiding-map" / "vantage" / "index.html").is_file()


def test_vantage_carries_the_ciso_content():
    v = ok.editions()["vantage"]
    regs = {r["id"] for r in v["modules"]["registers"]}
    assert {"risks", "decisions", "exceptions", "tools", "stakeholders", "team", "lessons"} <= regs
    assert len(v["modules"]["cadence"]["items"]) >= 15 and len(v["modules"]["playbooks"]["items"]) >= 8
    assert {m["kind"] for m in v["modules"]["scorecard"]["metrics"]} == {"KPI", "KRI"}
    page = (ROOT / "guiding-map" / "vantage" / "index.html").read_text()
    assert ok.MARK in page and "http://" not in page.split("<script>", 1)[0]


def test_a_new_app_is_one_command(tmp_path, monkeypatch):
    monkeypatch.setattr(ok, "EDITIONS", tmp_path / "editions")
    monkeypatch.setattr(ok, "GM", tmp_path)
    (tmp_path / "editions").mkdir()
    (tmp_path / "editions" / "starter.json").write_text((ROOT / "guiding-map" / "kit" / "editions" / "starter.json").read_text())
    for s in (192, 512):
        (tmp_path / f"icon-{s}.png").write_bytes((ROOT / "guiding-map" / f"icon-{s}.png").read_bytes())
    assert ok.main(["new", "founder-os", "--name", "Founder OS", "--tagline", "Build the company, keep your life"]) == 0
    e = json.loads((tmp_path / "editions" / "founder-os.json").read_text())
    assert e["id"] == "founder-os" and "template" not in e
    page = (tmp_path / "founder-os" / "index.html").read_text()
    assert "Founder OS" in page and '"id":"founder-os"' in page
    assert ok.main(["new", "founder-os", "--name", "Again"]) == 2


@pytest.mark.parametrize("change,needle", [
    (lambda e: e.update(id="Bad Id"), "id"),
    (lambda e: e["nav"].append("registers:nope"), "no register"),
    (lambda e: e["nav"].append("ghost"), "not switched on"),
    (lambda e: e["modules"]["registers"][0].update(title="missing"), "'title'"),
    (lambda e: e["modules"]["registers"][0]["fields"][0].update(type="html"), "type must be"),
    (lambda e: e["modules"]["cadence"]["items"][0].update(every="sometimes"), "'every'"),
    (lambda e: e["modules"]["feeds"]["items"][0].update(url="https://example.invalid/x.json"), "same address"),
])
def test_broken_editions_are_refused_in_plain_words(change, needle):
    e = json.loads(json.dumps(ok.editions()["vantage"]))
    change(e)
    err = " ".join(ok.validate(e))
    assert needle in err, err


def test_never_overwrites_a_folder_it_did_not_build(tmp_path, monkeypatch):
    monkeypatch.setattr(ok, "GM", tmp_path)
    (tmp_path / "vantage").mkdir()
    (tmp_path / "vantage" / "index.html").write_text("<html>someone else's page</html>")
    with pytest.raises(ValueError, match="not an app built by the kit"):
        ok.build(ok.editions()["vantage"])


def test_edition_text_cannot_break_out_into_markup_or_script():
    e = json.loads(json.dumps(ok.editions()["vantage"]))
    e["tagline"] = "</script><script>window.__pwned=1</script>"
    e["name"] = "<b>V</b>"
    page = ok.render(e)["index.html"].decode()
    assert "<script>window.__pwned" not in page and "<b>V</b>" not in page.split("<script>window.OSK_EDITION")[0]
    data = page.split("window.OSK_EDITION = ", 1)[1].split(";</script>", 1)[0]
    assert json.loads(data)["tagline"] == e["tagline"]


def test_core_principles_reach_every_app_in_its_own_words():
    v = ok.resolve(ok.editions()["vantage"])
    core = [p["id"] for p in ok.core_principles()["principles"] if p["core"]]
    ids = [p["id"] for p in v["principles"]]
    assert ids[: len(core)] == core and len(set(ids)) == len(ids)
    own = {p["id"]: p["text"] for p in v["principles"]}
    assert "organisation" in own["ikigai"]                     # Vantage says it in a CISO's words
    s = ok.resolve(ok.editions()["starter"])
    assert [p["id"] for p in s["principles"]][: len(core)] == core and s["north_star"]
    bad = json.loads(json.dumps(ok.editions()["starter"]))
    bad["principles"] = ["made-up"]
    assert any("made-up" in m for m in ok.validate(bad))


def test_a_changed_principle_makes_every_app_rebuild(tmp_path, monkeypatch):
    p = json.loads(ok.PRINCIPLES.read_text())
    p["principles"].append({"id": "kaizen", "core": True, "name": "Kaizen", "text": "A better way to say it, for every app."})
    f = tmp_path / "principles.json"
    f.write_text(json.dumps(p))
    monkeypatch.setattr(ok, "PRINCIPLES", f)
    assert any("vantage" in m and "not current" in m for m in ok.check())
    for ed in ("starter", "vantage"):                          # a new core principle reaches every app, whatever its own words
        assert "A better way to say it" in ok.render(ok.editions()[ed])["index.html"].decode()


def test_kit_news_is_checked_and_reaches_the_right_apps(tmp_path, monkeypatch):
    news = [{"date": "2026-10-21", "text": "Something every app gets now."}, {"date": "2026-10-21", "editions": ["vantage"], "text": "Only Vantage gets this one."}]
    f = tmp_path / "whatsnew.json"
    f.write_text(json.dumps(news))
    monkeypatch.setattr(ok, "WHATSNEW", f)
    assert len(ok.resolve(ok.editions()["vantage"])["whatsnew"]) == 2 and len(ok.resolve(ok.editions()["starter"])["whatsnew"]) == 1
    f.write_text(json.dumps([{"date": "soon", "text": "x"}, {"date": "2026-10-21", "editions": ["ghost"], "text": "For an app that is not there."}]))
    probs = " ".join(ok.news_problems())
    assert "needs a date" in probs and "'ghost' does not exist" in probs


def test_a_store_project_is_one_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SITE_DOMAIN", "example.org")
    assert ok.app_id("vantage") == "org.example.vantage" and ok.app_id("founder-os") == "org.example.founderos"
    d = ok.mobile("vantage", tmp_path / "m", "https://example.invalid")
    cfg = json.loads((d / "capacitor.config.json").read_text())
    pkg = json.loads((d / "package.json").read_text())
    assert cfg["appId"] == "org.example.vantage" and cfg["webDir"] == "www"
    assert pkg["dependencies"]["@capacitor/core"] == ok.CAPACITOR and not any("^" in v or "~" in v for v in pkg["dependencies"].values())
    assert (d / "www" / "index.html").read_bytes() == ok.render(ok.editions()["vantage"])["index.html"]
    twa = json.loads((d / "twa-manifest.json").read_text())
    assert twa["host"] == "example.invalid" and twa["startUrl"] == "/vantage/"
    assert "keystore" in (d / ".gitignore").read_text()
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "x.txt").write_text("someone else's")
    with pytest.raises(ValueError, match="not a project"):
        ok.mobile("vantage", tmp_path / "other")


def test_store_readiness_blocks_what_would_fail(monkeypatch):
    assert not [p for p in ok.mobile_problems("vantage") if p[0] == "fail"]
    assert any("4.2" in p[1] for p in ok.mobile_problems("vantage"))           # Apple's rule is named, honestly
    real = ok.mobile_source

    def with_cdn(eid):
        e, files = real(eid)
        files = dict(files)
        files["index.html"] = files["index.html"].replace(b"<head>", b'<head><script src="https://cdn.example.invalid/x.js"></script>', 1)
        return e, files
    monkeypatch.setattr(ok, "mobile_source", with_cdn)
    assert any(p[0] == "fail" and "another site" in p[1] for p in ok.mobile_problems("vantage"))


def test_assetlinks_needs_a_real_fingerprint(tmp_path):
    with pytest.raises(ValueError, match="fingerprint"):
        ok.assetlinks("vantage", "not-a-fingerprint", tmp_path / "a.json")
    fp = ":".join(["AB"] * 32)
    p = ok.assetlinks("vantage", fp, tmp_path / "a.json")
    assert json.loads(p.read_text())[0]["target"]["sha256_cert_fingerprints"] == [fp]


def test_every_kit_app_stays_store_ready():
    for eid, e in ok.editions().items():
        if not e.get("template"):
            assert not [p for p in ok.mobile_problems(eid) if p[0] == "fail"], eid
