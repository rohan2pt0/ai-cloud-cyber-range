#!/usr/bin/env python3
"""Mission control for the estate (doc 102): the management operating system, run by AI agents, the way a flight
control room or a military operations centre works.

    ./securax mission                  the mission board: observe, orient, decide, act (and the one thing that needs you)
    ./securax mission poll update      the Go/No-Go poll before an update: every console says GO or NO-GO, and why
    ./securax mission rules            the flight rules: each pre-agreed situation, what fires now, and who acts
    ./securax mission rules --act      the autopilot acts on the rules it may act on alone (safe, reversible steps)
    ./securax mission crew             who does what (RACI): every role is an AI agent, except the decisions kept for you
    ./securax mission aar              the week's after-action review: intended, happened, what differed and why, keep, change
    ./securax mission costs            what the estate costs: money (your own list), machine (disk) and model tokens
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
    res = {"op": op, "go": all(c["go"] for c in consoles), "consoles": consoles}
    if state is None:
        log_event({"kind": "poll", "op": op, "go": res["go"], "no_go": [c["console"] for c in consoles if not c["go"]]})
    return res


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def log_event(ev: dict, keep: int = 500) -> None:
    """One line in the mission log (the after-action review reads it). Bounded; a failed write never fails the caller."""
    try:
        p = home() / "mission.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = p.read_text("utf-8").splitlines()[-(keep - 1):] if p.exists() else []
        lines.append(json.dumps({"ts": int(time.time()), **ev}))
        tmp = p.with_suffix(".tmp")
        tmp.write_text("\n".join(lines) + "\n", "utf-8")
        os.replace(tmp, p)
    except OSError:
        pass


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


# ------------------------------------------------------------------------------------------------------ the cost view
def costs(measure=None, budget=None, subs_path: pathlib.Path | None = None) -> dict:
    """Discipline 6: what the estate costs, in money, machine and model tokens, from what it can measure. Money comes only
    from the owner's own list (vault/mission/subscriptions.json, private); nothing is guessed."""
    out = {"money": {}, "machine": {}, "tokens": {}}
    sp = subs_path or ROOT / "vault" / "mission" / "subscriptions.json"
    try:
        subs = json.loads(sp.read_text("utf-8"))
        for row in subs:
            cur = str(row.get("currency", "INR"))
            out["money"][cur] = round(out["money"].get(cur, 0) + float(row.get("per_month", 0)), 2)
        out["money_items"] = [str(r.get("name", "")) for r in subs]
    except (OSError, ValueError, TypeError, AttributeError):
        out["money_note"] = ('not set: list what you pay for in vault/mission/subscriptions.json, e.g. '
                             '[{"name": "OpenCode Go", "per_month": 10, "currency": "USD"}]')
    try:
        if measure is None:
            spec = __import__("importlib.util").util.spec_from_file_location("securax_storage_m", ROOT / "governance" / "storage.py")
            st = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(st)
            measure = st.measure
        m = measure()
        out["machine"] = {"estate_gb": round(m.get("estate_bytes", 0) / 1e9, 2), "backups_gb": round(m["backups"]["bytes"] / 1e9, 2),
                          "disk_free_pct": m["disk"]["free_pct"]}
    except Exception as e:  # noqa: BLE001 - a view, never a failure
        out["machine"] = {"note": f"not measured: {e}"[:120]}
    try:
        rep = budget() if budget else _budget()
        out["tokens"] = {"this_month": sum(int(r.get("month_used", 0)) for r in rep.get("callers", [])), "callers": len(rep.get("callers", []))}
    except Exception:  # noqa: BLE001 - the gateway may be off or need a key
        out["tokens"] = {"note": "the gateway did not answer (is the estate up?)"}
    return out


def _budget() -> dict:
    key = _env("SECURAX_GATEWAY_KEY")
    req = urllib.request.Request("http://127.0.0.1:8080/v1/budget", headers={"Authorization": f"Bearer {key}"} if key else {})
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.loads(r.read())


# ------------------------------------------------------------------------------------------------ after-action review
def _stamp_ts(stamp: str) -> float:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return time.mktime(time.strptime(stamp[:19], fmt))
        except ValueError:
            continue
    return 0.0


