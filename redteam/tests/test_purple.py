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
    assert {g["id"] for g in sc["alert_gaps"]} <= {"pii-aadhaar"}      # single PII redaction is log-only by design
    assert all(g["suggestion"] for g in sc["alert_gaps"])
    by = {s["id"]: s for s in data["scenarios"]}
    assert by["tool-coercion"]["incident"] == "agentic-tool-coercion"
    assert by["out-exfil-image"]["incident"] == "output-exfil-channel"
    assert by["direct-injection"]["incident"] == "injection-probe"


def test_the_report_names_what_it_does_not_prove(tmp_path):
    data, sc = _run()
    md = purple.markdown(data, sc)
    assert "Does **not** prove" in md and "Detection backlog" in md and "| direct-injection |" in md
