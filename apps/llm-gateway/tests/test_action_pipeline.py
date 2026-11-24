"""The rejection pipeline (deterministic backbone, slice 2; threat model deterministic-backbone db-t1, db-r1, db-i1, db-d1, db-e1):
every AI-produced write passes schema, types, the gate and policy, an idempotency key and an audit append, or is rejected with
a machine-readable reason and NOTHING is written. An "ask" lands in the approvals list with the gate's reasons; an "auto" runs,
lands in the audit chain and can be undone inside its window, and only then."""
import json
import logging
import sys
import threading

import pytest
from app import actions, approvals
from fastapi.testclient import TestClient

TICK = {"type": "habit.tick", "payload": {"habit_id": "walk", "date": "2026-11-24"}, "confidence": 0.97}
PAY = {"type": "payment.send", "payload": {"payee_id": "landlord", "amount": 25000, "currency": "INR"}, "confidence": 0.99}


@pytest.fixture(autouse=True)
def _clean():
    approvals.reset()
    actions.reset()
    yield
    approvals.reset()


class Audit:
    def __init__(self, fail=False):
        self.events, self.fail = [], fail

    def __call__(self, e):
        if self.fail:
            raise OSError("audit log unavailable")
        self.events.append(json.loads(json.dumps(e, default=str)))


def run(p, emit=None, **kw):
    return actions.submit(p, emit=emit or Audit(), **kw)


# ---------------------------------------------------------------- the routes, end to end
def test_auto_executes_records_an_undo_and_audits_with_reasons():
    a = Audit()
    r = run(TICK, a, now=1000)
    assert r["status"] == "executed" and r["route"] == "auto" and r["undo_s"] == 300 and r["undo_until"] == 1300
    assert actions.ledger(now=1000)[0]["can_undo"] is True
    ev = [e for e in a.events if e["decision"] == "action_executed"]
    assert len(ev) == 1 and ev[0]["route"] == "auto" and ev[0]["reasons"] and "walk" not in json.dumps(ev)   # no payload values


def test_undo_works_inside_the_window_and_only_then():
    r = run(TICK, now=1000)
    with pytest.raises(ValueError, match="undo window .* has closed"):
        actions.undo(r["action_id"], emit=Audit(), now=1301)
    assert actions.undo(r["action_id"], emit=Audit(), now=1200)["status"] == "undone"
    with pytest.raises(ValueError, match="already undone"):
        actions.undo(r["action_id"], emit=Audit(), now=1201)
    with pytest.raises(KeyError, match="no action"):
        actions.undo("act_missing", emit=Audit())


def test_irreversible_with_high_confidence_lands_in_the_approvals_list_with_reasons_then_runs_once():
    a = Audit()
    r = run(PAY, a)
    assert r["status"] == "ask" and r["approve"].startswith("./securax approve ap_")
    pend = approvals.pending()
    assert len(pend) == 1 and pend[0]["id"] == r["approval_id"] and pend[0]["tool"] == "action:payment.send"
    assert any(x.startswith("irreversible") for x in pend[0]["reasons"])
    assert actions.ledger() == [] and any(e["decision"] == "action_ask" for e in a.events)      # nothing written yet
    assert run(PAY)["approval_id"] == r["approval_id"]                     # asking again does not add a second entry
    approvals.grant(r["approval_id"], by="owner")
    done = run(PAY)
    assert done["status"] == "executed" and done["undo_s"] == 0 and "approved" in done["reasons"][-1]
    with pytest.raises(ValueError, match="cannot be undone"):
        actions.undo(done["action_id"], emit=Audit())
    changed = {**PAY, "payload": {**PAY["payload"], "amount": 99000}}
    assert run(changed)["status"] == "ask"                                 # the grant covered that exact payload only


def test_unknown_type_falls_back_with_a_decision_request_and_writes_nothing():
    r = run({"type": "rocket.launch", "payload": {}, "confidence": 1.0})
    assert r["status"] == "rejected" and r["stage"] == "gate" and r["code"] == "fallback"
    assert r["decision_request"]["recommended"] == "do_nothing" and "unknown_action_type" in r["reasons"][0]
    assert actions.ledger() == [] and approvals.pending() == []


