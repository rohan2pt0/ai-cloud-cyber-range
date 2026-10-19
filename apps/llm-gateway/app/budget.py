"""AI allowances per caller: a daily and a monthly token limit, a warning at 80%, a hard stop at 100%, and extensions a person
grants on the machine (the way paid AI plans let you continue on extra credits, but with nothing to buy).

    AI_BUDGET_DAY_TOKENS    tokens per caller per day     (0 = no daily limit)
    AI_BUDGET_MONTH_TOKENS  tokens per caller per month   (0 = no monthly limit)
    AI_BUDGET_COUNT_LOCAL   1 = also count the local model (default 0: it costs no money, and the rate limit already caps loops)

Pattern: a hard limit that blocks and a soft threshold that only warns (as AI gateways such as LiteLLM do), and a short window
inside a longer one (as AI subscriptions pair a session limit with a weekly one), so one heavy day cannot spend the month.
Extensions live in the AI control file (`./securax ai budget extend`), which only a person on the machine can write; they apply
to the current day or month and are logged. Spend is kept in a small file on the gateway's own volume, so a restart does not
reset the month.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
import time

from . import killswitch

DAY = int(os.getenv("AI_BUDGET_DAY_TOKENS", "0") or 0)
MONTH = int(os.getenv("AI_BUDGET_MONTH_TOKENS", "0") or 0)
COUNT_LOCAL = os.getenv("AI_BUDGET_COUNT_LOCAL", "0") == "1"
WARN_AT = 0.8
STATE = pathlib.Path(os.getenv("AI_BUDGET_STATE", "/var/lib/securax/budget.json"))

_led: dict = {"day": {}, "month": {}}
_warned: set[tuple[str, str, str]] = set()


def _keys() -> tuple[str, str]:
    return time.strftime("%Y-%m-%d"), time.strftime("%Y-%m")


def load(path: pathlib.Path | None = None) -> None:
    try:
        data = json.loads((path or STATE).read_text("utf-8"))
        _led.update(day=data.get("day", {}), month=data.get("month", {}))
    except (OSError, ValueError):
        pass


def _save(path: pathlib.Path | None = None) -> None:
    p = path or STATE
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".budget.")
        with os.fdopen(fd, "w") as f:
            json.dump(_led, f)
        os.replace(tmp, p)
    except OSError:
        pass                                   # no writable volume (tests, a bare run): counting still works in memory


def used(principal: str) -> tuple[int, int]:
    d, m = _keys()
    return _led["day"].get(d, {}).get(principal, 0), _led["month"].get(m, {}).get(principal, 0)


def extension(principal: str, period: str) -> int:
    """Tokens a person added for this caller (or everyone) for the current day or month."""
    d, m = _keys()
    key = d if period == "day" else m
    return sum(int(e.get("tokens") or 0) for e in killswitch.state().get("budget_extensions") or []
               if e.get("period") == period and str(e.get("for")) == key and e.get("caller") in ("*", principal))


def limits(principal: str) -> tuple[int, int]:
    """(daily, monthly) allowance including extensions; 0 = that limit is off."""
    return (DAY + extension(principal, "day") if DAY else 0), (MONTH + extension(principal, "month") if MONTH else 0)


def counts(zone: str) -> bool:
    return COUNT_LOCAL or zone != "local"


def refusal(principal: str) -> dict | None:
    """The limit this caller has reached, or None."""
    (du, mu), (dl, ml) = used(principal), limits(principal)
    if ml and mu >= ml:
        return {"period": "month", "limit": ml, "used": mu, "resets": "on the 1st"}
    if dl and du >= dl:
        return {"period": "day", "limit": dl, "used": du, "resets": "at midnight"}
    return None


def spend(principal: str, tokens: int, path: pathlib.Path | None = None) -> list[str]:
    """Count the tokens; returns the periods that just crossed the warning line (each warned once)."""
    d, m = _keys()
    for period, key in (("day", d), ("month", m)):
        _led[period] = {key: _led[period].get(key, {})}                    # keep only the current day and month
        _led[period][key][principal] = _led[period][key].get(principal, 0) + tokens
    _save(path)
    out = []
    (du, mu), (dl, ml) = used(principal), limits(principal)
    for period, u, lim, key in (("day", du, dl, d), ("month", mu, ml, m)):
        if lim and u >= WARN_AT * lim and (principal, period, key) not in _warned:
            _warned.add((principal, period, key))
            out.append(period)
    return out


def headers(principal: str) -> dict[str, str]:
    (du, mu), (dl, ml) = used(principal), limits(principal)
    h = {}
    if dl:
        h["X-AI-Budget-Day-Left"] = str(max(0, dl - du))
    if ml:
        h["X-AI-Budget-Month-Left"] = str(max(0, ml - mu))
    return h


def report() -> dict:
    d, m = _keys()
    callers = sorted(set(_led["day"].get(d, {})) | set(_led["month"].get(m, {})))
    rows = []
    for p in callers:
        (du, mu), (dl, ml) = used(p), limits(p)
        rows.append({"caller": p, "day_used": du, "day_limit": dl, "month_used": mu, "month_limit": ml})
    return {"day_limit": DAY, "month_limit": MONTH, "warn_at": WARN_AT, "count_local": COUNT_LOCAL, "callers": rows}


load()
