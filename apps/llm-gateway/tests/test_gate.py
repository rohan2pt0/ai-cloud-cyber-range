"""The decision gate (deterministic backbone, slice 1; threat model deterministic-backbone db-s1, db-s2, db-e1): plain code
routes every AI-proposed action to auto (with an undo), ask (a person first) or fallback (no action, a decision request).
Confidence can only lower the route; irreversibility, reach and sensitivity are facts from code, never bought by a number."""
import pytest
from app import actions, gate

SAFE = {"policy": "allow", "confidence": 0.97, "irreversible": False, "external": False,
        "criticality": "low", "sensitivity": "none"}


def d(**over):
    return gate.decide({**SAFE, **over})


def test_reversible_internal_high_confidence_runs_with_an_undo_window():
    r = d()
    assert r["route"] == "auto" and r["undo_s"] == 300 and r["reasons"][0].startswith("auto:")


def test_irreversible_asks_whatever_the_confidence():
    for conf in (1.0, 0.97, 0.6, 0.1):
        r = d(irreversible=True, confidence=conf)
        assert r["route"] == "ask" and r["undo_s"] == 0
        assert any(x.startswith("irreversible") for x in r["reasons"])
    assert d(irreversible=True, confidence=0.1)["recommended"] == "reject"     # a guess at something final: lean to no


def test_unknown_type_and_policy_block_fall_back_to_no_action():
    r = gate.decide({**SAFE, "confidence": 1.0}, known=False)
    assert r["route"] == "fallback" and r["recommended"] == "do_nothing" and "unknown_action_type" in r["reasons"][0]
    assert d(policy="deny")["route"] == "fallback" and "policy_blocked" in d(policy="deny")["reasons"][0]
    assert d(policy="none")["route"] == "fallback"
    assert d(policy="something-odd")["route"] == "fallback"                   # an unreadable policy is no policy


def test_the_kill_switch_stops_every_ai_proposal():
    assert d(ai_stopped=True)["route"] == "fallback"


@pytest.mark.parametrize("conf,route", [(0.0, "fallback"), (0.49, "fallback"), (0.5, "ask"), (0.89, "ask"), (0.9, "auto"),
                                        (1.0, "auto")])
def test_the_confidence_bands(conf, route):
    assert d(confidence=conf)["route"] == route


@pytest.mark.parametrize("bad", [None, "0.99", True, float("nan"), float("inf"), -0.1, 1.01, [0.99]])
def test_a_missing_or_spoofed_confidence_falls_back(bad):
    r = d(confidence=bad)
    assert r["route"] == "fallback" and "confidence_invalid" in r["reasons"][0]


@pytest.mark.parametrize("over,reason", [({"external": True}, "external"), ({"criticality": "high"}, "criticality_high"),
                                         ({"criticality": "critical"}, "criticality_critical"),
                                         ({"sensitivity": "medium"}, "sensitive_data_medium"),
                                         ({"sensitivity": "typo"}, "sensitive_data_critical"),
                                         ({"policy": "require_approval"}, "policy_requires_approval")])
def test_reach_weight_personal_data_or_policy_ask_even_at_high_confidence(over, reason):
    r = d(**over)
    assert r["route"] == "ask" and any(x.startswith(reason) for x in r["reasons"]) and r["undo_s"] == 0


def test_the_undo_window_comes_from_the_server_and_is_clamped(monkeypatch):
    monkeypatch.setenv("GATE_UNDO_S", "5")
    assert d()["undo_s"] == gate.UNDO_MIN_S
    monkeypatch.setenv("GATE_UNDO_S", "99999999")
    assert d()["undo_s"] == gate.UNDO_MAX_S
    monkeypatch.setenv("GATE_UNDO_S", "abc")
    assert d()["undo_s"] == 300
    assert d(undo_s=1)["undo_s"] == 300                    # a field in the action is ignored: the gate alone sets it


def test_the_gate_is_pure_and_deterministic():
    a = {**SAFE}
    assert [gate.decide(a) for _ in range(3)] == [gate.decide(a)] * 3 and a == SAFE


def test_every_declared_contract_is_well_formed_and_irreversible_types_ask():
    for name, c in actions.CONTRACTS.items():
        assert set(c) == {"irreversible", "external", "criticality", "sensitivity", "schema"}, name
        assert c["schema"]["additionalProperties"] is False, name
        if c["irreversible"]:
            facts = {"policy": "allow", "confidence": 1.0, **{k: c[k] for k in c if k != "schema"}}
            assert gate.decide(facts)["route"] == "ask", name
    for t in ("payment.send", "message.send", "record.delete", "data.export"):        # the owner's four, held by name
        assert actions.CONTRACTS[t]["irreversible"] is True


def test_the_action_policy_reads_like_the_tool_policy(monkeypatch, tmp_path):
    assert actions.policy_for("payment.send") == "require_approval"
    assert actions.policy_for("habit.tick") == "allow"
    assert actions.policy_for("rocket.launch") == "none"
    f = tmp_path / "p.json"
    f.write_text('{"allow": ["habit.*"], "deny": ["habit.tick"]}')
    monkeypatch.setenv("ACTION_POLICY_FILE", str(f))
    assert actions.policy_for("habit.tick") == "deny"
    f.write_text("{broken")
    assert actions.policy_for("note.add") == "deny"                            # a broken policy fails closed
