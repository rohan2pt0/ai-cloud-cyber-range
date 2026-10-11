"""estate-sync: auth is fail-closed, per-key timestamp merge is correct, blobs are bounded.

No external DB needed — the service uses stdlib sqlite3 against a temp file, so CI runs
it with zero infra. These lock in the contract the Guiding Map PWA depends on."""
import importlib

import pytest
from fastapi.testclient import TestClient

TOK = "test-device-token-123"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", f"{TOK}, another-token")
    import syncsvc.main as m
    importlib.reload(m)                       # pick up the patched env
    with TestClient(m.app) as c:              # TestClient context fires startup (db init)
        yield c


def _h(tok=TOK):
    return {"Authorization": f"Bearer {tok}"}


def test_auth_is_fail_closed_when_unconfigured(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.delenv("SYNC_TOKENS", raising=False)
    import syncsvc.main as m
    importlib.reload(m)
    with TestClient(m.app) as c:
        r = c.get("/sync/state?user=me", headers=_h())
        assert r.status_code == 503            # no tokens -> refuse, never an open store


def test_missing_or_bad_token_rejected(client):
    assert client.get("/sync/state?user=me").status_code == 401
    assert client.get("/sync/state?user=me", headers=_h("wrong")).status_code == 401


def test_get_before_any_put_is_404(client):
    assert client.get("/sync/state?user=me", headers=_h()).status_code == 404


def test_put_then_get_roundtrip(client):
    body = {"payload": {"gm_a": "1", "gm_b": "2"}, "meta": {"gm_a": 100, "gm_b": 100}}
    r = client.put("/sync/state?user=me", json=body, headers=_h())
    assert r.status_code == 200 and r.json()["keys"] == 2
    got = client.get("/sync/state?user=me", headers=_h()).json()
    assert got["payload"] == {"gm_a": "1", "gm_b": "2"}


def test_per_key_merge_newer_wins_older_ignored(client):
    client.put("/sync/state?user=me",
               json={"payload": {"gm_a": "old"}, "meta": {"gm_a": 100}}, headers=_h())
    # A stale device pushes an OLDER value for gm_a and a NEW key gm_c.
    client.put("/sync/state?user=me",
               json={"payload": {"gm_a": "stale", "gm_c": "new"}, "meta": {"gm_a": 50, "gm_c": 200}},
               headers=_h())
    got = client.get("/sync/state?user=me", headers=_h()).json()
    assert got["payload"]["gm_a"] == "old"     # older write did NOT clobber
    assert got["payload"]["gm_c"] == "new"     # genuinely new field accepted


def test_existing_keys_not_dropped_by_partial_push(client):
    client.put("/sync/state?user=me",
               json={"payload": {"gm_a": "1", "gm_b": "2"}, "meta": {"gm_a": 1, "gm_b": 1}}, headers=_h())
    client.put("/sync/state?user=me",
               json={"payload": {"gm_a": "1b"}, "meta": {"gm_a": 9}}, headers=_h())
    got = client.get("/sync/state?user=me", headers=_h()).json()
    assert got["payload"]["gm_b"] == "2"       # a device that never saw gm_b must not erase it


def test_users_are_isolated(client):
    client.put("/sync/state?user=alice", json={"payload": {"x": "a"}, "meta": {"x": 1}}, headers=_h())
    client.put("/sync/state?user=bob", json={"payload": {"x": "b"}, "meta": {"x": 1}}, headers=_h())
    assert client.get("/sync/state?user=alice", headers=_h()).json()["payload"]["x"] == "a"
    assert client.get("/sync/state?user=bob", headers=_h()).json()["payload"]["x"] == "b"


def test_oversized_body_rejected(client, monkeypatch):
    import syncsvc.main as m
    monkeypatch.setattr(m, "MAX_BODY", 50)
    r = client.put("/sync/state?user=me",
                   json={"payload": {"k": "x" * 1000}, "meta": {"k": 1}}, headers=_h())
    assert r.status_code == 413


def test_malformed_body_is_400_not_500(client):
    r = client.put("/sync/state?user=me", content=b"not json", headers=_h())
    assert r.status_code == 400
    r = client.put("/sync/state?user=me", json=[1, 2, 3], headers=_h())
    assert r.status_code == 400


def test_clock_head_ok(client):
    assert client.head("/sync/").status_code == 200
    assert client.head("/sync").status_code == 200
