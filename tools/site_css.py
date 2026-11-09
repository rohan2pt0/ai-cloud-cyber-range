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

# The site's brand variables, layered over the standard's tokens: light first, then dark. The dark theme keeps the navy, gold
# and radius from light and overrides the surfaces and text (--bg, --card, --ink, --text, --muted, --line, --gold2), plus the
# status colours (--green, --amber, --red), lifted so a light on the dark navy card #111e33 passes WCAG AA.
LIGHT = {"--navy": "#0b1b33", "--navy2": "#13294b", "--ink": "#0f1c33", "--text": "#2b3a55", "--muted": "#5b6b86",
         "--line": "#e3e8f0", "--bg": "#f6f8fb", "--card": "#fff", "--gold": "#e8b84a", "--gold2": "#8a6514",
         "--green": "#13723a", "--amber": "#b45309", "--red": "#b91c1c", "--radius": "16px"}
DARK = {**LIGHT, "--bg": "#0a1220", "--card": "#111e33", "--ink": "#edf2f9", "--text": "#c4cfdd", "--muted": "#96a5ba",
        "--line": "#26374e", "--gold2": "#e8b84a", "--green": "#4ade80", "--amber": "#fbbf24", "--red": "#f87171"}


def render() -> str:
    spec = importlib.util.spec_from_file_location("securax_site_design", ROOT / "governance" / "design.py")
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    return design.css(LIGHT, DARK) + DARK_RULES


# The pages' own inline <style> loads after this file, so a dark override needs one more element in its selector to win.
# Tinted pills, tags and code keep their light backgrounds otherwise, and their lifted text becomes unreadable on them.
DARK_RULES = ("@media (prefers-color-scheme:dark){"
              "html .l-g,html .tag-g{background:rgba(74,222,128,.14)}"
              "html .l-a{background:rgba(251,191,36,.14)}"
              "html .l-r,html .tag-r{background:rgba(248,113,113,.14)}"
              "html code{background:#1b2a42;color:var(--ink)}"
              "html .models ul{color:var(--text)}"
              "html .btn-line{border-color:var(--ink);color:var(--ink)}"
              "html .offer{background:linear-gradient(160deg,#2a2210,var(--card))}}\n"
              # Both themes: the hero's glow was #2a5596, where the gold eyebrow (4.0:1) and the small print (3.7:1) failed AA.
              "html .hero{background:radial-gradient(900px 520px at 80% 0,#1f4378 0,transparent 62%),"
              "linear-gradient(165deg,var(--navy) 0,var(--navy2) 100%)}"
              "html .micro{color:#c8d4e6}\n")


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