def aar(now: float | None = None, days: int = 7) -> dict:
    """The week's after-action review (army practice): what was intended, what happened, what differed and why, what to
    keep and what to change. Drafted from the estate's own records; nothing is sent anywhere."""
    now = now or time.time()
    since = now - days * 86400
    out = {"intended": SPEC["intent"], "happened": {}, "differed": [], "keep": [], "change": []}
    try:
        hist = json.loads((ROOT / "routines" / ".history.json").read_text("utf-8"))
    except (OSError, ValueError):
        hist = {}
    runs = fails = 0
    for job, rs in hist.items():
        week = [r for r in rs if _stamp_ts(str(r.get("t", ""))) >= since]
        bad = [r for r in week if r.get("code")]
        runs, fails = runs + len(week), fails + len(bad)
        if bad:
            out["differed"].append(f"routine {job} failed {len(bad)} of {len(week)} time(s); last words: {(bad[-1].get('tail') or '')[-120:]}")
            out["change"].append(f"fix the routine {job} (./securax autopilot learn has its postmortem draft)")
    out["happened"]["routine runs"] = runs
    out["happened"]["routine failures"] = fails
    outages = 0
    try:
        for line in (ROOT / "watch.log").read_text("utf-8").splitlines():
            if "NOT READY" in line and _stamp_ts(line[:19]) >= since:
                outages += 1
    except OSError:
        pass
    out["happened"]["outages the watchdog healed"] = outages
    if outages:
        out["differed"].append(f"the estate was not ready {outages} time(s) and the watchdog healed it")
    holds = []
    try:
        for line in (home() / "mission.jsonl").read_text("utf-8").splitlines():
            ev = json.loads(line)
            if ev.get("kind") == "poll" and ev.get("ts", 0) >= since and not ev.get("go"):
                holds.append(ev)
    except (OSError, ValueError):
        pass
    out["happened"]["updates held by Go/No-Go"] = len(holds)
    for h in holds[-3:]:
        out["differed"].append(f"an {h.get('op')} was held: NO-GO from {', '.join(h.get('no_go', []))}")
    b = backups(now)
    out["happened"]["newest clean backup (hours old)"] = b["clean_age_h"]
    if b["clean_age_h"] is not None and b["clean_age_h"] <= 26 and not b["newest_suspect"]:
        out["keep"].append("daily backups are fresh and clean")
    else:
        out["change"].append("get a clean backup again (./securax backup; ./securax doctor says why it fails)")
    try:
        lessons = subprocess.run(["git", "-C", str(ROOT), "log", f"--since={days}.days", "--format=%s", "--", "LESSONS.md"],
                                 capture_output=True, text=True, timeout=20).stdout.strip().splitlines()
    except (OSError, subprocess.SubprocessError):
        lessons = []
    out["happened"]["lessons recorded"] = len(lessons)
    if not runs:
        out["change"].append("no routine ran this week: is the scheduler running? (./securax routines list shows the jobs; ./securax go installs the schedule)")
    elif not fails and not outages and not holds:
        out["keep"].append("a quiet week: every routine ran, nothing needed healing, nothing was held")
    return out


def aar_markdown(r: dict, week: str) -> str:
    lines = [f"# After-action review, week {week}", "", f"**Intended:** {r['intended']}", "", "## What happened"]
    lines += [f"- {k}: {v}" for k, v in r["happened"].items()]
    for title, key in (("What differed, and why", "differed"), ("Keep", "keep"), ("Change", "change")):
        lines += ["", f"## {title}"] + ([f"- {x}" for x in r[key]] or ["- nothing"])
    return "\n".join(lines) + "\n"


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


def html_card(metrics: list[dict], b: dict | None = None) -> str:
    """The mission board as one folded line in the Command Center (doc 102): the update's Go/No-Go, the rules firing, and the one
    thing that needs the owner. It uses the metrics the cockpit has just measured and asks nothing over the network (the main
    build is asked by the update itself)."""
    import html
    E = html.escape
    st = {"backups": backups() if b is None else b, "cockpit": {m["id"]: m for m in metrics}, "ci_main": None}
    consoles = [c for c in poll("update", st)["consoles"] if c["console"] != "main build"]
    no_go = [c for c in consoles if not c["go"]]
    fired = [r for r in rules(st) if r["fires"]]
    yours = [r for r in fired if r["who"] == "owner"]
    line = ("NO-GO for the nightly update: " + ", ".join(c["console"] for c in no_go)) if no_go else "GO for the nightly update"
    line += f" · {len(fired)} flight rule{'s' if len(fired) != 1 else ''} firing · " + (f"needs you: {yours[0]['then']}" if yours else "nothing needs you")
    rows = "".join(f"<li>{'✔' if c['go'] else '✘'} " + E(c["why"] if c["why"].startswith(c["console"] + ":") else f"{c['console']}: {c['why']}")
                   + "</li>" for c in consoles)
    acts = "".join(f"<li><b>{E(r['id'])}</b> ({'you' if r['who'] == 'owner' else 'the autopilot acts'}): {E(r['then'])}</li>" for r in fired)
    return (f"<details class='card panel' id='mission'><summary><b>Mission</b> <span class='muted'>· {E(line)}</span></summary>"
            f"<p class='muted'>{E(SPEC['intent'])}</p><ul>{rows}</ul>" + (f"<ul>{acts}</ul>" if acts else "")
            + "<p class='muted'>The whole board: <code>./securax mission</code></p></details>").replace("https://", "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax mission", description=__doc__.split("\n\n")[0])
    ap.add_argument("what", nargs="?", default="board", choices=["board", "poll", "rules", "crew", "aar", "costs"])
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
    if a.what == "costs":
        c = costs()
        if a.json:
            print(json.dumps(c, indent=1))
        else:
            print("What the estate costs (discipline 6):")
            print("  money:   " + (", ".join(f"{v} {k} a month" for k, v in c["money"].items()) or c.get("money_note", "")))
            mc = c["machine"]
            print("  machine: " + (f"{mc['estate_gb']} GB used by the estate ({mc['backups_gb']} GB of it backups); disk {mc['disk_free_pct']}% free"
                                   if "estate_gb" in mc else mc.get("note", "")))
            tk = c["tokens"]
            print("  tokens:  " + (f"{tk['this_month']:,} this month across {tk['callers']} caller(s)" if "this_month" in tk else tk.get("note", "")))
        return 0
    if a.what == "aar":
        r = aar()
        week = time.strftime("%G-W%V")
        md = aar_markdown(r, week)
        out = ROOT / "vault" / "mission" / f"aar-{week}.md"       # private: vault/ is never committed
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md, "utf-8")
        except OSError:
            out = None
        print(json.dumps(r, indent=1) if a.json else md + (f"\n(saved: vault/mission/{out.name})" if out else ""))
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
