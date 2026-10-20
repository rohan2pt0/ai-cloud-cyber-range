"""UI AUDIT for the exercise portal: every screen, as every role, in dark and light, on a desktop and a 390 px phone.

A game is played first (scoring rounds, a red-team success, task answers, reports, judging, a password change) so every
screen has real content. Then, per role and screen: no page error, no text below WCAG AA contrast, no sideways scrolling on
the phone, and the role only gets its own menu. Screenshots of the main screens go to OUT_DIR.

    python3 exercise/tests/ui_audit.py [OUT_DIR]       (needs playwright + chromium; the sandbox journey runs it)
"""
import importlib.util
import json
import pathlib
import sys
import tempfile
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from exercise import engine, portal, scenario  # noqa: E402

_s = importlib.util.spec_from_file_location("gm_audit", ROOT / "guiding-map" / "tests" / "ui_audit.py")
_gm = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_gm)
CONTRAST_JS, EXE = _gm.CONTRAST_JS, _gm.exe
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(tempfile.gettempdir()) / "exercise-ui-audit"
VIEWS = {"blue": ["overview", "rules", "plan", "scorelog", "timeline", "incident", "sitrep", "myreports", "targets", "awareness", "news", "missions", "frameworks", "tracks", "progress", "creds", "restore"],
         "white": ["overview", "rules", "plan", "scorelog", "timeline", "judge-incident", "judge-sitrep", "judge-task", "control", "targets", "awareness", "news", "missions",
                   "frameworks", "tracks", "progress", "creds", "attack", "attacks"],
         "red": ["overview", "rules", "targets", "news", "attack", "attacks"]}


