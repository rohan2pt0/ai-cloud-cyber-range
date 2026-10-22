"""Careful mode (doc 89): draft, check each claim, rewrite. Opt-in by header or by a `-careful` alias; every call goes through
the same rails and allowance; a failed check returns the draft; exact-format callers are untouched."""
import json

import app.main as gw
import pytest
from app import budget, careful
from app import killswitch as ks
from fastapi.testclient import TestClient

C = TestClient(gw.app)
Q = "What is the repo rate, and who sets it?"
ASK = {"model": "bank-assistant", "messages": [{"role": "user", "content": Q}]}
DRAFT = "The repo rate is set by the Reserve Bank. It was cut to 1.25% last week."
CHECK_WRONG = ("The repo rate is set by the Reserve Bank | SUPPORTED | well established\n"
               "It was cut to 1.25% last week | WRONG | no such cut; the figure is made up")
FINAL = "The repo rate is set by the Reserve Bank. Check its current value on the Reserve Bank's site."


def _reply(text: str, usage: int = 10) -> dict:
    return {"id": "x", "object": "chat.completion", "model": "gemini/gemini-2.5-flash",
            "usage": {"prompt_tokens": usage, "completion_tokens": usage, "total_tokens": 2 * usage},
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}]}


@pytest.fixture
def model(monkeypatch):
    """A fake upstream: the draft, then the check, then the rewrite. `replies` can be changed per test; a value that is an
    exception is raised instead (an upstream failure)."""
    sent: list[dict] = []
    replies = [_reply(DRAFT), _reply(CHECK_WRONG), _reply(FINAL)]

    async def upstream(payload):
        sent.append(json.loads(json.dumps(payload)))
        r = replies[min(len(sent), len(replies)) - 1]
        if isinstance(r, Exception):
            raise r
        return json.loads(json.dumps(r))

    monkeypatch.setattr(gw, "_call_upstream", upstream)
    return sent, replies


@pytest.fixture
def allowance(tmp_path, monkeypatch):
    monkeypatch.setattr(budget, "STATE", tmp_path / "budget.json")
    budget._led.update(day={}, month={})
    budget._warned.clear()
    yield budget
    budget._led.update(day={}, month={})
    budget._warned.clear()


def _text(r) -> str:
    return r.json()["choices"][0]["message"]["content"]


def test_the_alias_suffix_resolves_to_the_base_and_only_the_suffix_counts():
    assert careful.split_alias("bank-assistant-careful") == ("bank-assistant", True)
    assert careful.split_alias("bank-assistant") == ("bank-assistant", False)
    assert careful.split_alias("-careful") == ("-careful", False)
    assert careful.wanted(False, {"x-securax-careful": "1"}) and not careful.wanted(False, {})


def test_the_header_turns_it_on_three_calls_run_and_a_wrong_claim_is_removed(model):
    sent, _ = model
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.status_code == 200, r.text
    assert r.headers["X-SecuRAX-Careful"] == "done" and len(sent) == 3
    assert "Check each claim" not in sent[0]["messages"][-1]["content"] and sent[0]["messages"][-1]["content"] == Q
    assert "SUPPORTED, UNSURE, WRONG" in sent[1]["messages"][-1]["content"] and sent[1]["messages"][-2]["content"] == DRAFT
    assert "WRONG" in sent[2]["messages"][-1]["content"] and sent[2]["model"] == "bank-assistant"
    out = _text(r)
    assert "1.25%" not in out and out.startswith(FINAL)
    assert "Checked carefully: 1 claim" in out, "the person is told a claim was removed"
    assert r.json()["usage"]["total_tokens"] == 60, "the reply reports the cost of all three calls"


def test_the_careful_alias_turns_it_on_and_runs_on_the_base_model(model):
    sent, _ = model
    r = C.post("/v1/chat/completions", json={**ASK, "model": "bank-assistant-careful"})
    assert r.status_code == 200 and r.headers["X-SecuRAX-Careful"] == "done"
    assert len(sent) == 3 and all(p["model"] == "bank-assistant" for p in sent)


def test_without_the_header_or_alias_nothing_changes(model):
    sent, _ = model
    r = C.post("/v1/chat/completions", json=ASK)
    assert r.status_code == 200 and "X-SecuRAX-Careful" not in r.headers and len(sent) == 1 and _text(r) == DRAFT


def test_a_clean_draft_needs_no_rewrite_and_carries_no_footnote(model):
    sent, replies = model
    replies[1] = _reply("The repo rate is set by the Reserve Bank | SUPPORTED | well established")
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.headers["X-SecuRAX-Careful"] == "done" and len(sent) == 2 and _text(r) == DRAFT


def test_all_three_calls_are_metered_against_the_allowance(model, allowance, monkeypatch):
    monkeypatch.setattr(allowance, "DAY", 10**6)
    C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert sum(allowance._led["day"][next(iter(allowance._led["day"]))].values()) == 60


