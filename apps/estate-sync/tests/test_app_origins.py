"""Store apps (doc 98): an Android or iOS app runs from its own origin, so the sync service answers it, and only it: only the
state and snapshot calls, never with cookies, and the device token is still required."""
import importlib

import pytest
from fastapi.testclient import TestClient

TOKEN = "device-token-for-tests"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", TOKEN)
    monkeypatch.delenv("SYNC_APP_ORIGINS", raising=False)
    import syncsvc.main as m
    importlib.reload(m)
    with TestClient(m.app) as c:
        yield c


@pytest.mark.parametrize("origin", ["capacitor://localhost", "https://localhost"])
def test_the_app_origin_may_ask_and_read(client, origin):
    pre = client.options("/sync/state?user=me", headers={"Origin": origin, "Access-Control-Request-Method": "PUT"})
    assert pre.status_code == 204 and pre.headers["access-control-allow-origin"] == origin
    assert "authorization" in pre.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-credentials" not in pre.headers
    put = client.put("/sync/state?user=me", headers={"Origin": origin, "Authorization": f"Bearer {TOKEN}"},
                     json={"payload": {"osk:vantage:profile": "{}"}, "meta": {"osk:vantage:profile": 1}})
    assert put.status_code == 200 and put.headers["access-control-allow-origin"] == origin


def test_the_token_is_still_required(client):
    r = client.get("/sync/state?user=me", headers={"Origin": "capacitor://localhost"})
    assert r.status_code in (401, 403)


def test_other_origins_and_other_paths_get_nothing(client):
    r = client.options("/sync/state?user=me", headers={"Origin": "https://evil.example.invalid", "Access-Control-Request-Method": "PUT"})
    assert "access-control-allow-origin" not in r.headers
    r = client.get("/sync/users", headers={"Origin": "capacitor://localhost", "Authorization": f"Bearer {TOKEN}"})
    assert "access-control-allow-origin" not in r.headers