def seed(folder: pathlib.Path) -> tuple[engine.Game, dict]:
    tokens = engine.Game.create(folder, team=8)
    g = engine.Game(folder)
    g.start(time.time() - 200 * 60)
    rows = scenario.checks(g.scenario())
    for i in range(6):
        g.record_round(8, [(r, not (i == 3 and r["host"] == "www"), "ok" if i != 3 else "HTTP 500") for r in rows],
                       usersim=[("alex.sample", "ws3-1", True, "logged in"), ("bea.example", "ws3-2", i != 2, "wrong password")], ts=time.time() - (6 - i) * 600)
    g.attack(8, "red", "www", "Defaced the public website", "screenshot: index.html replaced", techniques=["T1491.002"])
    g.attack(8, "red-bot", "dns1", "Logged in as rangeadmin with the original password", "ssh rangeadmin@10.8.1.2", source="bot")
    s1 = g.submit_task(8, "blue-8", "p1-endpoints", "1. Change every default password.\n2. Limit remote login to the admin group.\n3. Send logs to the SIEM.")
    g.judge(s1, "white", 41, "accepted", "Good, add detection steps")
    g.use_hint(8, "blue-8", "p1-network")
    g.submit_task(8, "blue-8", "p2-repeat", "We rotated every credential the red team used.")
    g.abandon_task(8, "blue-8", "p2-data")
    tokens["blue-8:Asha"] = g.add_player(8, "Asha")
    i1 = g.file_incident(8, "blue-8:Asha", {"target": "www", "compromised": True, "chronology": "10:02 defaced; 10:20 restored from image",
                                            "impact": "Integrity of the public site", "source": "Malicious activity", "action_plan": "Rebuilt; password changed",
                                            "techniques": ["T1491.002", "T1078.001"], "defences": ["D3-CRO", "D3-FIM", "D3-RF"]})
    g.judge(i1, "white", 16, "accepted", "Clear timeline; attach the web log next time")
    g.file_incident(8, "blue-8", {"target": "dns1", "compromised": True, "chronology": "Unknown login as rangeadmin at 11:40"})
    g.file_sitrep(8, "blue-8", {"event_overview": "Two compromises, both contained.", "status": "All services up", "other_business": "None"})
    g.cred_change(8, "blue-8", "bea.example", "ws3-2", "Fiction-Pass-77!", "reused password found in a paste")
    g.special(8, "white", 5, "Shared an indicator with exercise control")
    g.plan_mark(8, "blue-8", "t0-inventory", "done")
    g.plan_mark(8, "blue-8", "t0-baseline", "blocked", "no access to the PLC yet")
    g.record_round(8, [(r, True, "ok") for r in rows], rules=[("www", "Green-team account works", True, "ok"),
                                                             ("dns1", "Green-team account works", False, "key login refused")])
    return g, tokens


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"page_errors": [], "contrast": [], "overflow": [], "checks": []}
    tmp = pathlib.Path(tempfile.mkdtemp())
    g, tokens = seed(tmp / "g")
    srv = portal.serve(g, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=EXE) if EXE else p.chromium.launch()
        for role, tok in (("blue", tokens["blue-8:Asha"]), ("white", tokens["white"]), ("red", tokens["red"])):
            for width in (1280, 390):
                pg = br.new_page(viewport={"width": width, "height": 900})
                pg.on("pageerror", lambda e, r=role: report["page_errors"].append(f"{r}: {e}"))
                pg.goto(base)
                pg.fill("#token", tok)
                pg.click("#loginform button")
                pg.wait_for_selector("#nav button")
                menu = pg.eval_on_selector_all("#nav button", "bs => bs.map(b => b.textContent)")
                report["checks"].append((f"{role}@{width}: menu has {len(menu)} entries", len(menu) == len(VIEWS[role]), menu))
                for theme in ("dark", "light"):
                    pg.evaluate("t => { document.documentElement.dataset.theme = t; }", theme)
                    for v in VIEWS[role]:
                        pg.evaluate("v => { sessionStorage.setItem('view', v); }", v)
                        pg.evaluate("v => window.dispatchEvent(new Event('x'))", v)
                        pg.reload()
                        pg.evaluate("t => { document.documentElement.dataset.theme = t; }", theme)
                        pg.wait_for_selector("main .card")
                        pg.wait_for_timeout(150)
                        heading = pg.text_content("main .card h1") or ""
                        report["checks"].append((f"{role}@{width}/{theme}/{v}: renders", bool(heading) and "error" not in heading.lower(), heading))
                        body = pg.text_content("main") or ""
                        report["checks"].append((f"{role}@{width}/{theme}/{v}: no raw object text", "[object " not in body and "undefined" not in body, body[:120]))
                        for item in pg.evaluate(CONTRAST_JS):
                            report["contrast"].append({"where": f"{role}@{width}/{theme}/{v}", **item})
                        if width == 390 and pg.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1"):
                            report["overflow"].append(f"{role}/{theme}/{v}")
                        if width == 1280 and (role, v) in (("blue", "timeline"), ("blue", "targets"), ("blue", "missions"), ("white", "judge-incident"), ("blue", "awareness"),
                                                              ("blue", "frameworks"), ("blue", "tracks"), ("blue", "progress"), ("blue", "incident")):
                            pg.screenshot(path=str(OUT / f"{role}-{v}-{theme}.png"), full_page=False)
                pg.close()
        br.close()
    srv.shutdown()
    failed = [c for c in report["checks"] if not c[1]]
    for c in failed:
        print("✗", c[0], str(c[2])[:150])
    for c in report["contrast"][:20]:
        print("contrast", c)
    print(f"checks {len(report['checks']) - len(failed)}/{len(report['checks'])}; page errors {len(report['page_errors'])}; "
          f"contrast failures {len(report['contrast'])}; phone overflow {len(report['overflow'])}")
    for e in report["page_errors"][:10]:
        print("page error:", e)
    for o in report["overflow"][:10]:
        print("overflow:", o)
    (OUT / "summary.json").write_text(json.dumps({**report, "checks": [list(c) for c in report["checks"]]}, indent=1, default=str))
    return 0 if not failed and not report["page_errors"] and not report["contrast"] and not report["overflow"] else 1


if __name__ == "__main__":
    sys.exit(main())
