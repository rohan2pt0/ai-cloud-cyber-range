#!/usr/bin/env python3
"""Mission control for the estate (doc 102): the management operating system, run by AI agents, the way a flight
control room or a military operations centre works.

    ./securax mission                  the mission board: observe, orient, decide, act (and the one thing that needs you)
    ./securax mission poll update      the Go/No-Go poll before an update: every console says GO or NO-GO, and why
    ./securax mission rules            the flight rules: each pre-agreed situation, what fires now, and who acts
    ./securax mission rules --act      the autopilot acts on the rules it may act on alone (safe, reversible steps)
    ./securax mission crew             who does what (RACI): every role is an AI agent, except the decisions kept for you
    ./securax mission --json

Ideas taken, and why:
- Flight rules (NASA mission control): the response to each known situation is agreed BEFORE it happens, so nobody has
  to improvise at 3 am. Here each rule names its trigger, its action, and whether an agent may act alone.
- Go/No-Go poll (launch control): before a risky step every console reports GO or NO-GO; one NO-GO holds the launch.
- Commander's intent and mission command (military doctrine): agents act alone inside a stated intent and limits, and
  escalate only what is outside them.
- OODA (observe, orient, decide, act): one loop, one screen.
- Two-person rule (maker-checker): anything that cannot be undone needs a second check (CI and review) or the owner.
Standard library only; it reads the cockpit's snapshot and the estate's own logs, and asks GitHub only for the poll.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "governance" / "mission.json").read_text("utf-8"))


def _env(key: str, default: str = "") -> str:
    v = os.environ.get(key, "")
    if v:
        return v
    try:
        m = re.search(rf"(?m)^{re.escape(key)}=(.*)$", (ROOT / "local" / "compose" / ".env").read_text("utf-8"))
        return m.group(1).strip() if m else default
    except OSError:
        return default


def cockpit() -> dict:
    """The cockpit's latest snapshot (./securax cockpit writes it): every vital sign by id."""
    try:
        d = json.loads((ROOT / "portal" / "cockpit.json").read_text("utf-8"))
        return {"ts": d.get("ts", 0), "metrics": {m["id"]: m for m in d.get("metrics", [])}}
    except (OSError, ValueError):
        return {"ts": 0, "metrics": {}}


# --------------------------------------------------------------------------------------------------- Go/No-Go consoles
def backups(now: float | None = None) -> dict:
    """The newest backup on disk: its age in hours, and whether the newest one was taken from data that looked encrypted."""
    now = now or time.time()
    d = pathlib.Path(_env("SECURAX_BACKUP_DIR", str(ROOT / "backups")))
    files = sorted(d.glob("securax-*.tar.gz*"), key=lambda p: p.stat().st_mtime, reverse=True) if d.is_dir() else []
    clean = [f for f in files if "-SUSPECT" not in f.name]
    return {"newest_suspect": bool(files) and "-SUSPECT" in files[0].name,
            "clean_age_h": round((now - clean[0].stat().st_mtime) / 3600, 1) if clean else None}


