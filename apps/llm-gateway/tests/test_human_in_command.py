"""RBI MRM draft (June 2026): a person can stop one model or all AI at once (no restart, no API that can switch it back),
every answer discloses it is AI, and a per-caller daily token budget stops a runaway agent."""
import json

import pytest
from app import killswitch as ks
from app import main as m
from fastapi.testclient import TestClient

C = TestClient(m.app)
ASK = {"model": "bank-assistant", "messages": [{"role": "user", "content": "What is my branch's IFSC format?"}]}


@pytest.fixture
def ctl(tmp_path, monkeypatch):
    f = tmp_path / "ai-control.json"
    monkeypatch.setattr(ks, "PATH", f)
    ks._cache.update(key=None, state={})
    return f


def test_nothing_stopped_without_a_file_and_answers_say_they_are_ai(ctl):
    assert ks.stopped("bank-assistant") is None
    r = C.post("/v1/chat/completions", json=ASK)
    assert r.status_code == 200 and r.headers["X-AI-Generated"] == "true"


def test_stopping_one_model_refuses_it_at_once_and_leaves_the_others(ctl):
    ctl.write_text(json.dumps({"models": {"bank-assistant": {"by": "ciso", "at": "2026-10-17T10:00", "reason": "drift found in validation"}}}))
    r = C.post("/v1/chat/completions", json=ASK)
    assert r.status_code == 503 and r.json()["error"]["type"] == "ai_suspended"
    assert "drift found" in r.json()["error"]["message"] and "human" in r.json()["error"]["message"].lower()
    assert C.post("/v1/chat/completions", json={**ASK, "model": "bank-assistant-local"}).status_code == 200


def test_stop_all_and_resume_take_effect_without_a_restart(ctl):
    ctl.write_text(json.dumps({"all": {"by": "ciso", "reason": "incident"}, "models": {}}))
    assert C.post("/v1/chat/completions", json={**ASK, "model": "anything"}).status_code == 503
    ctl.write_text(json.dumps({"all": None, "models": {}, "note": "resumed"}))      # a different size: the change is seen
    assert C.post("/v1/chat/completions", json=ASK).status_code == 200


def test_a_malformed_switch_file_stops_all_ai(ctl):
    ctl.write_text("{not json")
    assert ks.stopped("bank-assistant")["scope"] == "all"


def test_a_daily_token_budget_stops_a_runaway_caller(ctl, monkeypatch):
    monkeypatch.setattr(m, "TOKEN_BUDGET_PER_DAY", 1)
    m._spent.clear()
    assert C.post("/v1/chat/completions", json=ASK).status_code == 200          # the first call spends the budget
    r = C.post("/v1/chat/completions", json=ASK)
    assert r.status_code == 429 and "budget" in r.json()["detail"]
    m._spent.clear()
