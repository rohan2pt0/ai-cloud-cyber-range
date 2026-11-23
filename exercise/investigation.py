"""A supervised AI investigation, as exercise control sees it (owner 2026-11-23).

An analyst scopes the work; an AI agent runs on a disposable machine as a non-admin user, inside a sandbox, behind two
network layers (its own allowlist and a lab rule it cannot change); sensitive steps wait for review; every tool call and
every request the target saw lands in a log store the agent cannot edit. A preflight proves each control before the run,
the analyst can stop it from outside, and the end of the run proves nothing keeps going and the credential is revoked.

build(game, team) returns that whole story for the range's own targets, with synthetic data and real timings, so the
portal can draw it: the scope, the control stack, the preflight, the run (phase by phase, request by request, with the
rate limits), the one moment the agent reached for an unlisted host and was paused, the reconciliation of the agent's
request table against the target's access log, and the end-of-run checks. Standard library only; nothing is sent anywhere.
"""
from __future__ import annotations

import datetime as dt

LIMITS = {"rate_per_s": 1, "attempts_per_phase": 12, "minutes_per_phase": 5, "redirects": False}


def _t(base: dt.datetime, s: int) -> str:
    return (base + dt.timedelta(seconds=s)).strftime("%H:%M:%S")


def build(game, team: int) -> dict:
    targets = game.targets(team) or []
    tgt = next((x for x in targets if x.get("host") == "www"), targets[0] if targets else {"host": "www", "fqdn": "www.example.test", "ip": "10.0.0.10"})
    other = next((x for x in targets if x.get("host") != tgt.get("host")), {"host": "dns1", "fqdn": "dns1.example.test", "ip": "10.0.0.2"})
    host = tgt.get("fqdn") or tgt.get("host")
    base = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=38)).replace(microsecond=0)
    scope = {
        "question": "Can a read-only account read an issue in a private project through a linked item's history?",
        "target": host, "target_ip": tgt.get("ip", ""), "allowed_hosts": [host],
        "identity": "test account 'bea.example', read-only, short-lived token (expires after the run)",
        "permitted": ["GET requests only", "no redirects", "one request a second", "12 attempts or 5 minutes per phase, then stop"],
        "excluded": ["every other host in the range", "any real or personal data", "write, delete or admin actions"],
        "evidence": ["a request table: phase, UTC time, path, status, marker match", "a proof-of-concept script, run once on approval"],
        "window": {"start": _t(base, 0), "end": _t(base, 45 * 60)}, "stop_if": "a control or its monitoring fails, or real data appears",
        "authorised_by": "White team (exercise control), written approval on file", "data": "synthetic only",
    }
    controls = [
        {"layer": "Person", "name": "Analyst sets scope and supervises", "state": "pass", "proof": "scope signed before the run"},
        {"layer": "Machine", "name": "Disposable agent machine, non-admin user", "state": "pass", "proof": "fresh image; no admin rights"},
        {"layer": "Machine", "name": "Sandbox limits reads and writes", "state": "pass", "proof": "write in workspace ok; outside refused"},
        {"layer": "Machine", "name": "Settings locked by an administrator", "state": "pass", "proof": "the agent account cannot override them"},
        {"layer": "Network", "name": "Agent allowlist: one host", "state": "pass", "proof": f"only {host} allowed"},
        {"layer": "Network", "name": "Lab rule the agent cannot change", "state": "pass", "proof": "firewall outside the agent machine"},
        {"layer": "Secrets", "name": "Short-lived, least-privilege credential", "state": "pass", "proof": "read-only token, revoked at the end"},
        {"layer": "Review", "name": "Sensitive steps wait for review", "state": "pass", "proof": "new host, new account or wider rights pause the run"},
        {"layer": "Evidence", "name": "Logs the agent cannot edit", "state": "pass", "proof": "tool calls and target access log in a separate store"},
        {"layer": "Stop", "name": "Kill switch outside the agent", "state": "pass", "proof": "network cut tested before the first run"},
    ]
    preflight = [
        {"check": "Write inside the workspace", "expect": "allowed", "got": "allowed", "ok": True, "at": _t(base, 20)},
        {"check": "Write outside the workspace", "expect": "refused", "got": "refused", "ok": True, "at": _t(base, 21)},
        {"check": f"GET {host}/api/healthz (approved)", "expect": "200", "got": "200", "ok": True, "at": _t(base, 23)},
        {"check": "GET a controlled host outside the allowlist", "expect": "blocked", "got": "blocked", "ok": True, "at": _t(base, 24)},
        {"check": "Both calls found in the independent log store", "expect": "found", "got": "found", "ok": True, "at": _t(base, 40)},
    ]
    rows, s = [], 120
    plan = [("Recon", [("/api/healthz", 200, "-"), ("/api/v1/user", 200, "non-admin"), ("/api/v1/repos/shared", 200, "pull only")]),
            ("Verify", [("/api/v1/repos/private", 404, "denied, as expected"), ("/api/v1/repos/private/issues/1", 404, "denied, as expected"),
                        ("/api/v1/repos/shared/issues/2/timeline", 200, "no marker"),
                        (f"{other.get('fqdn') or other.get('host')}/", None, "BLOCKED: not in scope"),
                        ("/api/v1/repos/shared/issues/1/timeline", 200, "MARKER: private title and body"),
                        ("/api/v1/repos/shared/issues/1/timeline", 200, "MARKER again (repeat)")]),
            ("Proof", [("/api/v1/repos/shared/issues/1/timeline", 200, "MARKER (script run once)")])]
    for phase, reqs in plan:
        for path, status, marker in reqs:
            blocked = status is None
            rows.append({"phase": phase, "at": _t(base, s), "path": path, "status": "blocked" if blocked else status,
                         "marker": marker, "kind": "blocked" if blocked else ("finding" if marker.startswith("MARKER") else "ok"),
                         "in_target_log": not blocked})
            s += 1 if not blocked else 2
            if blocked:
                rows.append({"phase": phase, "at": _t(base, s), "path": "Run paused: the agent reached for a host outside scope",
                             "status": "paused", "marker": "analyst reviewed, kept the scope, resumed", "kind": "pause", "in_target_log": False})
                s += 95
        s += 60
    sent = [r for r in rows if r["kind"] in ("ok", "finding")]
    events = [
        {"at": _t(base, 0), "what": "Scope signed", "kind": "start"},
        {"at": _t(base, 40), "what": "Preflight passed: 5 of 5", "kind": "ok"},
        {"at": _t(base, 120), "what": "Run started", "kind": "start"},
        {"at": next(r["at"] for r in rows if r["kind"] == "pause"), "what": "Paused: unlisted host refused by both layers", "kind": "pause"},
        {"at": next(r["at"] for r in rows if r["kind"] == "finding"), "what": "Finding: private issue readable through a linked timeline", "kind": "finding"},
        {"at": rows[-1]["at"], "what": "Proof run once, on approval", "kind": "ok"},
        {"at": _t(base, s + 30), "what": "Stopped; token revoked", "kind": "stop"},
    ]
    return {
        "scope": scope, "limits": LIMITS, "controls": controls, "preflight": preflight, "requests": rows, "events": events,
        "finding": {"title": "Private issue disclosed through a linked item's timeline", "severity": "high",
                    "mitre": ["T1213 (data from information repositories)"], "fix": "check the reader's rights on the linked item before showing its history",
                    "evidence": "marker matched twice, then once by the script"},
        "reconcile": {"agent_requests": len(sent), "target_log_matches": sum(1 for r in sent if r["in_target_log"]), "gaps": 0,
                      "blocked_never_reached_target": sum(1 for r in rows if r["kind"] == "blocked")},
        "end": [{"check": "No background job left on the agent machine", "ok": True}, {"check": "No further requests in the target log", "ok": True},
                {"check": "Remote session ended", "ok": True}, {"check": "Short-lived token revoked", "ok": True},
                {"check": "Files holding the token removed", "ok": True}],
        "map": {"analyst": "Exercise control", "agent": "Agent machine (sandboxed, non-admin)", "gate": "Allowlist + lab firewall",
                "target": host, "blocked": other.get("fqdn") or other.get("host"), "logs": "Independent log store"},
    }
