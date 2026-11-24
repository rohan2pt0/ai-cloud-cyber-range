"""The rejection pipeline (deterministic backbone, slice 2): the ONE path every AI-produced write takes before it touches
stored state. The AI proposes, code decides; a proposal that fails any stage is rejected with a machine-readable reason
(stage, code, field, message), so the caller regenerates or escalates, and NOTHING is written.

  1. schema       the envelope and the payload match the declared contract for the action type (required fields, no extras)
  2. types        each field's type, range, length, pattern and allowed values
  3. gate         the decision gate (app/gate.py) with the declared policy and the kill switch: auto, ask or fallback
                  (fallback is a rejection that carries a decision request with a recommended default)
  4. idempotency  the same proposal (its key, or the hash of type and payload) executes once; a key reused for a
                  different payload is refused
  5. audit        the decision is appended to the tamper-evident audit chain BEFORE the write; if that fails, no write

"ask" records a pending approval (app.approvals, with the gate's reasons); once a person grants it, the same proposal sent
again is consumed once and executed. "auto" executes now and keeps an undo window. Every outcome is counted (`stats()`), so
`./securax progress` can show the rejection rate and the share of operations a model proposed.

Standard library only. The write itself is a pluggable `executor` (the rail to a real store); by default it is the gateway's
bounded in-memory action ledger, which the caller and the person read and undo through the gateway. State is in memory, like
the approvals it builds on, and every read-modify-write takes `_LOCK` (sync endpoints run in a thread pool; LESSONS 2026-11-14).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import secrets
import threading
import time
from collections import OrderedDict, defaultdict

from . import approvals, gate, guardrails, killswitch

STAGES = ("schema", "types", "gate", "idempotency", "audit")
LEDGER_CAP = 1000            # the ledger and the idempotency store keep the newest 1000 (bounded memory, threat db-d1)
IDEM_TTL_S = 24 * 3600
MAX_PENDING = int(os.getenv("GATE_MAX_PENDING", "100"))   # at the cap a new ask falls back instead of queueing (db-d1)
ENVELOPE = {"type", "payload", "confidence", "origin", "idempotency_key", "claims"}
CLAIMS = {"irreversible", "external", "criticality", "sensitivity"}
_DATE = r"^\d{4}-\d{2}-\d{2}$"


def _obj(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


_ID = {"type": "string", "minLength": 1, "maxLength": 64, "pattern": r"^[A-Za-z0-9_.:-]+$"}
# The declared contract per action type: what the payload must look like, and what the action IS (code, not a model, says
# whether it can be undone, leaves the estate, matters, or carries personal data). A model's claim can only make these stricter.
CONTRACTS: dict[str, dict] = {
    "habit.tick": {"irreversible": False, "external": False, "criticality": "low", "sensitivity": "none",
                   "schema": _obj({"habit_id": _ID, "date": {"type": "string", "pattern": _DATE}}, ["habit_id"])},
    "note.add": {"irreversible": False, "external": False, "criticality": "low", "sensitivity": "low",
                 "schema": _obj({"text": {"type": "string", "minLength": 1, "maxLength": 2000},
                                 "tags": {"type": "array", "maxItems": 10, "items": {"type": "string", "maxLength": 32}}}, ["text"])},
    "goal.progress": {"irreversible": False, "external": False, "criticality": "medium", "sensitivity": "low",
                      "schema": _obj({"goal_id": _ID, "percent": {"type": "number", "minimum": 0, "maximum": 100}},
                                     ["goal_id", "percent"])},
    "reminder.set": {"irreversible": False, "external": False, "criticality": "low", "sensitivity": "none",
                     "schema": _obj({"title": {"type": "string", "minLength": 1, "maxLength": 120},
                                     "date": {"type": "string", "pattern": _DATE}}, ["title", "date"])},
    "payment.send": {"irreversible": True, "external": True, "criticality": "critical", "sensitivity": "high",
                     "schema": _obj({"payee_id": _ID, "amount": {"type": "number", "minimum": 1, "maximum": 10_000_000},
                                     "currency": {"type": "string", "enum": ["INR", "USD", "EUR", "GBP", "AED", "SGD"]},
                                     "memo": {"type": "string", "maxLength": 140}}, ["payee_id", "amount", "currency"])},
    "message.send": {"irreversible": True, "external": True, "criticality": "medium", "sensitivity": "medium",
                     "schema": _obj({"to_id": _ID, "body": {"type": "string", "minLength": 1, "maxLength": 4000}}, ["to_id", "body"])},
    "record.delete": {"irreversible": True, "external": False, "criticality": "high", "sensitivity": "low",
                      "schema": _obj({"record_id": _ID}, ["record_id"])},
    "data.export": {"irreversible": True, "external": True, "criticality": "high", "sensitivity": "high",
                    "schema": _obj({"scope": {"type": "string", "enum": ["profile", "money", "health", "everything"]},
                                    "to_id": _ID}, ["scope", "to_id"])},
}
# The action policy (glob patterns over action types), the same shape as the tool policy (guardrails.DEFAULT_TOOL_POLICY).
DEFAULT_ACTION_POLICY = {"allow": ["habit.*", "note.*", "goal.*", "reminder.*", "payment.*", "message.*", "record.*", "data.*"],
                         "require_approval": ["payment.*"], "deny": []}


def load_policy() -> dict:
    """ACTION_POLICY_FILE (JSON) if set, else the default. A broken file fails closed: every action is denied."""
    path = os.getenv("ACTION_POLICY_FILE", "")
    if not path:
        return dict(DEFAULT_ACTION_POLICY)
    try:
        data = json.loads(open(path, encoding="utf-8").read())
        if not isinstance(data, dict):
            raise ValueError("not an object")
        return {k: list(data.get(k) or []) for k in ("allow", "require_approval", "deny")}
    except (OSError, ValueError):
        return {"allow": [], "require_approval": [], "deny": ["*"]}


def policy_for(atype: str, policy: dict | None = None) -> str:
    pol = policy if policy is not None else load_policy()
    m = guardrails._match                              # the tool policy's own glob matcher: one way to read a policy
    if m(atype, pol.get("deny", [])):
        return "deny"
    if m(atype, pol.get("require_approval", [])):
        return "require_approval"
    return "allow" if m(atype, pol.get("allow", [])) else "none"


class Rejected(Exception):
    """A proposal failed a stage. `as_dict()` is the machine-readable reason the caller acts on."""

    def __init__(self, stage: str, code: str, message: str, field: str = "", extra: dict | None = None):
        super().__init__(f"{stage}: {code}: {message}")
        self.stage, self.code, self.field, self.message, self.extra = stage, code, field, message, extra or {}

    def as_dict(self) -> dict:
        return {"status": "rejected", "stage": self.stage, "code": self.code, "field": self.field,
                "message": self.message, **self.extra}


# --------------------------------------------------------------------------- schema and types (a small JSON Schema subset)
_PY = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "object": dict, "array": list}


def _check(value, schema: dict, path: str) -> None:
    t = schema.get("type")
    if t == "object":
        if not isinstance(value, dict):
            raise Rejected("schema", "not_an_object", f"{path or 'payload'} must be an object", path)
        props = schema.get("properties", {})
        for k in schema.get("required", []):
            if k not in value:
                raise Rejected("schema", "missing_field", f"'{k}' is required", f"{path}.{k}".lstrip("."))
        if schema.get("additionalProperties") is False:
            for k in value:
                if k not in props:
                    raise Rejected("schema", "unknown_field", f"'{k}' is not in the contract", f"{path}.{k}".lstrip("."))
        for k, v in value.items():
            if k in props:
                _check(v, props[k], f"{path}.{k}".lstrip("."))
        return
    want = _PY.get(t)
    if want and (not isinstance(value, want) or (t in ("number", "integer") and isinstance(value, bool))):
        raise Rejected("types", "wrong_type", f"{path} must be a {t}", path)
    if t == "number" and value != value:                                  # NaN is a number that is not one
        raise Rejected("types", "out_of_range", f"{path} is not a finite number", path)
    if "enum" in schema and value not in schema["enum"]:
        raise Rejected("types", "not_allowed", f"{path} must be one of {schema['enum']}", path)
    if "minimum" in schema and value < schema["minimum"]:
        raise Rejected("types", "out_of_range", f"{path} must be at least {schema['minimum']}", path)
    if "maximum" in schema and value > schema["maximum"]:
        raise Rejected("types", "out_of_range", f"{path} must be at most {schema['maximum']}", path)
    if t == "string":
        if len(value) < schema.get("minLength", 0):
            raise Rejected("types", "too_short", f"{path} is too short", path)
        if len(value) > schema.get("maxLength", 10_000):
            raise Rejected("types", "too_long", f"{path} is too long", path)
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise Rejected("types", "bad_format", f"{path} does not have the expected format", path)
    if t == "array":
        if len(value) > schema.get("maxItems", 100):
            raise Rejected("types", "too_many", f"{path} has too many items", path)
        for i, item in enumerate(value):
            _check(item, schema.get("items", {}), f"{path}[{i}]")


def _envelope(p) -> None:
    if not isinstance(p, dict):
        raise Rejected("schema", "not_an_object", "a proposal must be a JSON object")
    for k in p:
        if k not in ENVELOPE:                        # e.g. a caller's own "undo_s" or "route" (threat db-t1)
            raise Rejected("schema", "unknown_field", f"'{k}' is not part of a proposal", k)
    for k in ("type", "payload", "confidence"):
        if k not in p:
            raise Rejected("schema", "missing_field", f"'{k}' is required", k)
    if not isinstance(p["type"], str) or not re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*", p["type"]):
        raise Rejected("types", "bad_format", "type must look like 'area.verb'", "type")
    if p.get("origin", "model") not in ("model", "code"):
        raise Rejected("types", "not_allowed", "origin must be 'model' or 'code'", "origin")
    k = p.get("idempotency_key")
    if k is not None and (not isinstance(k, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,128}", k)):
        raise Rejected("types", "bad_format", "idempotency_key must be 8-128 letters, digits or _.:-", "idempotency_key")
    claims = p.get("claims", {})
    if not isinstance(claims, dict) or any(c not in CLAIMS for c in claims):
        raise Rejected("schema", "unknown_field", f"claims may hold only {sorted(CLAIMS)}", "claims")


# --------------------------------------------------------------------------- state
_LOCK = threading.Lock()
_IDEM: "OrderedDict[str, dict]" = OrderedDict()     # key -> {"h", "t", "result"}
LEDGER: "OrderedDict[str, dict]" = OrderedDict()    # action id -> the accepted action
_COUNTS: dict = defaultdict(int)


def canon(atype: str, payload) -> str:
    return json.dumps({"type": atype, "payload": payload}, sort_keys=True, separators=(",", ":"), default=str)


def _sensitivity(payload) -> str:
    """The strictest PII severity the gateway's own rails find in any string of the payload (code, not a model's word)."""
    found = "none"
    stack = [payload]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)
        elif isinstance(v, str):
            _, fs = guardrails.redact_pii(v)
            found = gate.stricter(found, *(f.severity for f in fs))
    return found


def _redacted(payload) -> str:
    return guardrails.redact_pii(json.dumps(payload, sort_keys=True, default=str))[0][:400]


def _ledger_executor(entry: dict) -> None:
    LEDGER[entry["id"]] = entry
    while len(LEDGER) > LEDGER_CAP:
        LEDGER.popitem(last=False)


def _count_reject(stage: str) -> None:
    _COUNTS["rejected"] += 1
    _COUNTS[f"rejected_{stage}"] += 1


def submit(proposal, *, emit, executor=None, principal: str = "", now: float | None = None) -> dict:
    """Run one proposal through every stage. Returns {"status": "executed"|"ask"|"rejected", ...}; never raises for a bad
    proposal. `emit` appends to the audit chain (main._emit); `executor(entry)` does the write (default: the action ledger)."""
    now = now if now is not None else time.time()
    executor = executor or _ledger_executor
    origin = proposal.get("origin", "model") if isinstance(proposal, dict) else "model"
    with _LOCK:
        _COUNTS["proposals"] += 1
        _COUNTS[f"origin_{origin if origin in ('model', 'code') else 'model'}"] += 1
    atype = proposal.get("type") if isinstance(proposal, dict) else None

    def reject(r: Rejected) -> dict:
        with _LOCK:
            _count_reject(r.stage)
        try:
            emit({"decision": "action_rejected", "action_type": str(atype)[:64], "stage": r.stage, "code": r.code,
                  "field": r.field[:64], "reasons": r.extra.get("reasons", []), "principal": principal, "category": "LLM06"})
        except Exception:  # noqa: BLE001 - a rejection stands even if the audit is down; nothing was written
            pass
        return r.as_dict()

    try:
        _envelope(proposal)
        contract = CONTRACTS.get(atype)
        if contract:
            _check(proposal["payload"], contract["schema"], "")
        elif not isinstance(proposal["payload"], dict):
            raise Rejected("schema", "not_an_object", "payload must be an object", "payload")
    except Rejected as r:
        return reject(r)

    payload, claims = proposal["payload"], proposal.get("claims", {})
    c = contract or {}
    facts = {"type": atype, "policy": policy_for(atype), "confidence": proposal.get("confidence"),
             "irreversible": bool(c.get("irreversible")) or bool(claims.get("irreversible")),
             "external": bool(c.get("external")) or bool(claims.get("external")),
             "criticality": gate.stricter(c.get("criticality", "low"), claims.get("criticality", "none")),
             "sensitivity": gate.stricter(c.get("sensitivity", "none"), claims.get("sensitivity", "none"), _sensitivity(payload)),
             "ai_stopped": origin == "model" and bool((killswitch.stopped("") or {}).get("scope") == "all")}
    d = gate.decide(facts, known=bool(contract))
    body = canon(atype, payload)
    h = hashlib.sha256(body.encode()).hexdigest()
    key = proposal.get("idempotency_key") or "h:" + h
    tool = "action:" + atype

    with _LOCK:
        while _IDEM and (len(_IDEM) > LEDGER_CAP or now - next(iter(_IDEM.values()))["t"] > IDEM_TTL_S):
            _IDEM.popitem(last=False)
        seen = _IDEM.get(key)
        if seen:
            if seen["h"] != h:
                _count_reject("idempotency")
                r = Rejected("idempotency", "key_reused", "this idempotency key was used for a different proposal",
                             "idempotency_key")
                out = r.as_dict()
            else:
                _COUNTS["replayed"] += 1
                return {**copy.deepcopy(seen["result"]), "replayed": True}
        else:
            out = None
    if out:
        try:
            emit({"decision": "action_rejected", "action_type": atype, "stage": "idempotency", "code": "key_reused",
                  "principal": principal, "category": "LLM06"})
        except Exception:  # noqa: BLE001
            pass
        return out

    if d["route"] == "fallback":
        return reject(Rejected("gate", "fallback", "the gate did not let this run; a person decides", "type", {
            "reasons": d["reasons"], "decision_request": {
                "question": f"An assistant proposed '{atype}'. What should happen?",
                "options": ["do_nothing", "do_it_myself", "ask_again"], "recommended": "do_nothing"}}))

    with _LOCK:                                      # the idempotency check, the approval, the audit and the write: one step
        if key in _IDEM:                             # another thread executed it while we decided
            if _IDEM[key]["h"] != h:
                _count_reject("idempotency")
                return Rejected("idempotency", "key_reused", "this idempotency key was used for a different proposal",
                                "idempotency_key").as_dict()
            _COUNTS["replayed"] += 1
            return {**copy.deepcopy(_IDEM[key]["result"]), "replayed": True}
        reasons = list(d["reasons"])
        if d["route"] == "ask":
            if approvals.consume(tool, body):
                reasons.append("approved: a person granted this exact action once")
            else:
                return _ask(d, reasons, atype, tool, body, h, payload, origin, principal, emit, now)
        undo_s = d["undo_s"] if d["route"] == "auto" else (0 if facts["irreversible"] else gate.undo_window_s())
        aid = "act_" + secrets.token_hex(6)
        entry = {"id": aid, "type": atype, "payload": copy.deepcopy(payload), "route": d["route"], "reasons": reasons,
                 "origin": origin, "executed_at": now, "undo_until": now + undo_s if undo_s else 0, "status": "done",
                 "key_hash": hashlib.sha256(key.encode()).hexdigest()[:16]}
        try:
            emit({"decision": "action_executed", "action_id": aid, "action_type": atype, "route": d["route"],
                  "reasons": reasons, "undo_s": undo_s, "payload_hash": h[:16], "origin": origin,
                  "principal": principal, "category": "LLM06"})
        except Exception:  # noqa: BLE001 - no audit line, no write (stage 5)
            _count_reject("audit")
            return Rejected("audit", "audit_unavailable", "the decision could not be recorded, so nothing was written").as_dict()
        try:
            executor(entry)
        except Exception as e:  # noqa: BLE001 - a failed write is reported and audited, never recorded as done
            _COUNTS["failed"] += 1
            try:
                emit({"decision": "action_failed", "action_id": aid, "action_type": atype, "error": type(e).__name__})
            except Exception:  # noqa: BLE001
                pass
            return {"status": "failed", "action_id": aid, "message": "the write failed; nothing was kept"}
        _COUNTS["executed"] += 1
        result = {"status": "executed", "action_id": aid, "route": d["route"], "reasons": reasons, "undo_s": undo_s,
                  "undo_until": entry["undo_until"]}
        _IDEM[key] = {"h": h, "t": now, "result": result}
        return copy.deepcopy(result)


def _ask(d, reasons, atype, tool, body, h, payload, origin, principal, emit, now) -> dict:
    """Record a pending approval with the gate's reasons (called under _LOCK). At the queue's cap, fall back instead."""
    listed = {p["args_hash"] for p in approvals.pending()}
    if approvals.args_hash(tool, body) not in listed and len(listed) >= MAX_PENDING:
        r = Rejected("gate", "fallback", "too many actions are already waiting for a person", "type",
                     {"reasons": reasons + ["approvals_queue_full"], "decision_request": {
                         "question": "The approvals queue is full. Clear it first.",
                         "options": ["do_nothing", "ask_again"], "recommended": "do_nothing"}})
        _count_reject("gate")
        try:
            emit({"decision": "action_rejected", "action_type": atype, "stage": "gate", "code": "fallback",
                  "reasons": r.extra["reasons"], "principal": principal, "category": "LLM06"})
        except Exception:  # noqa: BLE001
            pass
        return r.as_dict()
    pid = approvals.record_pending(tool, body, now=now, reasons=reasons, preview=_redacted(payload))
    try:
        emit({"decision": "action_ask", "action_type": atype, "approval_id": pid, "reasons": reasons,
              "payload_hash": h[:16], "origin": origin, "principal": principal, "category": "LLM06"})
    except Exception:  # noqa: BLE001 - nothing is written on an ask; the approval itself is the record a person sees
        pass
    _COUNTS["asked"] += 1
    return {"status": "ask", "route": "ask", "approval_id": pid, "reasons": reasons, "recommended": d["recommended"],
            "approve": f"./securax approve {pid}"}


def undo(aid: str, *, emit, by: str = "", now: float | None = None) -> dict:
    """Take back an executed action inside its undo window (checked here, on the server). Raises KeyError or ValueError."""
    now = now if now is not None else time.time()
    with _LOCK:
        e = LEDGER.get(aid)
        if not e:
            raise KeyError(f"no action '{aid}'")
        if e["status"] != "done":
            raise ValueError(f"action '{aid}' is already {e['status']}")
        if not e["undo_until"]:
            raise ValueError(f"action '{aid}' cannot be undone (irreversible)")
        if now > e["undo_until"]:
            raise ValueError(f"the undo window for '{aid}' has closed")
        emit({"decision": "action_undone", "action_id": aid, "action_type": e["type"], "by": by or "operator",
              "category": "LLM06"})
        e["status"], e["undone_at"], e["undone_by"] = "undone", now, by or "operator"
        _COUNTS["undone"] += 1
        return {"action_id": aid, "status": "undone"}


def ledger(now: float | None = None) -> list[dict]:
    """The newest actions first, as a person sees them: type, status, why, and the undo deadline (no payload values)."""
    now = now if now is not None else time.time()
    with _LOCK:
        rows = list(LEDGER.values())[::-1]
    return [{"id": e["id"], "type": e["type"], "status": e["status"], "route": e["route"], "reasons": e["reasons"],
             "origin": e["origin"], "executed_at": e["executed_at"],
             "can_undo": e["status"] == "done" and e["undo_until"] > now, "undo_until": e["undo_until"],
             "preview": _redacted(e["payload"])} for e in rows]


def stats() -> dict:
    """Counts since start: proposals, rejections by stage, asks, executions, undos, and the two rates progress shows."""
    with _LOCK:
        c = dict(_COUNTS)
    n = c.get("proposals", 0)
    return {"proposals": n, "by_origin": {"model": c.get("origin_model", 0), "code": c.get("origin_code", 0)},
            "rejected": c.get("rejected", 0), "rejected_by_stage": {s: c.get(f"rejected_{s}", 0) for s in STAGES},
            "asked": c.get("asked", 0), "executed": c.get("executed", 0), "replayed": c.get("replayed", 0),
            "undone": c.get("undone", 0), "failed": c.get("failed", 0),
            "rejection_rate": round(c.get("rejected", 0) / n, 4) if n else 0.0,
            "model_share": round(c.get("origin_model", 0) / n, 4) if n else 0.0}


def reset() -> None:
    """For tests: clear all state."""
    with _LOCK:
        _IDEM.clear()
        LEDGER.clear()
        _COUNTS.clear()
