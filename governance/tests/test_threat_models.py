"""Threat models as plain text (doc 133, principle `threat-model`): every STRIDE category considered, every threat mitigated with proof that
exists, accepted with a date, or ruled out with a reason, and the number of models only goes up. Synthetic models in a temp tree, no network."""
import datetime
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fitness_tm", ROOT / "lifecycle" / "fitness.py")
ft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ft)
TODAY = datetime.date(2026, 11, 8)
CATS = {"S": "Spoofing", "T": "Tampering", "R": "Repudiation", "I": "Information disclosure", "D": "Denial of service", "E": "Elevation of privilege"}


def threat(i, s, **kw):
    t = {"id": i, "stride": s, "element": "a", "threat": "something could go wrong here, in a sentence", "status": "not-applicable",
         "reason": "it cannot happen because there is no such path"}
    t.update(kw)
    return t


def model(**over):
    m = {"boundaries": ["the internet"], "elements": [{"id": "a", "kind": "process"}, {"id": "b", "kind": "external"}],
         "flows": [{"from": "a", "to": "b", "data": "x", "crosses": "the internet"}],
         "threats": [threat(f"t-{c}", c) for c in "STRIDE"]}
    m.update(over)
    return m


def run(tmp_path, baseline=1, **models):
    return ft.threat_model_problems({"categories": CATS, "models": models}, tmp_path, baseline, TODAY)


def test_a_complete_model_passes(tmp_path):
    assert run(tmp_path, m=model()) == []


def test_all_six_stride_categories_must_be_considered(tmp_path):
    p = run(tmp_path, m=model(threats=[threat(f"t-{c}", c) for c in "STRID"]))        # no elevation of privilege
    assert any("E" in x and "not been considered" in x for x in p)


def test_a_mitigated_threat_needs_evidence_that_exists(tmp_path):
    (tmp_path / "proof.txt").write_text("a test")
    ok = threat("t-S", "S", status="mitigated", mitigation="the link asks first", evidence="proof.txt")
    bad = threat("t-S", "S", status="mitigated", mitigation="the link asks first", evidence="missing.txt")
    none = threat("t-S", "S", status="mitigated", evidence="proof.txt")
    rest = [threat(f"t-{c}", c) for c in "TRIDE"]
    assert run(tmp_path, m=model(threats=[ok] + rest)) == []
    assert any("evidence" in x for x in run(tmp_path, m=model(threats=[bad] + rest)))
    assert any("mitigation" in x for x in run(tmp_path, m=model(threats=[none] + rest))), "proof without a mitigation says nothing"


def test_an_accepted_threat_needs_a_real_reason_and_a_review_date_that_has_not_passed(tmp_path):
    why = "the damage is a wrong address and the account is protected by a passkey"
    rest = [threat(f"t-{c}", c) for c in "TRIDE"]
    assert run(tmp_path, m=model(threats=[threat("t-S", "S", status="accepted", reason=why, review="2026-11-20")] + rest)) == []
    assert any("review" in x for x in run(tmp_path, m=model(threats=[threat("t-S", "S", status="accepted", reason=why)] + rest)))
    assert any("review" in x for x in run(tmp_path, m=model(threats=[threat("t-S", "S", status="accepted", reason="fine", review="2026-11-20")] + rest)))
    assert any("passed" in x for x in run(tmp_path, m=model(threats=[threat("t-S", "S", status="accepted", reason=why, review="2026-01-01")] + rest))), \
        "an accepted risk is pulled back into view on its date"


def test_ruling_a_threat_out_needs_the_reason(tmp_path):
    rest = [threat(f"t-{c}", c) for c in "TRIDE"]
    assert any("ruled-out" in x for x in run(tmp_path, m=model(threats=[threat("t-S", "S", reason="no")] + rest)))


def test_a_model_must_name_where_trust_changes_and_use_declared_elements(tmp_path):
    assert any("crosses" in x or "cross" in x for x in run(tmp_path, m=model(flows=[{"from": "a", "to": "b", "data": "x"}])))
    assert any("not declared" in x for x in run(tmp_path, m=model(flows=[{"from": "a", "to": "zzz", "data": "x", "crosses": "net"}])))
    bad = [threat("t-S", "S", element="ghost")] + [threat(f"t-{c}", c) for c in "TRIDE"]
    assert any("element" in x for x in run(tmp_path, m=model(threats=bad)))
    assert any("unique" in x for x in run(tmp_path, m=model(threats=[threat("same", c) for c in "STRIDE"])))


def test_the_number_of_models_only_goes_up(tmp_path):
    assert run(tmp_path, baseline=1, a=model()) == []
    assert any("baseline" in x for x in run(tmp_path, baseline=2, a=model()))


def test_the_real_models_pass_and_name_the_open_risks_with_dates():
    reg = json.loads((ROOT / "governance" / "threat-models.json").read_text("utf-8"))
    base = json.loads((ROOT / "lifecycle" / "fitness.json").read_text("utf-8"))["budgets"]["threat_models_baseline"]
    assert ft.check_threat_modelled(base)["ok"]
    assert {"command-door", "hosted-apps"} <= set(reg["models"])
    accepted = [t for m in reg["models"].values() for t in m["threats"] if t["status"] == "accepted"]
    assert accepted and all(t["review"] for t in accepted), "an accepted risk is listed with its date, never hidden"


def test_the_principle_is_core_and_names_the_tools_without_depending_on_one():
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    p = princ["threat-model"]
    assert p["core"] is True and "STRIDE" in p["text"] and "Threat Modeling Tool" in p["text"] and "plain text" in p["text"]
    assert "threat-model" in (ROOT / "AGENTS.md").read_text("utf-8")
