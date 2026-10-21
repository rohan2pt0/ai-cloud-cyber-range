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
