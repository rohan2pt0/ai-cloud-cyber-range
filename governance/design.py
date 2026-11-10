"""The design standard's shared CSS (doc 100), made from governance/design.json so every page the estate generates
(cockpit, ready reckoner, control navigator) carries the same tokens and basics. Change a colour in design.json and
every one of them follows on its next build.

    python3 governance/design.py            print the CSS block
    python3 governance/design.py premium    print the premium language's CSS (design-premium-language)

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


# ---- The premium language (design.json "premium"): opt-in until the owner says yes to the three hero screens. ----
PREMIUM = STD["premium"]
FONT_FILE = pathlib.Path(__file__).resolve().parent.parent / PREMIUM["type"]["display_font_file"]


def font_face(src: str | None = None) -> str:
    """The display serif's @font-face. src: a URL to the .woff2 next to a hosted page; default a data: URI, so a page opened
    from disk (file://, where browsers refuse font files) still gets the serif and never a Times fallback."""
    import base64
    if src is None:
        src = "data:font/woff2;base64," + base64.b64encode(FONT_FILE.read_bytes()).decode()
    return ("@font-face{font-family:'Instrument Serif';font-style:normal;font-weight:400;font-display:swap;"
            f"src:url({src}) format('woff2')}}\n")


def finish_css() -> str:
    """One CSS layer per finish: a lit pebble from a radial highlight on the base and a thin bright rim. No images."""
    out = []
    for name, f in PREMIUM["finishes"].items():
        out.append(f".finish-{name}{{--f-base:{f['base']};--f-hi:{f['highlight']};--f-rim:{f['rim']}}}")
    out.append(".pebble{display:inline-block;width:var(--pebble,28px);height:var(--pebble,28px);border-radius:50%;"
               "background:radial-gradient(circle at 32% 26%,var(--f-hi) 0,var(--f-base) 62%);"
               "box-shadow:inset 0 0 0 1px var(--f-rim),inset 0 -3px 6px rgba(0,0,0,.25)}")
    return "".join(out) + "\n"


def premium_css(extra_light: dict | None = None, extra_dark: dict | None = None, font_src: str | None = None) -> str:
    """The premium tokens in both themes, the type, spacing, motion and material variables, the finishes, and the same
    basics css() gives (safe area, focus, reduced motion, 44 px targets)."""
    t, ty, mo, sp = PREMIUM["tokens"], PREMIUM["type"], PREMIUM["motion"], PREMIUM["space_px"]
    px = STD["rules"]["min_target_px"]
    shared = {"--font-display": ty["display"], "--font-text": ty["text"],
              **{f"--s{i + 1}": f"{v}px" for i, v in enumerate(sp)},
              "--r-card": f"{PREMIUM['radius_px']['card']}px", "--r-ctl": f"{PREMIUM['radius_px']['control']}px",
              "--t-fast": f"{mo['fast_ms']}ms", "--t-base": f"{mo['base_ms']}ms", "--t-slow": f"{mo['slow_ms']}ms", "--ease": mo["ease"],
              "--shadow": PREMIUM["material"]["shadow_light"]}
    light = _block({**t["light"], **shared, **(extra_light or {})})
    dark = _block({**t["dark"], "--shadow": PREMIUM["material"]["shadow_dark"], **(extra_dark or {})})
    return (font_face(font_src)
            + f":root{{{light}}}\n@media (prefers-color-scheme:dark){{:root{{{dark}}}}}\n"
            f"body{{font-family:var(--font-text);line-height:{ty['body_line_height']};"
            "padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)}\n"
            f".num,td.num,data,time{{font-variant-numeric:{ty['numbers']}}}\n"
            f".display{{font-family:var(--font-display);font-weight:400;letter-spacing:{ty['heading_tracking']}}}\n"
            "a{color:var(--accent);text-decoration:underline;text-underline-offset:3px}\n"
            ":focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:4px}\n"
            f"button,summary,.btn{{min-height:{px}px}}\n"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}\n"
            + finish_css() + glass_css() + buttons_css())


