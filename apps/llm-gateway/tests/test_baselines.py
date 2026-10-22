"""Per-caller baselines (doc 92): a stolen key is spotted by how it behaves. Every test drives an injected clock, never sleep."""
import hashlib
import json
import time

import app.main as gw
from app import baseline as bl
from app import identity as idn
from fastapi.testclient import TestClient

DAY0 = 1_800_000_000 // 86400 * 86400          # a fixed midnight UTC
H = 3600


def _seed(who="caller-a", model="bank-assistant", days=2, hours=range(9, 18), per_hour=3, start=DAY0):
    """A caller that works 09:00-17:59 UTC, a few calls an hour, on one model. Returns the time just after the seed."""
    for d in range(days):
        for h in hours:
            for i in range(per_hour):
                assert bl.observe(who, model, now=start + d * 86400 + h * H + i * 60) == []
    return start + days * 86400


def test_nothing_is_flagged_before_a_day_of_history():
    for i in range(3):
        bl.observe("fresh", "bank-assistant", now=DAY0 + 9 * H + i)
    t = DAY0 + 9 * H + 23 * H                      # 23 h later: a burst, a new model, an odd hour, and still nothing
    found = [a for i in range(100) for a in bl.observe("fresh", "other-model" if i % 2 else "bank-assistant", now=t + i)]
    assert found == [] and bl.report()["anomalies"] == []


def test_a_burst_is_flagged_once_per_hour():
    t = _seed() + 10 * H                           # a usual working hour
    found = [a for i in range(60) for a in bl.observe("caller-a", "bank-assistant", now=t + i)]
    assert [a["kind"] for a in found] == ["burst"], "one audit line for the hour, not one per request"
    assert "21 requests this hour" in found[0]["detail"] and found[0]["caller"] == "caller-a"
    nxt = [a for i in range(60) for a in bl.observe("caller-a", "bank-assistant", now=t + H + i)]
    assert [a["kind"] for a in nxt] == ["burst"], "a new hour of the same burst is a new line"


def test_a_usual_busy_hour_is_not_a_burst():
    t = _seed(per_hour=10) + 10 * H                # limit = max(20, 5 x 10) = 50
    assert [a for i in range(50) for a in bl.observe("caller-a", "bank-assistant", now=t + i)] == []


def test_a_new_model_is_flagged_once():
    t = _seed() + 10 * H
    first = bl.observe("caller-a", "gpt-big-cloud", now=t)
    assert [a["kind"] for a in first] == ["new_model"] and "gpt-big-cloud" in first[0]["detail"]
    assert bl.observe("caller-a", "gpt-big-cloud", now=t + 1) == []
    assert bl.observe("caller-a", "gpt-big-cloud", now=t + 5 * H) == [], "only once per model, even in a later hour"
    assert bl.observe("caller-a", "bank-assistant", now=t + 2) == [], "the usual model is never flagged"


def test_a_model_learned_in_the_first_day_is_usual():
    bl.observe("caller-a", "builder", now=DAY0 + 9 * H)
    t = _seed() + 10 * H
    assert bl.observe("caller-a", "builder", now=t) == []


def test_an_odd_hour_is_flagged_only_with_more_than_ten_requests():
    t = _seed() + 3 * H                            # 03:00 UTC: never active then
    quiet = [a for i in range(10) for a in bl.observe("caller-a", "bank-assistant", now=t + i)]
    assert quiet == [], "ten calls at an odd hour are not enough"
    loud = [a for i in range(30) for a in bl.observe("caller-a", "bank-assistant", now=t + 10 + i)]
    assert [a["kind"] for a in loud] == ["odd_hour", "burst"], "the 11th call is odd; the 21st is also a burst; each once"
    assert "03:00 UTC" in loud[0]["detail"]


def test_memory_caps_hold():
    for i in range(bl.MAX_CALLERS + 25):
        bl.observe(f"c{i}", "m", now=DAY0 + i)
    assert len(bl._callers) == bl.MAX_CALLERS and "c0" not in bl._callers and f"c{bl.MAX_CALLERS + 24}" in bl._callers
    bl.reset()
    t = _seed() + 10 * H
    for i in range(bl.MAX_ANOMALIES + 50):          # a key cycling through many models
        bl.observe("caller-a", f"model-{i}", now=t + i)
    c = bl._callers["caller-a"]
    assert len(c["models"]) == bl.MAX_MODELS and len(c["counts"]) == bl.HOURS and len(c["flagged"]) <= 2 * bl.MAX_MODELS
    assert len(bl._anomalies) == bl.MAX_ANOMALIES and len(bl.report()["anomalies"]) == bl.REPORT_N
    assert bl.report()["anomalies"][0]["detail"].startswith(f"asked for model-{bl.MAX_ANOMALIES + 49}"), "newest first"
    long = bl.observe("caller-a", "x" * 5000, now=t + 9999)
    assert len(long[0]["detail"]) < 200 and max(len(m) for m in c["models"]) <= bl.NAME_MAX


