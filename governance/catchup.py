#!/usr/bin/env python3
"""`./securax catchup` — one short brief of what needs YOU right now, from your own estate (doc 122).

Mattermost's AI summarises a channel into "what happened + what needs a decision". The sovereign version of that is to
summarise YOUR OWN estate — the Life OS rhythm, the things to act on today (overdue findings, overdue risk treatments,
failing routines, a red cockpit reading) and the one next step — into a brief you can read in ten seconds.

  ./securax catchup            the brief (AI summary when a gateway is up; always the ground-truth "act today" list)
  ./securax catchup --json     the gathered signals, for a routine or the Life OS

Zero input: it reads only what the estate already knows, on your box. It goes through the gateway (so it inherits the
rails, the allowance and the audit trail) ONLY when one is configured; with no gateway it prints the structured brief
from the signals alone — the "act today" list is the ground truth and is ALWAYS shown, so an AI summary can never hide a
real overdue item. Nothing leaves your box beyond the one gateway call you already trust for chat.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _mod(name: str, rel: str):
    """Load a sibling module BY PATH (never `from governance import …`): the full test run puts other modules named
    'progress'/'repairs' in sys.modules and a bare import can bind to the wrong one (LESSONS 2026-10-21)."""
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gather(now: float | None = None) -> dict:
    """Everything the brief is built from, collected offline from the estate's own state."""
    now = now or time.time()
    out: dict = {"at": int(now), "errors": []}
    try:
        prog = _mod("catchup_progress", "governance/progress.py")
        p = prog.build(now)
        out["rhythm"] = p.get("rhythm", {})
        out["nudges"] = p.get("nudges", [])
        out["next"] = p.get("next")
    except Exception as e:  # noqa: BLE001 - one unreadable source must never hide the others
        out["errors"].append(f"progress: {type(e).__name__}")
    try:
        rep = _mod("catchup_repairs", "governance/repairs.py")
        r = rep.collect()
        out["act"] = [i for i in r.get("items", []) if i.get("level") == "act"]
        out["later"] = [i for i in r.get("items", []) if i.get("level") != "act"]
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"repairs: {type(e).__name__}")
        out.setdefault("act", [])
        out.setdefault("later", [])
    return out


def structured_brief(s: dict) -> str:
    """The ground-truth brief from the signals alone — no model needed. Always shown."""
    lines: list[str] = []
    act = s.get("act", [])
    if act:
        lines.append(f"Act today ({len(act)}):")
        for i in act[:8]:
            lines.append(f"  ✗ [{i.get('area', '?')}] {i.get('title', '')}")
            if i.get("fix"):
                lines.append(f"      → {i['fix']}")
    else:
        lines.append("Act today: nothing overdue — the red list is clear. ✓")
    nx = s.get("next")
    if nx and nx.get("title"):
        lines.append("")
        lines.append(f"Your one next step: {nx['title']}" + (f"  → {nx['do']}" if nx.get("do") else ""))
    for n in s.get("nudges", [])[:2]:
        lines.append(f"  • {n}")
    r = s.get("rhythm", {})
    if r.get("known"):
        lines.append("")
        lines.append(f"Life OS rhythm: {r.get('checkins_7d', 0)} check-in(s) this week, {r.get('checkins_30d', 0)} in 30 days.")
    if s.get("errors"):
        lines.append("")
        lines.append("(some sources could not be read: " + ", ".join(s["errors"]) + ")")
    return "\n".join(lines)


SUMMARY_Q = (
    "Below is the current state of my own estate — what needs acting on today, my one next step, and my Life OS rhythm. "
    "In at most six lines, tell me: the top three things that genuinely need ME today (most consequential first), any "
    "decision that is pending, and what I can safely ignore for now. Do not invent anything that is not in the state; if "
    "there is nothing urgent, say so plainly."
)


def ai_summary(s: dict) -> str | None:
    """A model's read of the signals, through the gateway (rails + allowance + audit). None when no gateway or it errors."""
    if not os.getenv("GATEWAY_URL"):
        return None
    try:
        personas = _mod("catchup_personas", "agents/personas.py")
        res = personas.ask_agent("productivity", SUMMARY_Q, context=structured_brief(s))
        return res.get("answer")
    except Exception:  # noqa: BLE001 - the structured brief is always there as the floor
        return None


def render(s: dict) -> str:
    ground = structured_brief(s)
    ai = ai_summary(s)
    if ai:
        return "CATCHUP — your estate, right now\n\n" + ai.strip() + "\n\n— the facts it read —\n" + ground
    return "CATCHUP — your estate, right now\n\n" + ground


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="One short brief of what needs you right now, from your own estate.")
    ap.add_argument("--json", action="store_true", help="the gathered signals as JSON")
    a = ap.parse_args(argv)
    s = gather()
    if a.json:
        print(json.dumps(s, indent=2))
    else:
        print(render(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
