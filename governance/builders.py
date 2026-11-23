#!/usr/bin/env python3
"""Early warning before a builder provider runs out of money (queue builder-no-money-spof).

    python3 governance/builders.py --line    ask each provider once, remember it, print one plain line (exit 0 always)

Asks lifecycle/autobuild_ci.py allowance() who can pay for a build. The state file ($SECURAX_BUILDERS_STATE, else
~/.securax/builders.json) keeps since when each provider has been out and up to 60 daily credit samples. The line:
all fine; amber when one is out under 24 h or its credit runs out within 7 days; RED with the one fix when out over 24 h.
A provider with no key is "not checked here (no key)", never red. ./securax progress only reads the saved line.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DAY = 86400
MAX_SAMPLES = 60
FIX = {"gocode": "turn on Go Extra Usage, or wait for the monthly reset",
       "openrouter": "buy OpenRouter credit",
       "gemini": "check the Google AI Studio key or its free quota"}
NO_KEY = ("placeholder", "401", "no key", "api key not valid", "api_key_invalid", "invalid api key", "no auth credentials")


def default_state() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_BUILDERS_STATE") or pathlib.Path.home() / ".securax" / "builders.json")


def _load(path) -> dict:
    try:
        d = json.loads(pathlib.Path(path).read_text("utf-8"))
        if isinstance(d, dict):
            return d
    except (OSError, ValueError):
        pass
    return {}


def _credit(why: str) -> float | None:
    m = re.search(r"credit left: \$(-?[\d.]+)", why or "")
    try:
        return float(m.group(1)) if m else None
    except ValueError:
        return None


def _days_left(samples: list) -> float | None:
    """Days of credit left at the average daily spend, from daily samples [[day, left], ...]; None unless it is falling."""
    if len(samples) < 2:
        return None
    (d0, l0), (d1, l1) = samples[0], samples[-1]
    span = d1 - d0
    if span <= 0 or l1 >= l0:
        return None
    return l1 / ((l0 - l1) / span)


def check(answers: dict, state_path, now: float) -> str:
    state = _load(state_path)
    since = state.get("since") if isinstance(state.get("since"), dict) else {}
    samples = state.get("samples") if isinstance(state.get("samples"), dict) else {}
    day = int(now // DAY)
    parts, red = [], False
    for name, a in answers.items():
        why = re.sub(r"\s*(?:at\s+)?https?://\S+", "", str(a.get("why", ""))).strip()   # the line is public: no account links or ids
        nokey = (not a.get("ok")) and any(k in why.lower() for k in NO_KEY)
        left = _credit(why)
        if left is not None:
            s = [x for x in samples.get(name, []) if isinstance(x, list) and len(x) == 2]
            if s and s[-1][0] == day:
                s[-1] = [day, left]
            else:
                s.append([day, left])
            samples[name] = s[-MAX_SAMPLES:]
        if a.get("ok"):
            since.pop(name, None)
            dl = _days_left(samples.get(name, [])) if left is not None else None
            if dl is not None and dl < 7:
                parts.append(f"{name} runs out in about {max(1, round(dl))} days at the current spend ({why})")
            continue
        if nokey:
            since.pop(name, None)
            parts.append(f"{name}: not checked here (no key)")
            continue
        t0 = since.setdefault(name, now)
        if now - t0 >= DAY:
            red = True
            parts.append(f"{name} has been out for {int((now - t0) // DAY)} day(s): {FIX.get(name, 'check its key')}")
        else:
            parts.append(f"{name} is out ({why[:80]})")
    if not parts:
        line = f"Builders: all {len(answers)} providers can build."
    else:
        line = ("RED Builders: " if red else "Builders (amber): ") + "; ".join(parts)
    state.update({"since": since, "samples": samples, "line": line, "at": int(now)})
    try:
        p = pathlib.Path(state_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, indent=1), "utf-8")
    except OSError:
        pass
    return line


def last_line(state_path=None) -> str | None:
    """The saved line, read only; None when there is none or the file is damaged."""
    line = _load(state_path or default_state()).get("line")
    return line if isinstance(line, str) and line else None


def main(argv: list[str]) -> int:
    spec = importlib.util.spec_from_file_location("autobuild_ci", ROOT / "lifecycle" / "autobuild_ci.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        print(check(mod.allowance(), default_state(), time.time()))
    except Exception as e:  # noqa: BLE001 (a warning must never break the job that carries it)
        print(f"Builders: not checked ({type(e).__name__})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
