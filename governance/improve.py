#!/usr/bin/env python3
"""IMPROVE — one calm weekly nudge that moves YOU, aimed by your Wheel of Life (doc 112).

Reads your Life OS wheel (the eight areas you score in the quarterly check-in), finds the area you rated LOWEST, and
gives ONE high-leverage, set-and-forget change for it — drawn from `./securax environment`, grounded in the
behavioural and elite-sport research. One signal a week, aimed where it helps most — the opposite of a regulator dump.

    ./securax improve            print this week's one lever for your weakest area
    ./securax improve --send     the same, short, to your phone (the weekly `improve` routine, Saturdays)
    ./securax improve --json     for the cockpit / other tools

It reads only what you already scored on THIS machine; nothing leaves your box. Not scored your wheel yet? It says so
and points you to the five-minute quarterly check-in, so the nudge is always honest about what it knows.
Standard library only. Exit code 0 always (it is a nudge, never a gate).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Each Life OS wheel area (the WHEEL_DIMS key in guiding-map/index.html) and the environment domain word that
# `environment.for_struggles()` filters on, so the lowest-scored area selects the right set-and-forget levers.
WHEEL = [
    ("career", "Career", "career"),
    ("money", "Finances", "finances"),
    ("health", "Health", "health"),
    ("family", "Family & Friends", "relationships"),
    ("love", "Partner / Romance", "relationships"),
    ("growth", "Personal Growth", "personal growth"),
    ("fun", "Fun & Recreation", "fun"),
    ("env", "Environment / Home", "environment"),
]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def wheel_scores(state: dict | None) -> dict:
    """{area_key: 1-10} from the synced Life OS state (the `sovS` blob the PWA pushes). {} when nothing is scored."""
    try:
        payload = (state or {}).get("payload") or {}
        sov = payload.get("sovS")
        sov = json.loads(sov) if isinstance(sov, str) else (sov or {})
        wheel = sov.get("wheel") or {}
        return {k: v for k, v in wheel.items() if isinstance(v, (int, float)) and v > 0}
    except (ValueError, AttributeError, TypeError):
        return {}


def weakest(scores: dict) -> dict | None:
    """The lowest-scored area as {key, label, domain, score}; None when nothing is scored. Ties break by wheel order."""
    order = {k: i for i, (k, _, _) in enumerate(WHEEL)}
    meta = {k: (label, dom) for k, label, dom in WHEEL}
    scored = [(k, v) for k, v in scores.items() if k in meta]
    if not scored:
        return None
    k, v = min(scored, key=lambda kv: (kv[1], order[kv[0]]))
    label, dom = meta[k]
    return {"key": k, "label": label, "domain": dom, "score": v}


def lever_for(domain_word: str, week: int) -> dict | None:
    """One set-and-forget lever for the area's domain, rotated by week so it is not the same one every time."""
    env = _load("securax_env_improve", "governance/environment.py")
    levers = env.for_struggles([domain_word])
    return levers[week % len(levers)] if levers else None


def build(now: float | None = None, state: dict | None = None) -> dict:
    now = now or time.time()
    pr = _load("securax_progress_improve", "governance/progress.py")
    st = state if state is not None else pr.life_state()
    area = weakest(wheel_scores(st))
    if not area:
        return {"known": False, "at": int(now)}
    return {"known": True, "area": area, "lever": lever_for(area["domain"], int(now // (7 * 86400))), "at": int(now)}


def short(p: dict) -> str:
    """The phone message: one calm line, the change, the if-then, and the first step — never a wall of text."""
    if not p.get("known"):
        return ("This week, score your Wheel of Life (five minutes, all taps) so I can aim at the area that needs you "
                "most. Open the Life OS and start the quarterly check-in.")
    a, lv = p["area"], p["lever"]
    if not lv:
        return (f"Your lowest area is {a['label']} ({a['score']}/10). One change to make this week: "
                f"./securax environment {a['domain']}")
    step = next(iter(lv["set_once"].values()), "")
    return (f"This week, one lever for your lowest area — {a['label']} ({a['score']}/10):\n"
            f"→ {lv['change']}\n"
            f"If-then: {lv['if_then']}\n"
            f"Set it once: {step}")


def report(p: dict, say=print) -> None:
    if not p.get("known"):
        say(short(p))
        return
    a, lv = p["area"], p["lever"]
    say("IMPROVE · this week's one lever, aimed at the Wheel-of-Life area you rated lowest.\n")
    say(f"Lowest area: {a['label']} — you rated it {a['score']}/10.")
    if not lv:
        say(f"See the changes for it: ./securax environment {a['domain']}")
        return
    say(f"\n→ {lv['change']}")
    say(f"   Why: {lv['why']}")
    say(f"   If-then: {lv['if_then']}")
    if lv.get("start_small"):
        say(f"   Start small: {lv['start_small']}")
    say("   Set it once:")
    for where, how in lv["set_once"].items():
        say(f"     · {where}: {how}")
    say("\nOne lever, set once, then forgotten. Next week aims at whatever is lowest then.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="improve", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    p = build()
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=1))
    elif a.send:
        msg = short(p)
        subprocess.run([sys.executable, str(ROOT / "governance" / "notify.py"), "send", msg, "--title", "This week: one lever"],
                       capture_output=True, timeout=60)
        print(msg)
    else:
        report(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
