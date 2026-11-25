"""The audit chain survives a restart (doc 105 gap G14): the chain head is stored beside the log, the next run links to the
last hash of the one before it, and a tail deleted before a restart, an edited line, a reordering or a missing first line
is named by the verifier. A mismatch between the head and the log is recorded as an `audit_gap` event, never repaired quietly."""
import importlib.util
import json
import logging
import pathlib
import threading
import time

import pytest
from app import main as m

_s = importlib.util.spec_from_file_location("auditchain", pathlib.Path(__file__).resolve().parents[3] / "governance" / "auditchain.py")
ac = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ac)


class Run:
    """A fake gateway lifetime: captures audit lines in memory and writes them to a real log file, like AUDIT_LOG_FILE."""

    def __init__(self, tmp_path):
        self.head = tmp_path / "audit-head.json"
        self.log = tmp_path / "audit.log"
        self.lines = []
        run = self

        class Grab(logging.Handler):
            def emit(self, record):
                msg = record.getMessage()
                run.lines.append(msg)
                with open(run.log, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
        self.h = Grab()
        m.audit.addHandler(self.h)
        self.lvl = m.audit.level
        m.audit.setLevel(logging.INFO)

    def boot(self, with_log=True):
        m._CHAIN.update(boot="stale000", seq=0, prev="0" * 64)      # a new process starts with nothing in memory
        return m.chain_boot(self.head, str(self.log) if with_log else "")

    def events(self, n):
        for i in range(n):
            m._emit({"decision": "allow", "i": i})

    def close(self):
        m.audit.removeHandler(self.h)
        m.audit.setLevel(self.lvl)

    def rewrite_log(self, lines):
        self.lines = list(lines)
        self.log.write_text("".join(x + "\n" for x in lines), "utf-8")


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "HEAD_EVERY", 1)                          # an exact head for most tests; batching has its own test
    r = Run(tmp_path)
    yield r
    r.close()


def test_events_restart_events_verify_across_the_boundary(run):
    assert run.boot()["status"] == "first_boot"
    run.events(3)
    before = json.loads(run.lines[-1])
    assert run.boot()["status"] == "continued"
    run.events(2)
    n, probs = ac.verify(run.lines)
    assert probs == [] and n == len(run.lines)
    bootev = [json.loads(x) for x in run.lines if '"decision": "boot"' in x][1]
    assert bootev["previous_seq"] == before["chain"]["seq"] and bootev["first_boot"] is False
    assert bootev["chain"]["prev"] == before["h"] and bootev["chain"]["seq"] == before["chain"]["seq"] + 1


def test_no_head_file_means_a_first_boot_recorded_explicitly(run):
    assert not run.head.exists()
    assert run.boot(with_log=False)["status"] == "first_boot"
    first = json.loads(run.lines[0])
    assert first["first_boot"] is True and first["chain"]["prev"] == "0" * 64 and first["chain"]["seq"] == 1
    assert ac.verify(run.lines) == (1, [])
    head = json.loads(run.head.read_text("utf-8"))
    assert head["seq"] == 1 and head["prev"] == first["h"] and head["boot"] == first["chain"]["boot"] and head["ts"]


def test_the_head_is_written_atomically_after_every_event(run):
    run.boot()
    run.events(2)
    assert json.loads(run.head.read_text("utf-8"))["prev"] == json.loads(run.lines[-1])["h"]
    assert not run.head.with_name(run.head.name + ".tmp").exists()


def test_tail_deleted_with_a_log_file_is_an_audit_gap_and_flagged(run):
    run.boot()
    run.events(5)
    run.rewrite_log(run.lines[:-3])                                  # an attacker removes the last 3 lines
    assert run.boot()["status"] == "gap"
    run.events(1)
    gap = [json.loads(x) for x in run.lines if '"audit_gap"' in x]
    assert len(gap) == 1 and gap[0]["head"]["seq"] == 6 and gap[0]["log_last"]["seq"] == 3
    probs = ac.verify(run.lines)[1]
    assert any("gap in the chain" in p for p in probs)
    assert len(probs) == 1                                           # the chain itself continues from the real last line


def test_tail_deleted_without_a_log_file_is_a_break_the_verifier_names(run):
    run.boot(with_log=False)
    run.events(5)
    kept = run.lines[:-3]
    run.boot(with_log=False)                                         # head remembers seq 6; the log lost the last 3
    run.events(1)
    probs = ac.verify(kept + run.lines[6:])[1]
    assert any("3 event(s) at the end of the previous run were deleted before the restart" in p for p in probs), probs