def test_baselines_survive_a_restart(tmp_path):
    t = _seed() + 10 * H
    bl.observe("caller-a", "gpt-big-cloud", now=t)
    p = tmp_path / "state.json"
    bl.save(p)
    before = json.loads(json.dumps(bl._callers))
    bl.reset()
    bl.load(p)
    assert json.loads(json.dumps(bl._callers)) == before and bl.report()["anomalies"][0]["kind"] == "new_model"
    assert bl.observe("caller-a", "gpt-big-cloud", now=t + 1) == [], "a restart does not re-flag a known model"
    p.write_text('{"callers": {"bad": {"first": "x"}}, "anomalies": [1, {"ts": 1}]}')
    bl.reset()
    bl.load(p)                                      # a damaged file is skipped, never a crash
    assert bl._callers == {} and bl.report()["anomalies"] == []


def test_a_new_model_through_the_gateway_is_audited_and_never_blocked(monkeypatch):
    events = []
    real = gw._emit
    monkeypatch.setattr(gw, "_emit", lambda e: (events.append(e), real(e)))
    principal = hashlib.sha256(b"testclient").hexdigest()[:12]        # auth off: the caller is the client address, hashed
    now = time.time()
    for h in range(48):
        bl.observe(principal, "bank-assistant", now=now - (48 - h) * H)
    client = TestClient(gw.app)
    ask = {"model": "never-used-model", "messages": [{"role": "user", "content": "hello SECRET-PROMPT-TEXT"}]}
    r = client.post("/v1/chat/completions", json=ask)
    assert r.status_code == 200, "detection only: the call still goes through"
    (ev,) = [e for e in events if e.get("decision") == "anomaly"]
    assert ev["kind"] == "new_model" and ev["principal"] == principal and "chain" in ev, "written into the audit chain"
    assert client.post("/v1/chat/completions", json=ask).status_code == 200
    assert len([e for e in events if e.get("decision") == "anomaly"]) == 1, "written once"
    rep = client.get("/v1/anomalies").json()
    assert rep["anomalies"][0]["kind"] == "new_model" and set(rep["anomalies"][0]) == {"ts", "caller", "kind", "detail"}
    bl.save()
    stored = json.dumps(bl._callers) + json.dumps(list(bl._anomalies)) + bl.STATE.read_text() + json.dumps(ev)
    assert "SECRET-PROMPT-TEXT" not in stored and "hello" not in stored, "no prompt or answer text is stored"


def test_a_key_is_named_by_its_id_never_by_its_secret(monkeypatch):
    cfg = idn.Config(mode="required")
    cfg.api_keys = [{"id": "webui", "sha256": idn.hash_key("sk-good-test-key"), "roles": ["service"]}]
    monkeypatch.setattr(gw, "AUTH", idn.Authenticator(cfg))
    client = TestClient(gw.app)
    ask = {"model": "bank-assistant", "messages": [{"role": "user", "content": "hi"}]}
    assert client.post("/v1/chat/completions", json=ask, headers={"Authorization": "Bearer sk-good-test-key"}).status_code == 200
    (c,) = bl._callers.values()
    assert c["name"] == "key:webui" and "sk-good-test-key" not in json.dumps(bl._callers)


def test_the_endpoint_is_guarded_like_the_budget_report(monkeypatch):
    cfg = idn.Config(mode="required")
    cfg.api_keys = [{"id": "webui", "sha256": idn.hash_key("sk-good"), "roles": ["service"]},
                    {"id": "reader", "sha256": idn.hash_key("sk-user"), "roles": ["user"]}]
    monkeypatch.setattr(gw, "AUTH", idn.Authenticator(cfg))
    client = TestClient(gw.app)
    for path in ("/v1/budget", "/v1/anomalies"):
        assert client.get(path).status_code == 401, path
        assert client.get(path, headers={"Authorization": "Bearer sk-user"}).status_code == 403, path
        assert client.get(path, headers={"Authorization": "Bearer sk-good"}).status_code == 200, path
