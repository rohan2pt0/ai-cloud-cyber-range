"""Build-integrity gate — catch the build.js $-replacement bug that duplicated the inlined
ops layer and leaked raw code as page text (jsdom tolerated it; Chromium did not).

Cheap static checks that run in the python CI job alongside the PII gate.
"""
import pathlib

GM = pathlib.Path(__file__).resolve().parents[1]


def test_ops_inlined_exactly_once():
    idx = (GM / "index.html").read_text(encoding="utf-8")
    # Distinctive symbols from the ops layer must appear exactly once. Duplication is the
    # signature of the old build.js bug (ops inserted twice, the second copy as raw text).
    for marker in ("function ensureGloss", "function guidesHTML", "window.gmAsk ="):
        assert idx.count(marker) == 1, f"'{marker}' appears {idx.count(marker)}x — build.js corruption?"


def test_no_premature_script_close():
    idx = (GM / "index.html").read_text(encoding="utf-8")
    # Base app (4) + inlined ops (1) + failsafe (1) = 6 closing script tags. A premature
    # close (raw code leaking into the page) shows up as extra </script> tokens.
    assert idx.count("</script>") <= 7, f"{idx.count('</script>')} </script> tags — premature close / duplication?"


def test_ops_source_matches_inlined():
    # The committed index.html must contain the current ops.js (the drift guard proves equality
    # via `node build.js`; here we sanity-check the inline actually happened).
    ops = (GM / "ops.js").read_text(encoding="utf-8")
    idx = (GM / "index.html").read_text(encoding="utf-8")
    assert "window.gmGuideFilter" in ops and "window.gmGuideFilter" in idx


def test_version_badge_matches_VERSION_file():
    # The header badge once said "v13.0.2" (a hardcoded legacy string) while the product was 0.1.0.
    # build.js now stamps it from the repo's VERSION file; this fails if it ever drifts or is hardcoded.
    import re
    version = (GM.parent / "VERSION").read_text(encoding="utf-8").strip()
    idx = (GM / "index.html").read_text(encoding="utf-8")
    m = re.search(r'id="app_ver"[^>]*>(v[^<]*)</span>', idx)
    assert m, 'version badge (id="app_ver") missing from index.html'
    assert m.group(1) == f"v{version}", f"badge shows {m.group(1)} but VERSION is {version} — run `node build.js`"
    assert "v13.0" not in idx, "legacy hardcoded app version string is back"


def test_fresh_profile_never_renders_a_dangling_possessive():
    # A fresh install has no name yet: the title read "'s Life OS" (and, earlier, "My's Life OS").
    idx = (GM / "index.html").read_text(encoding="utf-8")
    assert 'var poss=fn?fn+"\'s":"My";' in idx
    assert 'fn+"\'s Life OS"' not in idx and 'fn+"\'s Life Operating System"' not in idx


def test_command_center_rechecks_status_instead_of_one_snapshot():
    hub = (GM / "hub.html").read_text(encoding="utf-8")
    assert "setInterval(tick, 5000)" in hub, "status must be re-polled, or a slow-booting app stays red"
    assert ".dot.starting" in hub and ".dot.off" in hub
