#!/usr/bin/env python3
"""Repairs: everything that needs fixing, in one list, each with its fix.

    ./securax repairs            the list, the most urgent first (exit 1 when something needs action today)
    ./securax repairs --json     the same, for the Command Center

Modelled on Home Assistant's Repairs page. Problems used to be spread over the cockpit, the risk register, the routines
check and the findings register; you had to know where to look. Repairs reads them all and says, for each one, what is
wrong and the one command or step that fixes it. It runs nothing slow itself: health and security come from the last
cockpit snapshot (`./securax cockpit` refreshes it; `./securax up` does too), and the age of that snapshot is shown.

- **Act today (✗):** a red cockpit reading, an overdue finding or risk treatment, a failing routine.
- **Schedule (◐):** an amber reading, a risk acceptance that ends within 14 days, a routine that found nothing for weeks.

Setup steps you have not done yet are not repairs; they stay in `./securax finish`. Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "portal" / "cockpit.json"


def _mod(name: str, rel: str):
    s = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def _cockpit(snap: pathlib.Path) -> tuple[list[dict], float | None]:
    try:
        data = json.loads(snap.read_text("utf-8"))
    except (OSError, ValueError):
        return [], None
    out = [{"level": "act" if m["status"] == "red" else "schedule", "area": m.get("area", "Estate"), "title": m["label"] + ": " + m["value"],
            "why": m.get("why", ""), "fix": m.get("cmd") or m.get("action") or "./securax doctor"}
           for m in data.get("metrics", []) if m.get("status") in ("red", "amber") and m.get("id") != "findings"]   # listed one by one below
    return out, data.get("ts")


def _findings() -> list[dict]:
    fd = _mod("securax_findings", "governance/findings.py")
    reg = fd.load()
    out = [{"level": "act", "area": "Findings", "title": f"{f['id']} overdue since {f['due']}: {f['title'][:70]}",
            "why": f"{f['severity']} finding" + (" on the known-exploited list" if f.get("kev") else "") + (f" on {f['asset']}" if f.get("asset") else ""),
            "fix": f"fix it, then ./securax findings fixed {f['id']}   (or accept: ./securax findings accept {f['id']} --reason ... --until DATE)"}
           for f in fd.overdue(reg)]
    out += [{"level": "schedule", "area": "Findings", "title": f"{f['id']} risk acceptance ends {f['accepted']['until']}",
             "why": f"accepted by {f['accepted']['by']}: {f['accepted']['reason'][:60]}",
             "fix": f"decide again: ./securax findings accept {f['id']} --reason ... --until DATE, or fix it"} for f in fd.expiring(reg)]
    return out


def _risks() -> list[dict]:
    rm = _mod("securax_risks", "governance/risks.py")
    return [{"level": "act", "area": "Risks", "title": f"Risk {r['id']} treatment overdue since {r['due']}: {(r.get('threat') or r.get('vulnerability') or '')[:60]}",
             "why": "an open risk past its treatment date" + (f", owner {r['owner']}" if r.get("owner") else ""), "fix": "./securax risks overdue"} for r in rm.overdue(rm.load())]


def _routines() -> list[dict]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from routines import prune
    return [{"level": "act" if i["verdict"] == "failing" else "schedule", "area": "Routines", "title": f"Routine {i['id']}: {i['why']}",
             "why": {"failing": "a failing routine trains you to ignore alerts", "nothing": "a report nobody needs is noise",
                     "duplicate": "two routines doing one job", "never": "it is switched on but never runs"}[i["verdict"]],
             "fix": i["fix"]} for i in prune.report()[0]]


def collect(snap: pathlib.Path = SNAP) -> dict:
    items, ts = _cockpit(snap)
    errors = []
    for fn in (_findings, _risks, _routines):
        try:
            items += fn()
        except Exception as e:  # noqa: BLE001 - one unreadable source must never hide the others
            errors.append(f"{fn.__name__.strip('_')}: {type(e).__name__}")
    items.sort(key=lambda i: (i["level"] != "act", i["area"]))
    return {"items": items, "act": sum(i["level"] == "act" for i in items), "snapshot_ts": ts, "errors": errors}


def summary(rep: dict) -> dict:
    """What the Command Center shows: the count and the first thing to do."""
    top = rep["items"][0] if rep["items"] else None
    return {"count": len(rep["items"]), "act": rep["act"], "top": top["title"] if top else ""}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rep = collect()
    if "--json" in argv:
        print(json.dumps(rep, indent=1))
        return 1 if rep["act"] else 0
    age = (time.time() - rep["snapshot_ts"]) / 3600 if rep["snapshot_ts"] else None
    note = ("  (health readings from a cockpit snapshot " + (f"{age:.0f} h old" if age >= 1 else "under an hour old") + "; refresh: ./securax cockpit)"
            if age is not None else "  (no cockpit snapshot yet, so health readings are not included: ./securax cockpit)")
    if not rep["items"]:
        print("✔ Nothing to repair." + note)
        return 0
    print(f"{len(rep['items'])} to repair, {rep['act']} today:" + note)
    for i in rep["items"]:
        print(f"  {'✗' if i['level'] == 'act' else '◐'} [{i['area']}] {i['title']}")
        if i["why"]:
            print(f"      why: {i['why']}")
        print(f"      fix: {i['fix']}")
    for e in rep["errors"]:
        print(f"  (could not read {e})")
    return 1 if rep["act"] else 0


if __name__ == "__main__":
    sys.exit(main())
