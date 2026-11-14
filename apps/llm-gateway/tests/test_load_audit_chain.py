"""Load test of the tamper-evident audit chain (test campaign 2026-11-14). The gateway runs synchronous endpoints in a
thread pool, so audit events are written from many threads at once. Under that load the chain must stay one unbroken
line: every sequence number once, in order, and every event linked to the hash of the one before it. A fork here would
make an honest log look tampered with, or hide real tampering."""
import json
import logging
import sys
import threading

import app.main as m


def test_the_audit_chain_holds_under_concurrent_writers():
    lines = []

    class Grab(logging.Handler):
        def emit(self, record):
            lines.append(record.getMessage())

    h = Grab()
    m.audit.addHandler(h)
    lvl = m.audit.level
    m.audit.setLevel(logging.INFO)
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)          # switch threads as often as possible, so a race shows itself
    try:
        def worker(n):
            for i in range(150):
                m._emit({"event": "load_test", "worker": n, "i": i})
        ts = [threading.Thread(target=worker, args=(n,)) for n in range(32)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    finally:
        sys.setswitchinterval(old)
        m.audit.removeHandler(h)
        m.audit.setLevel(lvl)
    ev = [json.loads(x) for x in lines if '"load_test"' in x]
    assert len(ev) == 32 * 150
    by_seq = {}
    for e in ev:
        assert e["chain"]["seq"] not in by_seq, f"sequence {e['chain']['seq']} was written twice"
        by_seq[e["chain"]["seq"]] = e
    seqs = sorted(by_seq)
    assert seqs == list(range(seqs[0], seqs[0] + len(seqs))), "the sequence has gaps"
    for s in seqs[1:]:
        assert by_seq[s]["chain"]["prev"] == by_seq[s - 1]["h"], f"event {s} does not link to event {s - 1}: the chain forked"
        body = {k: v for k, v in by_seq[s].items() if k != "h"}
        assert m.chain_hash(body) == by_seq[s]["h"], f"event {s} hash does not match its content"
