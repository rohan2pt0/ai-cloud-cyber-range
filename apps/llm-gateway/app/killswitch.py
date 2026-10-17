"""Human-in-command: a person can stop one model, or all AI, at once, and the gateway obeys on the next request.

RBI's draft Model Risk Management guidance (June 2026) expects override, suspension and deactivation ("kill switch") for AI
models. The switch is a small JSON file written by `./securax ai stop|resume` and mounted read-only into the gateway:

    {"all": {"by": "...", "at": "...", "reason": "..."} | null,
     "models": {"<model name as callers ask for it>": {"by": "...", "at": "...", "reason": "..."}}}

A file, not an API: nothing that can call the gateway can switch the AI back on, and the switch works with no restart (the
file is re-read when it changes). An unreadable or malformed file stops ALL AI: when the stop signal is in doubt, stopping is
the safe reading. No file means nothing is stopped.
"""
from __future__ import annotations

import json
import os
import pathlib

PATH = pathlib.Path(os.getenv("AI_CONTROL_FILE", "/etc/securax/controls/ai-control.json"))
_cache: dict = {"key": None, "state": {}}


def state(path: pathlib.Path | None = None) -> dict:
    p = path or PATH
    try:
        st = p.stat()
    except FileNotFoundError:
        return {}
    except OSError:
        return {"all": {"by": "gateway", "reason": "the AI control file cannot be read, so all AI is stopped until it can"}}
    key = (str(p), st.st_mtime_ns, st.st_size)
    if _cache["key"] != key:
        try:
            data = json.loads(p.read_text("utf-8") or "{}")
            if not isinstance(data, dict) or not isinstance(data.get("models", {}), dict):
                raise ValueError("not an object")
        except (OSError, ValueError):
            data = {"all": {"by": "gateway", "reason": "the AI control file is malformed, so all AI is stopped until it is fixed"}}
        _cache.update(key=key, state=data)
    return _cache["state"]


def stopped(model: str, path: pathlib.Path | None = None) -> dict | None:
    """The stop record that applies to this model (all-AI first), or None when it may run."""
    s = state(path)
    if s.get("all"):
        return {"scope": "all", **s["all"]}
    rec = (s.get("models") or {}).get(model or "")
    return {"scope": model, **rec} if rec else None
