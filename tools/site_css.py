#!/usr/bin/env python3
"""Write the product site's one stylesheet (website/site.css) from the shared design standard (doc 100).

The site keeps its own brand colours (navy and gold) but takes the standard's basics from governance/design.py — safe-area
padding (notch-safe edges, effective on a page whose viewport meta is viewport-fit=cover), a visible keyboard focus, reduced
motion and 44 px targets — so a change in design.json reaches the site too, never a palette of its own.

    python3 tools/site_css.py            write website/site.css
    python3 tools/site_css.py --check    exit 1 when it is stale (CI runs this)

Standard library only.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "website" / "site.css"

# The site's brand variables on the premium language (design.json "premium": obsidian and ivory, gold as leaf), layered
# over the standard's tokens: light first, then dark. The dark theme keeps the navy, gold
# and radius from light and overrides the surfaces and text (--bg, --card, --ink, --text, --muted, --line, --gold2), plus the
# status colours (--green, --amber, --red), lifted so a light on the dark navy card #111e33 passes WCAG AA.
LIGHT = {"--navy": "#1b1a18", "--navy2": "#2a2825", "--ink": "#1b1a18", "--text": "#3a3732", "--muted": "#5f5b54",
         "--line": "#e3ddd2", "--bg": "#f6f3ee", "--card": "#fffdf9", "--gold": "#e2c172", "--gold2": "#7a5a12", "--edge": "#857e72",
         "--green": "#1f6b3a", "--amber": "#7d5300", "--red": "#a8261b", "--radius": "20px",
         # website-premium: the night the hero, the proof strip and the closing share (the sky's own colours, near-black navy),
         # champagne from the lit gold (F0 0.944, 0.776, 0.373 under a soft box), jade from the keycaps, and ivory depth.
         "--night": "#070c18", "--night2": "#0c1427", "--night3": "#13203b", "--on-night": "#eef1f6", "--on-night-mut": "#aeb8ca",
         "--champagne": "#e8d29b", "--jade": "#0d6a51", "--ivory2": "#efe9df", "--hair": "rgba(27,26,24,.09)",
         "--lift": "0 1px 2px rgba(27,26,24,.05),0 14px 36px -14px rgba(27,26,24,.18)"}
DARK = {**LIGHT, "--bg": "#18181b", "--card": "#222226", "--ink": "#f3efe7", "--text": "#d9d4ca", "--muted": "#aba69d",
        "--line": "#38373d", "--edge": "#7d7972", "--gold2": "#e2c172", "--green": "#7fcf98", "--amber": "#e6b85c", "--red": "#f2958b",
        "--jade": "#7fd3b3", "--ivory2": "#1d1d21", "--hair": "rgba(255,255,255,.07)",
        "--lift": "0 1px 0 rgba(255,255,255,.04) inset,0 18px 40px -18px rgba(0,0,0,.6)"}


# The text face: Jost, the same file the Life OS embeds (guiding-map/fonts, SIL OFL 1.1), copied next to this stylesheet by
# website/build.sh as sans.woff2 (the site's policy allows same-origin fonts). One variable file covers every weight.
SANS_FACE = ("@font-face{font-family:'Jost';font-style:normal;font-weight:100 900;font-display:swap;"
             "src:url(sans.woff2) format('woff2')}\n")


def render() -> str:
    spec = importlib.util.spec_from_file_location("securax_site_design", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    return design.font_face("serif.woff2") + SANS_FACE + design.css(LIGHT, DARK) + PREMIUM_RULES + _glass_rules() + DARK_RULES


# The premium look (design-premium-showcase): headings in the self-hosted serif (website/build.sh copies the one font file
# next to this stylesheet; the site's policy allows same-origin fonts), a calm banner instead of a gold block, numbers in
# tabular figures.
PREMIUM_RULES = ("html h1,html h2{font-family:'Instrument Serif',Georgia,serif;font-weight:400;letter-spacing:-.01em}"
                 "html h1{line-height:1.02}"
                 "html .banner{background:var(--card);color:var(--ink);border-bottom:1px solid var(--line);font-weight:500}"
                 "html .banner a{color:var(--gold2);text-decoration:underline;text-underline-offset:3px}"
                 ".num,data,time{font-variant-numeric:tabular-nums}"
                 # the owner's tactile and accessibility rules: a skip link, more contrast on request, Windows high-contrast
                 # mode, and squircle corners where the browser can draw them (plain rounded corners elsewhere)
                 ".skip{position:absolute;left:-9999px;top:8px;z-index:10000;background:var(--navy);color:#fff;padding:8px 16px;border-radius:999px}.skip:focus{left:16px}"
                 "@media (prefers-contrast:more){:root{--muted:#3f3c37;--line:#6f695f}}"
                 "@media (prefers-contrast:more) and (prefers-color-scheme:dark){:root{--muted:#d6d1c8;--line:#8f8b84}}"
                 "@media (forced-colors:active){.btn,.card,button{border:1px solid ButtonText}:focus-visible{outline:2px solid Highlight}}"
                 "@supports (corner-shape:squircle){.card,.btn,.term,button{corner-shape:squircle}}"
                 "html .btn:active{transform:scale(.97)}html .btn:disabled{opacity:.45;cursor:not-allowed}"
                 # The menu bar at laptop width: the brand never shrinks (its byline used to run under "How it works"), the
                 # byline shows only where it fits, and the menu tightens a little before the phone menu takes over at 960 px.
                 "@media (min-width:961px){html .nav .brand{flex:0 0 auto}html .nav ul{min-width:0}}"
                 "@media (max-width:1359px){html .nav .brand small{display:none}}"
                 "@media (min-width:961px) and (max-width:1199px){html .nav ul{gap:14px}html .nav ul a{font-size:14px}html .nav .wrap{gap:16px}}"
                 # ui-rules-lint slice 3: running text keeps a readable measure (at most ~75 characters a line) on a wide screen
                 "html .note,html .caption,html .sub{max-width:min(100%,58ch)}html .micro{max-width:min(100%,52ch)}"
                 "html .center .note,html .center .micro,html .caption,html .center .sub{margin-left:auto;margin-right:auto}\n")


def _glass_rules() -> str:
    # The sticky menu bar is the site's one floating layer, so it is the one place for glass (premium.material.glass).
    import json
    g = json.loads((ROOT / "governance" / "design.json").read_text("utf-8"))["premium"]["material"]["glass"]
    blur = f"blur({g['blur_px']}px) saturate({g['saturate']})"
    return ("@supports ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){"
            f"html header.nav{{background:{g['obsidian']};-webkit-backdrop-filter:{blur};backdrop-filter:{blur}}}}}"
            "@media (prefers-reduced-transparency:reduce){html header.nav{background:#1b1a18;-webkit-backdrop-filter:none;backdrop-filter:none}}\n")


# The pages' own inline <style> loads after this file, so a dark override needs one more element in its selector to win.
# Tinted pills, tags and code keep their light backgrounds otherwise, and their lifted text becomes unreadable on them.
DARK_RULES = ("@media (prefers-color-scheme:dark){"
              "html .l-g,html .tag-g{background:rgba(74,222,128,.14)}"
              "html .l-a{background:rgba(251,191,36,.14)}"
              "html .l-r,html .tag-r{background:rgba(248,113,113,.14)}"
              "html code{background:#2b2b30;color:var(--ink)}"
              "html .models ul{color:var(--text)}"
              "html .btn-line{border-color:var(--ink);color:var(--ink)}"
              "html .offer{background:linear-gradient(160deg,#2b2620,var(--card))}}\n"
              # Both themes: an obsidian hero with a faint warm glow (the old blue glow failed AA under the gold eyebrow). A hero
              # drawn as the night sky (class sx-sky, the home page) takes its look from the shared lux.css instead.
              "html .hero:not(.sx-sky){background:radial-gradient(900px 520px at 80% 0,#3a352c 0,transparent 62%),"
              "linear-gradient(165deg,var(--navy) 0,var(--navy2) 100%)}"
              "html .micro{color:#d8d2c6}\n")


def main(argv: list[str]) -> int:
    css = render()
    if "--check" in argv:
        cur = OUT.read_text("utf-8") if OUT.exists() else ""
        if cur != css:
            print("website/site.css is stale: run  python3 tools/site_css.py")
            return 1
        return 0
    OUT.write_text(css, "utf-8")
    print("website/site.css: generated from governance/design.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
