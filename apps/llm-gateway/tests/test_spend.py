"""Rupee caps per AI provider (app/spend.py; owner 2026-11-08: Rs 1,000 a month each; queue spend-guard slice 1).
Each call is priced in rupees (LiteLLM's cost header, else a table, else a high unknown rate), charged to the provider that
really answered; 80% warns once a month; at the cap the local model answers instead, said in a header and the audit log;
a restart keeps the month and a new month starts at zero."""
import json

import pytest
from fastapi.testclient import TestClient

INFO = {"data": [
    {"model_name": "bank-assistant", "litellm_params": {"model": "gemini/gemini-3.5-flash-lite"}},
    {"model_name": "bank-assistant", "litellm_params": {"model": "ollama/qwen2.5:1.5b"}},
    {"model_name": "bank-assistant-local", "litellm_params": {"model": "ollama/qwen2.5:1.5b"}},
    {"model_name": "grok", "litellm_params": {"model": "xai/grok-4-fast"}},
]}


def reply(model, cost_usd=None, usage=None):
    r = {"id": "x", "object": "chat.completion", "model": model,
         "usage": usage or {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
         "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "ok"}}]}
    if cost_usd is not None:
        r["_cost_usd"] = cost_usd
    return r


def test_the_provider_of_a_model_comes_from_litellm():
    from app import spend
    spend.learn(INFO)
    assert spend.provider_of("bank-assistant") == "gemini"            # the ladder's head
    assert spend.provider_of("gemini-3.5-flash-lite") == "gemini"     # a served model id, without its prefix
    assert spend.provider_of("bank-assistant-local") == "ollama" and "ollama" in spend.FREE
    assert spend.provider_of("grok") == "xai"
    assert spend.provider_of("unknown-alias") == "cloud" and spend.provider_of("x-local", local_zone=True) == "local"


def test_prices_from_litellm_then_the_table_then_the_high_unknown_rate(monkeypatch):
    from app import spend
    monkeypatch.setenv("AI_INR_PER_USD", "95")
    assert spend.price("m", {}, 0.01) == (pytest.approx(0.95), "litellm")
    monkeypatch.setenv("AI_PRICES_INR", json.dumps({"m": [10, 40]}))
    assert spend.price("m", {"prompt_tokens": 1_000_000, "completion_tokens": 500_000}, None) == (pytest.approx(30.0), "table")
    monkeypatch.setenv("AI_UNKNOWN_INR_PER_MTOK", "1000")
    assert spend.price("other", {"prompt_tokens": 1000, "completion_tokens": 0}, None) == (pytest.approx(1.0), "unknown")


def test_caps_default_to_the_owners_rs_1000_and_can_differ_per_provider(monkeypatch):
    from app import spend
    monkeypatch.delenv("AI_SPEND_CAP_INR", raising=False)
    assert spend.cap("gemini") == 1000.0 and spend.cap("ollama") == 0.0
    monkeypatch.setenv("AI_SPEND_CAP_INR_GEMINI", "500")
    assert spend.cap("gemini") == 500.0 and spend.cap("xai") == 1000.0


def test_80_percent_warns_once_and_the_cap_is_reported_once(monkeypatch):
    from app import spend
    monkeypatch.setenv("AI_SPEND_CAP_INR", "100")
    assert spend.charge("gemini", 79) == []
    assert spend.charge("gemini", 2) == ["warn"]
    assert spend.charge("gemini", 5) == []                             # once a month, not on every call
    assert spend.charge("gemini", 20) == ["cap"] and spend.over("gemini")
    assert spend.charge("ollama", 50) == [] and spend.spent("ollama") == 0    # local is free and never counted


def test_a_restart_keeps_the_month_and_a_new_month_starts_at_zero(monkeypatch, tmp_path):
    from app import spend
    p = tmp_path / "s.json"
    spend.charge("gemini", 12.5, path=p)
    spend.reset()
    spend.load(p)
    assert spend.spent("gemini") == pytest.approx(12.5)
    spend._led["month"] = "2000-01"                                     # as if the stored month had ended
    assert spend.spent("gemini") == 0


def test_a_call_is_charged_to_the_provider_that_answered_and_says_its_cost(monkeypatch):
    import app.main as m
    from app import spend
    spend.learn(INFO)

    async def up(payload):
        return reply("gemini-3.5-flash-lite", cost_usd=0.002)
    monkeypatch.setattr(m, "_call_upstream", up)
    monkeypatch.setenv("AI_INR_PER_USD", "95")
    r = TestClient(m.app).post("/v1/chat/completions", json={"model": "bank-assistant", "messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200 and "_cost_usd" not in r.text            # the private key never reaches the caller
    assert float(r.headers["X-AI-Cost-INR"]) == pytest.approx(0.19)
    assert spend.spent("gemini") == pytest.approx(0.19)


def test_at_the_cap_the_local_model_answers_and_says_so(monkeypatch):
    import app.main as m
    from app import spend
    spend.learn(INFO)
    monkeypatch.setenv("AI_SPEND_CAP_INR", "10")
    spend.charge("gemini", 10)
    asked = []

    async def up(payload):
        asked.append(payload["model"])
        return reply("qwen2.5:1.5b")
    events = []
    monkeypatch.setattr(m, "_call_upstream", up)
    monkeypatch.setattr(m, "_emit", lambda e: events.append(e))
    r = TestClient(m.app).post("/v1/chat/completions", json={"model": "bank-assistant", "messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200 and asked == ["bank-assistant-local"]
    assert "cap is reached" in r.headers.get("X-AI-Spend", "") and float(r.headers["X-AI-Cost-INR"]) == 0
    assert any(e.get("decision") == "spend_cap_fallback" and e.get("provider") == "gemini" for e in events)
    # another provider under its cap still answers itself
    async def up2(payload):
        asked.append(payload["model"])
        return reply("grok-4-fast", cost_usd=0.0)
    monkeypatch.setattr(m, "_call_upstream", up2)
    TestClient(m.app).post("/v1/chat/completions", json={"model": "grok", "messages": [{"role": "user", "content": "hi"}]})
    assert asked[-1] == "grok"


def test_the_warning_reaches_the_audit_log(monkeypatch):
    import app.main as m
    from app import spend
    spend.learn(INFO)
    monkeypatch.setenv("AI_SPEND_CAP_INR", "1")
    monkeypatch.setenv("AI_INR_PER_USD", "100")

    async def up(payload):
        return reply("gemini-3.5-flash-lite", cost_usd=0.009)          # Rs 0.90 of Rs 1
    events = []
    monkeypatch.setattr(m, "_call_upstream", up)
    monkeypatch.setattr(m, "_emit", lambda e: events.append(e))
    TestClient(m.app).post("/v1/chat/completions", json={"model": "bank-assistant", "messages": [{"role": "user", "content": "hi"}]})
    assert any(e.get("decision") == "spend_warning" and e.get("provider") == "gemini" for e in events)


def test_the_spend_report_needs_the_metrics_role(monkeypatch):
    import app.main as m
    from app import spend
    spend.charge("gemini", 3)
    rep = spend.report()
    assert rep["providers"]["gemini"]["inr"] == 3 and rep["providers"]["gemini"]["cap_inr"] == 1000.0
    assert "/v1/spend" in {getattr(r, "path", "") for r in m.app.routes}
