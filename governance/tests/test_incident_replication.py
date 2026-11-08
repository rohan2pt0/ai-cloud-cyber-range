"""Read-only replication of the regulatory incident clock (doc 91): an open incident is mirrored to every node, so a
node going off never loses sight of a running regulator deadline — while the authoritative tamper-evident chain stays
single-origin and a copy is never silently trusted. The transport itself is drilled by the two_nodes sandbox journey;
here we prove the incident layer on top of a fake in-memory store (no network)."""
import importlib.util
import pathlib
from datetime import datetime, timezone

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("incident", ROOT / "governance" / "incident.py")
inc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inc)
NOW = datetime(2026, 11, 4, tzinfo=timezone.utc)


def fake_store():
    store = {}

    def _sync(method, body=None, timeout=4):
        if method == "PUT":
            for k, v in (body.get("payload") or {}).items():
                store[k] = v          # last writer wins per key, like the real sync KV (None = tombstone)
            return {"ok": True}
        if method == "GET":
            return {"payload": dict(store)}
        return None
    return store, _sync


def test_an_open_incident_is_mirrored_read_only_self_verifying_and_tamper_evident(tmp_path, monkeypatch):
    store, _sync = fake_store()
    monkeypatch.setattr(inc, "_sync", _sync)
    monkeypatch.setenv("SYNC_TOKENS", "sbx-token")
    monkeypatch.setenv("SYNC_NODE_NAME", "node-a")

    # node A opens an incident — it is mirrored to the shared store under a node-namespaced key
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "a"))
    inc.main(["open", "Ransomware on a file server", "--regulators", "cert-in"], now=NOW)
    key = next(k for k in store if k.startswith("node-a:"))
    assert store[key]["node"] == "node-a" and store[key]["events"][0]["kind"] == "open"

    # node B (its own name and empty incident dir) sees it as a read-only, verified copy with the same deadlines
    monkeypatch.setenv("SYNC_NODE_NAME", "node-b")
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "b"))
    mirrors = inc.mirror_cases()
    assert len(mirrors) == 1
    mc = mirrors[0]
    assert mc.node == "node-a" and mc.verify() == [] and mc.state()["title"] == "Ransomware on a file server"

    # the copy is READ-ONLY: the authoritative chain is never forked from another node
    with pytest.raises(RuntimeError):
        mc.append("note", {"text": "edit from B"})

    # a tampered mirror is caught by the chain it carries — never silently trusted
    store[key]["events"][0]["data"]["title"] = "Altered"
    assert inc.mirror_cases()[0].verify(), "a tampered mirror must fail verification"


def test_same_incident_id_on_two_nodes_does_not_collide(tmp_path, monkeypatch):
    """INC-<date>-001 can be minted on two nodes for different incidents; the node-namespaced key keeps both."""
    store, _sync = fake_store()
    monkeypatch.setattr(inc, "_sync", _sync)
    monkeypatch.setenv("SYNC_TOKENS", "sbx-token")
    monkeypatch.setenv("SYNC_NODE_NAME", "node-a")
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "a"))
    inc.main(["open", "A-side event", "--regulators", "cert-in"], now=NOW)
    monkeypatch.setenv("SYNC_NODE_NAME", "node-b")
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "b"))
    inc.main(["open", "B-side event", "--regulators", "cert-in"], now=NOW)       # same INC-<date>-001 id, different incident
    assert len([k for k in store if ":INC-" in k]) == 2, "both nodes' same-id incidents are stored, not one overwriting the other"
    # from a third node, both are visible, each attributed to its origin
    monkeypatch.setenv("SYNC_NODE_NAME", "node-c")
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "c"))
    seen = {(m.node, m.state()["title"]) for m in inc.mirror_cases()}
    assert seen == {("node-a", "A-side event"), ("node-b", "B-side event")}


def test_closing_an_incident_tombstones_the_mirror(tmp_path, monkeypatch):
    store, _sync = fake_store()
    monkeypatch.setattr(inc, "_sync", _sync)
    monkeypatch.setenv("SYNC_TOKENS", "sbx-token")
    monkeypatch.setenv("SYNC_NODE_NAME", "node-a")
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "a"))
    inc.main(["open", "Phishing", "--regulators", "cert-in"], now=NOW)
    key = next(k for k in store if k.startswith("node-a:"))
    inc.main(["close", key.split(":", 1)[1]], now=NOW)
    assert store[key] is None, "a closed incident is tombstoned in the shared store (bounded, backups hold the record)"
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "b"))
    assert inc.mirror_cases() == [], "a closed incident is not shown as a live copy on other nodes"


def test_with_no_sync_configured_nothing_is_mirrored_and_the_tool_stays_offline(tmp_path, monkeypatch):
    monkeypatch.delenv("SYNC_TOKENS", raising=False)
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "a"))
    # _sync returns None with no token even if called; mirror_cases is empty and open still works
    assert inc.mirror_cases() == []
    assert inc.main(["open", "Local only", "--regulators", "cert-in"], now=NOW) == 0
    assert [c.verify() for c in inc.cases()] == [[]]
