"""Rupee caps per AI provider (owner, 2026-11-08: Rs 1,000 a month per provider; queue spend-guard, doc 105 G16).

The token allowance (app/budget.py) limits how much a caller may use; this limits what a provider may cost. Each answered
call is priced in rupees and charged to the provider that really answered (a ladder may fall back from one provider to
another); at 80% of a provider's monthly cap the gateway warns once, and at the cap a paid call is answered by the local
model instead, with a header and an audit event saying so. Nothing fails silently and no bill grows past the line.

    AI_SPEND_CAP_INR              monthly cap per paid provider, in rupees (default 1000; 0 = no cap)
    AI_SPEND_CAP_INR_<PROVIDER>   a different cap for one provider, e.g. AI_SPEND_CAP_INR_GEMINI=500
    AI_INR_PER_USD                the rate for costs LiteLLM reports in dollars (default 95: the rupee traded about 93.7-94.9
                                  in early November 2026; rounded up so the cap trips early, never late)
    AI_PRICES_INR                 JSON {model alias or model: [rupees per million input tokens, per million output]} for a
                                  model LiteLLM cannot price
    AI_UNKNOWN_INR_PER_MTOK       what a paid call with no known price is charged per million tokens (default 1000: high on
                                  purpose, so an unpriced model reaches the cap early and is flagged)
    AI_SPEND_FALLBACK_MODEL       the local model that answers at the cap (default bank-assistant-local)

The price comes from LiteLLM's x-litellm-response-cost header (US dollars, from LiteLLM's own price list), else the table,
else the unknown rate. Which provider a model belongs to comes from LiteLLM's /model/info (the prefix of each deployment's
model, e.g. gemini/..., ollama/...), cached; ollama is local and free. Spend is kept in a small file on the gateway's own
volume, so a restart does not reset the month; a new month starts at zero.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
import threading
import time

FREE = {"ollama", "ollama_chat", "local", "mock"}
STATE = pathlib.Path(os.getenv("AI_SPEND_STATE", "/var/lib/securax/spend.json"))
WARN_AT = 0.8
_lock = threading.Lock()
_led: dict = {"month": "", "inr": {}, "warned": []}
_providers: dict = {"at": 0.0, "alias": {}, "model": {}}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def inr_per_usd() -> float:
    return _env_float("AI_INR_PER_USD", 95.0)


def cap(provider: str) -> float:
    if provider in FREE:
        return 0.0
    return _env_float("AI_SPEND_CAP_INR_" + provider.upper().replace("-", "_"), _env_float("AI_SPEND_CAP_INR", 1000.0))


def fallback_model() -> str:
    return os.getenv("AI_SPEND_FALLBACK_MODEL", "bank-assistant-local")


# ── Which provider a model belongs to ────────────────────────────────────────────────────────────────────────────────
def learn(model_info: dict, now: float | None = None) -> None:
    """Read LiteLLM's /model/info answer: alias -> the provider of its deployment, and each deployment model -> provider."""
    alias, model = {}, {}
    for d in (model_info or {}).get("data", []) or []:
        lp = (d or {}).get("litellm_params") or {}
        full = str(lp.get("model") or "")
        prov = full.split("/", 1)[0] if "/" in full else str(lp.get("custom_llm_provider") or "")
        if not prov:
            continue
        name = str(d.get("model_name") or "")
        if name and name not in alias:            # the first deployment of an alias is its ladder's head
            alias[name] = prov
        model[full] = prov
        model[full.split("/", 1)[-1]] = prov
    _providers.update({"at": now if now is not None else time.time(), "alias": alias, "model": model})


def stale(now: float | None = None) -> bool:
    return (now if now is not None else time.time()) - _providers["at"] > 600


def provider_of(name: str, local_zone: bool = False) -> str:
    """The provider of a model alias or a served model id; 'local' for a local model; 'cloud' when it is not known yet."""
    n = str(name or "")
    p = _providers["alias"].get(n) or _providers["model"].get(n) or _providers["model"].get(n.split("/", 1)[-1])
    if p:
        return p
    if "/" in n:
        return n.split("/", 1)[0]
    return "local" if local_zone else "cloud"


# ── The monthly ledger ───────────────────────────────────────────────────────────────────────────────────────────────
def _month() -> str:
    return time.strftime("%Y-%m")


def load(path: pathlib.Path | None = None) -> None:
    try:
        d = json.loads((path or STATE).read_text("utf-8"))
        if isinstance(d, dict) and isinstance(d.get("inr"), dict):
            _led.update({"month": str(d.get("month") or ""), "inr": {str(k): float(v) for k, v in d["inr"].items()},
                         "warned": [str(x) for x in d.get("warned") or []]})
    except (OSError, ValueError, TypeError):
        pass


def _save(path: pathlib.Path | None = None) -> None:
    p = path or STATE
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".spend-")
        with os.fdopen(fd, "w") as f:
            json.dump(_led, f)
        os.replace(tmp, p)
    except OSError:
        pass                                        # a read-only volume never breaks an answer; the cap still holds in memory


def _roll() -> None:
    if _led["month"] != _month():
        _led.update({"month": _month(), "inr": {}, "warned": []})


def spent(provider: str) -> float:
    with _lock:
        _roll()
        return float(_led["inr"].get(provider, 0.0))


def over(provider: str) -> bool:
    c = cap(provider)
    return bool(c) and spent(provider) >= c


def price(model: str, usage: dict | None, cost_usd: float | None) -> tuple[float, str]:
    """(rupees, how it was priced): 'litellm' from the header, 'table' from AI_PRICES_INR, 'unknown' at the high rate."""
    if cost_usd is not None and cost_usd >= 0:
        return cost_usd * inr_per_usd(), "litellm"
    u = usage or {}
    tin, tout = int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
    try:
        table = json.loads(os.getenv("AI_PRICES_INR", "") or "{}")
    except ValueError:
        table = {}
    row = table.get(model) or table.get(str(model).split("/", 1)[-1])
    if isinstance(row, (list, tuple)) and len(row) == 2:
        return (tin * float(row[0]) + tout * float(row[1])) / 1e6, "table"
    return (tin + tout or int(u.get("total_tokens") or 0)) * _env_float("AI_UNKNOWN_INR_PER_MTOK", 1000.0) / 1e6, "unknown"


def charge(provider: str, inr: float, path: pathlib.Path | None = None) -> list[str]:
    """Add a call's cost to its provider's month. Returns ['warn'] the first time 80% is crossed this month, ['cap'] when the
    cap is reached by this call (each at most once a month), else []."""
    if provider in FREE or inr <= 0:
        return []
    out: list[str] = []
    with _lock:
        _roll()
        before = float(_led["inr"].get(provider, 0.0))
        after = before + inr
        _led["inr"][provider] = round(after, 6)
        c = cap(provider)
        if c:
            for tag, line in (("warn", WARN_AT * c), ("cap", c)):
                key = f"{provider}:{tag}"
                if before < line <= after and key not in _led["warned"]:
                    _led["warned"].append(key)
                    out.append(tag)
        _save(path)
    return out


def report() -> dict:
    with _lock:
        _roll()
        rows = {p: {"inr": round(v, 2), "cap_inr": cap(p), "share": round(v / cap(p), 3) if cap(p) else None}
                for p, v in sorted(_led["inr"].items())}
        return {"month": _led["month"], "inr_per_usd": inr_per_usd(), "providers": rows}


def reset() -> None:
    with _lock:
        _led.update({"month": "", "inr": {}, "warned": []})
    _providers.update({"at": 0.0, "alias": {}, "model": {}})


load()
