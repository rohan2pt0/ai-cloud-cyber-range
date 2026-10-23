#!/usr/bin/env python3
"""Is SecuRAX making you better off? Visible progress, and the one next step (doc 93, the north star in AGENTS.md).

    ./securax progress            your life rhythm (Life OS), how much stronger the estate got, and the ONE next step
    ./securax progress --send     the same, short, to your phone (the weekly `progress` routine, Sundays 6:40pm)
    ./securax progress --json     for the cockpit

What it counts, in the last 30 days, and only what really happened:
- Your rhythm (Life OS): days you checked in, your last weekly review and your last quarterly check-in. A rhythm that slipped is
  named gently, with the two-minute way back. Read from the Life OS data on THIS machine; nothing leaves it.
- Stronger than before (antifragile): drills passed, failures the estate learned from and recovered, restores proven, open
  postmortem actions, and single points of failure still open.
- The one next step: the most useful thing not yet set up (./securax finish), so the estate grows to its full use one step
  at a time.
Standard library only. Exit codes: 0 always (it is a report).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "governance"))
HUB = os.environ.get("SECURAX_SYNC_URL", "http://127.0.0.1:8088/sync")
DAY = 86400
DATE_KEY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def _env(key: str) -> str:
    import continuity
    return continuity.env(key)


def life_state(fetch=None) -> dict | None:
    """The Life OS data held on this machine (the same copy your devices sync to). None when it cannot be read."""
    if fetch:
        return fetch()
    tok = next((t.strip() for t in _env("SYNC_TOKENS").split(",") if t.strip()), "")
    user = os.environ.get("PROGRESS_USER") or "me"
    req = urllib.request.Request(f"{HUB}/state?user={user}", headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:                      # noqa: S310 (this machine's own sync service)
            return json.loads(r.read())
    except (OSError, ValueError, urllib.error.HTTPError):
        return None


def _value(payload: dict, key: str):
    v = payload.get(key)
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return v
    return v


def rhythm(state: dict | None, now: float) -> dict:
    if not state:
        return {"known": False}
    payload, meta = state.get("payload") or {}, state.get("meta") or {}

    def ago(key: str) -> float | None:
        ts = meta.get(key)
        return None if not isinstance(ts, (int, float)) else round((now - ts / 1000) / DAY, 1)
    energy = _value(payload, "gm_energy")
    days = sorted(k for k in (energy or {}) if isinstance(energy, dict) and DATE_KEY.match(str(k)))
    cutoff = dt.date.fromtimestamp(now - 30 * DAY).isoformat()
    week_cut = dt.date.fromtimestamp(now - 7 * DAY).isoformat()
    return {"known": True, "checkins_30d": sum(d >= cutoff for d in days), "checkins_7d": sum(d >= week_cut for d in days),
            "last_checkin_days": ago("gm_energy"), "last_week_review_days": ago("gm_week_review"),
            "last_quarter_days": ago("gm_quarter_done"), "goals_touched_days": ago("gm_woop")}


def _jsonl(path: pathlib.Path) -> list[dict]:
    try:
        return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
    except (OSError, ValueError):
        return []


def stronger(now: float) -> dict:
    """What made the estate stronger in the last 30 days. Each number is something that really ran."""
    import continuity
    cut = now - 30 * DAY

    def recent(rows: list[dict]) -> list[dict]:
        out = []
        for r in rows:
            try:
                if dt.datetime.fromisoformat(r["when"]).timestamp() >= cut:
                    out.append(r)
            except (KeyError, ValueError):
                continue
        return out
    drills = recent(_jsonl(continuity.drills_path()) + _jsonl(home() / "autopilot" / "drills.jsonl"))
    restores = 0
    try:
        for line in (home() / "drills.log").read_text("utf-8").splitlines():
            if " drill ok " in line and dt.datetime.fromisoformat(line.split()[0].replace("Z", "+00:00")).timestamp() >= cut:
                restores += 1
    except (OSError, ValueError, IndexError):
        pass
    learned = {}
    try:
        learned = json.loads((home() / "autopilot" / "learned.json").read_text("utf-8"))
    except (OSError, ValueError):
        pass
    try:
        import postmortem
        open_actions = postmortem.actions()
    except Exception:  # noqa: BLE001 (a report never fails on one missing part)
        open_actions = []
    try:
        import resilience
        weak = len(resilience.blocking(resilience.analyse(resilience.cards())))
    except Exception:  # noqa: BLE001
        weak = None
    tts = _jsonl(home() / "continuity" / "tabletops.jsonl")
    adv_closed, adv_repeat = 0, 0                                         # the bounty/red-team learning loop (redteam/adversary.py)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("adversary_ledger", ROOT / "redteam" / "adversary.py")
        adv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adv)
        reg = adv.load()
        adv_closed, adv_repeat = adv.recent_closed(reg, dt.date.fromtimestamp(now)), len(adv.repeat_classes(reg))
    except Exception:  # noqa: BLE001 (a report never fails on one missing part)
        pass
    return {"drills_passed": sum(1 for r in drills if r.get("ok")), "drills_failed": sum(1 for r in drills if not r.get("ok")),
            "restores_proven": restores, "failures_learned": len(learned),
            "failures_recovered": sum(1 for v in learned.values() if not v.get("open")),
            "failures_open": sum(1 for v in learned.values() if v.get("open")),
            "actions_open": len(open_actions), "actions_late": sum(1 for a in open_actions if a["problems"]),
            "weak_points": weak, "tabletops": len(tts), "adversary_closed": adv_closed, "adversary_repeat": adv_repeat}


def next_step() -> dict | None:
    try:
        import finish
        left = [s for s in finish.status() if not s["done"]]
        return {"title": left[0]["title"], "gives": left[0]["gives"], "id": left[0]["id"], "left": len(left)} if left else None
    except Exception:  # noqa: BLE001
        return None


def nudges(r: dict) -> list[str]:
    """Gentle, specific, two minutes each. Never a lecture."""
    out = []
    if not r.get("known"):
        return ["Open the Life OS once on this machine (./securax open): your rhythm shows here from then on."]
    if r["checkins_7d"] == 0:
        out.append("No check-in this week. The way back is one: open the Life OS, two minutes, today.")
    if r["last_week_review_days"] is None or r["last_week_review_days"] > 8:
        out.append("Your weekly review is due: 15 minutes this Sunday keeps the week pointed at what matters to you.")
    if r["last_quarter_days"] is None or r["last_quarter_days"] > 95:
        out.append("A quarterly check-in (the wheel and your OKRs) is due: it is where purpose turns into this quarter's plan.")
    return out


def new_features(now: float, days: int = 30) -> list[dict]:
    """What arrived in the estate lately (features.json "added"), newest first, so a person hears about it and uses it."""
    try:
        feats = json.loads((ROOT / "features.json").read_text("utf-8"))["features"]
    except (OSError, ValueError, KeyError):
        return []
    cut = time.strftime("%Y-%m-%d", time.gmtime(now - days * 86400))
    fresh = [f for f in feats if str(f.get("added", "")) >= cut]
    return [{"name": f["name"], "cmd": f["open"]["cmd"], "added": f["added"], "outcome": f.get("outcome", "")}
            for f in sorted(fresh, key=lambda f: f["added"], reverse=True)]


def build(now: float | None = None, life=None) -> dict:
    now = now or time.time()
    r = rhythm(life_state(life), now)
    return {"rhythm": r, "stronger": stronger(now), "next": next_step(), "nudges": nudges(r), "new": new_features(now), "at": int(now)}


def report(p: dict, say=print) -> None:
    r, s, n = p["rhythm"], p["stronger"], p["next"]
    say("PROGRESS · is SecuRAX making you better off? The last 30 days, only what really happened.\n")
    say("Your rhythm (Life OS)")
    if r.get("known"):
        say(f"  check-ins: {r['checkins_7d']} this week, {r['checkins_30d']} in 30 days")
        for label, k in (("weekly review", "last_week_review_days"), ("quarterly check-in", "last_quarter_days"), ("goals updated", "goals_touched_days")):
            say(f"  {label}: " + ("not yet" if r[k] is None else f"{r[k]:.0f} day(s) ago"))
    for x in p["nudges"]:
        say("  → " + x)
    say("\nStronger than before (each one really ran)")
    say(f"  drills passed: {s['drills_passed']}" + (f", failed: {s['drills_failed']} (each one is now a fix to make)" if s["drills_failed"] else ""))
    say(f"  restores proven: {s['restores_proven']} · tabletop exercises: {s['tabletops']}")
    say(f"  failures the estate learned from: {s['failures_learned']}, recovered: {s['failures_recovered']}, still open: {s['failures_open']}")
    say(f"  adversary findings closed (bounty/red-team), now permanently probed: {s['adversary_closed']}"
        + (f"  ·  repeat-class rate: {s['adversary_repeat']} (a class came back)" if s.get('adversary_repeat') else "  ·  none has come back"))
    say(f"  postmortem actions open: {s['actions_open']}" + (f" ({s['actions_late']} late or without an owner)" if s["actions_late"] else ""))
    if s["weak_points"] is not None:
        say(f"  single points of failure still open: {s['weak_points']}" + ("  (./securax resilience)" if s["weak_points"] else ""))
    if p.get("new"):
        say("\nNew in the estate (the last 30 days): try one")
        for f in p["new"][:5]:
            say(f"  {f['added']}  {f['name']}: {f['cmd']}")
    say("\nThe one next step")
    if n:
        say(f"  {n['title']}: {n['gives']}")
        say(f"  how: ./securax finish {n['id']}   ({n['left']} optional step(s) left in all)")
    else:
        say("  Everything is set up. Keep the rhythm; the estate keeps itself.")


def short(p: dict) -> str:
    r, s, n = p["rhythm"], p["stronger"], p["next"]
    bits = []
    if r.get("known"):
        bits.append(f"{r['checkins_7d']} check-in(s) this week")
    bits.append(f"{s['drills_passed']} drill(s) passed, {s['failures_recovered']} failure(s) turned into fixes this month")
    msg = "Your week with SecuRAX: " + "; ".join(bits) + "."
    if p["nudges"]:
        msg += " " + p["nudges"][0]
    if n:
        msg += f" Next step: {n['title']} (./securax finish {n['id']})."
    if p.get("new"):
        msg += f" New: {p['new'][0]['name']} ({p['new'][0]['cmd']})" + (f" and {len(p['new']) - 1} more" if len(p["new"]) > 1 else "") + "."
    return msg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="progress", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    p = build()
    if a.json:
        print(json.dumps(p, indent=1))
    elif a.send:
        msg = short(p)
        subprocess.run([sys.executable, str(ROOT / "governance" / "notify.py"), "send", msg, "--title", "Your week with SecuRAX"],
                       capture_output=True, timeout=60)
        print(msg)
    else:
        report(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
