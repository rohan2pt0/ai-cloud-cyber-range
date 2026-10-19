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


@pytest.fixture
def allowance(ctl, tmp_path, monkeypatch):
    from app import budget as b
    monkeypatch.setattr(b, "STATE", tmp_path / "budget.json")
    b._led.update(day={}, month={})
    b._warned.clear()
    yield b
    b._led.update(day={}, month={})
    b._warned.clear()


def test_the_daily_allowance_stops_a_runaway_caller_and_says_how_to_extend(allowance, monkeypatch):
    monkeypatch.setattr(allowance, "DAY", 1)
    assert C.post("/v1/chat/completions", json=ASK).status_code == 200          # the first call spends the allowance
    r = C.post("/v1/chat/completions", json=ASK)
    assert r.status_code == 429 and "today's AI allowance" in r.json()["detail"] and "ai budget extend --day" in r.json()["detail"]


def test_the_month_is_the_outer_limit_so_one_heavy_day_cannot_spend_it(allowance, monkeypatch):
    monkeypatch.setattr(allowance, "DAY", 10**9)
    monkeypatch.setattr(allowance, "MONTH", 1)
    C.post("/v1/chat/completions", json=ASK)
    r = C.post("/v1/chat/completions", json=ASK)
    assert r.status_code == 429 and "this month's" in r.json()["detail"]


def test_the_local_model_is_not_counted_by_default(allowance, monkeypatch):
    monkeypatch.setattr(allowance, "DAY", 1)
    for _ in range(3):
        assert C.post("/v1/chat/completions", json={**ASK, "model": "bank-assistant-local"}).status_code == 200


def test_a_warning_at_80_percent_then_an_extension_a_person_grants(allowance, ctl, monkeypatch):
    monkeypatch.setattr(allowance, "DAY", 100)
    assert allowance.spend("p1", 79) == [] and allowance.spend("p1", 1) == ["day"] and allowance.spend("p1", 1) == []   # warned once
    allowance.spend("p1", 19)
    assert allowance.refusal("p1")["period"] == "day"
    import time
    ctl.write_text(json.dumps({"budget_extensions": [{"period": "day", "for": time.strftime("%Y-%m-%d"), "tokens": 50, "caller": "*"}]}))
    assert allowance.refusal("p1") is None and allowance.limits("p1")[0] == 150
    assert allowance.headers("p1")["X-AI-Budget-Day-Left"] == "50"


def test_spend_survives_a_restart(allowance, monkeypatch):
    monkeypatch.setattr(allowance, "MONTH", 10)
    allowance.spend("p2", 7)
    allowance._led.update(day={}, month={})            # the gateway restarts
    allowance.load()
    assert allowance.used("p2")[1] == 7


def test_the_budget_report_lists_callers_by_hashed_id(allowance, monkeypatch):
    monkeypatch.setattr(allowance, "DAY", 1000)
    C.post("/v1/chat/completions", json=ASK)
    rep = C.get("/v1/budget").json()
    assert rep["day_limit"] == 1000 and rep["callers"] and len(rep["callers"][0]["caller"]) == 12
