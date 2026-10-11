"""Approved-action executor — the ONLY path by which the autonomous agent may change state.

The research agent is read-only: it queues state-changing steps (login, submit, buy) as
`PendingAction`s and never touches them. This module executes ONE such action, and only when a
human explicitly approves THAT action at call time. Every design choice here is about making an
autonomous write safe enough for a security professional to allow:

  * Explicit per-call approval — `approve=True` is required; there is no "approve all" and no
    stored standing consent. An un-approved call is refused and logged, never executed.
  * Every gate re-validated at execution time — SSRF (syntactic + DNS) and the allowlist are
    checked again here, independently of whatever produced the action.
  * Append-only audit trail — every attempt (refused or executed) is recorded. The audit NEVER
    stores the body/headers (they may hold credentials or a session cookie): only method, URL,
    reason, approval, allow-decision and outcome.
  * No credential storage — secrets are passed in the action at call time and are not persisted.
  * No auto-redirect — an action does not transparently follow a 3xx to a new target.

All effectful I/O (the HTTP call, the audit sink, DNS) is injected, so this is unit-tested fully
offline with zero network and zero writes.
"""
from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import safety

DEFAULT_AUDIT = Path(__file__).resolve().parent / ".audit.jsonl"


@dataclass
class Action:
    """A state-changing web request awaiting human approval. `data`/`headers` may carry secrets
    and are NEVER written to the audit log."""
    method: str
    url: str
    data: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    reason: str = ""


def _default_perform(action: Action) -> tuple:
    import httpx
    with httpx.Client(follow_redirects=False, timeout=30.0) as c:
        r = c.request(action.method.upper(), action.url,
                      data=action.data or None, headers=action.headers or None)
        return r.status_code, r.text[:4000]


def _default_audit(entry: dict) -> None:
    DEFAULT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def execute_action(action: Action, *, approve: bool, allow: list,
                   deny: Optional[list] = None,
                   perform: Callable[[Action], tuple] = _default_perform,
                   audit_log: Callable[[dict], None] = _default_audit,
                   resolver=socket.getaddrinfo, now: Optional[float] = None) -> dict:
    """Execute `action` iff `approve` is True AND it passes every gate. Returns a result dict and
    always writes exactly one audit entry. Credentials in action.data/headers are never audited."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now if now is not None else time.time()))
    # The audit record — deliberately free of the body/headers.
    record = {"ts": ts, "method": action.method.upper(), "url": action.url,
              "reason": action.reason, "approved": bool(approve)}

    def _finish(outcome: str, allowed: bool, extra: Optional[dict] = None) -> dict:
        record.update({"allowed": allowed, "outcome": outcome})
        if extra:
            record.update({k: v for k, v in extra.items() if k in ("status",)})
        audit_log(dict(record))
        return {"executed": outcome == "executed", "outcome": outcome, **(extra or {})}

    if action.method.upper() in {"GET", "HEAD"}:
        # This path is for WRITES only. A read is not a state-changing action and must not be
        # laundered through the approval/audit flow (and a GET must not carry a body).
        return _finish("refused: GET/HEAD is a read — use the research agent, not the executor",
                       allowed=False)
    if not approve:
        return _finish("refused: approval required", allowed=False)

    # Order: syntactic SSRF → allowlist (policy) → DNS. Checking the allowlist before resolving
    # avoids a DNS lookup for a host we'd refuse anyway, and gives the most specific refusal reason.
    ok, why = safety.is_safe_target(action.url)
    if not ok:
        return _finish(f"refused: SSRF gate ({why})", allowed=False)
    ok, why = safety.domain_allowed(action.url, allow, deny)
    if not ok:
        return _finish(f"refused: allowlist ({why})", allowed=False)
    ok, why = safety.resolved_ips_safe(_host(action.url), resolver)
    if not ok:
        return _finish(f"refused: DNS gate ({why})", allowed=False)

    try:
        status, body = perform(action)
    except Exception as exc:  # noqa: BLE001
        return _finish(f"error: {str(exc)[:160]}", allowed=True)
    return _finish("executed", allowed=True, extra={"status": status, "response_tail": (body or "")[-600:]})


def _host(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).hostname or ""


def main(argv=None) -> int:
    """Human-driven CLI: run ONE approved action from a JSON file. There is intentionally no MCP
    tool for this — approval must come from a person, never from a model that could self-approve.

      ./securax act path/to/action.json --allow shop.example --approve
    action.json: {"method":"POST","url":"https://…","data":{…},"headers":{…},"reason":"…"}
    """
    import argparse
    import sys
    ap = argparse.ArgumentParser(prog="agents.web_research.executor",
                                 description="Execute ONE approved, allowlisted, SSRF-checked web action.")
    ap.add_argument("action_json", help="path to the action JSON file")
    ap.add_argument("--allow", action="append", default=[], help="allowed domain (repeatable, required)")
    ap.add_argument("--deny", action="append", default=[])
    ap.add_argument("--approve", action="store_true", help="REQUIRED: your explicit go-ahead for THIS action")
    args = ap.parse_args(argv)
    if not args.allow:
        print("refusing: pass --allow <domain> (the action's host must be allowlisted).", file=sys.stderr)
        return 2
    try:
        spec = json.loads(Path(args.action_json).read_text())
        action = Action(method=spec["method"], url=spec["url"], data=spec.get("data", {}),
                        headers=spec.get("headers", {}), reason=spec.get("reason", ""))
    except Exception as exc:  # noqa: BLE001
        print(f"bad action file: {exc}", file=sys.stderr)
        return 2
    if not args.approve:
        print(f"DRY RUN (not approved): would {action.method} {action.url}\n"
              f"reason: {action.reason}\nRe-run with --approve to execute.", file=sys.stderr)
    res = execute_action(action, approve=args.approve, allow=args.allow, deny=args.deny)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("executed") or not args.approve else 1


if __name__ == "__main__":
    raise SystemExit(main())
