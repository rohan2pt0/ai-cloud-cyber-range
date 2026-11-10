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


# The owner's UI rules a browser can measure (doc 100; queue ui-rules-lint): 44 px tap targets, 16 px inputs, the right
# keyboard on number/phone/e-mail fields, body line height 1.4-1.6, no pure-black backgrounds, underlined links in running
# text, at most 75 characters a line, nothing that only a mouse hover reveals, and numeric right-aligned. Other audits load this file by path and reuse UI_RULES_JS.
UI_RULES_JS = r"""() => {
  const out = [];
  const vis = e => e.offsetParent && e.getBoundingClientRect().width > 0 && !e.closest('details:not([open]) > :not(summary)');
  const label = e => (e.textContent || e.getAttribute('aria-label') || e.name || e.id || '').trim().slice(0, 30);
  // 1. tap targets: buttons and stand-alone links (not links inside running text) at least 44 x 44
  document.querySelectorAll('button, [role=button], a.btn, summary, input[type=checkbox], input[type=radio], select').forEach(e => {
    if (!vis(e)) return; if (getComputedStyle(e).display === 'inline' || e.classList.contains('gm-term')) return;   // WCAG 2.5.8: a target inside a line of text (or an inline help term) is exempt
    const t = (e.type === 'checkbox' || e.type === 'radio') ? (e.closest('label') || e) : e; const r = t.getBoundingClientRect();
    if (r.height < 43.5 || r.width < 43.5) out.push(['tap-target', label(e), Math.round(r.width) + 'x' + Math.round(r.height), (e.className && String(e.className).slice(0, 30)) || e.tagName]);
  });
  // 2. inputs at 16 px or more (smaller makes a phone zoom in)
  document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=hidden]), select, textarea').forEach(e => {
    if (vis(e) && parseFloat(getComputedStyle(e).fontSize) < 16) out.push(['input-font', label(e), getComputedStyle(e).fontSize]);
  });
  // 3. the right keyboard: number, phone and e-mail fields say so (type or inputmode)
  document.querySelectorAll('input[type=text], input:not([type])').forEach(e => {
    const hint = ((e.name || '') + ' ' + (e.id || '') + ' ' + (e.placeholder || '') + ' ' + (e.getAttribute('aria-label') || '')).toLowerCase();
    if (vis(e) && /phone|mobile|email|e-mail|amount|age|number|count|pin\b|otp/.test(hint) && !e.getAttribute('inputmode')) out.push(['keyboard', label(e) || hint.slice(0, 30), 'no inputmode']);
  });
  // 4. body text: line height 1.4-1.6 for paragraphs of running text
  document.querySelectorAll('p, li').forEach(e => {
    if (!vis(e) || (e.textContent || '').trim().length < 80) return;
    const cs = getComputedStyle(e), lh = parseFloat(cs.lineHeight) / parseFloat(cs.fontSize);
    if (lh && (lh < 1.35 || lh > 1.75)) out.push(['line-height', label(e), lh.toFixed(2)]);
  });
  // 5. never pure black backgrounds
  [document.documentElement, document.body, ...document.querySelectorAll('main, section, header, footer, .card')].forEach(e => {
    if (e && /^rgba?\(0, 0, 0(, 1)?\)$/.test(getComputedStyle(e).backgroundColor)) out.push(['pure-black', e.tagName, 'background is #000']);
  });
  // 6. links in running text are underlined (colour alone is not enough)
  document.querySelectorAll('p a, li a').forEach(e => {
    if (!vis(e) || e.classList.contains('btn') || e.closest('nav, header, footer, .nav, .menu, .foot, [role=navigation]')) return;
    if (!/underline/.test(getComputedStyle(e).textDecorationLine)) out.push(['link-underline', label(e), 'not underlined']);
  });
  // 7. line length: running text averages at most 75 characters a line (45-75 is the comfortable measure; on a phone
  //    the screen sets the lower bound, so only the upper one is held). Lines are counted from the text's own boxes.
  document.querySelectorAll('p, li, div').forEach(e => {
    const text = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (e.closest('.banner, [role=banner], nav, header')) return;   // a one-line announcement strip or the menu is not running text
    if (!vis(e) || text.length < 90 || e.querySelector('p, li, ul, ol, pre, table, code, div, button, input, select')) return;
    if (e.tagName === 'DIV' && [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim().length < 30) return;   // a leaf block of running text
    const rg = document.createRange(); rg.selectNodeContents(e);
    const tops = new Set([...rg.getClientRects()].filter(r => r.width > 1).map(r => Math.round(r.top)));
    const per = tops.size ? text.length / tops.size : 0;
    if (tops.size && per > 75) out.push(['line-length', label(e), Math.round(per) + ' chars a line']);
  });
  // 8. no hover-only controls: what a ':hover' rule reveals must already be visible without a mouse (touch has none)
  const seen = new Set();
  [...document.styleSheets].forEach(sh => { let rules; try { rules = sh.cssRules; } catch (x) { return; }
    const walk = list => [...list].forEach(r => {
      if (r.cssRules && !r.selectorText) { walk(r.cssRules); return; }
      if (!r.selectorText || !/:hover/.test(r.selectorText)) return;
      const st = r.style, reveals = st.opacity === '1' || st.visibility === 'visible' || (st.display && st.display !== 'none') || st.pointerEvents === 'auto';
      if (!reveals) return;
      r.selectorText.split(',').filter(x => /:hover\s*\S/.test(x)).forEach(sel => {
        const target = sel.replace(/:hover/g, '').trim(); let els = [];
        try { els = [...document.querySelectorAll(target)]; } catch (x) { return; }
        els.forEach(el => { if (seen.has(el) || !el.offsetParent && getComputedStyle(el).display !== 'none') return;
          const cs = getComputedStyle(el);
          if (!el.matches('button, a, [role=button], input, select, summary') && !el.querySelector('button, a, [role=button]')) return;
          if (cs.opacity === '0' || cs.visibility === 'hidden' || cs.display === 'none' || cs.pointerEvents === 'none') { seen.add(el); out.push(['hover-only', label(el), sel.trim().slice(0, 50)]); }
        });
      });
    });
    walk(rules);
  });
  // 9. numbers in tables line up: a numeric cell (money, a count, a percent) is right-aligned so the digits compare
  const num = /^[-+]?[₹$]?\s?[\d,]+(\.\d+)?\s?(%|[A-Za-z]{1,3})?$/;
  document.querySelectorAll('tbody td, tbody th').forEach(e => {
    if (!vis(e) || !num.test((e.textContent || '').trim())) return;
    const ta = getComputedStyle(e).textAlign; if (ta !== 'right' && ta !== 'end') out.push(['numeric-align', label(e), ta]);
  });
  return out;
}"""

