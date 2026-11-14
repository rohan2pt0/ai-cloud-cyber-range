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


def test_every_app_builds_the_same_night_sky_and_seal_in():
    """The night sky and the gold seal (owner, 2026-11-14) are one engine in shared/sky.js, built into the Life OS and every
    kit edition, and the gold is one pair of tokens in lux.css; no app draws its own copy."""
    sky = (ROOT / "guiding-map" / "shared" / "sky.js").read_text("utf-8")
    sky_mark = "SecuRAX shared night sky"
    assert sky_mark in sky and "function seal()" in sky and "prefers-reduced-motion" in sky
    css = SX.read_text("utf-8")
    assert "--sx-gold-face:" in css and "--sx-gold-edge:" in css and ".sx-seal{" in css
    assert "readdirSync(SHARED_DIR)" in (ROOT / "guiding-map" / "build.js").read_text("utf-8"), "the Life OS builds in every shared script"
    assert sky_mark in (ROOT / "guiding-map" / "index.html").read_text("utf-8"), "the built Life OS carries the sky"
    spec = importlib.util.spec_from_file_location("oskit_for_sky", ROOT / "governance" / "oskit.py")
    ok = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ok)
    for eid, e in ok.editions(include_templates=False).items():
        assert sky_mark in ok.render(e)["index.html"].decode("utf-8"), f"the {eid} edition builds the sky in"
    ops = (ROOT / "guiding-map" / "ops.js").read_text("utf-8") + (ROOT / "guiding-map" / "kit" / "core.js").read_text("utf-8")
    assert "createRadialGradient" not in ops and "<linearGradient id=\"sxSealG\"" not in ops, "no private sky or seal"


def test_one_type_pair_and_the_touch_engine_ride_in_every_app():
    """The type pair (the house serif for display, Jost for text; both SIL OFL, embedded so they work offline) and the touch
    and light engine (shared/touch.js) are built into every app from the one copy (owner, 2026-11-14)."""
    import base64
    jost = (ROOT / "guiding-map" / "fonts" / "Jost-Variable.woff2").read_bytes()
    assert jost[:4] == b"wOF2" and len(jost) < 40_000
    assert (ROOT / "guiding-map" / "fonts" / "Jost-OFL.txt").exists(), "a bundled font ships its OFL licence"
    b64 = base64.b64encode(jost).decode()
    touch = (ROOT / "guiding-map" / "shared" / "touch.js").read_text("utf-8")
    mark = "SecuRAX shared touch and light"
    assert mark in touch and "prefers-reduced-motion" in touch and "passive: true" in touch
    life = (ROOT / "guiding-map" / "index.html").read_text("utf-8")
    assert b64 in life and mark in life, "the Life OS carries the sans and the touch engine"
    spec = importlib.util.spec_from_file_location("oskit_for_type", ROOT / "governance" / "oskit.py")
    ok = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ok)
    serif = base64.b64encode((ROOT / "guiding-map" / "fonts" / "InstrumentSerif-Regular.woff2").read_bytes()).decode()
    for eid, e in ok.editions(include_templates=False).items():
        page = ok.render(e)["index.html"].decode("utf-8")
        assert b64 in page and serif in page and mark in page, f"the {eid} edition carries both faces and the touch engine"
    css = SX.read_text("utf-8")
    for token in ("--sx-serif:", "--sx-sans:", "--sx-platinum-face:", ".sx-glass{", ".sx-velvet{", ".sx-seal-gem{"):
        assert token in css, token


def test_materials_are_lit_from_measured_optics_in_one_shared_renderer():
    """Gold, platinum, diamond, enamel and velvet are rendered, not painted (owner, 2026-11-14): one physically based
    renderer in shared/materials.js, built into every app, with the measured constants it claims, and a CSS fallback."""
    m = (ROOT / "guiding-map" / "shared" / "materials.js").read_text("utf-8")
    mark = "SecuRAX shared materials"
    for needle in ("F0G=vec3(.944,.776,.373)", "F0P=vec3(.679,.642,.588)", "2.410,0", "2.426,1", "2.444,2",
                   "add(34.5,", "add(40.75,", "uP[73]", "refract(", "getShaderPrecisionFormat", "webglcontextlost"):
        assert needle in m, needle
    assert mark in (ROOT / "guiding-map" / "index.html").read_text("utf-8"), "the Life OS carries the renderer"
    spec = importlib.util.spec_from_file_location("oskit_for_mat", ROOT / "governance" / "oskit.py")
    ok = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ok)
    for eid, e in ok.editions(include_templates=False).items():
        page = ok.render(e)["index.html"].decode("utf-8")
        assert mark in page and "http://" not in page, f"the {eid} edition carries the renderer, offline"
    css = SX.read_text("utf-8")
    assert ".sx-seal.sx-mat-on" in css and ".sx-mat-gold-on" in css, "lit surfaces retire their painted stand-ins"


def test_every_device_is_a_principle_and_has_a_proof():
    """Every-device (owner, 2026-11-14): the principle lives in the one source, AGENTS.md teaches it, and the device audit
    that proves it is real and runs in the sandbox on every change."""
    import json
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    assert "every-device" in princ and princ["every-device"]["core"]
    assert "every-device" in (ROOT / "AGENTS.md").read_text("utf-8")
    audit = (ROOT / "guiding-map" / "tests" / "device_audit.py").read_text("utf-8")
    for d in ("iPhone SE", "iPhone 15 Pro Max", "Pixel 7", "iPad Mini", "iPad Pro 11 landscape", "Pixel 7 landscape", "Desktop 1920"):
        assert d in audit, d
    for check in ("scrolls sideways", "cut off", "small target", "Unlock is off screen", "viewport-fit=cover"):
        assert check in audit, check
    assert "device_audit.py" in (ROOT / "sandbox" / "run.py").read_text("utf-8")


def test_the_renderer_lets_go_of_departed_surfaces_before_its_budget():
    """Test campaign 2026-11-14: after 60 tab switches Vantage's gold stopped rendering, because surfaces whose element had
    left the page still counted against the budget. They are let go before the budget is checked, and slow devices draw at
    a lower resolution rather than stutter."""
    m = (ROOT / "guiding-map" / "shared" / "materials.js").read_text("utf-8")
    i = m.index("function attach(")
    body = m[i:m.index("function draw(", i)]
    assert "prune();" in body and body.index("prune();") < body.index("return;\n    var cs"), "prune before the budget check"
    assert "Q = Math.max(0.5" in m, "adaptive quality"


def test_the_robustness_audit_runs_in_the_sandbox():
    run = (ROOT / "sandbox" / "run.py").read_text("utf-8")
    assert "robustness_audit.py" in run and "ROBUSTNESS AUDIT: PASS" in run
