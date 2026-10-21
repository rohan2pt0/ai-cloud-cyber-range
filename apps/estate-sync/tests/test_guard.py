"""Doc 87: a request limit per device token (429 + Retry-After, then served again), and one alert after repeated refused sign-ins.
Nobody is locked out, and no token ever appears in the alert or in /healthz. A fake clock moves time, so nothing sleeps."""
import importlib
import json

import pytest
from fastapi.testclient import TestClient

TOK, OTHER = "fake-device-token-alpha", "fake-device-token-bravo"


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", f"{TOK},{OTHER}")
    monkeypatch.setenv("SYNC_RATE_LIMIT", "5")
    monkeypatch.setenv("SYNC_RATE_WINDOW_S", "60")
    for k in ("SYNC_REFUSED_ALERT_AT", "SYNC_REFUSED_WINDOW_S", "SYNC_ACCESS_TEAM", "SYNC_ACCESS_AUD", "SYNC_ACCESS_EMAILS"):
        monkeypatch.delenv(k, raising=False)
    import syncsvc.main as m
    importlib.reload(m)
    clock = Clock()
    m.LIMITER.clock = clock
    m.REFUSED.clock = clock
    with TestClient(m.app) as c:
        yield m, c, clock, tmp_path / "refused-signins.jsonl"


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_defaults_are_600_a_minute_and_10_in_15_minutes(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    for k in ("SYNC_RATE_LIMIT", "SYNC_RATE_WINDOW_S", "SYNC_REFUSED_ALERT_AT", "SYNC_REFUSED_WINDOW_S"):
        monkeypatch.setenv(k, "junk")                      # a broken setting keeps the safe default, never switches the guard off
    import syncsvc.main as m
    importlib.reload(m)
    assert (m.LIMITER.limit, m.LIMITER.window) == (600, 60)
    assert (m.REFUSED.threshold, m.REFUSED.window) == (10, 900)
    for k, v in (("SYNC_RATE_LIMIT", "0"), ("SYNC_RATE_LIMIT", "-3")):
        monkeypatch.setenv(k, v)
        importlib.reload(m)
        assert m.LIMITER.limit == 600


def test_429_after_the_limit_then_served_again_after_the_window(svc):
    m, c, clock, _ = svc
    for _ in range(5):
        assert c.get("/sync/state?user=me", headers=h(TOK)).status_code == 404     # allowed (no data yet)
    r = c.get("/sync/state?user=me", headers=h(TOK))
    assert r.status_code == 429
    assert 1 <= int(r.headers["retry-after"]) <= 60
    assert TOK not in r.text
    clock.t += 30
    r = c.put("/sync/state?user=me", json={"payload": {"a": 1}, "meta": {"a": 5}}, headers=h(TOK))
    assert r.status_code == 429 and int(r.headers["retry-after"]) == 30            # the oldest hit leaves the window in 30 s
    clock.t += 30
    assert c.get("/sync/state?user=me", headers=h(TOK)).status_code == 404         # the window slid: served again


def test_another_token_is_unaffected(svc):
    m, c, clock, _ = svc
    for _ in range(6):
        c.get("/sync/state?user=me", headers=h(TOK))
    assert c.get("/sync/state?user=me", headers=h(TOK)).status_code == 429
    assert c.get("/sync/state?user=me", headers=h(OTHER)).status_code == 404
    assert c.get("/sync/users", headers=h(OTHER)).status_code == 200


def test_refused_requests_do_not_spend_a_tokens_allowance_and_health_is_not_limited(svc):
    m, c, clock, _ = svc
    for _ in range(20):
        assert c.get("/sync/state?user=me", headers=h("wrong-token")).status_code == 401
        assert c.get("/healthz").status_code == 200
    assert c.get("/sync/state?user=me", headers=h(TOK)).status_code == 404


def test_the_limiter_never_keeps_a_token_and_its_memory_is_bounded():
    from syncsvc import guard
    lim = guard.RateLimiter(2, 60, max_keys=3, clock=Clock())
    for i in range(10):
        lim.hit(guard.token_key(f"fake-token-{i}"))
    assert len(lim._hits) == 3
    assert not any("fake-token" in k for k in lim._hits)
    assert guard.token_key(TOK) != guard.token_key(OTHER) and TOK not in guard.token_key(TOK)


def test_refused_sign_ins_alert_once_at_the_threshold_and_never_lock_out(svc):
    m, c, clock, alerts = svc
    for _ in range(9):
        c.get("/sync/state?user=me", headers=h("guessed-token-" + TOK[:6]))
    assert not alerts.exists() and c.get("/healthz").json()["refused_signin_alerts"] == 0
    c.get("/sync/state?user=me", headers=h("guessed-token"))                           # the tenth in the window
    lines = alerts.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["count"] == 10 and rec["event"] == "refused sign-ins" and rec["addr"] and rec["ts"].endswith("Z")
    for _ in range(15):                                                                 # more of the same burst: still one line
        c.get("/sync/state?user=me", headers=h("guessed-token"))
    assert len(alerts.read_text().splitlines()) == 1
    health = c.get("/healthz")
    assert health.json()["refused_signin_alerts"] == 1
    assert c.get("/sync/state?user=me", headers=h(TOK)).status_code == 404             # the right token still works: no lockout
    for text in (alerts.read_text(), health.text):
        assert TOK not in text and OTHER not in text and "guessed-token" not in text and "Bearer" not in text
    clock.t += 901                                                                      # the window passes
    assert c.get("/healthz").json()["refused_signin_alerts"] == 0
    for _ in range(10):                                                                 # a new burst alerts again
        c.get("/sync/state?user=me", headers=h("guessed-token"))
    assert len(alerts.read_text().splitlines()) == 2


def test_a_refused_websocket_hello_counts_too(svc):
    m, c, clock, alerts = svc
    for _ in range(10):
        with c.websocket_connect("/sync/ws") as ws:
            ws.send_text(json.dumps({"token": "guessed-token", "user": "me"}))
            with pytest.raises(Exception):
                ws.receive_text()
    assert c.get("/healthz").json()["refused_signin_alerts"] == 1
    assert "guessed-token" not in alerts.read_text()


def test_the_alert_file_keeps_its_last_500_lines(tmp_path):
    from syncsvc import guard
    clock = Clock()
    path = tmp_path / "refused-signins.jsonl"
    rs = guard.RefusedSignins(1, 900, str(path), clock=clock)
    for i in range(guard.ALERT_LINES + 20):
        assert rs.refused(f"192.0.2.{i % 250}-{i}")                                     # documentation-range fake addresses
    lines = path.read_text().splitlines()
    assert len(lines) == guard.ALERT_LINES
    assert json.loads(lines[-1])["addr"].endswith(f"-{guard.ALERT_LINES + 19}")
    assert len(rs._seen) <= guard.MAX_KEYS
