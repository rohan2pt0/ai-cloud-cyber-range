"""Which model answered (doc 83): the gateway keeps a bounded, in-memory tally of served models over the last 24 h, so a quiet
fall from the strong model to a small local rung shows in the cockpit. Only model names and times are kept, never text."""
import time

import app.main as gw
import pytest
from app import identity as idn
from fastapi.testclient import TestClient

c = TestClient(gw.app)
ASK = {"model": "bank-assistant", "messages": [{"role": "user", "content": "hello"}]}


@pytest.fixture(autouse=True)
def _empty_tally():
    gw._SERVED.clear()
    yield
    gw._SERVED.clear()


def test_two_calls_are_counted_and_a_weak_fallback_is_named(monkeypatch):
    answers = iter(["gemini/gemini-2.5-flash", "ollama/qwen2.5:0.5b"])

    async def upstream(payload):
        return {"id": "x", "object": "chat.completion", "model": next(answers),
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "SECRET-ANSWER-TEXT"}}]}

    monkeypatch.setattr(gw, "_call_upstream", upstream)
    for _ in range(2):
        assert c.post("/v1/chat/completions", json=ASK).status_code == 200
    rep = c.get("/v1/served").json()
    assert rep["window_h"] == 24 and rep["calls"] == 2 and rep["weak_share"] == 0.5
    assert {(r["served"], r["calls"], r["weak"]) for r in rep["by_served"]} == {
        ("gemini/gemini-2.5-flash", 1, False), ("ollama/qwen2.5:0.5b", 1, True)}
    assert all(e[1] == "bank-assistant" for e in gw._SERVED), "the requested alias is kept with each call"
    assert "SECRET-ANSWER-TEXT" not in repr(list(gw._SERVED)) and "hello" not in repr(list(gw._SERVED)), "no text is stored"
    assert c.get("/v1/served", params={"model": "builder"}).json()["calls"] == 0


def test_the_mock_provider_path_is_counted_too():
    assert c.post("/v1/chat/completions", json=ASK).status_code == 200
    rep = c.get("/v1/served").json()
    assert rep["calls"] == 1 and rep["by_served"][0]["served"] == "bank-assistant" and rep["weak_share"] == 0.0


def test_calls_older_than_24_hours_drop_out():
    now = time.time()
    gw._note_served("bank-assistant", "ollama/qwen2.5:0.5b", now=now - 25 * 3600)
    gw._note_served("bank-assistant", "gemini/gemini-2.5-flash", now=now - 60)
    rep = gw._served_report(now=now)
    assert rep["calls"] == 1 and rep["weak_share"] == 0.0 and rep["by_served"][0]["served"] == "gemini/gemini-2.5-flash"
    assert len(gw._SERVED) == 1, "the stale entry is dropped, not just hidden"


def test_the_tally_is_capped():
    now = time.time()
    for i in range(gw.SERVED_CAP + 50):
        gw._note_served("bank-assistant", f"model-{i % 3}", now=now)
    assert len(gw._SERVED) == gw.SERVED_CAP
    assert gw._served_report(now=now)["calls"] == gw.SERVED_CAP


def test_the_endpoint_is_guarded_like_the_budget_report(monkeypatch):
    cfg = idn.Config(mode="required")
    cfg.api_keys = [{"id": "webui", "sha256": idn.hash_key("sk-good"), "roles": ["service"]},
                    {"id": "reader", "sha256": idn.hash_key("sk-user"), "roles": ["user"]}]
    monkeypatch.setattr(gw, "AUTH", idn.Authenticator(cfg))
    client = TestClient(gw.app)
    for path in ("/v1/budget", "/v1/served"):
        assert client.get(path).status_code == 401, path
        assert client.get(path, headers={"Authorization": "Bearer sk-user"}).status_code == 403, path
        assert client.get(path, headers={"Authorization": "Bearer sk-good"}).status_code == 200, path
