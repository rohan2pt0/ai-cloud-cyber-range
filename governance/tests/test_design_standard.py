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
        tokens = STD["premium"]["tokens"]
        for theme, block in (("light", light), ("dark", dark)):
            for k, v in tokens[theme].items():
                assert f"{k}:{v}" in block, f"{rel}: {theme} {k} should be {v}"
        assert '<html lang="' in page and "viewport-fit=cover" in page and "safe-area-inset" in page, rel
        assert ":focus-visible" in page and "prefers-reduced-motion" in page, rel
        assert f"min-height:{STD['rules']['min_target_px']}px" in page, rel


def test_the_command_center_shows_one_open_action_and_folds_the_rest():
    # one-open-action: one card open, the rest under "Later (n)" (design.json rules)
    hub = (ROOT / "guiding-map" / "hub.html").read_text("utf-8")
    assert STD["rules"]["max_actions_shown"] == 1 and STD["rules"]["rest_folded_as"] == "Later (n)"
    assert "var one = all[0], later = all.slice(1);" in hub and "<summary>Later ('+later.length" in hub
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
        for k, v in STD["premium"]["tokens"][theme].items():
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
    # The site's dark theme lifts its green, amber and red so a status light stays readable on its dark card (WCAG AA),
    # measured on the card the site really uses, not pinned to old values.
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_site_css_dark_t", ROOT / "tools" / "site_css.py")
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    _, dark = blocks(sc.render())
    vals = dict(kv.split(":", 1) for kv in dark.split(";") if ":" in kv)
    card = vals["--card"]
    for k in ("--green", "--amber", "--red"):
        assert _ratio(vals[k], card) >= 4.5, f"site.css dark {k} {vals[k]} is {_ratio(vals[k], card):.2f}:1 on {card}"


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


def test_the_life_os_today_is_on_the_premium_language_and_follows_the_phone():
    # design-premium-showcase: the Life OS keeps its own token names but takes the premium values, in a layer loaded last.
    ops = (ROOT / "guiding-map" / "ops.js").read_text("utf-8")
    layer = ops[ops.index("function premiumCSS()"):ops.index("function greetHTML()")]
    for theme, sel in (("light", ":root{"), ("dark", "html[data-theme=dark]{")):
        t = PREM["tokens"][theme]
        block = layer[layer.index(sel):]
        block = block[:block.index("}")]
        for mine, std in (("--bg", "--bg"), ("--card", "--card"), ("--text", "--ink"), ("--muted", "--mut"), ("--border", "--line")):
            assert f"{mine}:{t[std]}" in block, f"Life OS {theme} {mine} should be {t[std]}"
    assert "premiumCSS();" in ops and "document.head.appendChild(st)" in layer, "the layer is (re)appended last"
    page = (ROOT / "guiding-map" / "index.html").read_text("utf-8")
    assert 'S.theme="dark"' not in page.replace(" ", ""), "no forced dark default: the theme follows the phone"
    assert "prefers-color-scheme: dark" in page and "S.themeChosen=true" in page
    # red means danger only: progress tiles never take a status colour
    assert 'var prog = v.t === "today" || v.t === "stack";' in ops and "color:var(--text);line-height:1.15" in ops


def test_the_product_site_is_on_the_premium_language():
    # design-premium-showcase: the site keeps its own variable names (navy, gold) but on obsidian-and-ivory values, with
    # the serif for headings linked as a same-origin file that website/build.sh copies in (the site CSP refuses data: fonts).
    css = (ROOT / "website" / "site.css").read_text("utf-8")
    light, dark = blocks(css)
    for theme, block in (("light", light), ("dark", dark)):
        t = PREM["tokens"][theme]
        for mine, std in (("--bg", "--bg"), ("--card", "--card"), ("--ink", "--ink"), ("--muted", "--mut"), ("--line", "--line")):
            assert f"{mine}:{t[std]}" in block, f"site.css {theme} {mine} should be {t[std]}"
    assert "url(serif.woff2)" in css and "html h1,html h2{font-family:'Instrument Serif'" in css
    build = (ROOT / "website" / "build.sh").read_text("utf-8")
    assert "guiding-map/fonts/InstrumentSerif-Regular.woff2 website/serif.woff2" in build
    for page in ("index.html", "assess/index.html", "nbfc/index.html", "personal/index.html"):
        src = (ROOT / "website" / page).read_text("utf-8")
        assert "rgba(11,27,51," not in src and "#2a5596" not in src, f"{page}: the old navy is gone"


