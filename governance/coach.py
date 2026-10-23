#!/usr/bin/env python3
"""The one thing to run when you do not know what to do: it tells you, in plain words, the single next step.

    ./securax next            where you are, and the ONE next thing to do (plain language, one action)
    ./securax next --json     the same, for the app

SecuRAX has many commands; this is the only one you have to remember. It looks at where you are — is the estate running,
have your life papers been read in, is the safety setup finished — and prints exactly one next step: the command to run,
why, and what you will see. No jargon, no list to pick from. Run it any time; it is safe and reads nothing private aloud.

It does not reinvent the checks: it reuses `./securax finish` for the optional setup and the Life OS's own import ledger.
Standard library only. Exit code is always 0 (it is a guide, not a gate)."""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import socket
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_up(timeout: float = 1.0) -> bool:
    """Best-effort: is the estate answering on this machine? Try the app's plain port, then the names-on HTTPS port."""
    for port in (8088, 9443):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def life_data_in() -> bool:
    """Have the life workbooks or documents been read in yet? (Their import ledgers, written on this machine only.)"""
    for rel in ("vault/life/ledger.json", "vault/life/docs-register.json", "portal/inbox-import.json"):
        p = ROOT / rel
        try:
            if p.stat().st_size > 2:                      # more than "{}"
                return True
        except OSError:
            continue
    return False


def app_url() -> str:
    try:
        return _load("addr", "governance/addr.py").web_url("hub", 8088)
    except Exception:  # noqa: BLE001
        return "http://localhost:8088"


def next_finish_item() -> dict | None:
    """The top optional safety step not done yet (reusing ./securax finish), or None when all are done."""
    try:
        finish = _load("finish", "governance/finish.py")
        left = [s for s in finish.status() if not s.get("done")]
        return {"id": left[0]["id"], "title": left[0]["title"], "gives": left[0]["gives"]} if left else None
    except Exception:  # noqa: BLE001 (a guide never fails on one missing part)
        return None


def coach(up: bool | None = None) -> dict:
    up = is_up() if up is None else up
    url = app_url()
    if not up:
        return {"stage": "not-running",
                "headline": "SecuRAX is not running yet.",
                "step": "Start everything with one command. It checks what is missing and only fixes that; if Docker needs a nudge it tells you how, in plain words.",
                "cmd": "./securax go", "why": "nothing else works until the estate is running",
                "app_url": url, "optional": None}
    if not life_data_in():
        return {"stage": "no-data",
                "headline": "SecuRAX is running. Now bring your life into it.",
                "step": ("Put your life spreadsheets in your Downloads folder (or vault/life/) and run the import; for documents "
                         "(policies, statements, ID scans) drop them in vault/life/docs/ and run the docs reader. Everything is "
                         "read on this machine and nothing leaves it."),
                "cmd": "./securax lifeos import workbook    (then: ./securax lifeos docs)",
                "why": "with your papers read in, the Life OS shows what needs you — a lapsing policy, a missing nominee — oldest and most urgent first",
                "app_url": url, "optional": None}
    opt = next_finish_item()
    return {"stage": "ready",
            "headline": "You are set up — open your Life OS and use it.",
            "step": f"Open the app and work the Inbox: each item becomes one action with a date, or a note. The vital few show first. Open it at {url} (add it to your home screen to use it like an app).",
            "cmd": "", "why": "this is where your day runs: tasks, papers, money, goals and your private AI",
            "app_url": url,
            "optional": (f"When you have time, one more safety step: {opt['title']} — {opt['gives']} (./securax finish {opt['id']})."
                         if opt else None)}


def render(c: dict) -> str:
    out = ["", f"  {c['headline']}", f"    → {c['step']}"]
    if c["cmd"]:
        out.append(f"    Run:  {c['cmd']}")
    out.append(f"    Why:  {c['why']}")
    if c.get("optional"):
        out.append(f"    {c['optional']}")
    out += ["", "  Lost at any point? This is the only command to remember:  ./securax next", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="./securax next", description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    c = coach()
    print(json.dumps(c, indent=2) if a.json else render(c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
