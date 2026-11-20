"""DEMO: the cyber range portal with a played-out exercise, made of dummy data, in one command. No Docker, no model.

    python3 -m exercise.demo [--port 8000] [--host 0.0.0.0] [--out DEMO-TOKENS.txt]

It creates a throwaway exercise (team 8, the sample scenario), plays it like a real morning: six scoring rounds with one
outage, a website defacement and a red-team bot login, a hint, tasks submitted and judged, an incident report and a
situation report, a credential change and a plan with one blocked step. Then it serves the portal and prints one sign-in
token per role (blue team, white team / judges, red team), also written to --out, so a presenter signs in from a phone.
Every name, address and password in it is fictional. Nothing is kept: the game lives in a temporary folder.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import tempfile
import time

from exercise import engine, portal, scenario


def seed(folder: pathlib.Path) -> tuple[engine.Game, dict]:
    tokens = engine.Game.create(folder, team=8)
    g = engine.Game(folder)
    g.start(time.time() - 200 * 60)
    rows = scenario.checks(g.scenario())
    for i in range(6):
        g.record_round(8, [(r, not (i == 3 and r["host"] == "www"), "ok" if i != 3 else "HTTP 500") for r in rows],
                       usersim=[("alex.sample", "ws3-1", True, "logged in"), ("bea.example", "ws3-2", i != 2, "wrong password")],
                       ts=time.time() - (6 - i) * 600)
    g.attack(8, "red", "www", "Defaced the public website", "screenshot: index.html replaced", techniques=["T1491.002"])
    g.attack(8, "red-bot", "dns1", "Logged in as rangeadmin with the original password", "ssh rangeadmin@10.8.1.2", source="bot")
    s1 = g.submit_task(8, "blue-8", "p1-endpoints", "1. Change every default password.\n2. Limit remote login to the admin group.\n3. Send logs to the SIEM.")
    g.judge(s1, "white", 41, "accepted", "Good, add detection steps")
    g.use_hint(8, "blue-8", "p1-network")
    g.submit_task(8, "blue-8", "p2-repeat", "We rotated every credential the red team used.")
    tokens["blue-8:Asha"] = g.add_player(8, "Asha")
    i1 = g.file_incident(8, "blue-8:Asha", {"target": "www", "compromised": True, "chronology": "10:02 defaced; 10:20 restored from image",
                                            "impact": "Integrity of the public site", "source": "Malicious activity",
                                            "action_plan": "Rebuilt; password changed", "techniques": ["T1491.002", "T1078.001"],
                                            "defences": ["D3-CRO", "D3-FIM", "D3-RF"]})
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="exercise.demo", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    g, tokens = seed(pathlib.Path(tempfile.mkdtemp(prefix="securax-demo-")) / "game")
    srv = portal.serve(g, host=a.host, port=a.port)
    lines = ["SecuRAX cyber range demo (dummy data). Sign in with one token per role:",
             f"  Blue team (defenders): {tokens['blue-8:Asha']}",
             f"  White team (judges, exercise control): {tokens['white']}",
             f"  Red team (attackers): {tokens['red']}",
             f"Portal: http://{a.host}:{srv.server_address[1]}/"]
    print("\n".join(lines), flush=True)
    if a.out:
        pathlib.Path(a.out).write_text("\n".join(lines) + "\n", "utf-8")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
