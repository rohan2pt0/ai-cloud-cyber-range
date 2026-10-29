"""Human-in-command tool-call approvals (doc 124): a require-approval tool is BLOCKED and recorded pending; a human grant
makes that EXACT (tool, args) pass exactly ONCE; a different argument, a second use, or an expired grant is blocked again;
three blocked calls in a row STOP and ask for a human. The grant endpoint is operator-only and audited. LLM06/ASI02."""
import json
import logging

import pytest
from app import approvals as ap
from app import guardrails as g
from fastapi.testclient import TestClient


# ---------------------------------------------------------------- approvals store (pure logic)
def test_grant_makes_the_exact_call_pass_once_only():
    ap.reset()
    args = '{"to":"ACME","amt":100}'
    assert ap.consume("wire_transfer", args) is False          # nothing granted yet
    pid = ap.record_pending("wire_transfer", args)
    assert pid in {p["id"] for p in ap.pending()}
    ap.grant(pid, by="asha")
    assert ap.consume("wire_transfer", args) is True           # first use: allowed
    assert ap.consume("wire_transfer", args) is False          # single-use: second blocked


def test_a_different_argument_is_not_covered_and_expiry_is_enforced():
    ap.reset()
    ap.grant(ap.record_pending("send_email", '{"to":"a@b.c"}'))
    assert ap.consume("send_email", '{"to":"EVIL@x.y"}') is False     # args-scoped
    ap.reset()
    ap.grant(ap.record_pending("send_email", "{}", now=1000), now=1000)
    assert ap.consume("send_email", "{}", now=1000 + ap.TTL_SECONDS + 1) is False   # expired


def test_unknown_pending_id_cannot_be_granted():
    ap.reset()
    with pytest.raises(KeyError):
        ap.grant("ap_nope")


# ---------------------------------------------------------------- guardrails integration
def _tc(name, args="{}"):
    return [{"id": "t1", "type": "function", "function": {"name": name, "arguments": args}}]


def test_inspect_blocks_and_records_pending_then_allows_after_grant():
    ap.reset()
    _, f1 = g.inspect_tool_calls(_tc("wire_transfer", '{"amt":5}'), approver=ap)
    assert any(x.rule == "TOOL-003-needs-approval" for x in f1)
    pend = ap.pending()
    assert pend and pend[0]["tool"] == "wire_transfer"
    ap.grant(pend[0]["id"])
    _, f2 = g.inspect_tool_calls(_tc("wire_transfer", '{"amt":5}'), approver=ap)
    assert any(x.rule == "TOOL-004-approved" for x in f2)
    assert not any(x.severity in g.BLOCKING for x in f2)       # the approved call is not withheld
    _, f3 = g.inspect_tool_calls(_tc("wire_transfer", '{"amt":5}'), approver=ap)
    assert any(x.rule == "TOOL-003-needs-approval" for x in f3)   # single-use: blocked again


def test_without_an_approver_a_require_approval_tool_still_blocks():
    ap.reset()
    _, f = g.inspect_tool_calls(_tc("wire_transfer"))
    assert any(x.rule == "TOOL-003-needs-approval" and x.severity in g.BLOCKING for x in f)
    assert not ap.pending()                                    # no approver → nothing recorded


# ---------------------------------------------------------------- the endpoints (operator-only, audited) and the chat loop
class _Loopback:
    """Set the ASGI client peer to loopback so the operator gate (loopback, or authenticated) is satisfied in tests
    (TestClient's default peer is not loopback; FastAPI's pinned Starlette has no client= option — LESSONS 2026-10-22)."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            scope = {**scope, "client": ("127.0.0.1", 0)}
        await self.app(scope, receive, send)


@pytest.fixture
def m():
    import app.main as main
    main.approvals.reset()
    return main


def test_list_and_grant_endpoints_and_audit(m, caplog):
    caplog.set_level(logging.INFO, logger="audit")
    c = TestClient(_Loopback(m.app))
    pid = m.approvals.record_pending("wire_transfer", '{"amt":9}')
    r = c.get("/v1/approvals")
    assert r.status_code == 200 and any(p["id"] == pid for p in r.json()["pending"])
    r = c.post(f"/v1/approvals/{pid}/approve")
    assert r.status_code == 200 and r.json()["approved"]["tool"] == "wire_transfer"
    assert m.approvals.consume("wire_transfer", '{"amt":9}') is True      # the grant really landed
    lines = [json.loads(x.getMessage()) for x in caplog.records if x.name == "audit"]
    assert any(e.get("decision") == "tool_approval_granted" and e.get("approval_id") == pid for e in lines)
    assert c.post("/v1/approvals/ap_missing/approve").status_code == 404


def test_grant_is_refused_to_an_anonymous_off_box_caller(m):
    c = TestClient(m.app)                                       # NOT loopback-wrapped: default peer is off-box
    pid = m.approvals.record_pending("wire_transfer", "{}")
    assert c.post(f"/v1/approvals/{pid}/approve").status_code == 403


def test_chat_withholds_a_transfer_until_approved_then_stops_after_three(m, monkeypatch):
    async def fake_upstream(payload):
        return {"model": "bank-assistant", "choices": [{"message": {"role": "assistant", "content": "",
                "tool_calls": _tc("wire_transfer", '{"to":"X","amt":1}')}, "finish_reason": "tool_calls"}], "usage": {}}
    monkeypatch.setattr(m, "_call_upstream", fake_upstream)
    c = TestClient(_Loopback(m.app))

    def once():
        return c.post("/v1/chat/completions", json={"model": "bank-assistant",
                      "messages": [{"role": "user", "content": "move funds"}]},
                      headers={"x-securax-conversation": "conv-A"})

    r1 = once()
    msg1 = r1.json()["choices"][0]["message"]["content"]
    assert "withheld" in msg1.lower() and not r1.json()["choices"][0]["message"].get("tool_calls")
    pend = m.approvals.pending()
    assert pend, "the blocked transfer should be recorded pending"
    # a second and third blocked call in the same conversation → stop and hand to a human
    once()
    r3 = once()
    assert "stopped" in r3.json()["choices"][0]["message"]["content"].lower()
