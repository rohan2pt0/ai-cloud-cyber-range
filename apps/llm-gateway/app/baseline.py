"""Per-caller baselines (doc 92): a stolen key is spotted by how it behaves, not only by whether it is valid.

For each caller the gateway keeps a small, bounded picture of normal use:
  - requests per hour over the last 7 days (a ring of 168 hour buckets),
  - the models it asks for (at most MAX_MODELS, least recently used dropped first),
  - the hours of the day (UTC) it has been active in.

Once a caller has at least 24 h of history, three things are unusual:
  burst      this hour's requests exceed max(BURST_FLOOR, BURST_FACTOR x its 95th-percentile hourly rate)
  new_model  it asks for a model it has never used (flagged once per model)
  odd_hour   it is active in an hour of day it has never been active in, with more than ODD_HOUR_MIN requests

Detection only: nothing here blocks a call. Only hashed caller ids, model names, counts and times are kept, never prompt or
answer text. At most MAX_CALLERS callers are tracked (least recently seen dropped first) and the last MAX_ANOMALIES anomalies.
State is kept in a small file on the gateway's own volume (the same convention as budget.py), so a restart does not forget
what normal looks like:

    AI_BASELINE_STATE   path of the state file (default /var/lib/securax/baselines.json)
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
import time
from collections import OrderedDict, deque

STATE = pathlib.Path(os.getenv("AI_BASELINE_STATE", "/var/lib/securax/baselines.json"))
HOURS = 168                    # 7 days of hour buckets
HISTORY_S = 24 * 3600          # no judgement before a caller has a day of history
BURST_FLOOR = 20
BURST_FACTOR = 5
ODD_HOUR_MIN = 10
MAX_CALLERS = 500
MAX_MODELS = 32
MAX_ANOMALIES = 200            # kept; the endpoint shows the last 50
REPORT_N = 50
NAME_MAX = 64                  # model names and caller names are clipped; they are labels, never content
SAVE_EVERY_S = 60

_callers: OrderedDict[str, dict] = OrderedDict()
_anomalies: deque = deque(maxlen=MAX_ANOMALIES)
_last_save = [0.0]


def _clip(s: object) -> str:
    return "".join(ch for ch in str(s or "") if ch.isprintable())[:NAME_MAX]


def _new(first_hour: int, name: str) -> dict:
    return {"name": name, "first": first_hour, "cur": first_hour, "counts": [0] * HOURS, "slots": [-1] * HOURS,
            "models": {}, "hod": 0, "flagged": {}}


def _count(c: dict, hour: int) -> int:
    i = hour % HOURS
    return c["counts"][i] if c["slots"][i] == hour else 0


def _p95(c: dict, hour: int) -> int:
    """95th percentile of the caller's hourly counts over the earlier hours of the last 7 days (empty hours count as 0)."""
    vals = [_count(c, h) for h in range(max(c["first"], hour - HOURS + 1), hour)]
    if not vals:
        return 0
    s = sorted(vals)
    return s[min(len(s) - 1, max(0, int(round(0.95 * (len(s) - 1)))))]


def _flag_once(c: dict, kind: str, key: str, hour: int) -> bool:
    """True the first time this caller+kind+key is seen in this hour (one audit line, not one per request)."""
    k = f"{kind}:{key}"
    if c["flagged"].get(k) == hour:
        return False
    c["flagged"][k] = hour
    if len(c["flagged"]) > 2 * MAX_MODELS:          # bounded: forget the oldest marks
        for old in sorted(c["flagged"], key=c["flagged"].get)[: len(c["flagged"]) - 2 * MAX_MODELS]:
            c["flagged"].pop(old, None)
    return True


