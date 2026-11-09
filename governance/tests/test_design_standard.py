"""The design standard (doc 100) is checked, not hoped for: a page on the standard carries the shared tokens in both themes,
has language, viewport and safe-area settings, shows a visible keyboard focus, honours reduced motion, gives touch targets of
at least 44 px, and offers no more than three actions before everything else is folded away."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
STD = json.loads((ROOT / "governance" / "design.json").read_text())


def blocks(css: str) -> tuple[str, str]:
    light = re.search(r":root\{([^}]*)\}", css).group(1)
    dark = re.search(r"prefers-color-scheme:dark\)\{:root\{([^}]*)\}", css).group(1)
    return light, dark


def test_pages_on_the_standard_carry_the_shared_tokens_and_basics():
    for rel in STD["rules"]["pages_on_the_standard"]:
        page = (ROOT / rel).read_text("utf-8")
        light, dark = blocks(page)
        tokens = STD["premium"]["tokens"] if rel in STD["rules"].get("pages_on_the_premium_language", []) else STD["tokens"]
        for theme, block in (("light", light), ("dark", dark)):
            for k, v in tokens[theme].items():
                assert f"{k}:{v}" in block, f"{rel}: {theme} {k} should be {v}"
        assert '<html lang="' in page and "viewport-fit=cover" in page and "safe-area-inset" in page, rel
        assert ":focus-visible" in page and "prefers-reduced-motion" in page, rel
        assert f"min-height:{STD['rules']['min_target_px']}px" in page, rel


def test_the_command_center_shows_three_actions_at_most_and_folds_the_rest():
    hub = (ROOT / "guiding-map" / "hub.html").read_text("utf-8")
    assert f"all.slice(0, {STD['rules']['max_actions_shown']})" in hub
    for fold in ('id="everything"', 'id="addons"', 'id="healthBox"'):
        tag = hub[hub.index(fold) - 40: hub.index(fold) + 40]
        assert "<details" in tag and " open" not in tag, fold
    assert "Status unknown" in hub and "Status may be out of date" in hub    # no 'all clear' without a fresh check


def test_every_generated_page_takes_its_tokens_from_one_place(tmp_path):
    # The cockpit, the ready reckoner and the control navigator get their colours and basics from governance/design.py,
    # never from a palette of their own, so a change in design.json reaches every one of them.
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_design_t", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    css = design.css()
    light, dark = blocks(css)
    for theme, block in (("light", light), ("dark", dark)):
        for k, v in STD["tokens"][theme].items():
            assert f"{k}:{v}" in block, f"design.css(): {theme} {k} should be {v}"
    assert ":focus-visible" in css and "prefers-reduced-motion" in css and "safe-area-inset" in css
    assert f"min-height:{STD['rules']['min_target_px']}px" in css
    for rel in STD["rules"]["generators_on_the_standard"]:
        src = (ROOT / rel).read_text("utf-8")
        assert "design.py" in src and "viewport-fit=cover" in src, rel
        assert not re.search(r":root\{--bg:#", src), f"{rel} defines its own palette; take it from governance/design.py"
    spec = importlib.util.spec_from_file_location("securax_reckoner_t", ROOT / "governance" / "reckoner.py")
    rk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rk)
    rk.build(tmp_path)
    page = next(tmp_path.glob("*.html")).read_text("utf-8")
    assert css in page and "viewport-fit=cover" in page


def test_brand_apps_keep_their_colours_but_meet_the_basics():
    for rel in STD["rules"]["brand_apps_with_the_basics"]:
        src = (ROOT / rel).read_text("utf-8")
        assert ":focus-visible" in src and "prefers-reduced-motion" in src, rel


def test_the_site_stylesheet_is_the_generators_output():
    # The product site keeps its own navy and gold but takes the standard's basics from governance/design.py, so a change in
    # design.json reaches the site too. website/site.css is the checked-in result of tools/site_css.py; the two must agree.
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_site_css_t", ROOT / "tools" / "site_css.py")
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    css = sc.render()
    on_disk = (ROOT / "website" / "site.css").read_text("utf-8")
    assert on_disk == css, "website/site.css is stale: run  python3 tools/site_css.py"
    assert ":focus-visible" in on_disk and "prefers-reduced-motion" in on_disk, "website/site.css"


def test_the_product_site_pages_take_their_colours_from_the_one_stylesheet():
    # The four product-site pages keep their navy and gold but take every colour from the shared generated website/site.css,
    # never from an inline palette of their own, and meet the notch-safe basics.
    pages = {
        "website/index.html": 'rel="stylesheet" href="site.css"',
        "website/assess/index.html": 'rel="stylesheet" href="../site.css"',
        "website/nbfc/index.html": 'rel="stylesheet" href="../site.css"',
        "website/personal/index.html": 'rel="stylesheet" href="../site.css"',
    }
    for rel, href in pages.items():
        page = (ROOT / rel).read_text("utf-8")
        assert href in page, f"{rel}: missing {href}"
        assert "viewport-fit=cover" in page, rel
        assert ":root{" not in page, f"{rel} defines its own palette; take it from website/site.css"
        assert "background:#fff" not in page, f"{rel} hardcodes white cards; use var(--card)"


def test_the_dark_status_colours_pass_on_the_dark_card():
    # The site's dark theme keeps its own lifted green, amber and red so a status light stays readable on the navy card
    # #111e33 (WCAG AA); the light values are the deep shades the site has always used on white.
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_site_css_dark_t", ROOT / "tools" / "site_css.py")
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    _, dark = blocks(sc.render())
    for k, v in (("--green", "#4ade80"), ("--amber", "#fbbf24"), ("--red", "#f87171")):
        assert f"{k}:{v}" in dark, f"site.css dark {k} should be {v} (AA on #111e33)"


def test_site_css_cli_writes_and_checks_exactly(tmp_path):
    # main() is the CLI: it writes the file and returns 0, checks a current file and returns 0, and a stale one and
    # returns exactly 1 (so a loosened or dropped return value fails here; the forge gate mutates these returns).
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_site_css_cli_t", ROOT / "tools" / "site_css.py")
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    out = tmp_path / "site.css"
    sc.OUT = out
    assert sc.main([]) == 0                                        # the write path returns 0
    assert out.read_text("utf-8") == sc.render()                  # and writes the generator's output
    assert sc.main(["--check"]) == 0                              # a current file checks clean, exit 0
    out.write_text("stale", "utf-8")
    assert sc.main(["--check"]) == 1                              # a stale file fails with exactly 1


def test_dark_pills_tags_and_code_are_overridden_after_the_inline_styles():
    # The inline <style> of each page loads after site.css; without these higher-specificity dark rules the light pill and
    # code backgrounds stay, and text on them fell to 1.4-2.4:1 in the first real-browser audit.
    css = (ROOT / "website" / "site.css").read_text("utf-8")
    for sel in ("html .l-g", "html .tag-r", "html code", "html .models ul"):
        assert sel in css, f"site.css dark rules lack {sel}"


# ---- The premium language (design-premium-language): measured, not described. ----
PREM = STD["premium"]


def _lum(h: str) -> float:
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _ratio(a: str, b: str) -> float:
    x, y = _lum(a), _lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def test_every_premium_text_colour_is_aa_on_both_surfaces_in_both_themes():
    for theme, t in PREM["tokens"].items():
        for fg in ("--ink", "--mut", "--accent", "--red", "--amber", "--green"):
            for bg in ("--bg", "--card", "--raise"):
                assert _ratio(t[fg], t[bg]) >= 4.5, f"{theme}: {fg} on {bg} is {_ratio(t[fg], t[bg]):.2f}:1"
        assert _ratio(t["--on-action"], t["--action"]) >= 4.5, f"{theme}: the action button's text"
        assert _ratio(t["--on-accent"], t["--accent"]) >= 4.5, f"{theme}: text on the accent"


def test_dark_is_dark_grey_never_pure_black_and_surfaces_rise_lighter():
    d = PREM["tokens"]["dark"]
    for k in ("--bg", "--card", "--raise"):
        assert d[k].lower() not in PREM["never"]["page_backgrounds"], k
        assert _lum(d[k]) > _lum("#0b0b0c"), f"{k} is too close to black"
    assert _lum(d["--bg"]) < _lum(d["--card"]) < _lum(d["--raise"]), "dark surfaces rise with lighter greys"


def test_the_scale_motion_and_finishes_are_complete():
    assert PREM["space_px"] == [4, 8, 16, 24, 32]
    m = PREM["motion"]
    assert 150 <= m["fast_ms"] <= m["base_ms"] <= m["slow_ms"] <= 250
    for name, f in PREM["finishes"].items():
        assert set(f) >= {"base", "highlight", "rim", "tier"}, name
        assert _lum(f["highlight"]) > _lum(f["base"]) and _lum(f["rim"]) > _lum(f["highlight"]), f"{name}: base < highlight < rim"
    assert {f["tier"] for f in PREM["finishes"].values()} == {"core", "limited"}


def test_premium_css_carries_the_basics_the_serif_and_every_finish():
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_design_p", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    css = design.premium_css()
    light, dark = blocks(css)
    for theme, block in (("light", light), ("dark", dark)):
        for k, v in PREM["tokens"][theme].items():
            assert f"{k}:{v}" in block, f"premium_css(): {theme} {k}"
    assert "font-family:'Instrument Serif'" in css and "data:font/woff2;base64," in css
    assert ":focus-visible" in css and "prefers-reduced-motion" in css and "safe-area-inset" in css
    assert f"min-height:{STD['rules']['min_target_px']}px" in css
    assert all(f".finish-{n}{{" in css for n in PREM["finishes"])
    assert "prefers-reduced-motion" in design.HAPTIC_JS and "data-haptic" in design.HAPTIC_JS


def test_the_display_serif_is_self_hosted_and_matches_the_life_os():
    import base64
    font = (ROOT / PREM["type"]["display_font_file"]).read_bytes()
    assert font[:4] == b"wOF2" and len(font) < 64_000
    assert base64.b64encode(font).decode() in (ROOT / "guiding-map" / "index.html").read_text("utf-8")
    assert (ROOT / "guiding-map" / "fonts" / "Instrument_Serif-OFL.txt").exists()
    for rel in STD["rules"]["pages_on_the_premium_language"]:
        page = (ROOT / rel).read_text("utf-8")
        assert base64.b64encode(font).decode() in page, f"{rel}: the serif is embedded, so it works offline"
        assert "#000000" not in page and not re.search(r"background:#000[;}\s]", page), f"{rel}: no pure black"


def test_the_hosted_door_is_on_the_premium_language_and_may_load_its_serif(tmp_path):
    # The door people reach from the hosted site (guiding-map/command/, published to /command/) has a strict policy with no
    # inline code, so it links the serif as a same-origin file that the publish step copies in, and its policy allows fonts.
    css = (ROOT / "guiding-map" / "command" / "door.css").read_text("utf-8")
    light, dark = blocks(css.replace(":root{color-scheme:light dark;", ":root{"))
    for theme, block in (("light", light), ("dark", dark)):
        for k, v in PREM["tokens"][theme].items():
            assert f"{k}:{v}" in block, f"door.css: {theme} {k}"
    assert "url(serif.woff2)" in css and "prefers-reduced-motion" in css and "min-height:44px" in css
    page = (ROOT / "guiding-map" / "command" / "index.html").read_text("utf-8")
    assert "font-src 'self'" in page
    assert '"./serif.woff2"' in (ROOT / "guiding-map" / "command" / "sw.js").read_text("utf-8"), "cached for offline"
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_pwa_publish_t", ROOT / "tools" / "pwa_publish.py")
    pub = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pub)
    res = pub.publish(tmp_path)
    assert res["command"] == [], res["command"]
    assert (tmp_path / "command" / "serif.woff2").read_bytes() == (ROOT / PREM["type"]["display_font_file"]).read_bytes()
