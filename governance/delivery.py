#!/usr/bin/env python3
"""How often do we ship, and how often does a change need a fix? The first two delivery keys, from git alone.

    python3 governance/delivery.py    ships a week and change-fail rate, over the last 4 weeks

Reads `git log --first-parent main --format=%H%x09%ct%x09%s`, falling back to HEAD when there is no main branch. A merge
is a commit whose subject ends with "(#<number>)". Ships a week = merges / 4. The change-fail rate is the share of those
merges whose subject starts with "Fix"/"Revert" (any case) or contains "hotfix". Lead time and time to restore need CI
history; they come in a later slice.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import time

MERGE_RE = re.compile(r"\(#\d+\)\s*$")
FIX_RE = re.compile(r"^(fix|revert)\b", re.IGNORECASE)
DAYS = 28
WEEKS = 4
DAY = 86400


def _log(cwd: pathlib.Path) -> list[tuple[str, int, str]] | None:
    """The first-parent log as (hash, time, subject) rows, or None when git is missing or cannot read the history."""
    for ref in ("main", "HEAD"):
        try:
            run = subprocess.run(["git", "-C", str(cwd), "log", "--first-parent", ref, "--format=%H%x09%ct%x09%s"],
                                 capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if run.returncode == 0:
            break
    else:
        return None
    rows = []
    for line in run.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        try:
            rows.append((parts[0], int(parts[1]), parts[2]))
        except ValueError:
            continue
    return rows


def compute(cwd: pathlib.Path | None = None, now: float | None = None) -> dict:
    now = now if now is not None else time.time()
    rows = _log(cwd or pathlib.Path.cwd())
    if rows is None:
        return {"merges": 0, "fixed": 0, "ships_per_week": 0.0, "change_fail_rate": 0.0, "git_ok": False}
    cut = now - DAYS * DAY
    merges = [r for r in rows if MERGE_RE.search(r[2]) and r[1] >= cut]
    ships = len(merges)
    fixed = sum(1 for r in merges if FIX_RE.match(r[2]) or "hotfix" in r[2].lower())
    return {"merges": ships, "fixed": fixed, "ships_per_week": ships / WEEKS,
            "change_fail_rate": fixed / ships if ships else 0.0, "git_ok": True}


def main(argv: list[str] | None = None) -> int:
    d = compute()
    print(f"{d['ships_per_week']:g} ships a week (last 4 weeks)")
    print(f"{round(d['change_fail_rate'] * 100)}% of merges needed a fix")
    print("Lead time and time to restore need CI history: they come in a later slice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
