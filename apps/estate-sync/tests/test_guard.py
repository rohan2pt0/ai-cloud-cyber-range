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


# ───────────── which address is the client: X-Real-IP only from a trusted proxy (doc 87) ─────────────
PROXY = ("172.18.0.5", 40000)          # a peer on the private Docker range (the bundled nginx)
OUTSIDE = ("198.51.100.7", 40000)      # documentation-range fake address: not a proxy


def _alert_addrs(alerts):
    return [json.loads(ln)["addr"] for ln in alerts.read_text().splitlines()] if alerts.exists() else []


def with_peer(app, peer):
    """The app as seen from one peer address. Starlette's TestClient(client=...) is newer than the pinned FastAPI
    0.115 stack CI installs, so the address is set in the ASGI scope instead; lifespan events pass through."""
    async def wrapped(scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            scope = {**scope, "client": peer}
        await app(scope, receive, send)
    return wrapped


def _refuse(m, client, n, real_ip=None):
    hdr = {**h("guessed-token"), **({"X-Real-IP": real_ip} if real_ip is not None else {})}
    with TestClient(with_peer(m.app, client)) as c:
        for _ in range(n):
            assert c.get("/sync/state?user=me", headers=hdr).status_code == 401


def test_a_trusted_proxys_x_real_ip_names_the_client(svc):
    m, c, clock, alerts = svc
    _refuse(m, PROXY, 10, real_ip="203.0.113.9")
    assert _alert_addrs(alerts) == ["203.0.113.9"]


def test_an_untrusted_peers_x_real_ip_is_ignored(svc):
    m, c, clock, alerts = svc
    _refuse(m, OUTSIDE, 10, real_ip="203.0.113.9")
    assert _alert_addrs(alerts) == ["198.51.100.7"]


@pytest.mark.parametrize("bad", ["not-an-address", "203.0.113.9, 198.51.100.1", "203.0.113.0/24", "", "x" * 200])
def test_a_garbage_x_real_ip_falls_back_to_the_peer(svc, bad):
    m, c, clock, alerts = svc
    _refuse(m, PROXY, 10, real_ip=bad)
    assert _alert_addrs(alerts) == ["172.18.0.5"]


def test_two_clients_behind_the_proxy_are_counted_separately(svc):
    m, c, clock, alerts = svc
    _refuse(m, PROXY, 9, real_ip="203.0.113.9")
    _refuse(m, PROXY, 9, real_ip="203.0.113.10")
    assert not alerts.exists()                                                        # 18 refusals, but 9 each: no alert
    _refuse(m, PROXY, 1, real_ip="203.0.113.10")
    assert _alert_addrs(alerts) == ["203.0.113.10"]


def test_the_websocket_hello_uses_the_same_rule(svc):
    m, c, clock, alerts = svc
    for client in (PROXY, OUTSIDE):
        with TestClient(with_peer(m.app, client)) as wc:
            for _ in range(10):
                with wc.websocket_connect("/sync/ws", headers={"X-Real-IP": "203.0.113.9"}) as ws:
                    ws.send_text(json.dumps({"token": "guessed-token", "user": "me"}))
                    with pytest.raises(Exception):
                        ws.receive_text()
    assert _alert_addrs(alerts) == ["203.0.113.9", "198.51.100.7"]


def test_trusted_proxies_default_setting_and_junk():
    from syncsvc import guard
    nets = guard.trusted_proxies("")
    assert {str(n) for n in nets} == {"127.0.0.0/8", "::1/128", "172.16.0.0/12"}
    assert {str(n) for n in guard.trusted_proxies(" 10.9.0.0/16 , 192.0.2.4 ,junk")} == {"10.9.0.0/16", "192.0.2.4/32"}
    assert guard.trusted_proxies("junk,also-junk") == ()                              # junk trusts NOBODY, never everybody
    assert guard.client_addr("172.18.0.5", ["203.0.113.9"], ()) == "172.18.0.5"
    assert guard.client_addr("::1", ["2001:db8::7"], nets) == "2001:db8::7"
    assert guard.client_addr("::ffff:172.18.0.5", ["203.0.113.9"], nets) == "203.0.113.9"      # IPv4-mapped peer is still the proxy
    assert guard.client_addr("172.18.0.5", ["203.0.113.9", "203.0.113.10"], nets) == "172.18.0.5"   # two headers: refused, not guessed
    assert guard.client_addr("172.18.0.5", [], nets) == "172.18.0.5"
    assert guard.client_addr("testclient", ["203.0.113.9"], nets) == "testclient"
    assert guard.client_addr("127.0.0.1", [" 203.0.113.9 "], nets) == "203.0.113.9"


def test_the_trusted_list_comes_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TRUSTED_PROXIES", "198.51.100.0/24")
    import syncsvc.main as m
    importlib.reload(m)
    try:
        assert [str(n) for n in m.TRUSTED_PROXIES] == ["198.51.100.0/24"]
        assert m.guard.client_addr("198.51.100.7", ["203.0.113.9"], m.TRUSTED_PROXIES) == "203.0.113.9"
        assert m.guard.client_addr("172.18.0.5", ["203.0.113.9"], m.TRUSTED_PROXIES) == "172.18.0.5"
    finally:
        monkeypatch.delenv("SYNC_TRUSTED_PROXIES")
        importlib.reload(m)