def test_personal_data_found_by_the_rails_makes_a_safe_type_ask_and_the_preview_is_redacted():
    mail = "asha" + chr(64) + "example.org"                               # built at run time (LESSONS 2026-11-14, pii gate)
    r = run({"type": "note.add", "payload": {"text": f"write to {mail}"}, "confidence": 0.99})
    assert r["status"] == "ask" and any(x.startswith("sensitive_data") for x in r["reasons"])
    assert mail not in json.dumps(approvals.pending())


def test_a_claim_can_only_make_it_stricter():
    r = run({**TICK, "claims": {"irreversible": False, "sensitivity": "none"}})
    assert r["route"] == "auto"
    assert run({**PAY, "claims": {"irreversible": False, "external": False}})["status"] == "ask"   # cannot unmark a payment
    assert run({**TICK, "payload": {"habit_id": "run"}, "claims": {"external": True}})["status"] == "ask"


def test_the_kill_switch_turns_ai_proposals_into_fallbacks(monkeypatch):
    monkeypatch.setattr(actions.killswitch, "stopped", lambda model: {"scope": "all", "by": "owner"})
    assert run(TICK)["code"] == "fallback"
    assert run({**TICK, "origin": "code"})["status"] == "executed"          # deterministic code is not the AI


# ---------------------------------------------------------------- each rejection stage, by its own message
@pytest.mark.parametrize("p,stage,code,msg", [
    ("not a dict", "schema", "not_an_object", "must be a JSON object"),
    ({"type": "habit.tick", "payload": {"habit_id": "w"}}, "schema", "missing_field", "'confidence' is required"),
    ({**TICK, "undo_s": 99999}, "schema", "unknown_field", "'undo_s' is not part of a proposal"),
    ({**TICK, "payload": {"date": "2026-11-24"}}, "schema", "missing_field", "'habit_id' is required"),
    ({**TICK, "payload": {"habit_id": "w", "sql": "DROP"}}, "schema", "unknown_field", "'sql' is not in the contract"),
    ({**TICK, "claims": {"route": "auto"}}, "schema", "unknown_field", "claims may hold only"),
    ({**TICK, "payload": {"habit_id": 7}}, "types", "wrong_type", "habit_id must be a string"),
    ({**TICK, "payload": {"habit_id": "w", "date": "tomorrow"}}, "types", "bad_format", "date does not have the expected format"),
    ({**PAY, "payload": {**PAY["payload"], "amount": 0}}, "types", "out_of_range", "amount must be at least 1"),
    ({**PAY, "payload": {**PAY["payload"], "amount": True}}, "types", "wrong_type", "amount must be a number"),
    ({**PAY, "payload": {**PAY["payload"], "currency": "BTC"}}, "types", "not_allowed", "currency must be one of"),
    ({**TICK, "type": "Habit Tick"}, "types", "bad_format", "type must look like 'area.verb'"),
    ({**TICK, "origin": "oracle"}, "types", "not_allowed", "origin must be 'model' or 'code'"),
    ({**TICK, "confidence": 0.2}, "gate", "fallback", "the gate did not let this run"),
])
def test_each_stage_rejects_with_a_machine_readable_reason(p, stage, code, msg):
    a = Audit()
    r = run(p, a)
    assert (r["status"], r["stage"], r["code"]) == ("rejected", stage, code)
    assert msg in r["message"] or msg in json.dumps(r)
    assert actions.ledger() == [] and approvals.pending() == []
    assert actions.stats()["rejected_by_stage"][stage] == 1
    assert any(e["decision"] == "action_rejected" and e["stage"] == stage for e in a.events)


def test_the_rejection_carries_its_reason_as_an_exception_too():
    with pytest.raises(actions.Rejected, match=r"^types: out_of_range: percent must be at most 100"):
        actions._check({"goal_id": "g", "percent": 101}, actions.CONTRACTS["goal.progress"]["schema"], "")


def test_a_failed_audit_append_writes_nothing():
    r = run(TICK, Audit(fail=True))
    assert (r["stage"], r["code"]) == ("audit", "audit_unavailable")
    assert actions.ledger() == [] and actions.stats()["rejected_by_stage"]["audit"] == 1


def test_a_failed_write_is_reported_not_kept():
    def broken(entry):
        raise OSError("disk full")
    r = run(TICK, executor=broken)
    assert r["status"] == "failed" and actions.stats()["executed"] == 0
    assert run(TICK)["status"] == "executed"                               # not cached as done: a retry can still run


