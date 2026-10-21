"""KIT AUDIT: open each OS kit app (doc 95) in a real browser with realistic data, visit EVERY screen in dark and light mode,
at phone width, and measure: page errors, WCAG AA contrast of every visible text, and horizontal scroll at 390 px.
Exit 0 only when every app passes.

    python3 guiding-map/tests/kit_audit.py [OUT_DIR]       (needs playwright + chromium)
"""
import functools
import http.server
import importlib.util
import json
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

GM = pathlib.Path(__file__).resolve().parent.parent
_s = importlib.util.spec_from_file_location("gm_audit", GM / "tests" / "ui_audit.py")   # the same contrast measure as the Life OS audit
_gm = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_gm)
CONTRAST_JS, exe = _gm.CONTRAST_JS, _gm.exe
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/kit-audit")
APPS = [json.loads(p.read_text())["id"] for p in sorted((GM / "kit" / "editions").glob("*.json")) if not json.loads(p.read_text()).get("template")]
SEED = r"""() => { const K = window.OSK, t = K.ymd();
  K.set("profile", {name: "Asha", org: "Example Org", at: t});
  K.set("inbox", [{id: "a1", text: "Vendor renewal", at: t}, {id: "a2", text: "Board pack", at: t, kind: "action", next: "Draft the table", due: K.addDays(t, -1)}]);
  const rit = {}; for (let i = 0; i < 20; i++) rit[K.addDays(t, -i)] = i % 3 ? ["brief", "decide"] : ["brief"]; K.set("rituals", rit);
  const regs = (K.cfg("registers") || []);
  regs.forEach(r => { const row = {id: "r" + r.id, at: t}; r.fields.forEach(f => { row[f.id] = f.type === "scale" ? 5 : f.type === "number" ? 30 : f.type === "date" ? K.addDays(t, -2) : f.type === "select" ? f.options[0] : "Example " + f.label; }); K.set("reg." + r.id, [row]); });
  const sc = {}; ((K.cfg("scorecard") || {}).metrics || []).forEach((m, i) => { sc[m.id] = [{d: K.addDays(t, -40), v: m.base}, {d: t, v: (m.base + m.goal) / 2 + i}]; }); K.set("score", sc);
  const dims = ((K.cfg("wheel") || {}).dims || []); const s = {}; dims.forEach((d, i) => s[d.id] = 3 + i % 6); K.set("wheel", {s: s, at: t, hist: [{q: K.quarter(), s: s}]});
  K.set("started", K.addDays(t, -30)); K.set("~feed.govern", {maturity: 2, coverage: {basic: 55, standard: 20, advanced: 5}, budget: "Rs 2.2-6.9 Cr a year", at: t,
    top: [{what: "EDR on every endpoint", who: "Security engineering", when: "0-3 months", how_much: "Rs 50-80 L"}]});
  K.render(); }"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(GM))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port, fails = srv.server_address[1], []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for app in APPS:
            pg = br.new_page(viewport={"width": 390, "height": 844})
            errs = []
            pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{port}/{app}/index.html")
            pg.wait_for_function("() => window.OSK && document.getElementById('oskMain').innerHTML.length > 50")
            pg.evaluate(SEED)
            tabs = pg.evaluate("() => OSK.tabs().map(t => t.id)")
            for theme in ("dark", "light"):
                pg.evaluate(f"() => document.documentElement.setAttribute('data-theme', '{theme}')")
                for t in tabs:
                    pg.evaluate(f"() => OSK.go({json.dumps(t)})")
                    pg.wait_for_timeout(30)
                    if "This screen hit a problem" in pg.inner_text("#oskMain"):
                        fails.append(f"{app} {theme} {t}: the screen failed to render")
                    for c in pg.evaluate(CONTRAST_JS):
                        fails.append(f"{app} {theme} {t}: contrast {c['ratio']} < {c['need']} on {c['t']!r}")
                    wide = pg.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                    if wide > 1:
                        fails.append(f"{app} {theme} {t}: {wide}px horizontal scroll at phone width")
                pg.evaluate("() => OSK.go('today')")
                pg.screenshot(path=str(OUT / f"{app}-{theme}.png"), full_page=True)
            fails += [f"{app}: page error {e}" for e in errs]
            print(f"{app}: {len(tabs)} screens x 2 themes checked")
        br.close()
    srv.shutdown()
    for f in fails:
        print("✘ " + f)
    print("KIT AUDIT: " + ("PASS" if not fails else f"{len(fails)} problem(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
