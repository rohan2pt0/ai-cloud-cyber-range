"""The adversary ledger: every bounty/red-team finding is reproduced as a probe, and a closed one proves it stayed closed."""
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("adversary", HERE.parent / "adversary.py")
adv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adv)


def test_the_shipped_ledger_is_consistent():
    """Against the real red-team code: every finding's probe exists, every closed one has a lesson, no class recurred."""
    assert adv.problems(adv.load()) == []


def test_probe_ids_are_read_from_the_real_red_team_code():
    ids = adv._probe_ids()
    assert "history-poisoning" in ids and "poisoned-doc-override" in ids and "direct-injection" in ids


def test_a_closed_finding_without_a_living_regression_is_refused():
    reg = {"ledger": [{"id": "ADV-9001", "title": "made up", "class": "LLM01", "severity": "high",
                       "reported": "2026-10-01", "fixed": "2026-10-02",
                       "regression": {"probe": "no-such-probe"}, "lesson": "x"}]}
    probs = adv.problems(reg)
    assert any("ADV-9001" in p and "does not exist" in p for p in probs)


def test_every_finding_must_be_reproduced_even_when_still_open():
    reg = {"ledger": [{"id": "ADV-9002", "title": "noted but never fired", "class": "LLM01", "severity": "high",
                       "reported": "2026-10-01", "fixed": None, "regression": {}}]}
    assert any("ADV-9002" in p and "no regression" in p for p in adv.problems(reg))


def test_a_closed_finding_must_carry_a_lesson():
    reg = {"ledger": [{"id": "ADV-9003", "title": "fixed, no lesson", "class": "ASI06", "severity": "high",
                       "reported": "2026-10-01", "fixed": "2026-10-02", "regression": {"probe": "history-poisoning"}}]}
    assert any("ADV-9003" in p and "lesson" in p for p in adv.problems(reg))


def test_a_title_that_looks_like_a_payload_or_secret_is_refused():
    reg = {"ledger": [{"id": "ADV-9004", "title": "exfil to attacker@gmail.com", "class": "LLM05", "severity": "high",
                       "reported": "2026-10-01", "regression": {"probe": "history-poisoning"}}]}
    assert any("ADV-9004" in p and "payload" in p for p in adv.problems(reg))
    ok = {"ledger": [{"id": "ADV-9005", "title": "exfil to collect@evil.example", "class": "LLM05", "severity": "high",
                      "reported": "2026-10-01", "regression": {"probe": "history-poisoning"}}]}
    assert not any("ADV-9005" in p and "payload" in p for p in adv.problems(ok))


def test_a_class_that_recurs_after_it_was_closed_is_a_repeat_class():
    reg = {"ledger": [
        {"id": "ADV-1", "title": "a", "class": "LLM01", "severity": "high", "reported": "2026-01-01", "fixed": "2026-01-02",
         "regression": {"probe": "history-poisoning"}, "lesson": "x"},
        {"id": "ADV-2", "title": "b", "class": "LLM01", "severity": "high", "reported": "2026-06-01",
         "regression": {"probe": "history-poisoning"}}]}
    assert adv.repeat_classes(reg) == ["LLM01"]
    assert any("repeat-class" in p for p in adv.problems(reg))


def test_add_assigns_an_id_and_refuses_one_without_a_regression():
    import argparse
    reg = {"ledger": []}
    base = dict(title="t", klass="LLM01", severity="high", atlas="", probe="", test="", lesson="", drill="",
                source="bounty", reporter="", reported="2026-10-01", fixed="", id="")
    try:
        adv.add(reg, argparse.Namespace(**base))
        raise AssertionError("expected a refusal without a regression")
    except ValueError:
        pass
    f = adv.add(reg, argparse.Namespace(**{**base, "probe": "history-poisoning"}))
    assert f["id"] == "ADV-0001" and reg["ledger"][0]["regression"] == {"probe": "history-poisoning"}


def test_status_and_recent_closed_count_only_proven_regressions():
    import datetime as dt
    reg = adv.load()
    s = adv.status(reg)
    assert s["reproduced"] == s["findings"] and s["repeat_classes"] == []
    assert adv.recent_closed(reg, dt.date(2026, 10, 23)) >= 1          # within the default 30-day window
    assert adv.recent_closed(reg, dt.date(2027, 1, 1), days=30) == 0   # the fix is older than the window
