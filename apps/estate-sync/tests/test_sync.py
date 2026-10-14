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


def _hello(ws, tok=TOK, user="me"):
    import json
    ws.send_text(json.dumps({"token": tok, "user": user}))


def test_ws_rejects_bad_token(client):
    from starlette.websockets import WebSocketDisconnect
    with client.websocket_connect("/sync/ws") as ws:
        _hello(ws, tok="wrong")
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_text()
        assert e.value.code == 4401


def test_ws_push_on_put_reaches_other_device_only_signal(client):
    import json
    with client.websocket_connect("/sync/ws") as ws:
        _hello(ws)
        assert json.loads(ws.receive_text())["type"] == "ready"
        r = client.put("/sync/state?user=me", headers=_h(),
                       json={"payload": {"a": "1"}, "meta": {"a": 5}, "updated_at": "2026-01-01T00:00:00Z"})
        assert r.status_code == 200
        msg = json.loads(ws.receive_text())
        assert msg["type"] == "changed" and msg["updated_at"] == "2026-01-01T00:00:00Z"
        assert "payload" not in msg            # signal only: data moves through the merge endpoint


def test_ws_other_users_not_notified(client):
    import json
    with client.websocket_connect("/sync/ws") as ws:
        _hello(ws, user="alice")
        assert json.loads(ws.receive_text())["type"] == "ready"
        client.put("/sync/state?user=bob", headers=_h(), json={"payload": {"a": "1"}, "meta": {}})
        assert client.get("/healthz").json()["sockets"] == 1   # alice still connected, nothing queued for her


def test_ws_carries_origin_so_writer_can_ignore_its_own_echo(client):
    import json
    with client.websocket_connect("/sync/ws") as ws:
        _hello(ws)
        ws.receive_text()
        client.put("/sync/state?user=me", headers=_h(), json={"payload": {"a": "1"}, "meta": {}, "device": "dev1"})
        assert json.loads(ws.receive_text())["origin"] == "dev1"


def _put(client, payload, meta=None, user="me"):
    return client.put(f"/sync/state?user={user}", headers=_h(), json={"payload": payload, "meta": meta or {}})


def test_every_put_keeps_todays_snapshot_and_reports_it(client):
    r = _put(client, {"a": "1"}, {"a": 5})
    assert r.json()["snapshots"] == 1 and r.json()["latest_snapshot"]
    _put(client, {"b": "2"}, {"b": 6})                      # same day: the snapshot is replaced by the later merged state, not duplicated
    lst = client.get("/sync/snapshots?user=me", headers=_h()).json()
    assert len(lst) == 1 and lst[0]["keys"] == 2
    day = lst[0]["day"]
    got = client.get(f"/sync/snapshots/{day}?user=me", headers=_h()).json()
    assert got["payload"] == {"a": "1", "b": "2"}


def test_snapshots_are_per_user_authenticated_and_validated(client):
    _put(client, {"a": "1"}, user="alice")
    assert client.get("/sync/snapshots?user=bob", headers=_h()).json() == []
    assert client.get("/sync/snapshots?user=alice").status_code == 401
    assert client.get("/sync/snapshots/2026-01-01?user=alice", headers=_h()).status_code == 404
    assert client.get("/sync/snapshots/not-a-day?user=alice", headers=_h()).status_code == 400


def test_old_snapshots_are_pruned(client, monkeypatch):
    import sqlite3

    import syncsvc.main as m
    _put(client, {"a": "1"})
    with sqlite3.connect(m.DB_PATH) as c:
        c.execute("INSERT INTO snapshots VALUES('me','2020-01-01','{}','{}','x')")
        c.execute("INSERT INTO snapshots VALUES('me','2099-01-01','{}','{}','x')")
    _put(client, {"b": "2"})
    days = [r["day"] for r in client.get("/sync/snapshots?user=me", headers=_h()).json()]
    assert "2020-01-01" not in days and "2099-01-01" in days and len(days) == 2
