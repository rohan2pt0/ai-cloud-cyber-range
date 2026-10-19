#!/usr/bin/env python3
"""Verify the gateway's tamper-evident audit log (UK CAF C1.b; the hash-chain in apps/llm-gateway/app/main.py).

    ./securax audit verify            reads the running gateway's log
    python3 governance/auditchain.py < FILE

Every audit event carries {boot, seq, prev} and its own hash `h`. Within one gateway run (one `boot`), a line that was
edited, deleted, inserted or reordered breaks the chain at that point. A restart starts a new chain. Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import sys


def chain_hash(event: dict) -> str:          # must match apps/llm-gateway/app/main.py
    return hashlib.sha256(json.dumps(event, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def verify(lines) -> tuple[int, list[str]]:
    """(events checked, problems). Lines that are not chained audit events are ignored."""
    last: dict[str, tuple[int, str]] = {}
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
        where = f"run {c.get('boot')} event {c.get('seq')}"
        if chain_hash(ev) != h:
            out.append(f"{where}: the event was changed after it was written")
        prev = last.get(c.get("boot"))
        if prev is not None:                 # the first event seen of a run may be > 1: Docker rotates old lines out by design
            if c.get("seq") != prev[0] + 1:
                out.append(f"{where}: {c.get('seq') - prev[0] - 1} event(s) missing or out of order before this one")
            elif c.get("prev") != prev[1]:
                out.append(f"{where}: does not follow the event before it (a line was replaced)")
        last[c.get("boot")] = (c.get("seq"), h)
    return n, out


def main() -> int:
    n, probs = verify(sys.stdin)
    for p in probs:
        print("✗ " + p)
    if not n:
        print("no chained audit events found (is the gateway running a version with the tamper-evident log?)")
        return 1
    print(f"{'✗' if probs else '✔'} {n} audit events checked: " + (f"{len(probs)} problem(s)" if probs else "the chain is intact"))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
