"""Accurate answers without prompt engineering (doc 89): every chat request to a person-facing model carries today's date and
the answer rules a careful expert would write; exact-format callers and chat apps' housekeeping are left alone; and an answer
from a small offline model says so, except on JSON."""
import datetime as dt

import app.main as gw
from app import answering
from fastapi.testclient import TestClient

c = TestClient(gw.app)
AT = dt.datetime(2026, 10, 21, 9, 30, tzinfo=dt.timezone(dt.timedelta(minutes=330)))


def test_the_rules_name_the_date_and_forbid_inventing_things():
    r = answering.rules(AT)
    assert "Wednesday, 21 October 2026" in r and "UTC+05:30" in r
    for must in ("Never make up", "say so plainly", "may have changed", "false premise", "show the working", "exactly the format",
                 "India"):
        assert must in r, must


def test_the_rules_go_first_and_the_persons_own_instructions_still_follow():
    p = {"model": "bank-assistant", "messages": [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "hi"}]}
    assert answering.apply(p, at=AT)
    assert p["messages"][0]["role"] == "system" and answering.MARK in p["messages"][0]["content"]
    assert p["messages"][1]["content"] == "Be brief." and len(p["messages"]) == 3
    assert not answering.apply(p, at=AT), "never added twice (a retry, a chain of calls)"


def test_exact_format_callers_and_housekeeping_are_left_alone(monkeypatch):
    task = {"model": "bank-assistant", "messages": [{"role": "user", "content": "### Task:\nGenerate a concise title"}]}
    js = {"model": "bank-assistant", "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": "x"}]}
    build = {"model": "builder", "messages": [{"role": "user", "content": "write code"}]}
    for p in (task, js, build):
        assert not answering.apply(p, at=AT)
    assert not answering.apply({"model": "twin", "messages": [{"role": "user", "content": "x"}]}, {"x-answer-rules": "off"})
    monkeypatch.setenv("ANSWER_RULES", "off")
    assert not answering.apply({"model": "twin", "messages": [{"role": "user", "content": "x"}]})


def test_a_small_offline_model_says_so_but_never_on_json():
    p = {"model": "bank-assistant"}
    note = answering.footnote("Repo rate is 5.5%.", "ollama/qwen2.5:0.5b", p)
    assert "small offline model qwen2.5:0.5b" in note and note.startswith("Repo rate is 5.5%.")
    assert answering.footnote('{"severity": "high"}', "ollama/qwen2.5:0.5b", p) == '{"severity": "high"}'
    assert answering.footnote("fine", "ollama/qwen2.5:14b", p) == "fine", "a big local model (a GPU box) is not labelled"
    assert answering.footnote("fine", "gemini/gemini-2.5-flash", p) == "fine"
    assert answering.footnote("fine", "ollama/qwen2.5:0.5b", {"model": "builder"}) == "fine"
    assert answering.footnote("fine", "ollama/qwen2.5:0.5b", p, {"x-answer-note": "off"}) == "fine"


def test_through_the_real_gateway_the_rules_reach_the_model_and_the_note_reaches_the_person(monkeypatch):
    sent = []

    async def upstream(payload):
        sent.append(payload)
        return {"id": "x", "object": "chat.completion", "model": "ollama/qwen2.5:0.5b",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "It is Wednesday."}}]}

    monkeypatch.setattr(gw, "_call_upstream", upstream)
    r = c.post("/v1/chat/completions", json={"model": "bank-assistant", "messages": [{"role": "user", "content": "What day is it?"}]})
    assert r.status_code == 200, r.text
    first = sent[-1]["messages"][0]
    assert first["role"] == "system" and answering.MARK in first["content"] and "Today is" in first["content"]
    assert "small offline model" in r.json()["choices"][0]["message"]["content"]
    r = c.post("/v1/chat/completions", json={"model": "bank-assistant", "messages": [{"role": "user", "content": "### Task:\ntitle"}]})
    assert sent[-1]["messages"][0]["role"] == "user" and "small offline model" not in r.text


def test_a_question_about_something_that_changes_says_how_to_get_the_live_figure():
    ask = {"model": "bank-assistant", "messages": [{"role": "user", "content": "What is the current repo rate?"}]}
    out = answering.stale_note("It is 5.5%.", ask)
    assert out.startswith("It is 5.5%.") and answering.STALE in out and "globe" in out
    assert answering.stale_note(out, ask) == out, "never added twice"


def test_no_hint_when_search_results_came_with_it_or_the_question_does_not_change():
    searched = {"model": "bank-assistant", "messages": [
        {"role": "system", "content": "<context><source id='1'>rbi.org.in ...</source></context>"},
        {"role": "user", "content": "What is the current repo rate?"}]}
    assert answering.stale_note("5.5%", searched) == "5.5%"
    timeless = {"model": "bank-assistant", "messages": [{"role": "user", "content": "Explain how TLS works."}]}
    assert answering.stale_note("TLS ...", timeless) == "TLS ..."


def test_no_hint_on_json_exact_format_or_when_the_caller_opts_out():
    ask = {"model": "bank-assistant", "messages": [{"role": "user", "content": "latest NAV?"}]}
    assert answering.stale_note('{"nav": 1}', ask) == '{"nav": 1}'
    assert answering.stale_note("x", {**ask, "response_format": {"type": "json_object"}}) == "x"
    assert answering.stale_note("x", ask, {"x-answer-note": "off"}) == "x"
    assert answering.stale_note("x", {**ask, "model": "builder"}) == "x"            # only person-facing models
