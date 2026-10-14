"""The game-day framework: steps are timed, SLOs are enforced, a crashing step is a finding not a crash, the twin is left as found."""
import importlib.util
import pathlib
import time

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("gameday", REPO / "lifecycle" / "gameday.py")
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)


def test_a_passing_step_is_recorded_with_its_slo():
    r = gd.Run("t")
    assert r.step("fast", lambda: True, within=5)
    assert r.result()["ok"] and r.steps[0]["slo"] == 5


def test_a_step_that_overruns_its_slo_fails_even_if_its_check_passes():
    r = gd.Run("t")
    assert not r.step("slow", lambda: time.sleep(0.25) or True, within=0.1)
    assert not r.result()["ok"] and "SLO" in r.steps[0]["note"]


def test_polling_waits_for_recovery_and_gives_up_at_the_slo(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    calls = {"n": 0}

    def recovers_on_third():
        calls["n"] += 1
        return calls["n"] >= 3
    r = gd.Run("t")
    assert r.step("recovers", recovers_on_third, within=30, poll=True) and calls["n"] == 3
    r2 = gd.Run("t")
    assert not r2.step("never", lambda: False, within=0.05, poll=True) and "not satisfied" in r2.steps[0]["note"]


def test_a_crashing_step_is_reported_not_raised():
    r = gd.Run("t")
    assert not r.step("boom", lambda: 1 / 0)
    assert "ZeroDivisionError" in r.steps[0]["note"]


def test_the_twin_is_left_exactly_as_found(monkeypatch):
    calls = []
    monkeypatch.setattr(gd.bw, "twin_status", lambda: "dormant")
    monkeypatch.setattr(gd.bw, "twin_up", lambda **k: calls.append("up") or 0)
    monkeypatch.setattr(gd.bw, "twin_down", lambda: calls.append("down") or 0)
    monkeypatch.setattr(gd.bw, "twin_stop", lambda: calls.append("stop") or 0)
    monkeypatch.setitem(gd.SCENARIOS, "fake", ("fake", lambda r, s: r.step("x", lambda: True)))
    assert gd.run_scenarios(["fake"], keep=False)[0]["ok"] and calls == ["up", "down"]
    calls.clear()
    monkeypatch.setattr(gd.bw, "twin_status", lambda: "hibernating")
    gd.run_scenarios(["fake"], keep=False)
    assert calls == ["up", "stop"]
    calls.clear()
    gd.run_scenarios(["fake"], keep=True)
    assert calls == ["up"]


def test_slos_come_from_the_fitness_file_and_every_scenario_is_documented():
    s = gd.slo()
    assert {"node_detect", "node_recover", "control_plane_back", "restore_total"} <= set(s) and all(v > 0 for v in s.values())
    assert set(gd.SCENARIOS) == {"node-loss", "control-plane-restart", "snapshot-restore"}
    md = gd.report_md([{"scenario": "x", "ok": False, "seconds": 1, "steps": [{"step": "s", "ok": False, "seconds": 2, "slo": 1, "note": "late"}]}])
    assert "Does **not** prove" in md and "FAILED late" in md
