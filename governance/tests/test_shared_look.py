"""Reuse-first (owner, 2026-11-13: "make it a habit to reuse the modules for other pieces of software"): the SecuRAX shared
look lives in ONE file, guiding-map/shared/lux.css, and every app builds it in. An app adds context on top; it never keeps a
private copy of a shared primitive."""
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SX = ROOT / "guiding-map" / "shared" / "lux.css"
MARK = "SecuRAX shared look"
PRIMITIVES = [".sx-keys", ".sx-key", ".sx-check", ".sx-crest", ".sx-sky", ".sx-gold", ".sx-quiet"]


def test_the_shared_look_is_one_file_with_the_primitives():
    css = SX.read_text("utf-8")
    assert MARK in css
    for p in PRIMITIVES:
        assert re.search(re.escape(p) + r"[\s,{.:]", css), p


def test_every_app_builds_the_same_shared_look_in():
    build = (ROOT / "guiding-map" / "build.js").read_text("utf-8")
    assert "shared" in build and "lux.css" in build, "the Life OS build reads the shared file"
    spec = importlib.util.spec_from_file_location("oskit_for_sx", ROOT / "governance" / "oskit.py")
    ok = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ok)
    eds = ok.editions(include_templates=False)
    assert eds, "at least one kit edition"
    for eid, e in eds.items():
        assert MARK in ok.render(e)["index.html"].decode("utf-8"), f"the {eid} edition builds the shared look in"
    for built in ("guiding-map/index.html", "guiding-map/vantage/index.html"):
        assert MARK in (ROOT / built).read_text("utf-8"), f"{built} carries the shared look"


def test_no_app_keeps_a_private_copy_of_a_shared_primitive():
    for own in ("guiding-map/ops.js", "guiding-map/kit/kit.css", "guiding-map/index.html"):
        text = (ROOT / own).read_text("utf-8")
        text = text.split("s.id='sxLux'")[0] if own.endswith("index.html") else text   # the app's own code, before the inlined shared look
        for p in PRIMITIVES:
            assert not re.search(re.escape(p) + r"\s*\{", text), f"{own} defines {p}: add it to guiding-map/shared/lux.css instead"
