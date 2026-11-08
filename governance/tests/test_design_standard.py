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
        for theme, block in (("light", light), ("dark", dark)):
            for k, v in STD["tokens"][theme].items():
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
