#!/usr/bin/env python3
"""How much of the work Claude did, measured from git history, so you change your subscription on evidence, not on feel.

    ./securax ai share              this month and the two before it
    ./securax ai share --json       the same, for the cockpit

Every commit counts once, by who wrote it:
- **claude**: a `Co-Authored-By: Claude` trailer.
- **open models**: an `autobuild:` subject, or an `Assisted-by: SecuRAX` trailer (work done in `./securax opencode`, doc 83).
- **you**: anything else.

Merge commits are skipped. The goal is Claude at about a fifth of the commits (doc 23); the cockpit lights a caution lamp
above GOAL once a month has at least MIN_COMMITS commits. Commits are a proxy for effort, not tokens: a Claude commit can
be large. Standard library only. Exit codes: 0 ok, 1 not a git checkout.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOAL = 0.20
MIN_COMMITS = 10
SEP = "\x1e"


def kind(message: str) -> str:
    if re.search(r"^co-authored-by:\s*claude\b", message, re.I | re.M):
        return "claude"
    if message.lstrip().lower().startswith("autobuild:") or re.search(r"^assisted-by:\s*securax\b", message, re.I | re.M):
        return "cheap"
    return "you"


def commits(since: str, root: pathlib.Path = ROOT) -> list[tuple[str, str]]:
    """(YYYY-MM, message) for every non-merge commit since a date."""
    out = subprocess.run(["git", "-C", str(root), "log", "--no-merges", f"--since={since}", f"--format=%cs%n%B{SEP}"],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip() or "not a git checkout")
    rows = []
    for chunk in out.stdout.split(SEP):
        chunk = chunk.strip("\n")
        if chunk:
            day, _, msg = chunk.partition("\n")
            rows.append((day[:7], msg))
    return rows


def report(rows: list[tuple[str, str]]) -> list[dict]:
    months: dict[str, dict] = {}
    for m, msg in rows:
        months.setdefault(m, {"month": m, "claude": 0, "cheap": 0, "you": 0})[kind(msg)] += 1
    out = []
    for m in sorted(months, reverse=True):
        r = months[m]
        r["total"] = r["claude"] + r["cheap"] + r["you"]
        r["claude_share"] = round(r["claude"] / r["total"], 3) if r["total"] else 0.0
        r["over_goal"] = r["total"] >= MIN_COMMITS and r["claude_share"] > GOAL
        out.append(r)
    return out


def dependency(rep: list[dict]) -> dict:
    """The build's single point of failure: if, over the window, the open models wrote nothing while real work shipped, the
    estate can only be CHANGED by one external AI — whatever the runtime's own resilience. An inert open-model build (its CI
    secret OPENCODE_GO_API_KEY unset, so autobuild and the open-model review never run) is the usual cause."""
    total = sum(r["total"] for r in rep)
    open_models = sum(r["cheap"] for r in rep)
    claude = sum(r["claude"] for r in rep)
    return {"commits": total, "open_model_commits": open_models, "claude_commits": claude,
            "single_ai_dependency": total >= MIN_COMMITS and open_models == 0 and claude > 0}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    first = dt.date.today().replace(day=1)
    since = (first - dt.timedelta(days=62)).replace(day=1).isoformat()
    try:
        rep = report(commits(since))[:3]
    except RuntimeError as e:
        print(f"Cannot read history: {e}")
        return 1
    dep = dependency(rep)
    if "--json" in argv:
        print(json.dumps({"goal": GOAL, "months": rep, "dependency": dep}))
        return 0
    if not rep:
        print("No commits in the last three months.")
        return 0
    print(f"Who did the work (commits; goal: Claude at or under {GOAL:.0%})")
    for r in rep:
        print(f"  {r['month']}  Claude {r['claude']:>3}   open models {r['cheap']:>3}   you {r['you']:>3}   "
              f"→ Claude {r['claude_share']:.0%}" + ("  ⚠ over the goal" if r["over_goal"] else ""))
    if dep["single_ai_dependency"]:
        print("\n  ⚠ SINGLE POINT OF FAILURE (how the estate is BUILT): the open models wrote none of the last "
              f"{dep['commits']} commits, so only one external AI can change this estate today.")
        print("    The open-model build is inert until its CI secret is set: add OPENCODE_GO_API_KEY (doc 83, section 4),")
        print("    then `./securax autobuild \"task\"` and the open-model review run, and this line clears as they land commits.")
    print("Lower it: ./securax route \"task\" before you start; ./securax autobuild for everything it calls local.")
    print("Commits are a proxy for effort, not tokens. Change your plan only after two months under the goal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
