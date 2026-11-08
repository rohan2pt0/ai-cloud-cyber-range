"""UI AUDIT for the product site: every page, in light and dark, on a laptop and a 390 px phone.

For website/index.html, website/assess/index.html, website/nbfc/index.html and website/personal/index.html, at 1280 px and
390 px in light and dark: no page error, no visible text below WCAG AA contrast (4.5:1, or 3:1 for large text; text that is
only emoji is skipped), and no sideways scrolling (documentElement.scrollWidth > clientWidth). Screenshots of each page go to
OUT_DIR.

    python3 website/tests/ui_audit.py [OUT_DIR]       (needs playwright + chromium)
"""
import importlib.util
import json
import pathlib
import re
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The contrast and browser plumbing lives in the Guiding Map audit; load it by path so the two stay one. Never a sibling
# import: this file is a plain script, not part of a package.
_s = importlib.util.spec_from_file_location("gm_audit", ROOT / "guiding-map" / "tests" / "ui_audit.py")
_gm = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_gm)
CONTRAST_JS, EXE = _gm.CONTRAST_JS, _gm.exe

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(tempfile.gettempdir()) / "site-ui-audit"

PAGES = [
    ("home", "index.html"),
    ("assess", "assess/index.html"),
    ("nbfc", "nbfc/index.html"),
    ("personal", "personal/index.html"),
]

# Emoji draw their own colours, so a computed text colour on a coloured card is not a real contrast failure. A string of
# only these (with joiners and variation selectors) is skipped; text with a real word in it is still measured.
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\U0001F1E6-\U0001F1FF\U00002600-\U000027BF\U00002B00-\U00002BFF\U0000FE0F\U0000200D]")


def _emoji_only(text: str) -> bool:
    t = "".join(text.split())
    return bool(t) and all(_EMOJI.fullmatch(ch) is not None for ch in t)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"page_errors": [], "contrast": [], "overflow": []}
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=EXE) if EXE else p.chromium.launch()
        for name, rel in PAGES:
            for width in (1280, 390):
                for scheme in ("light", "dark"):
                    where = f"{name}@{width}/{scheme}"
                    ctx = br.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
                    pg = ctx.new_page()
                    pg.on("pageerror", lambda e, w=where: report["page_errors"].append(f"{w}: {e}"))
                    pg.goto((ROOT / "website" / rel).as_uri())
                    pg.wait_for_timeout(300)
                    for item in pg.evaluate(CONTRAST_JS):
                        if _emoji_only(item["t"]):
                            continue
                        report["contrast"].append({"where": where, **item})
                    if pg.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth"):
                        report["overflow"].append(where)
                    pg.screenshot(path=str(OUT / f"{name}-{width}-{scheme}.png"), full_page=False)
                    ctx.close()
        br.close()
    for e in report["page_errors"]:
        print("page error:", e)
    for o in report["overflow"]:
        print("overflow:", o)
    for c in report["contrast"]:
        print("contrast", c["where"], c["t"], f"{c['ratio']}:1 (need {c['need']})", c["fg"], "on", c["bg"], "|", c["cls"] or c["style"])
    print(f"pages {len(PAGES) * 2 * 2}; page errors {len(report['page_errors'])}; contrast failures {len(report['contrast'])}; "
          f"overflow {len(report['overflow'])}")
    (OUT / "summary.json").write_text(json.dumps(report, indent=1, default=str))
    return 0 if not report["page_errors"] and not report["contrast"] and not report["overflow"] else 1


if __name__ == "__main__":
    sys.exit(main())