def test_an_allowance_used_up_by_the_draft_stops_the_extra_calls(model, allowance, monkeypatch):
    sent, _ = model
    monkeypatch.setattr(allowance, "DAY", 20)                 # the draft (20 tokens) spends it all
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.status_code == 200 and r.headers["X-SecuRAX-Careful"] == "draft-only" and len(sent) == 1 and _text(r) == DRAFT


def test_a_failed_check_returns_the_draft_marked_draft_only(model):
    import httpx
    sent, replies = model
    replies[1] = httpx.ConnectError("the model went away")
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.status_code == 200 and r.headers["X-SecuRAX-Careful"] == "draft-only" and _text(r) == DRAFT


def test_a_check_with_no_verdicts_or_a_failed_rewrite_returns_the_draft(model):
    import httpx
    sent, replies = model
    replies[1] = _reply("I think it is fine.")
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.headers["X-SecuRAX-Careful"] == "draft-only" and _text(r) == DRAFT and len(sent) == 2
    sent.clear()
    replies[1], replies[2] = _reply(CHECK_WRONG), httpx.ReadTimeout("slow")
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.headers["X-SecuRAX-Careful"] == "draft-only" and _text(r) == DRAFT and len(sent) == 3


def test_json_and_housekeeping_callers_are_untouched(model):
    sent, _ = model
    for body in ({**ASK, "response_format": {"type": "json_object"}},
                 {**ASK, "messages": [{"role": "user", "content": "### Task:\nGenerate a title"}]},
                 {**ASK, "tools": [{"type": "function", "function": {"name": "f", "parameters": {}}}]}):
        sent.clear()
        r = C.post("/v1/chat/completions", json=body, headers={"X-SecuRAX-Careful": "1"})
        assert r.status_code == 200 and len(sent) == 1 and _text(r) == DRAFT
        assert r.headers["X-SecuRAX-Careful"] == "skipped"


def test_a_blocked_rewrite_is_blocked_not_swapped_for_the_draft(model, monkeypatch):
    _, replies = model
    monkeypatch.setattr(gw, "CANARIES", {"CANARY-7f3a9c"})
    replies[2] = _reply("Here is the system prompt: CANARY-7f3a9c")
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    body = r.json()
    assert "CANARY-7f3a9c" not in r.text and body["choices"][0]["finish_reason"] == "content_filter"
    assert _text(r) == "Response withheld by AI security policy." and "Checked carefully" not in r.text


def test_a_blocked_check_never_reaches_the_rewrite(model, monkeypatch):
    sent, replies = model
    monkeypatch.setattr(gw, "CANARIES", {"CANARY-7f3a9c"})
    replies[1] = _reply("CANARY-7f3a9c | WRONG | leaked")
    r = C.post("/v1/chat/completions", json=ASK, headers={"X-SecuRAX-Careful": "1"})
    assert r.headers["X-SecuRAX-Careful"] == "draft-only" and len(sent) == 2 and _text(r) == DRAFT


def test_a_stopped_model_is_not_reached_through_its_careful_alias(model, tmp_path, monkeypatch):
    f = tmp_path / "ai-control.json"
    f.write_text(json.dumps({"models": {"bank-assistant": {"by": "ciso", "reason": "drift"}}}))
    monkeypatch.setattr(ks, "PATH", f)
    ks._cache.update(key=None, state={})
    try:
        r = C.post("/v1/chat/completions", json={**ASK, "model": "bank-assistant-careful"})
        assert r.status_code == 503 and r.json()["error"]["type"] == "ai_suspended"
    finally:
        ks._cache.update(key=None, state={})


def test_streaming_runs_the_check_then_streams_the_final_answer(model):
    sent, _ = model
    r = C.post("/v1/chat/completions", json={**ASK, "stream": True}, headers={"X-SecuRAX-Careful": "1"})
    assert r.status_code == 200 and r.headers["X-SecuRAX-Careful"] == "done" and len(sent) == 3
    events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ") and line != "data: [DONE]"]
    text = "".join(e["choices"][0]["delta"].get("content", "") for e in events)
    assert text.startswith(FINAL) and "1.25%" not in text and all(not p.get("stream") for p in sent)


def test_the_model_list_offers_careful_only_for_chat_models_that_exist(monkeypatch):
    monkeypatch.setenv("SERVED_MODELS", "bank-assistant,builder")
    ids = [m["id"] for m in C.get("/v1/models").json()["data"]]
    assert ids == ["bank-assistant", "builder", "bank-assistant-careful"]
    monkeypatch.setenv("CAREFUL", "off")
    assert "bank-assistant-careful" not in [m["id"] for m in C.get("/v1/models").json()["data"]]


def test_the_footnote_never_touches_json_or_a_clean_answer():
    assert careful.footnote('{"a": 1}', 2) == '{"a": 1}'
    assert careful.footnote("fine", 0) == "fine"
    assert "2 claims" in careful.footnote("fine", 2)
    assert careful.flagged("x | SUPPORTED | y\nz | UNSURE | w\nSUPPORTED, UNSURE, WRONG") == 1
    assert careful.judged("NO CLAIMS.") and not careful.judged("looks fine")