# ---------------------------------------------------------------- idempotency and replay
def test_the_same_proposal_executes_once_and_a_reused_key_with_another_payload_is_refused():
    k = {"idempotency_key": "tick-walk-2026-11-24"}
    first = run({**TICK, **k})
    again = run({**TICK, **k})
    assert again["replayed"] is True and again["action_id"] == first["action_id"] and len(actions.ledger()) == 1
    other = run({**TICK, **k, "payload": {"habit_id": "read"}})
    assert (other["stage"], other["code"]) == ("idempotency", "key_reused")
    assert run(TICK)["action_id"] != first["action_id"] and len(actions.ledger()) == 2   # no key: its own (the payload hash)


def test_idempotency_holds_under_concurrent_callers():
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)                    # switch threads as often as possible, as test_load_audit_chain does
    results = []
    try:
        def worker(n):
            for i in range(40):
                p = {**TICK, "payload": {"habit_id": f"h{i}"}, "idempotency_key": f"key-{i:04d}-x"}
                results.append(run(p))
        ts = [threading.Thread(target=worker, args=(n,)) for n in range(16)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    finally:
        sys.setswitchinterval(old)
    assert len(actions.ledger()) == 40                                    # 16 callers x 40 proposals -> 40 writes
    s = actions.stats()
    assert s["executed"] == 40 and s["replayed"] == 16 * 40 - 40 and s["proposals"] == 16 * 40
    assert len({r["action_id"] for r in results}) == 40


def test_a_full_approvals_queue_falls_back_instead_of_growing(monkeypatch):
    monkeypatch.setattr(actions, "MAX_PENDING", 2)
    for i in range(2):
        assert run({**PAY, "payload": {**PAY["payload"], "amount": 10 + i}})["status"] == "ask"
    r = run({**PAY, "payload": {**PAY["payload"], "amount": 99}})
    assert r["code"] == "fallback" and "approvals_queue_full" in r["reasons"] and len(approvals.pending()) == 2


def test_stats_give_the_rejection_rate_and_the_model_share():
    run(TICK)
    run({**TICK, "payload": {"habit_id": "x"}, "origin": "code"})
    run({**TICK, "payload": {"habit_id": "y"}, "confidence": 0.1})
    run(PAY)
    s = actions.stats()
    assert s["proposals"] == 4 and s["executed"] == 2 and s["asked"] == 1 and s["rejected"] == 1
    assert s["rejection_rate"] == 0.25 and s["model_share"] == 0.75


# ---------------------------------------------------------------- the gateway endpoints
class _Loopback:
    """Loopback peer for the operator gate (Starlette's TestClient has no client= in CI's pin; LESSONS 2026-10-22)."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            scope = {**scope, "client": ("127.0.0.1", 0)}
        await self.app(scope, receive, send)


def test_the_endpoints_ask_execute_undo_and_count(caplog):
    import app.main as m
    caplog.set_level(logging.INFO, logger="audit")
    c = TestClient(_Loopback(m.app))
    r = c.post("/v1/actions/propose", json=TICK)
    assert r.status_code == 200 and r.json()["route"] == "auto"
    aid = r.json()["action_id"]
    assert c.get("/v1/actions").json()["actions"][0]["can_undo"] is True
    assert c.post(f"/v1/actions/{aid}/undo").json()["status"] == "undone"
    assert c.post(f"/v1/actions/{aid}/undo").status_code == 409
    r = c.post("/v1/actions/propose", json=PAY)
    assert r.status_code == 202
    listed = c.get("/v1/approvals").json()["pending"]
    assert listed[0]["id"] == r.json()["approval_id"] and listed[0]["reasons"]
    r = c.post("/v1/actions/propose", json={"type": "rocket.launch", "payload": {}, "confidence": 1})
    assert r.status_code == 422 and r.json()["stage"] == "gate"
    assert c.get("/v1/actions/stats").json()["rejected_by_stage"]["gate"] == 1
    assert 'guardrail_actions_total{outcome="executed"} 1' in c.get("/metrics").text
    chain = [json.loads(x.getMessage()) for x in caplog.records if x.name == "audit"]
    seen = {e["decision"] for e in chain if "chain" in e}
    assert {"action_executed", "action_undone", "action_ask", "action_rejected"} <= seen      # in the hash-chained log


def test_undo_and_the_ledger_are_refused_to_an_anonymous_off_box_caller():
    import app.main as m
    c = TestClient(m.app)                                                 # default peer: not loopback
    assert c.post("/v1/actions/act_x/undo").status_code == 403
    assert c.get("/v1/actions").status_code == 403