def glass_css() -> str:
    """Frosted glass for floating layers only (premium.material.glass): `.glass` on a light surface, `.glass-dark` on an
    obsidian bar. Blur only where the browser supports it; solid where it does not, or where the person asks for less
    transparency (prefers-reduced-transparency), so text keeps its contrast either way."""
    g = PREMIUM["material"]["glass"]
    blur = f"blur({g['blur_px']}px) saturate({g['saturate']})"
    return (f".glass{{background:var(--card);box-shadow:{g['rim_light']}}}.glass-dark{{background:#1b1a18}}"
            f"@supports ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){{"
            f".glass{{background:{g['light']};-webkit-backdrop-filter:{blur};backdrop-filter:{blur}}}"
            f".glass-dark{{background:{g['obsidian']};-webkit-backdrop-filter:{blur};backdrop-filter:{blur}}}"
            f"@media (prefers-color-scheme:dark){{.glass{{background:{g['dark']};box-shadow:{g['rim_dark']}}}}}}}"
            "@media (prefers-reduced-transparency:reduce){.glass{background:var(--card);-webkit-backdrop-filter:none;backdrop-filter:none}"
            ".glass-dark{background:#1b1a18;-webkit-backdrop-filter:none;backdrop-filter:none}}\n")


def buttons_css() -> str:
    """The three button kinds and their states (premium.buttons), high-contrast and forced-colours support, squircle
    corners where the browser can draw them, and a skip link. Shared by every page on the premium language."""
    b = PREMIUM["buttons"]
    cm = PREMIUM["contrast_more"]
    return (".btn-primary{background:var(--action);color:var(--on-action);border:1px solid var(--action);box-shadow:inset 0 0 0 1px var(--leaf);font-weight:600}"
            ".btn-secondary{background:transparent;color:var(--ink);border:1px solid var(--edge)}"
            ".btn-tertiary{background:none;border:0;color:var(--accent);text-decoration:underline;text-underline-offset:3px;padding:0;min-height:44px}"
            f".btn-primary,.btn-secondary{{border-radius:999px;padding:8px 20px;min-height:44px;cursor:pointer;transition:transform {b['press_ms']}ms var(--ease,ease),background-color 200ms var(--ease,ease)}}"
            f".btn-primary:active,.btn-secondary:active{{transform:scale({b['pressed_scale']})}}"
            f"button:disabled,.btn-primary:disabled,.btn-secondary:disabled{{opacity:{b['disabled_opacity']};cursor:not-allowed;transform:none}}"
            "[aria-busy=true]{position:relative;color:transparent!important;pointer-events:none}"
            "[aria-busy=true]::after{content:'';position:absolute;inset:0;margin:auto;width:16px;height:16px;border-radius:50%;"
            "border:2px solid var(--on-action);border-right-color:transparent;animation:sxspin .7s linear infinite}"
            ".btn-secondary[aria-busy=true]::after{border-color:var(--ink);border-right-color:transparent}"
            "@keyframes sxspin{to{transform:rotate(360deg)}}"
            ".skip{position:absolute;left:-9999px;top:8px;z-index:10000;background:var(--action);color:var(--on-action);padding:8px 16px;border-radius:999px}"
            ".skip:focus{left:16px}"
            f"@media (prefers-contrast:more){{:root{{{_block(cm['light'])}}}}}"
            f"@media (prefers-contrast:more) and (prefers-color-scheme:dark){{:root{{{_block(cm['dark'])}}}}}"
            "@media (forced-colors:active){.btn-primary,.btn-secondary,button,.card{border:1px solid ButtonText}"
            ":focus-visible{outline:2px solid Highlight}.pebble{forced-color-adjust:none}}"
            "@supports (corner-shape:squircle){.card,.btn-primary,.btn-secondary,button{corner-shape:squircle}}\n")


HAPTIC_JS = ("function securaxHaptic(kind){try{if(matchMedia('(prefers-reduced-motion: reduce)').matches||!navigator.vibrate"
             "||document.documentElement.classList.contains('gm-still'))return;"
             "navigator.vibrate(" + json.dumps({k: v for k, v in PREMIUM["haptics"].items() if k != "about"}, separators=(",", ":"))
             + "[kind]||0)}catch(e){}}"
             "document.addEventListener('click',function(e){var h=e.target.closest&&e.target.closest('[data-haptic]');"
             "if(h)securaxHaptic(h.getAttribute('data-haptic'))});")


HEAD = "<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>"   # notch-safe on phones


if __name__ == "__main__":
    import sys
    print(premium_css() if sys.argv[1:] == ["premium"] else css())