def main_is_green(slug: str = "", opener=urllib.request.urlopen) -> bool | None:
    """Did the last finished sandbox run on main pass? None when GitHub cannot be asked (offline is not a NO-GO)."""
    slug = slug or _brand("REPO_SLUG")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", slug or ""):
        return None
    url = f"https://api.github.com/repos/{slug}/actions/workflows/e2e.yml/runs?branch=main&status=completed&per_page=1"
    try:
        with opener(urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"}), timeout=10) as r:
            runs = json.loads(r.read()).get("workflow_runs") or []
    except Exception:  # noqa: BLE001 - offline or rate-limited: say so, do not block on it
        return None
    return None if not runs else runs[0].get("conclusion") == "success"


def _brand(key: str) -> str:
    try:
        m = re.search(rf"(?m)^{key}=(.*)$", (ROOT / "brand.env").read_text("utf-8"))
        return m.group(1).strip() if m else ""
    except OSError:
        return ""


def poll(op: str = "update", state: dict | None = None) -> dict:
    """Every console's GO or NO-GO for OP. STATE can be passed in (tests, or a caller that already measured)."""
    s = state if state is not None else {"backups": backups(), "ci_main": main_is_green(), "cockpit": cockpit()["metrics"]}
    m, b = s["cockpit"], s["backups"]
    consoles = []

    def say(name: str, go: bool, why: str) -> None:
        consoles.append({"console": name, "go": go, "why": why})

    say("ransomware", not b["newest_suspect"], "the newest backup found encrypted files: freeze until you check (./securax continuity show data-lost)"
        if b["newest_suspect"] else "no alarm")
    age = b["clean_age_h"]
    say("backup", age is not None and age <= 26, "a clean backup from the last day" if age is not None and age <= 26
        else ("no clean backup at all" if age is None else f"the newest clean backup is {age:.0f} h old"))
    disk = m.get("disk", {})
    say("disk", disk.get("status") != "red", f"disk: {disk.get('value', 'not measured')}")
    inc = m.get("incidents", {})
    say("incidents", inc.get("status") != "red", f"incidents: {inc.get('value', 'not measured')}")
    ci = s["ci_main"]
    say("main build", ci is not False, "the last nightly sandbox on main passed" if ci else
        ("GitHub could not be asked; going on the other consoles" if ci is None else "the last nightly sandbox on main FAILED: wait for the fix"))
    return {"op": op, "go": all(c["go"] for c in consoles), "consoles": consoles}


# ------------------------------------------------------------------------------------------------------- flight rules
def rules(state: dict | None = None) -> list[dict]:
    """Each flight rule with whether it fires now. A rule fires on the cockpit's vital signs or the backup console."""
    s = state if state is not None else {"backups": backups(), "cockpit": cockpit()["metrics"]}
    out = []
    for r in SPEC["flight_rules"]:
        m = s["cockpit"].get(r.get("metric", ""), {})
        if r.get("metric"):
            fires = m.get("status") in r.get("when", ["red"])
        elif r.get("when_backup") == "stale":
            a = s["backups"]["clean_age_h"]
            fires = a is None or a > 26
        elif r.get("when_backup") == "suspect":
            fires = s["backups"]["newest_suspect"]
        else:
            fires = False
        out.append({**r, "fires": bool(fires), "reading": m.get("value", "")})
    return out


def act(fired: list[dict], run=subprocess.run) -> list[dict]:
    """Do what the autopilot may do alone (pre-agreed, reversible, inside the intent). Everything else is only reported."""
    done = []
    for r in fired:
        if r["fires"] and r["who"] == "autopilot" and r.get("cmd"):
            rc = run(["bash", str(ROOT / "securax"), *r["cmd"]], capture_output=True, timeout=1800).returncode
            done.append({"rule": r["id"], "cmd": "./securax " + " ".join(r["cmd"]), "ok": rc == 0})
    return done


# -------------------------------------------------------------------------------------------------------- the board
def board() -> dict:
    ck = cockpit()
    b = backups()
    st = {"backups": b, "cockpit": ck["metrics"]}
    fired = [r for r in rules(st) if r["fires"]]
    worst = sorted((m for m in ck["metrics"].values() if m.get("status") in ("red", "amber")),
                   key=lambda m: (m["status"] != "red", -m.get("importance", 0)))
    return {"intent": SPEC["intent"], "observed_at": ck["ts"],
            "observe": {"red": sum(m["status"] == "red" for m in ck["metrics"].values()),
                        "amber": sum(m["status"] == "amber" for m in ck["metrics"].values())},
            "orient": [f"{m['label']}: {m['value']}" for m in worst[:3]],
            "decide": [{"rule": r["id"], "says": r["then"], "who": r["who"]} for r in fired],
            "you": [r["then"] for r in fired if r["who"] == "owner"][:1]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax mission", description=__doc__.split("\n\n")[0])
    ap.add_argument("what", nargs="?", default="board", choices=["board", "poll", "rules", "crew"])
    ap.add_argument("op", nargs="?", default="update")
    ap.add_argument("--act", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "poll":
        res = poll(a.op)
        if a.json:
            print(json.dumps(res, indent=1))
        else:
            print(f"Go/No-Go for {a.op}: {'GO' if res['go'] else 'NO-GO'}")
            for c in res["consoles"]:
                print(f"  {'GO   ' if c['go'] else 'NO-GO'} {c['console']:<11} {c['why']}")
        return 0 if res["go"] else 1
    if a.what == "rules":
        rs = rules()
        done = act(rs) if a.act else []
        if a.json:
            print(json.dumps({"rules": rs, "done": done}, indent=1))
        else:
            for r in rs:
                print(f"  {'FIRES' if r['fires'] else '  -  '} {r['id']:<22} {r['then']}  [{'agent acts' if r['who'] == 'autopilot' else 'needs you'}]")
            for d in done:
                print(f"  {'✔' if d['ok'] else '✘'} acted: {d['cmd']}")
        return 0
    if a.what == "crew":
        if a.json:
            print(json.dumps(SPEC["crew"], indent=1))
        else:
            for c in SPEC["crew"]:
                print(f"  {c['role']:<22} {c['agent']:<28} {c['does']}")
            print(f"\nKept for you: {SPEC['owner_decides']}")
        return 0
    res = board()
    if a.json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"Mission board. Intent: {res['intent']}")
    print(f"  Observe: {res['observe']['red']} red, {res['observe']['amber']} amber vital signs")
    print("  Orient:  " + ("; ".join(res["orient"]) or "nothing abnormal"))
    print("  Decide:  " + ("; ".join(f"{d['rule']} -> {d['says']}" for d in res["decide"]) or "no flight rule fires"))
    print("  You:     " + (res["you"][0] if res["you"] else "nothing needs you"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
