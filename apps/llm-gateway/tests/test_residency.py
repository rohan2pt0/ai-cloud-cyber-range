"""Data residency: classified data is only processed in zones the policy allows - rerouted or refused BEFORE anything leaves, for any jurisdiction."""
import json
import logging

import pytest
from app import guardrails as g
from app import identity as idn
from app import residency as rs
from app.main import app
from fastapi.testclient import TestClient


def F(rule):
    return g.Finding(rule, "x", "high", "")


def pol(mode="enforce", action="reroute", **over):
    data = {**rs.DEFAULT_POLICY, **over}
    return rs.Policy(mode=mode, action=action, data=data)


def test_default_policy_is_valid_and_strict_at_the_top():
    assert rs.problems(rs.DEFAULT_POLICY) == []
    assert "*" not in rs.DEFAULT_POLICY["classes"][rs.DEFAULT_POLICY["order"][-1]]["zones"]


def test_off_changes_nothing():
    d = pol("off").decide("bank-assistant", [F("PII-AADHAAR")])
    assert d.action == "allow" and d.model == "bank-assistant"


@pytest.mark.parametrize("finding,cls", [("PII-AADHAAR", "regulatory"), ("PII-CARD_PAN", "regulatory"), ("PII-INCOME_TAX_PAN", "regulatory"),
                                         ("PII-EMAIL", "confidential"), ("PII-IFSC", "public"), ("INJ-x", "public")])
def test_findings_set_the_class(finding, cls):
    assert pol().classify([F(finding)]) == cls


def test_the_highest_class_wins_and_a_caller_can_raise_but_never_lower_it():
    p = pol()
    assert p.classify([F("PII-EMAIL"), F("PII-AADHAAR")]) == "regulatory"
    assert p.classify([F("PII-AADHAAR")], ident_class="public", header="public") == "regulatory"      # cannot lower
    assert p.classify([], ident_class="confidential") == "confidential"
    assert p.classify([], header="REGULATORY") == "regulatory"
    assert p.classify([], header="nonsense") == "public"


def test_regulatory_data_is_rerouted_from_a_global_model_to_a_local_one():
    d = pol().decide("bank-assistant", [F("PII-AADHAAR")])
    assert d.action == "rerouted" and d.model == "bank-assistant-local" and d.cls == "regulatory"


def test_public_data_may_use_any_model():
    d = pol().decide("bank-assistant", [])
    assert d.action == "allow" and d.model == "bank-assistant"


def test_a_local_model_is_always_fine_and_unknown_models_are_treated_as_global():
    p = pol()
    assert p.decide("bank-assistant-local", [F("PII-AADHAAR")]).action == "allow"
    assert p.model_zone("some-new-cloud-model") == "global"


def test_block_action_refuses_instead_of_rerouting():
    d = pol(action="block").decide("bank-assistant", [F("PII-AADHAAR")])
    assert d.action == "blocked"


def test_no_allowed_model_configured_means_blocked_not_leaked():
    d = pol(reroute_to=[]).decide("bank-assistant", [F("PII-AADHAAR")])
    assert d.action == "blocked"
    d = pol(reroute_to=["some-cloud"]).decide("bank-assistant", [F("PII-AADHAAR")])           # the fallback itself is global
    assert d.action == "blocked"


def test_monitor_mode_reports_the_violation_but_changes_nothing():
    d = pol("monitor").decide("bank-assistant", [F("PII-AADHAAR")])
    assert d.action == "would_reroute" and d.model == "bank-assistant" and "VIOLATION" in d.reason


def test_detectors_follow_the_same_rule():
    p = pol()
    assert p.detector_allowed("regulatory", "llama-guard")                  # local detector is fine
    assert not p.detector_allowed("regulatory", "model-armor")              # a cloud detector is not sent regulated text
    assert p.detector_allowed("public", "model-armor")
    assert pol("off").detector_allowed("regulatory", "model-armor")


def test_another_jurisdiction_is_just_a_policy():
    eu = {"order": ["public", "personal"], "classes": {"public": {"zones": ["*"]}, "personal": {"zones": ["local", "eu"]}}, "default_class": "public",
          "class_by_finding": {"EMAIL": "personal"}, "model_zones": {"*-local": "local", "mistral-eu": "eu"}, "reroute_to": ["mistral-eu"]}
    p = pol(**eu)
    assert p.decide("bank-assistant", [F("PII-EMAIL")]).model == "mistral-eu"
    assert p.decide("mistral-eu", [F("PII-EMAIL")]).action == "allow"