NAV_OVERLAP_JS = """() => { const b = document.querySelector('.nav .brand'); if (!b) return false;
  const br = b.getBoundingClientRect();
  return [...document.querySelectorAll('.nav .wrap > ul > li, .nav .wrap > .btn, .nav .wrap > .menu > summary')]
    .filter(e => !e.closest('details:not([open]) > :not(summary)') && e.offsetParent && e.getBoundingClientRect().width > 0)
    .some(e => e.getBoundingClientRect().left < br.right - 0.5); }"""


def _emoji_only(text: str) -> bool:
    t = "".join(text.split())
    return bool(t) and all(_EMOJI.fullmatch(ch) is not None for ch in t)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"page_errors": [], "contrast": [], "overflow": [], "rules": []}
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
                    for rule, what, value in pg.evaluate(UI_RULES_JS):
                        report["rules"].append(f"{where}: {rule}: {what} ({value})")
                    # the menu bar: nothing in the visible bar may run under the brand (the byline once covered "How it works")
                    if pg.evaluate(NAV_OVERLAP_JS):
                        report["overflow"].append(where + " (menu bar: an item runs under the brand)")
                    pg.screenshot(path=str(OUT / f"{name}-{width}-{scheme}.png"), full_page=False)
                    ctx.close()
        br.close()
    for e in report["page_errors"]:
        print("page error:", e)
    for o in report["overflow"]:
        print("overflow:", o)
    for r in report["rules"]:
        print("ui rule:", r)
    for c in report["contrast"]:
        print("contrast", c["where"], c["t"], f"{c['ratio']}:1 (need {c['need']})", c["fg"], "on", c["bg"], "|", c["cls"] or c["style"])
    print(f"pages {len(PAGES) * 2 * 2}; page errors {len(report['page_errors'])}; contrast failures {len(report['contrast'])}; "
          f"overflow {len(report['overflow'])}; ui-rule breaks {len(report['rules'])}")
    (OUT / "summary.json").write_text(json.dumps(report, indent=1, default=str))
    return 0 if not report["page_errors"] and not report["contrast"] and not report["overflow"] and not report["rules"] else 1


if __name__ == "__main__":
    sys.exit(main())