def test_glass_is_kept_to_floating_layers_with_a_solid_fallback():
    # Glassmorphism, used the way the platforms use it: frosted only on what floats over scrolling content (sticky bars,
    # the tab bar, sheets, dialogs), opaque enough to read where blur is not drawn, and solid on request.
    g = PREM["material"]["glass"]
    for k in ("light", "dark", "obsidian"):
        assert float(g[k].rsplit(",", 1)[1].rstrip(")")) >= 0.9, f"glass {k} must stay legible without blur"
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_design_g", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    ops = (ROOT / "guiding-map" / "ops.js").read_text("utf-8")
    site = (ROOT / "website" / "site.css").read_text("utf-8")
    for name, src in (("design.premium_css()", design.premium_css()), ("ops.js", ops), ("site.css", site)):
        assert "@supports ((backdrop-filter:blur(1px))" in src and "prefers-reduced-transparency:reduce" in src, name
        assert f"blur({g['blur_px']}px)" in src, f"{name}: blur radius from design.json"
    for k in ("light", "dark", "obsidian"):
        assert g[k] in ops, f"ops.js glass {k} equals design.json"
    assert g["obsidian"] in site
    layer = ops[ops.index("function premiumCSS()"):ops.index("function greetHTML()")]
    glassed = {sel for sel in ("header", "#gmNav", "#gmMoreSheet .sh", "#gmOverlay") if sel + "{background:" in layer or sel + "{background:rgba" in layer}
    assert glassed <= {"header", "#gmNav", "#gmMoreSheet .sh", "#gmOverlay"} and ".gm-d3{background:rgba" not in layer, "no glass on cards"


def test_buttons_have_three_kinds_visible_edges_and_every_state():
    # premium.buttons: primary / secondary / tertiary; the secondary edge is 3:1 on every surface (WCAG 1.4.11); pressed,
    # busy, done and disabled exist; a suggestion is never the primary and never acts by itself.
    for theme, t in PREM["tokens"].items():
        for bg in ("--bg", "--card", "--raise"):
            assert _ratio(t["--edge"], t[bg]) >= 3, f"{theme}: --edge on {bg} is {_ratio(t['--edge'], t[bg]):.2f}:1"
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_design_b", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    css = design.premium_css()
    for need in (".btn-primary{", ".btn-secondary{", ".btn-tertiary{", "[aria-busy=true]", "button:disabled", "prefers-contrast:more",
                 "forced-colors:active", "corner-shape:squircle", ".skip{"):
        assert need in css, f"premium_css() lacks {need}"
    ops = (ROOT / "guiding-map" / "ops.js").read_text("utf-8")
    assert 'class="btn gm-secondary" data-haptic="success" onclick="gmReadAccept()"' in ops, "the lens suggestion is secondary"
    assert '<span class="gm-suggested">Suggested</span>' in ops and '<details class="gm-why"><summary>Why?</summary>' in ops
    assert 'G("gm_smart_off", false)' in ops and "scam warnings always stay" in ops
    assert 'data-haptic="success" class="tile' in ops and 'G("gm_still", false)' in ops and "prefers-reduced-motion: reduce" in ops
    assert 'askBtn.setAttribute("aria-busy", "true")' in ops
    for rel in ("guiding-map/hub.html", "guiding-map/command/index.html", "website/index.html"):
        assert 'class="skip"' in (ROOT / rel).read_text("utf-8"), f"{rel}: a skip link"


def test_every_remaining_page_is_on_the_premium_language():
    # The rollout (owner, 2026-11-10): the kit apps, the exercise portal and the docs carry the premium neutrals too.
    L, D = PREM["tokens"]["light"], PREM["tokens"]["dark"]
    kit = (ROOT / "guiding-map" / "kit" / "kit.css").read_text("utf-8")
    assert f"--bg:{D['--bg']}; --card:{D['--card']}; --ink:{D['--ink']}" in kit and f"--bg:{L['--bg']}; --card:{L['--card']}; --ink:{L['--ink']}" in kit
    assert "prefers-contrast:more" in kit and "forced-colors:active" in kit and ".skip" in kit
    assert 'class="skip"' in (ROOT / "guiding-map" / "kit" / "shell.html").read_text("utf-8")
    ex = (ROOT / "exercise" / "web" / "app.css").read_text("utf-8")
    assert f"--bg: {L['--bg']}; --panel: {L['--card']}" in ex and f"--bg: {D['--bg']}; --panel: {D['--card']}" in ex
    docs = (ROOT / "docs" / "stylesheets" / "premium.css").read_text("utf-8")
    assert f"--md-default-bg-color: {L['--bg']}" in docs and f"--md-default-bg-color: {D['--bg']}" in docs
    mk = (ROOT / "mkdocs.yml").read_text("utf-8")
    assert "stylesheets/premium.css" in mk and "font: false" in mk and "primary: custom" in mk
    for rel in ("guiding-map/kit/kit.css", "exercise/web/app.css"):
        assert "#0d1f35" not in (ROOT / rel).read_text("utf-8").split("}")[0], f"{rel}: no old navy page background"