def test_a_damaged_head_is_recorded_not_silently_repaired(run):
    run.boot()
    run.events(2)
    run.head.write_text("{not json", "utf-8")
    assert run.boot()["status"] == "head_unreadable"
    probs = ac.verify(run.lines)[1]
    assert any("gap in the chain" in p and "head file" in p for p in probs)


def test_a_deleted_head_with_a_log_is_an_audit_gap(run):
    run.boot()
    run.events(2)
    run.head.unlink()
    assert run.boot()["status"] == "head_missing"
    assert any('"audit_gap"' in x for x in run.lines)


def test_a_crash_between_log_line_and_head_is_not_a_gap(run):
    run.boot()
    run.events(2)
    good = run.head.read_text("utf-8")
    run.events(1)
    run.head.write_text(good, "utf-8")                               # the head is one event behind the log
    assert run.boot()["status"] == "continued_after_crash"
    assert ac.verify(run.lines)[1] == []


def test_an_edited_line_fails(run):
    run.boot()
    run.events(3)
    ev = json.loads(run.lines[2])
    ev["decision"] = "allow-but-edited"
    probs = ac.verify(run.lines[:2] + [json.dumps(ev)] + run.lines[3:])[1]
    assert any("changed after it was written" in p for p in probs)


def test_reordering_and_a_missing_first_line_fail(run):
    run.boot()
    run.events(3)
    swapped = [run.lines[1], run.lines[0]] + run.lines[2:]
    assert ac.verify(swapped)[1]
    probs = ac.verify(run.lines[1:])[1]
    assert any("first line(s) are missing" in p for p in probs)
    assert ac.verify(run.lines[1:], rotated=True)[1] == []           # a log rotated on purpose may begin mid-chain


def test_a_fresh_chain_in_the_middle_of_the_log_fails(run):
    run.boot()
    run.events(2)
    m._CHAIN.update(boot="newrun01", seq=0, prev="0" * 64)           # an old gateway: restart with no link
    m._emit({"decision": "allow"})
    probs = ac.verify(run.lines)[1]
    assert any("fresh chain" in p for p in probs)


def test_an_unwritable_head_never_stops_the_gateway(run, monkeypatch):
    monkeypatch.setattr(m, "AUDIT_HEAD", run.head.parent / "no-such-dir" / "audit-head.json")
    before = m._metrics["audit_head_write_error"]
    m._emit({"decision": "allow"})
    assert m._metrics["audit_head_write_error"] > before


def test_a_burst_batches_the_head_write_and_shutdown_flushes_it(run, monkeypatch):
    monkeypatch.setattr(m, "HEAD_EVERY", 16)
    monkeypatch.setattr(m, "HEAD_MAX_AGE_S", 3600.0)
    run.boot()
    m._HEAD.update(pending=0, at=time.monotonic())
    run.events(5)
    on_disk = json.loads(run.head.read_text("utf-8"))
    assert on_disk["seq"] == 1                                       # only the boot event so far: 5 events are batched
    run.events(11)
    assert json.loads(run.head.read_text("utf-8"))["seq"] == 17      # the 16th event since the last write wrote it
    run.events(3)
    with m._CHAIN_LOCK:
        m._save_head(sync=True)                                      # what the shutdown hook does
    assert json.loads(run.head.read_text("utf-8"))["prev"] == json.loads(run.lines[-1])["h"]


def test_the_head_costs_little_per_event(run, capsys, monkeypatch):
    monkeypatch.setattr(m, "HEAD_EVERY", 16)
    run.boot()
    m.audit.removeHandler(run.h)                                     # measure the gateway's own work, not the test's handler
    m._HEAD.update(pending=0, at=0.0)
    t = time.perf_counter()
    for _ in range(2000):
        m._emit({"decision": "allow"})
    with_head = (time.perf_counter() - t) / 2000 * 1000
    saved = m._save_head
    m._save_head = lambda sync=False: True
    try:
        t = time.perf_counter()
        for _ in range(2000):
            m._emit({"decision": "allow"})
        without = (time.perf_counter() - t) / 2000 * 1000
    finally:
        m._save_head = saved
    with capsys.disabled():
        print(f"\naudit emit: {with_head:.3f} ms/event with the head write, {without:.3f} ms/event without; head costs {with_head - without:.3f} ms")
    assert with_head - without < 2.0                                 # a loose guard; the measured figure is printed above


def test_load_with_32_writers_and_a_restart_in_the_middle_still_verifies(run):
    run.boot()

    def worker(n):
        for i in range(60):
            m._emit({"event": "load_test", "worker": n, "i": i})

    for _ in range(2):
        ts = [threading.Thread(target=worker, args=(n,)) for n in range(32)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        run.boot()
    n, probs = ac.verify(run.lines)
    assert probs == [] and n == 2 * 32 * 60 + 3
