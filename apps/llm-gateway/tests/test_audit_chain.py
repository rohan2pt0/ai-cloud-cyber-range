"""Tamper-evident audit (UK CAF C1.b): an edited, deleted or reordered event breaks the chain the verifier checks."""
import importlib.util
import json
import logging
import pathlib

from app import main as m
from fastapi.testclient import TestClient

_s = importlib.util.spec_from_file_location("auditchain", pathlib.Path(__file__).resolve().parents[3] / "governance" / "auditchain.py")
ac = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ac)


def _events(caplog, n=3):
    caplog.set_level(logging.INFO, logger="audit")
    c = TestClient(m.app)
    m._CHAIN.update(boot="testrun1", seq=0, prev="0" * 64)
    for _ in range(n):
        c.post("/v1/chat/completions", json={"model": "bank-assistant", "messages": [{"role": "user", "content": "hello"}]})
    return [r.getMessage() for r in caplog.records if r.name == "audit"]


def test_the_chain_verifies_and_shares_one_hash_function(caplog):
    lines = _events(caplog)
    assert lines and ac.verify(lines) == (len(lines), [])
    ev = json.loads(lines[0])
    h = ev.pop("h")
    assert m.chain_hash(ev) == ac.chain_hash(ev) == h


def test_editing_deleting_or_reordering_is_detected(caplog):
    lines = _events(caplog)
    edited = json.loads(lines[1])
    edited["decision"] = "allow-but-edited"
    assert any("changed" in p for p in ac.verify([lines[0], json.dumps(edited)] + lines[2:])[1])
    assert any("missing" in p for p in ac.verify([lines[0]] + lines[2:])[1])
    assert ac.verify([lines[1], lines[0]] + lines[2:])[1]
