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
         "--line": "#e3ddd2", "--bg": "#f6f3ee", "--card": "#fffdf9", "--gold": "#e2c172", "--gold2": "#7a5a12",
         "--green": "#1f6b3a", "--amber": "#7d5300", "--red": "#a8261b", "--radius": "20px"}
DARK = {**LIGHT, "--bg": "#18181b", "--card": "#222226", "--ink": "#f3efe7", "--text": "#d9d4ca", "--muted": "#aba69d",
        "--line": "#38373d", "--gold2": "#e2c172", "--green": "#7fcf98", "--amber": "#e6b85c", "--red": "#f2958b"}


def render() -> str:
    spec = importlib.util.spec_from_file_location("securax_site_design", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    return design.font_face("serif.woff2") + design.css(LIGHT, DARK) + PREMIUM_RULES + DARK_RULES


# The premium look (design-premium-showcase): headings in the self-hosted serif (website/build.sh copies the one font file
# next to this stylesheet; the site's policy allows same-origin fonts), a calm banner instead of a gold block, numbers in
# tabular figures.
PREMIUM_RULES = ("html h1,html h2{font-family:'Instrument Serif',Georgia,serif;font-weight:400;letter-spacing:-.01em}"
                 "html h1{line-height:1.02}"
                 "html .banner{background:var(--card);color:var(--ink);border-bottom:1px solid var(--line);font-weight:500}"
                 "html .banner a{color:var(--gold2);text-decoration:underline;text-underline-offset:3px}"
                 ".num,data,time{font-variant-numeric:tabular-nums}\n")


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
              # Both themes: an obsidian hero with a faint warm glow (the old blue glow failed AA under the gold eyebrow).
              "html .hero{background:radial-gradient(900px 520px at 80% 0,#3a352c 0,transparent 62%),"
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
