#!/usr/bin/env python3
"""Verify the gateway's tamper-evident audit log (UK CAF C1.b; the hash-chain in apps/llm-gateway/app/main.py).

    ./securax audit verify [--rotated]    reads the running gateway's log
    python3 governance/auditchain.py [--rotated] < FILE

Every audit event carries {boot, seq, prev} and its own hash `h`. The chain continues across restarts: the first event of a
new run links to the last hash of the run before it, and the sequence number goes on. So a line that was edited, deleted,
inserted or reordered breaks the chain at that point, and so does a tail deleted before a restart. The gateway also writes an
`audit_gap` event when its stored head and the log disagree; the verifier always reports it. A log that begins mid-chain is a
failure (the first lines are missing); pass --rotated when the log was rotated on purpose. Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import sys


def chain_hash(event: dict) -> str:          # must match apps/llm-gateway/app/main.py
    return hashlib.sha256(json.dumps(event, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def verify(lines, rotated: bool = False) -> tuple[int, list[str]]:
    """(events checked, problems). Lines that are not chained audit events are ignored."""
    last: tuple[str, int, str] | None = None      # (run, seq, hash) of the event before this one
    n, out = 0, []
    for raw in lines:
        raw = raw.strip()
        i = raw.find("{")
        if i < 0:
            continue
        try:
            ev = json.loads(raw[i:])
        except ValueError:
            continue
        if not isinstance(ev, dict) or "chain" not in ev or "h" not in ev:
            continue
        n += 1
        h = ev.pop("h")
        c = ev["chain"]
        boot, seq, prev = c.get("boot"), c.get("seq"), c.get("prev")
        where = f"run {boot} event {seq}"
        if chain_hash(ev) != h:
            out.append(f"{where}: the event was changed after it was written")
        if ev.get("decision") == "audit_gap":
            out.append(f"{where}: the gateway recorded a gap in the chain at a restart ({ev.get('reason', 'head and log disagree')}); "
                       "events were deleted or changed before this point, and this record stays for good")
        if not isinstance(seq, int):
            out.append(f"{where}: no usable sequence number")
        elif last is None:
            if not rotated and not (seq == 1 and prev == "0" * 64):
                out.append(f"{where}: the log starts here, not at the beginning: the first line(s) are missing "
                           "(use --rotated if the log was rotated on purpose)")
        elif boot == last[0]:
            if seq != last[1] + 1:
                out.append(f"{where}: {seq - last[1] - 1} event(s) missing or out of order before this one")
            elif prev != last[2]:
                out.append(f"{where}: does not follow the event before it (a line was replaced)")
        else:                                       # the gateway restarted: the new run must continue the old one
            if prev == "0" * 64 and seq == 1:
                if not (ev.get("decision") == "boot" and ev.get("first_boot") is True):
                    out.append(f"{where}: the gateway restarted with a fresh chain and no link to run {last[0]} "
                               "(a log from before restart-proof chaining, or the end of the log was deleted)")
            elif seq != last[1] + 1 or prev != last[2]:
                gone = seq - last[1] - 1
                out.append(f"{where}: does not continue from run {last[0]} event {last[1]}: "
                           + (f"{gone} event(s) at the end of the previous run were deleted before the restart"
                              if gone > 0 else "the end of the previous run was changed or replaced"))
        if isinstance(seq, int):
            last = (boot, seq, h)
    return n, out


def main() -> int:
    n, probs = verify(sys.stdin, rotated="--rotated" in sys.argv[1:])
    for p in probs:
        print("✗ " + p)
    if not n:
        print("no chained audit events found (is the gateway running a version with the tamper-evident log?)")
        return 1
    print(f"{'✗' if probs else '✔'} {n} audit events checked: " + (f"{len(probs)} problem(s)" if probs else "the chain is intact"))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
