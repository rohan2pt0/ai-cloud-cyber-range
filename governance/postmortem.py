#!/usr/bin/env python3
"""Blameless postmortems (Amazon's Correction of Error, Google SRE): after anything breaks, write down what happened, why,
and the MECHANISM that stops it happening again (good intentions do not count), then track those actions until done.

    ./securax postmortem new "Chat down after update" [--severity sev2]   writes vault/postmortems/<date>-<slug>.md
    ./securax postmortem list                                              every postmortem, with its open actions
    ./securax postmortem actions                                           open actions; overdue or ownerless ones first

An action is a checklist line:  - [ ] <what> — owner: <who> — due: YYYY-MM-DD   ([x] when done).
`actions` exits 1 when one is overdue or has no owner or due date, so a routine can nag about it.
Stays in vault/ (private, in your backups, never in git). Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIR = ROOT / "vault" / "postmortems"
ACTION = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(.+)$")
OWNER = re.compile(r"owner:\s*([^—|]+?)\s*(?:—|\||$)", re.I)
DUE = re.compile(r"due:\s*(\d{4}-\d{2}-\d{2})", re.I)

TEMPLATE = """# Postmortem: {title}

- **Date:** {date}  ·  **Severity:** {sev}  ·  **Status:** draft
- **Blameless:** we look for the gaps in the system that let a reasonable person make this mistake, not for someone to blame.

## Impact
What did people experience, for how long, and how many were affected? (numbers, not adjectives)

## Timeline (IST)
- HH:MM — first sign
- HH:MM — noticed by (alert / person)
- HH:MM — mitigated
- HH:MM — fully resolved

## What happened

## Why: five whys
1. Why did it happen?
2. Why was that possible?
3. Why was that not caught earlier?
4. Why did the safeguard not apply?
5. Why does the system allow that? (this is usually the real cause)

## What went well

## Where we were lucky

## Actions (mechanisms, not intentions: a test, a check, an alert, a default, an automation)
- [ ] Add a test or fitness check that fails if this happens again — owner: me — due: {due}
- [ ] Make the alert fire earlier, or make the failure impossible by default — owner: me — due: {due}

## Lessons for the docs
"""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "incident"


def new(title: str, sev: str, today: dt.date | None = None, folder: pathlib.Path | None = None) -> pathlib.Path:
    folder = folder or DIR
    today = today or dt.date.today()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{today.isoformat()}-{slug(title)}.md"
    n = 2
    while path.exists():
        path = folder / f"{today.isoformat()}-{slug(title)}-{n}.md"
        n += 1
    path.write_text(TEMPLATE.format(title=title.strip(), date=today.isoformat(), sev=sev,
                                    due=(today + dt.timedelta(days=14)).isoformat()), "utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def actions(folder: pathlib.Path | None = None, today: dt.date | None = None) -> list[dict]:
    """Every OPEN action across all postmortems, with what is wrong with it (overdue / no owner / no due date)."""
    folder = folder or DIR
    today = today or dt.date.today()
    out = []
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        for line in f.read_text("utf-8").splitlines():
            m = ACTION.match(line)
            if not m or m.group(1).lower() == "x":
                continue
            text, problems = m.group(2), []
            owner, due = OWNER.search(text), DUE.search(text)
            if not owner or not owner.group(1).strip():
                problems.append("no owner")
            if not due:
                problems.append("no due date")
            elif dt.date.fromisoformat(due.group(1)) < today:
                problems.append(f"overdue since {due.group(1)}")
            out.append({"file": f.name, "action": re.split(r"\s+—\s+owner:", text)[0].strip(),
                        "due": due.group(1) if due else "", "problems": problems})
    return sorted(out, key=lambda a: (not a["problems"], a["due"] or "9999"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax postmortem", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    n = sub.add_parser("new")
    n.add_argument("title")
    n.add_argument("--severity", default="sev3", choices=["sev1", "sev2", "sev3", "sev4"])
    sub.add_parser("list")
    sub.add_parser("actions")
    a = ap.parse_args(argv)
    if a.cmd == "new":
        p = new(a.title, a.severity)
        print(f"✔ written: {p.relative_to(ROOT)}\n  Fill it in within 48 hours while it is fresh; the actions are tracked by  ./securax postmortem actions")
        return 0
    if a.cmd == "list":
        files = sorted(DIR.glob("*.md")) if DIR.is_dir() else []
        open_by = {}
        for x in actions():
            open_by[x["file"]] = open_by.get(x["file"], 0) + 1
        for f in files:
            print(f"{f.name}   open actions: {open_by.get(f.name, 0)}")
        if not files:
            print('no postmortems yet. After an outage:  ./securax postmortem new "what broke"')
        return 0
    if a.cmd == "actions":
        acts = actions()
        for x in acts:
            flag = "✗ " + ", ".join(x["problems"]) if x["problems"] else "  open"
            print(f"{flag:<34} {x['action']}   ({x['file']})")
        if not acts:
            print("no open actions")
        return 1 if any(x["problems"] for x in acts) else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
