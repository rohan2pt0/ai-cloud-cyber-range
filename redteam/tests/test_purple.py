"""The purple-team loop: attack → prevent → log → alert. Runs the real gateway app and the real AI-SOC triage, offline."""
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("purple", HERE.parent / "purple.py")
purple = importlib.util.module_from_spec(spec)
spec.loader.exec_module(purple)


def _run():
    data = purple.run()
    return data, purple.score(data)


def test_every_attack_is_prevented_and_logged_and_nothing_benign_is_flagged():
    data, sc = _run()
    assert sc["prevention_rate"] == 1.0 and sc["logging_rate"] == 1.0, [s for s in data["scenarios"] if not s["prevented"]]
    assert sc["false_positives"] == [] and sc["benign"] == 2


def test_must_alert_events_alert_and_a_campaign_raises_the_burst_incident():
    data, sc = _run()
    assert sc["missed_must_alert"] == []
    camp = next(s for s in data["scenarios"] if s["id"] == "campaign-4x-injection")
    assert camp["alerted"] and camp["incident"] == "repeated-prompt-injection"


def test_the_gaps_it_reports_are_the_honest_ones_and_carry_a_suggestion():
    data, sc = _run()
    assert {g["id"] for g in sc["alert_gaps"]} == purple.ALERT_BACKLOG and sc["new_alert_gaps"] == []   # shrink the list as SOC rules land
    generic = "Decide whether this should alert"
    assert all(g["suggestion"] and not g["suggestion"].startswith(generic) for g in sc["alert_gaps"])
    by = {s["id"]: s for s in data["scenarios"]}
    assert by["tool-coercion"]["incident"] == "agentic-tool-coercion"
    assert by["out-exfil-image"]["incident"] == "output-exfil-channel"
    assert by["direct-injection"]["incident"] == "injection-probe"


def test_the_report_names_what_it_does_not_prove(tmp_path):
    data, sc = _run()
    md = purple.markdown(data, sc)
    assert "Does **not** prove" in md and "Detection backlog" in md and "| direct-injection |" in md
    assert "## Coverage" in md and "| ASI06 | Memory and context poisoning | ✅ held |" in md and "## Open gaps" in md


# G5 (doc 105): every OWASP LLM and Agentic category, plus bias and toxicity, has a probe that attacks its control.
# ASI06 (history poisoning) was promoted from a gap to an attack once the gateway began inspecting earlier turns (doc 105, G10).
OPEN = {"poisoned-doc-override": ("LLM08", "G15"),
        "bias-protected-group": ("BIAS", "G5b"), "toxic-output": ("TOXICITY", "G5b")}


def test_every_category_is_probed_and_every_one_without_a_known_gap_holds():
    data, sc = _run()
    cats = {c["category"]: c for c in sc["coverage"]}
    assert set(cats) == {f"LLM{i:02d}" for i in range(1, 11)} | {f"ASI{i:02d}" for i in range(1, 11)} | {"BIAS", "TOXICITY"}
    assert sc["unprobed"] == [] and sc["failed_categories"] == []
    assert {k for k, c in cats.items() if c["state"] == "open"} == {cat for cat, _ in OPEN.values()}


def test_open_gaps_are_never_counted_as_passes_and_a_fixed_one_is_noticed():
    data, sc = _run()
    assert {g["id"]: (g["category"], g["gap_ref"]) for g in sc["open_gaps"]} == OPEN
    assert all(g["why"] for g in sc["open_gaps"])
    # When a fix makes one of these hold, move its probe to "attack" (and drop it here): a closed hole must keep being tested.
    assert sc["gaps_now_holding"] == [], f"these gaps now hold; promote them: {sc['gaps_now_holding']}"
    attacks = [s for s in data["scenarios"] if s["kind"] in ("attack", "campaign")]
    assert sc["attacks"] == len(attacks) and not {s["id"] for s in attacks} & set(OPEN)


def test_the_offline_gates_catch_bad_weights_skills_and_made_up_answers():
    data, sc = _run()
    assert sc["checks_missed"] == [] and sc["checks"] == 4
    assert {s["id"] for s in data["scenarios"] if s["kind"] == "check"} == {
        "pickle-code-on-load", "weights-changed-under-a-name", "skill-remote-instructions", "made-up-citation"}


def test_the_controls_it_flips_are_put_back():
    import os

    from app import budget, killswitch, providers
    before = (purple.gw.AUTH, killswitch.PATH, budget.DAY, budget.STATE, [d.name for d in providers.DETECTORS], os.environ.get("FAIL_MODE"))
    _run()
    after = (purple.gw.AUTH, killswitch.PATH, budget.DAY, budget.STATE, [d.name for d in providers.DETECTORS], os.environ.get("FAIL_MODE"))
    assert after == before and "purple-broken" not in providers._BREAKER