def observe(principal: str, model: str, name: str = "", now: float | None = None) -> list[dict]:
    """Count one call by `principal` for `model`; return the anomalies it newly raises (each also kept for report())."""
    now = time.time() if now is None else now
    hour = int(now // 3600)
    model = _clip(model) or "?"
    c = _callers.get(principal)
    if c is None:
        c = _callers[principal] = _new(hour, _clip(name) or principal)
        while len(_callers) > MAX_CALLERS:
            _callers.popitem(last=False)
    _callers.move_to_end(principal)
    if name:
        c["name"] = _clip(name)
    if hour > c["cur"]:                              # the hour rolled: the one that ended joins the usual hours of day
        if _count(c, c["cur"]):
            c["hod"] |= 1 << (c["cur"] % 24)
        c["cur"] = hour
    i = hour % HOURS
    if c["slots"][i] != hour:
        c["slots"][i], c["counts"][i] = hour, 0
    c["counts"][i] += 1
    n = c["counts"][i]

    seasoned = (hour - c["first"]) * 3600 >= HISTORY_S
    out: list[dict] = []
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    if seasoned:
        limit = max(BURST_FLOOR, BURST_FACTOR * _p95(c, hour))
        if n > limit and _flag_once(c, "burst", "", hour):
            out.append({"ts": ts, "caller": c["name"], "kind": "burst",
                        "detail": f"{n} requests this hour; usual peak about {_p95(c, hour)} an hour (limit {limit})"})
        if model not in c["models"] and _flag_once(c, "new_model", model, -1):
            out.append({"ts": ts, "caller": c["name"], "kind": "new_model", "detail": f"asked for {model}, never used by this caller before"})
        hod = hour % 24
        if c["hod"] and not c["hod"] >> hod & 1 and n > ODD_HOUR_MIN and _flag_once(c, "odd_hour", "", hour):
            out.append({"ts": ts, "caller": c["name"], "kind": "odd_hour",
                        "detail": f"{n} requests at {hod:02d}:00 UTC, an hour this caller is never active in"})
    c["models"][model] = hour                        # learn the model (also while the first day of history builds up)
    if len(c["models"]) > MAX_MODELS:
        for old in sorted(c["models"], key=c["models"].get)[: len(c["models"]) - MAX_MODELS]:
            del c["models"][old]
    _anomalies.extend(out)
    if out or now - _last_save[0] >= SAVE_EVERY_S:
        _last_save[0] = now
        save()
    return out


def report(n: int = REPORT_N) -> dict:
    rows = list(_anomalies)[-n:]
    return {"anomalies": rows[::-1], "tracked_callers": len(_callers), "window_h": HOURS}


def save(path: pathlib.Path | None = None) -> None:
    p = path or STATE
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".baselines.")
        with os.fdopen(fd, "w") as f:
            json.dump({"callers": _callers, "anomalies": list(_anomalies)}, f, separators=(",", ":"))
        os.replace(tmp, p)
    except OSError:
        pass                                         # no writable volume (tests, a bare run): baselines still work in memory


def _valid(c: object) -> bool:
    return (isinstance(c, dict) and isinstance(c.get("first"), int) and isinstance(c.get("cur"), int)
            and isinstance(c.get("counts"), list) and len(c["counts"]) == HOURS and all(isinstance(x, int) for x in c["counts"])
            and isinstance(c.get("slots"), list) and len(c["slots"]) == HOURS and all(isinstance(x, int) for x in c["slots"])
            and isinstance(c.get("models"), dict) and isinstance(c.get("hod"), int) and isinstance(c.get("flagged"), dict))


def load(path: pathlib.Path | None = None) -> None:
    """Read the state file; anything malformed is skipped (an empty baseline only means less is flagged at first)."""
    try:
        data = json.loads((path or STATE).read_text("utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(data, dict):
        return
    callers = data.get("callers") if isinstance(data.get("callers"), dict) else {}
    for k, c in list(callers.items())[-MAX_CALLERS:]:
        if _valid(c):
            c["name"] = _clip(c.get("name")) or str(k)[:NAME_MAX]
            c["models"] = {_clip(m): int(h) for m, h in list(c["models"].items())[-MAX_MODELS:] if isinstance(h, int)}
            _callers[str(k)[:NAME_MAX]] = c
    for a in (data.get("anomalies") or [])[-MAX_ANOMALIES:]:
        if isinstance(a, dict) and {"ts", "caller", "kind", "detail"} <= set(a):
            _anomalies.append({k: _clip(a[k]) if k != "detail" else str(a[k])[:200] for k in ("ts", "caller", "kind", "detail")})


def reset() -> None:
    _callers.clear()
    _anomalies.clear()
    _last_save[0] = 0.0


load()
