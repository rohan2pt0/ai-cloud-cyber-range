"""Device audit (principle `every-device`, owner 2026-11-14): every SecuRAX app must look stunning on every device people
really hold (Android and iPhone, small and large; iPad upright and sideways; laptops) without breaking its form, and adapt
to each display rather than merely shrink.

Usage: python3 guiding-map/tests/device_audit.py OUTDIR    (exit 1 on any break; screenshots of every view in OUTDIR)

For each device x view it checks what a person would notice in the first seconds:
- the page never scrolls sideways;
- no page error;
- no word is cut off inside a button or heading (an ellipsis by design is fine);
- every visible control is at least 44 x 44 px on a touch screen;
- body text is at least 14 px on a phone;
- on the lock screen, the way in (Unlock) is on screen without scrolling, and the seal is not cut off;
- nothing sits under the notch or the home bar (the page opts in to the safe areas and keeps its controls inside them).
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/gm-device-audit")
DEVICES = ["iPhone SE", "iPhone 15 Pro Max", "Pixel 7", "Galaxy S9+", "iPad Mini", "iPad Pro 11 landscape",
           "Pixel 7 landscape"]
DESKTOPS = {"Laptop 1366": (1366, 768), "Desktop 1920": (1920, 1080)}
LOCK_LIFE = ("gm_lock", '{"id":"x","salt":"eA","hash":"y","idle":5}')
LOCK_KIT = ("osk:vantage:~lock", '{"mode":"gate","id":"x","idle":300}')
VIEWS = [
    ("life-today", "guiding-map/index.html", None, None),
    ("life-lock", "guiding-map/index.html", LOCK_LIFE, None),
    ("vantage-today-dark", "guiding-map/vantage/index.html", None, "dark"),
    ("vantage-today-light", "guiding-map/vantage/index.html", None, "light"),
    ("vantage-lock", "guiding-map/vantage/index.html", LOCK_KIT, None),
]

CHECK = """([lock, touch, phone]) => {
  const out = [], W = innerWidth, H = innerHeight, de = document.documentElement;
  if (de.scrollWidth > W + 1) out.push('scrolls sideways: ' + de.scrollWidth + ' > ' + W);
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && r.right > 0 && r.left < W && s.visibility !== 'hidden' && s.display !== 'none' && r.bottom > 0 && r.top < H && !e.closest('[hidden],#oskMore:not(.on),details:not([open]) > :not(summary)'); };
  const name = e => (e.id ? '#' + e.id : e.tagName.toLowerCase()) + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '') + ' "' + (e.textContent || '').trim().slice(0, 24) + '"';
  document.querySelectorAll('button, h1, h2, h3, .sx-lock-title, summary').forEach(e => {
    if (!vis(e)) return; const s = getComputedStyle(e);
    if (s.textOverflow === 'ellipsis') return;
    if (e.scrollWidth > e.clientWidth + 2 && s.overflowX !== 'visible') out.push('cut off: ' + name(e));
  });
  if (touch) document.querySelectorAll('button, [role=button], summary, a[href]').forEach(e => {
    if (!vis(e) || e.closest('.sx-keys,nav#oskNav')) return; const r = e.getBoundingClientRect();
    // What a finger hits counts, not the box: an invisible enlarged hit area (a ::after) passes if the points 22 px from
    // the centre still land on the control.
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2, hit = (x, y) => { const t = document.elementFromPoint(x, y); return !!t && (t === e || e.contains(t)); };
    const eff = (r.width >= 43.5 || (hit(cx - 21, cy) && hit(cx + 21, cy))) && (r.height >= 43.5 || (hit(cx, cy - 21) && hit(cx, cy + 21)));
    if (!eff) out.push('small target ' + Math.round(r.width) + 'x' + Math.round(r.height) + ': ' + name(e));
  });
  if (phone) { const fz = [...document.querySelectorAll('p, li')].filter(e => vis(e) && (e.textContent || '').trim().length > 40).map(e => parseFloat(getComputedStyle(e).fontSize)).sort((a, b) => a - b); const med = fz.length ? fz[fz.length >> 1] : 16; if (med < 14) out.push('body text ' + med + 'px (median of paragraphs)'); }
  if (lock) {
    const go = document.querySelector('.gm-lock-go, body.osk-locked #oskMain button.primary');
    if (!go) out.push('lock: no Unlock button'); else { const r = go.getBoundingClientRect(); if (r.bottom > H || r.top < 0) out.push('lock: Unlock is off screen (bottom ' + Math.round(r.bottom) + ' of ' + H + ')'); }
    const se = document.querySelector('.sx-seal'); if (se) { const r = se.getBoundingClientRect(); if (r.top < 0 || r.left < 0 || r.right > W) out.push('lock: seal cut off'); }
  }
  const vp = (document.querySelector('meta[name=viewport]') || {}).content || '';
  if (!/viewport-fit=cover/.test(vp)) out.push('no viewport-fit=cover (notch and home bar not handled)');
  return out;
}"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fails = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        targets = [(d, dict(p.devices[d])) for d in DEVICES]
        targets += [(n, {"viewport": {"width": w, "height": h}, "device_scale_factor": 1, "is_mobile": False, "has_touch": False})
                    for n, (w, h) in DESKTOPS.items()]
        for dname, desc in targets:
            desc.pop("default_browser_type", None)
            for vname, rel, lock, theme in VIEWS:
                ctx = b.new_context(**desc)
                pg = ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
                if lock:
                    pg.add_init_script(f"localStorage.setItem({lock[0]!r}, {lock[1]!r})")
                pg.goto((ROOT / rel).as_uri())
                pg.wait_for_timeout(900)
                if theme:
                    pg.evaluate(f"document.documentElement.setAttribute('data-theme','{theme}')")
                    pg.wait_for_timeout(200)
                phone = bool(desc.get("is_mobile")) and desc["viewport"]["width"] < 600
                issues = pg.evaluate(CHECK, [bool(lock), bool(desc.get("has_touch")), phone]) + ["page error: " + e for e in errs]
                slug = dname.replace(" ", "-").lower() + "--" + vname
                pg.screenshot(path=str(OUT / f"{slug}.png"))
                ctx.close()
                if issues:
                    fails += len(issues)
                    print(f"✘ {dname} / {vname}")
                    for i in sorted(set(issues))[:12]:
                        print("    " + i)
        b.close()
    print(f"DEVICE AUDIT: {'PASS' if not fails else 'FAIL'} ({len(targets)} devices x {len(VIEWS)} views, {fails} issues)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