def test_invalid_policies_are_refused_at_startup():
    assert rs.problems({**rs.DEFAULT_POLICY, "classes": {**rs.DEFAULT_POLICY["classes"], "regulatory": {"zones": ["*"]}}})
    with pytest.raises(ValueError):
        rs.Policy.from_env({"RESIDENCY_MODE": "enforce", "RESIDENCY_POLICY_JSON": json.dumps({"classes": {}})})
    with pytest.raises(ValueError):
        rs.Policy.from_env({"RESIDENCY_MODE": "sometimes"})


# --------------------------------------------------------------------------------------------------- the gateway end to end
def aadhaar():
    base = "234567890123"[:11]
    for d in "0123456789":
        if g.verhoeff_valid(base + d):
            return base + d
    raise AssertionError


@pytest.fixture
def client(monkeypatch):
    import app.main as m
    monkeypatch.setattr(m, "RES", pol())
    return TestClient(app)


def chat(client, text, model="bank-assistant", headers=None):
    return client.post("/v1/chat/completions", json={"model": model, "messages": [{"role": "user", "content": text}]}, headers=headers or {})


def test_gateway_sends_aadhaar_to_the_local_model_and_audits_why(client, caplog):
    caplog.set_level(logging.INFO, logger="audit")
    r = chat(client, f"customer aadhaar {aadhaar()} please summarise")
    assert r.status_code == 200 and r.json()["model"] == "bank-assistant-local"
    last = [json.loads(x.message) for x in caplog.records if x.name == "audit"][-1]
    assert last["residency"]["action"] == "rerouted" and last["residency"]["class"] == "regulatory"
    assert last["residency"]["requested_model"] == "bank-assistant"


def test_gateway_leaves_ordinary_prompts_alone(client):
    r = chat(client, "what is the repo rate?")
    assert r.status_code == 200 and r.json()["model"] == "bank-assistant"


def test_gateway_honours_the_data_class_header(client):
    r = chat(client, "quarterly figures", headers={"X-Data-Class": "regulatory"})
    assert r.json()["model"] == "bank-assistant-local"


def test_gateway_uses_the_callers_default_class(monkeypatch):
    import app.main as m
    c = idn.Config(mode="required")
    c.api_keys = [{"id": "reg-reporting", "sha256": idn.hash_key("sk-r"), "roles": ["service"], "data_class": "regulatory"}]
    monkeypatch.setattr(m, "AUTH", idn.Authenticator(c))
    monkeypatch.setattr(m, "RES", pol())
    r = chat(TestClient(app), "hello", headers={"Authorization": "Bearer sk-r"})
    assert r.json()["model"] == "bank-assistant-local"


def test_gateway_block_action_refuses_with_403(monkeypatch, caplog):
    import app.main as m
    monkeypatch.setattr(m, "RES", pol(action="block"))
    caplog.set_level(logging.INFO, logger="audit")
    r = chat(TestClient(app), f"aadhaar {aadhaar()}")
    assert r.status_code == 403 and r.json()["error"]["type"] == "data_residency"
    assert [json.loads(x.message) for x in caplog.records if x.name == "audit"][-1]["decision"] == "residency_blocked"


def test_cloud_detectors_are_not_sent_regulated_text(monkeypatch):
    import app.main as m
    seen = []

    async def spy(text, direction, allow=None):
        seen.append((text, allow and allow("model-armor"), allow and allow("llama-guard")))
        return []
    monkeypatch.setattr(m, "run_detectors", spy)
    monkeypatch.setattr(m, "RES", pol())
    chat(TestClient(app), f"aadhaar {aadhaar()}")
    assert seen and seen[0][1] is False and seen[0][2] is True
    assert aadhaar() not in seen[0][0]                                   # detectors get the REDACTED text


def test_default_is_off_and_unchanged():
    import app.main as m
    assert m.RES.mode == "off"
    assert chat(TestClient(app), f"aadhaar {aadhaar()}", model="bank-assistant").json()["model"] == "bank-assistant"