def test_alerts_are_calm_readable_and_said_once():
    # premium.alerts (owner, 2026-11-10: "make error reporting and such alerts with proper aesthetics"): text stays ink and
    # secondary text stays 4.5:1 on every tint, red is for danger only, a slipped habit is one attention card (never one
    # red box per habit), and Ask's errors arrive as titled alerts.
    for kind, k in PREM["alerts"]["kinds"].items():
        for theme in ("light", "dark"):
            t = PREM["tokens"][theme]
            for fg in ("--ink", "--mut"):
                assert _ratio(t[fg], k[theme]["bg"]) >= 4.5, f"{kind}/{theme}: {fg} on the tint is {_ratio(t[fg], k[theme]['bg']):.2f}:1"
            assert _ratio(k[theme]["rim"], k[theme]["bg"]) >= 3, f"{kind}/{theme}: the edge must be visible"
    ops = (ROOT / "guiding-map" / "ops.js").read_text("utf-8")
    page = (ROOT / "guiding-map" / "index.html").read_text("utf-8")
    pinned = ops[ops.index("function pinnedHTML()"):ops.index("function pinnedHTML()") + 1500]
    assert 'class="gm-alert attention"' in pinned and "var(--redBg)" not in pinned and "mandatory" not in pinned.lower()
    today = page[page.index("function renderToday(){"):page.index("function renderMoney(")]
    assert 'class="warn"' not in today and "hab-floor" in today, "no per-habit alarm on the full Today list"
    assert ops.count("askFail(out, ") >= 6 and "function askFail(out, kind, title, msg)" in ops
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_design_a", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    assert all(f".alert-{n}{{" in design.css() for n in PREM["alerts"]["kinds"]), "every generated page can show the four alerts"


def test_human_first_and_whole_view_are_core_and_tell_agents_what_to_do():
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    for pid in ("human-first", "whole-view"):
        assert princ[pid]["core"] is True, f"{pid} reaches every app"
    assert "Never trick anyone" in princ["human-first"]["text"] and "delete before adding" in princ["whole-view"]["text"]
    agents = (ROOT / "AGENTS.md").read_text("utf-8").split("## 1. Pick the tier")[0]
    assert "(`human-first`)" in agents and "(`whole-view`)" in agents and "**360 review**" in agents
    for q in ("**Person:**", "**First principles:**", "**Whole system:**", "**Craft:**", "**Proof:**", "**Ethics:**", "**System:**"):
        assert q in agents, f"the 360 review asks {q}"
    doc = (ROOT / "docs" / "securax" / "100-DESIGN-STANDARD.md").read_text("utf-8")
    assert "## 6c. Design for the human mind" in doc and "No dark patterns" in doc


def test_the_owner_ui_rules_are_measured_by_the_site_audit():
    # ui-rules-lint: the rules are checked in a real browser (website/tests/ui_audit.py), and any break fails the audit.
    src = (ROOT / "website" / "tests" / "ui_audit.py").read_text("utf-8")
    for rule in ("tap-target", "input-font", "keyboard", "line-height", "pure-black", "link-underline", "line-length", "hover-only"):
        assert f"['{rule}'" in src, f"the audit checks {rule}"
    assert 'and not report["rules"]' in src, "a rule break fails the audit"


def test_build_the_system_is_core_and_agents_have_the_loop():
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    assert princ["build-the-system"]["core"] is True and "not willpower" in princ["build-the-system"]["text"]
    agents = (ROOT / "AGENTS.md").read_text("utf-8").split("## 1. Pick the tier")[0]
    for step in ("**Cue:**", "**Smallest step:**", "**Visible reward:**", "**Environment:**", "**Feedback:**", "**Constraint:**"):
        assert step in agents, f"the system loop names {step}"
    assert "**Decide and recommend" in agents


def test_one_open_action_is_core_and_held_on_every_screen():
    # one-open-action (owner, 2026-11-10): one primary in view, chosen by risk, the rest folded under "Later (n)".
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    assert princ["one-open-action"]["core"] is True and "Later" in princ["one-open-action"]["text"]
    agents = (ROOT / "AGENTS.md").read_text("utf-8").split("## 1. Pick the tier")[0]
    assert "(`one-open-action`)" in agents and "test39.js" in agents
    pkg = (ROOT / "guiding-map" / "package.json").read_text("utf-8")
    assert " test39 " in pkg, "npm test runs the one-open-action test"


def test_the_wide_screen_rules_run_in_every_app_audit():
    # ui-rules-lint slice 3: line length and hover-only controls only show on a wide screen, so each app audit has a 1280 px pass
    for f in ("guiding-map/tests/ui_audit.py", "guiding-map/tests/kit_audit.py"):
        src = (ROOT / f).read_text("utf-8")
        assert '"width": 1280' in src and '"line-length", "hover-only"' in src, f
