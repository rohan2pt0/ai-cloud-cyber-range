"""Which routines earn their place: the "prune what gives you nothing" rule, measured instead of remembered.

    ./securax routines prune          what to fix, what to switch off, and the exact command for each
    ./securax routines off ID         switch a routine off on this machine (kept in routines/.off.json, not in git)
    ./securax routines on ID          switch it back on

A system that only ever grows gets abandoned, so this check looks for four things:

- **Failing:** the last 2 runs failed. Fix it or switch it off; a failing routine trains you to ignore alerts.
- **Found nothing:** a report has run at least 4 times in 28 days and never flagged anything (no ✗, ⚠, FAIL, WARN, error, red
  or amber in its output). Keep it only if you read it.
- **Duplicate:** it runs exactly the same command as another routine.
- **Never ran:** it is switched on, but has no recorded run since history began more than 35 days ago. Usually the
  schedule is not installed (`./securax routines install`) or the machine is off at that hour.

Guards (update, backup, regulator watch, alerts, restore drill) are never suggested for pruning, because silence is their
success; only a failing guard is shown. Nudges are reminders to you, so only a duplicate nudge is shown.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

from .scheduler import DEFAULT_HISTORY, Job, parse_jobs

WINDOW_DAYS = 28
MIN_RUNS = 4
NEVER_DAYS = 35


def _when(stamp: str) -> dt.datetime:
    return dt.datetime.strptime(stamp[:16], "%Y-%m-%dT%H:%M")


def review(jobs: list[Job], hist: dict, now: Optional[dt.datetime] = None) -> list[dict]:
    """[{id, verdict: failing|nothing|duplicate|never, why, fix}] for the routines that need a decision."""
    now = now or dt.datetime.now()
    out = []
    starts = [_when(r["t"]) for runs in hist.values() for r in runs]
    history_age = (now - min(starts)).days if starts else 0
    by_cmd: dict[str, str] = {}
    for j in jobs:
        if not j.enabled:
            continue
        runs = hist.get(j.id, [])
        recent = [r for r in runs if (now - _when(r["t"])).days <= WINDOW_DAYS]
        key = json.dumps(j.command)
        if len(runs) >= 2 and all(r["code"] != 0 for r in runs[-2:]):
            out.append({"id": j.id, "verdict": "failing", "why": "the last 2 runs failed",
                        "fix": f"see routines/.log, then fix it, or  ./securax routines off {j.id}"})
        elif j.kind == "report" and len(recent) >= MIN_RUNS and not any(r["found"] for r in recent):
            out.append({"id": j.id, "verdict": "nothing", "why": f"{len(recent)} runs in {WINDOW_DAYS} days, nothing flagged",
                        "fix": f"keep it only if you read it; otherwise  ./securax routines off {j.id}"})
        elif key in by_cmd and j.kind != "guard":
            out.append({"id": j.id, "verdict": "duplicate", "why": f"runs the same command as {by_cmd[key]}",
                        "fix": f"./securax routines off {j.id}   (or give it its own command)"})
        elif not runs and history_age > NEVER_DAYS:
            out.append({"id": j.id, "verdict": "never", "why": f"no run recorded in the {history_age} days of history",
                        "fix": "./securax routines install   (and keep the machine on at that hour)"})
        by_cmd.setdefault(key, j.id)
    return out


def load_history(path: Optional[Path] = None) -> dict:
    try:
        return json.loads(Path(path or DEFAULT_HISTORY).read_text())
    except Exception:  # noqa: BLE001 - no history yet: nothing to judge
        return {}


def report(jobs_path: Optional[Path] = None, history_path: Optional[Path] = None) -> tuple[list[dict], int]:
    jobs, _ = parse_jobs(jobs_path)
    hist = load_history(history_path)
    return review(jobs, hist), sum(len(v) for v in hist.values())


def main(argv=None) -> int:
    items, runs = report()
    if not items:
        print("Every routine earns its place." + ("" if runs else " (No runs recorded yet: the check needs a few weeks of history.)"))
        return 0
    label = {"failing": "✗ failing", "nothing": "○ found nothing", "duplicate": "≡ duplicate", "never": "? never ran"}
    print(f"{len(items)} routine(s) to decide on (a system that only grows gets abandoned):")
    for it in items:
        print(f"  {label[it['verdict']]:<16} {it['id']:<22} {it['why']}")
        print(f"  {'':<16} → {it['fix']}")
    return 1 if any(i["verdict"] == "failing" for i in items) else 0
