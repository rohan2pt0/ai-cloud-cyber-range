"""`./securax wargame` — a scored crisis-coordination tabletop (doc 126). The scenarios are generic (no real
organisation, person or case); scoring is deterministic (a keyword rubric against each inject's expected action plus
timeliness against its SLA) so it is identical offline and in CI; the after-action report names the coordination
gaps and an owned improvement action for each. No network."""
import datetime
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("wargame", ROOT / "governance" / "wargame.py")
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)
NOW = datetime.datetime(2026, 11, 6, 6, 0, tzinfo=datetime.timezone.utc)


def test_scenarios_are_present_and_generic():
    data = wg.lib()
    owners = data["owners"]
    assert set(data["scenarios"]) >= {"payment-fraud", "ransomware"}
    for sc in data["scenarios"].values():
        assert sc["name"] and sc["about"] and sc["injects"]
        assert sc.get("worst_case"), "every scenario must build in worst-cases"
        ats = [int(i["at_min"]) for i in sc["injects"]]
        assert ats == sorted(ats) or True  # order is not required in data; start() sorts
        for i in sc["injects"]:
            assert i["id"] and i["from"] and i["text"] and i["expect"]
            assert i["owner"] in owners
            assert i["severity"] in ("low", "medium", "high", "critical")
            assert int(i["sla_min"]) > 0
    # at least one designed worst-case inject lives in the timeline
    assert any("WORST CASE" in i["text"] for i in data["scenarios"]["payment-fraud"]["injects"])
    # deliberately generic: the shipped library names no real organisation, regulator or case
    blob = (ROOT / "governance" / "wargames.json").read_text("utf-8")
    for banned in ("Central Bank", "Maharashtra", "CERT-In", "RBI", "SEBI", "Belapur", "Rohan"):
        assert banned not in blob, f"the generic library must not name {banned!r}"


def test_start_fires_the_first_inject_and_sorts_the_timeline(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_WARGAME_DIR", str(tmp_path))
    assert wg.main(["start", "payment-fraud"], now=NOW) == 0
    run = wg.runs()[0]
    assert run["now_min"] == 0 and run["responses"] == {}
    ats = [int(i["at_min"]) for i in run["injects"]]
    assert ats == sorted(ats), "the stored timeline must be in time order"
    live = wg._live(run)
    assert [i["id"] for i in live] == ["i1"], "only the t=0 inject is live at the start"


def test_rubric_rewards_the_right_action_on_time_and_punishes_late_and_wrong(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_WARGAME_DIR", str(tmp_path))
    wg.main(["start", "ransomware"], now=NOW)
    rid = wg.runs()[0]["id"]
    # a strong, early answer to r1 (isolate, do not power off, preserve memory, start the clock and playbook)
    assert wg.main(["respond", rid, "r1", "--action",
                    "declare the incident, isolate the affected hosts without power off to preserve memory, "
                    "start the clock and the playbook", "--minutes", "10"], now=NOW) == 0
    run = wg.load_run(rid)
    r1 = run["responses"]["r1"]
    assert r1["on_time"] is True
    assert r1["correctness"] >= 0.6 and r1["score"] >= 0.75
    # a weak, late answer scores near zero and records what was missed
    wg.main(["respond", rid, "r2", "--action", "asked someone to look", "--minutes", "200"], now=NOW)
    run = wg.load_run(rid)
    r2 = run["responses"]["r2"]
    assert r2["on_time"] is False and r2["correctness"] == 0.0
    assert r2["score"] < 0.3 and r2["missed"]


def test_cannot_answer_an_inject_before_it_fires(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_WARGAME_DIR", str(tmp_path))
    wg.main(["start", "payment-fraud"], now=NOW)
    rid = wg.runs()[0]["id"]
    # i8 fires at t=240; answering it at t=0 must be refused and record nothing
    assert wg.main(["respond", rid, "i8", "--action", "parallelise", "--minutes", "0"], now=NOW) == 2
    assert "i8" not in wg.load_run(rid)["responses"]


def test_advance_moves_the_clock_to_the_next_inject(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_WARGAME_DIR", str(tmp_path))
    wg.main(["start", "payment-fraud"], now=NOW)
    rid = wg.runs()[0]["id"]
    assert wg.main(["advance", rid], now=NOW) == 0
    run = wg.load_run(rid)
    assert run["now_min"] == 20, "advance jumps to the next inject's at_min (i2 at t=20)"
    assert wg.main(["advance", rid, "--to", "120"], now=NOW) == 0
    assert wg.load_run(rid)["now_min"] == 120


def test_unanswered_fired_inject_counts_as_zero_in_the_score(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_WARGAME_DIR", str(tmp_path))
    wg.main(["start", "ransomware"], now=NOW)
    run = wg.runs()[0]
    # fire two injects, answer neither → overall score is 0, not undefined
    run["now_min"] = 20
    wg.save_run(run)
    run = wg.load_run(run["id"])
    assert wg._overall(run) == 0.0


def test_aar_reports_gaps_and_owned_improvement_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_WARGAME_DIR", str(tmp_path))
    wg.main(["start", "ransomware"], now=NOW)
    rid = wg.runs()[0]["id"]
    wg.main(["respond", rid, "r1", "--action",
             "declare the incident, isolate affected hosts, do not power off, preserve memory, start the clock and playbook",
             "--minutes", "10"], now=NOW)
    # advance past several injects without answering them → they become gaps
    wg.main(["advance", rid, "--to", "90"], now=NOW)
    run = wg.load_run(rid)
    report = wg._aar(run, NOW)
    assert "After-action report" in report and "Coordination gaps" in report
    assert "Improvement actions" in report
    # a fired-but-unanswered inject (r3 at t=40) must surface as a gap with its owning team named
    assert "r3" in report and run["owners"]["comms"] in report
    # the saved file lands in the run folder
    assert wg.main(["aar", rid, "--save"], now=NOW) == 0
    assert (tmp_path / rid / "after-action-report.md").exists()


def test_ai_grade_is_offline_safe(monkeypatch):
    # with no GATEWAY_URL the optional model grade is simply absent — never an error, never required
    monkeypatch.delenv("GATEWAY_URL", raising=False)
    inj = {"id": "x", "from": "SOC", "owner": "exec", "text": "t", "expect": "do the thing", "at_min": 0, "sla_min": 30}
    assert wg._ai_grade(inj, "I did the thing") is None
