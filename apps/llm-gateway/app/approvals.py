"""Human-in-command approvals for agent tool calls (doc 124).

The gateway already DENIES dangerous tools and flags money-movement tools as "needs approval" (guardrails.DEFAULT_TOOL_POLICY).
On its own that is a dead block. This turns it into an approve-then-proceed loop a human controls, the sovereign way:

  1. The model asks to call an approval-required tool (e.g. a transfer). The gateway blocks it and records a PENDING
     approval, keyed to the exact tool name + a hash of its arguments, and tells the caller the pending id.
  2. A human runs `./securax approvals` (list) and `./securax approve <id>` — which calls an admin-only gateway endpoint
     that GRANTS the approval: a single-use, short-TTL token scoped to that exact (tool, args) pair. Every step is audited.
  3. The next time the model emits that exact tool call, the gateway CONSUMES the approval once and lets it through.
     A second identical call, a different argument, or a call after the TTL is blocked again.

Pure standard library, no web framework, in-memory (a short-lived approval surviving a gateway restart is not wanted).
The caller never handles the token — approval is matched on (tool, args_hash), so the client stays dumb and the gateway
stays authoritative. This is LLM06 / ASI02 "excessive agency": a consequential action needs a person, once, on the record.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time

TTL_SECONDS = 600            # a granted approval is usable for 10 minutes, once
PENDING_TTL_SECONDS = 86400  # a pending request is forgotten after a day if never granted

_pending: dict[str, dict] = {}    # id       -> {id, tool, args_hash, args_preview, created, conversation}
_approved: dict[str, dict] = {}   # args_hash -> {tool, token, expires, used, by, granted_at}


def args_hash(tool: str, args) -> str:
    """A stable hash of a tool call: its name plus its arguments in canonical form, so the same call hashes the same and
    a changed argument does not. `args` may be a JSON string (as providers send it) or an already-parsed object."""
    if isinstance(args, str):
        try:
            args = json.loads(args or "{}")
        except Exception:  # noqa: BLE001 - unparseable arguments hash as their raw text
            args = {"_raw": args}
    canon = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{str(tool).strip().lower()}\n{canon}".encode()).hexdigest()


def _gc(now: float | None = None) -> None:
    now = now or time.time()
    for h, a in list(_approved.items()):
        if a["used"] or a["expires"] < now:
            _approved.pop(h, None)
    for i, p in list(_pending.items()):
        if p["created"] + PENDING_TTL_SECONDS < now:
            _pending.pop(i, None)


def record_pending(tool: str, args, conversation: str = "", now: float | None = None) -> str:
    """Note that this exact tool call is waiting for a human. Idempotent: the same (tool, args) reuses its pending id."""
    now = now or time.time()
    _gc(now)
    h = args_hash(tool, args)
    for p in _pending.values():
        if p["args_hash"] == h:
            return p["id"]
    pid = "ap_" + secrets.token_hex(5)
    preview = args if isinstance(args, str) else json.dumps(args, default=str)
    _pending[pid] = {"id": pid, "tool": str(tool), "args_hash": h, "args_preview": preview[:400],
                     "created": now, "conversation": conversation}
    return pid


def pending(now: float | None = None) -> list[dict]:
    _gc(now)
    return sorted(_pending.values(), key=lambda p: p["created"])


def grant(pid: str, by: str = "", now: float | None = None) -> dict:
    """A human approves a pending request. Mints a single-use, TTL-bound approval for its exact (tool, args). Raises KeyError."""
    now = now or time.time()
    p = _pending.get(pid)
    if not p:
        raise KeyError(f"no pending approval '{pid}'")
    _approved[p["args_hash"]] = {"tool": p["tool"], "token": secrets.token_hex(16), "expires": now + TTL_SECONDS,
                                 "used": False, "by": by or "operator", "granted_at": now}
    _pending.pop(pid, None)
    return {"id": pid, "tool": p["tool"], "args_hash": p["args_hash"], "expires": now + TTL_SECONDS, "by": by or "operator"}


def consume(tool: str, args, now: float | None = None) -> bool:
    """True exactly once if this (tool, args) has an unused, unexpired approval — and marks it used. Else False."""
    now = now or time.time()
    h = args_hash(tool, args)
    a = _approved.get(h)
    if not a or a["used"] or a["expires"] < now or a["tool"].strip().lower() != str(tool).strip().lower():
        return False
    a["used"] = True
    return True


def reset() -> None:
    """For tests: clear all state."""
    _pending.clear()
    _approved.clear()
