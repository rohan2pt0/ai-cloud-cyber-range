#!/usr/bin/env python3
"""Antifragility engine — turn every failure into a permanent strength.

The core loop that makes SecuRAX a *super-intelligent, self-improving* system (and the
Taleb "gains from disorder" principle, made concrete):

    1. CAPTURE   a failure (a bypass, a miss, an incident, a false positive) → the ledger.
    2. GENERALISE  it from a one-off payload into a detection pattern (heuristic, or an
                   LLM proposal via the gateway when available) — so the *class* is caught,
                   not just the exact string.
    3. HARDEN     a human approves the rule and it ships (HITL — the system never rewrites
                   its own security rules unattended).
    4. VERIFY     the engine re-runs every past failure against the current defences and
                   proves it is now blocked. A failure that is now defended is a STRENGTH.

The ledger (`learning/failure-ledger.jsonl`) is append-only institutional memory, kept in
Git. The number of past failures that current defences block is the **antifragility score** —
it only goes up. This is the UPSC "lessons learned → never repeat" discipline in code.

Governance note: payloads are truncated and PII-redacted before they are written, so the
institutional memory never itself becomes a data-leak.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "learning" / "failure-ledger.jsonl"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("gw_guardrails", "apps/llm-gateway/app/guardrails.py")
ALLOWED = {"vulnbank.example", "rbi.org.in", "cybercrime.gov.in"}


# --------------------------------------------------------------------------- #
# 1. CAPTURE
# --------------------------------------------------------------------------- #
def _safe(payload: str, limit: int = 300) -> str:
    """Redact PII and truncate before storing — the ledger must never leak data.

    Note: we redact PII but do NOT normalise, so the attack signal (e.g. invisible
    smuggling characters) is preserved as evidence — the ledger is a security test corpus,
    and `verify()` must be able to re-run the real payload against current defences."""
    clean, _ = G.redact_pii(payload or "")
    return clean[:limit]


def record_failure(kind: str, summary: str, payload: str = "", direction: str = "input",
                   source: str = "manual") -> dict:
    """Append a failure to the ledger. kind e.g. 'bypass', 'false-positive', 'incident'."""
    entry = {
        "id": hashlib.sha1(f"{summary}{payload}{dt.datetime.now()}".encode()).hexdigest()[:10],
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "summary": summary,
        "payload": _safe(payload),
        "direction": direction,
        "source": source,
        "status": "open",            # open -> hardened (a rule shipped) -> verified (now blocked)
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def load_ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(ln) for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]


# --------------------------------------------------------------------------- #
# 2. GENERALISE — turn a one-off payload into a detection-pattern proposal
# --------------------------------------------------------------------------- #
_IMPERATIVES = re.compile(
    r"\b(ignore|disregard|override|reveal|print|exfiltrate|send|transfer|delete|execute|"
    r"bypass|jailbreak|developer mode|system prompt|act as)\b", re.I)


def propose_rule(payload: str) -> dict:
    """Heuristic generalisation: extract the salient imperative tokens and build a regex
    candidate that would catch the whole *class* of this attack, not just this string.

    When the guardrail gateway is reachable, this can be upgraded to an LLM proposal
    (see learning/self_improve.py) — but the offline heuristic always works."""
    norm = G.normalise(payload or "")
    tokens = sorted({m.group(0).lower() for m in _IMPERATIVES.finditer(norm)})
    if not tokens:
        # fall back to the two longest distinctive words
        words = [w for w in re.findall(r"[a-z]{5,}", norm.lower())]
        tokens = sorted(set(words), key=len, reverse=True)[:2]
    pattern = r"\b(" + "|".join(re.escape(t) for t in tokens) + r")\b" if tokens else ""
    sev = "high" if _IMPERATIVES.search(norm) else "medium"
    return {"suggested_pattern": pattern, "suggested_severity": sev, "tokens": tokens,
            "note": "Human review required before shipping (HITL). Add to guardrails + a regression test."}


# --------------------------------------------------------------------------- #
# 4. VERIFY — prove every past failure is now a strength
# --------------------------------------------------------------------------- #
def _is_defended(entry: dict) -> bool:
    p = entry.get("payload", "")
    if not p:
        return False
    if entry.get("direction") == "output":
        v = G.inspect_output(p, ALLOWED, {"CANARY-7f3a9c"})
        return (not v.allowed) or any(f.rule.startswith(("SECRET-", "LEAK-", "OUT-")) for f in v.findings)
    if entry.get("kind") == "false-positive":
        # a false positive is "fixed" when the benign payload is now ALLOWED
        return G.inspect_input(p).allowed
    return not G.inspect_input(p).allowed


def verify() -> dict:
    ledger = load_ledger()
    defended = [e for e in ledger if _is_defended(e)]
    still_open = [e for e in ledger if not _is_defended(e)]
    score = round(len(defended) / len(ledger), 3) if ledger else 1.0
    return {
        "total_failures_recorded": len(ledger),
        "now_defended_strengths": len(defended),
        "still_open": [{"id": e["id"], "summary": e["summary"]} for e in still_open],
        "antifragility_score": score,   # fraction of past failures the system now withstands
    }


def report() -> dict:
    ledger = load_ledger()
    by_kind: dict[str, int] = {}
    for e in ledger:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
    v = verify()
    return {"by_kind": by_kind, **v}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Antifragility engine — failures become strengths.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="record a failure")
    r.add_argument("--kind", default="bypass")
    r.add_argument("--summary", required=True)
    r.add_argument("--payload", default="")
    r.add_argument("--direction", default="input")
    r.add_argument("--source", default="manual")
    p = sub.add_parser("propose", help="propose a detection rule from a payload")
    p.add_argument("--payload", required=True)
    sub.add_parser("verify", help="prove past failures are now defended")
    sub.add_parser("report", help="full antifragility report")
    args = ap.parse_args()

    if args.cmd == "record":
        print(json.dumps(record_failure(args.kind, args.summary, args.payload, args.direction, args.source), indent=2))
    elif args.cmd == "propose":
        print(json.dumps(propose_rule(args.payload), indent=2))
    elif args.cmd == "verify":
        print(json.dumps(verify(), indent=2))
    elif args.cmd == "report":
        print(json.dumps(report(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
