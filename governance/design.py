"""The design standard's shared CSS (doc 100), made from governance/design.json so every page the estate generates
(cockpit, ready reckoner, control navigator) carries the same tokens and basics. Change a colour in design.json and
every one of them follows on its next build.

    python3 governance/design.py            print the CSS block

`css(aliases)` returns the light tokens, the dark tokens, the page's own short names mapped onto them (so existing
rules such as var(--r) keep working), and the basics every page needs: safe-area padding, a visible keyboard focus,
reduced motion and 44 px targets for buttons and fold headers."""
import json
import pathlib

STD = json.loads((pathlib.Path(__file__).resolve().parent / "design.json").read_text("utf-8"))

# The short names older pages use, mapped onto the shared tokens. var() resolves where it is used, so each alias follows
# the theme: --r is the light red in light mode and the dark red in dark mode.
ALIASES = {"--g": "var(--green)", "--a": "var(--amber)", "--r": "var(--red)", "--acc": "var(--accent)", "--b": "var(--accent)"}


def _block(tokens: dict) -> str:
    return ";".join(f"{k}:{v}" for k, v in tokens.items())


def css(extra_light: dict | None = None, extra_dark: dict | None = None) -> str:
    """The shared tokens in both themes, the aliases, and the basics. extra_*: a page's own variables (not colours the
    standard owns), for example the text colour on a lamp."""
    t = STD["tokens"]
    px = STD["rules"]["min_target_px"]
    light = _block({**t["light"], **ALIASES, **(extra_light or {})})
    dark = _block({**t["dark"], **(extra_dark or {})})
    return (f":root{{{light}}}\n@media (prefers-color-scheme:dark){{:root{{{dark}}}}}\n"
            "body{padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)}\n"
            ":focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:4px}\n"
            f"button,summary,.btn{{min-height:{px}px}}summary{{display:list-item;padding:10px 0;cursor:pointer}}\n"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}\n")


HEAD = "<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>"   # notch-safe on phones


if __name__ == "__main__":
    print(css())
