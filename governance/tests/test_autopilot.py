"""The autopilot (doc 92) learns from failures (a draft, an escalation, a recovery, never about itself), picks the drills that
most need it and flags a slower recovery, and forecasts with a trend one odd reading cannot fool. No network, no estate."""
import importlib.util
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("autopilot", ROOT / "governance" / "autopilot.py")
ap = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ap)
NOW = time.mktime(time.strptime("2026-10-21T12:00", "%Y-%m-%dT%H:%M"))


def stamp(hours_ago: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M", time.localtime(NOW - hours_ago * 3600))


def run(**kw):
    said, drafts = [], []
    did = ap.learn(alert=said.append, say=lambda *_: None, now=NOW,
                   draft=lambda job, code, line: drafts.append((job, line)) or pathlib.Path(f"/vault/pm-{job}.md"), **kw)
    return did, said, drafts


def test_a_new_failure_gets_a_draft_and_an_alert_once(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    hist = {"daily-backup": [{"t": stamp(30), "code": 0}, {"t": stamp(5), "code": 1, "tail": "Could not read volume X"}]}
    did, said, drafts = run(history=hist)
    assert did["new"] == ["daily-backup"] and drafts == [("daily-backup", "Could not read volume X")]
    assert "postmortem draft" in said[0] and "Could not read volume X" in said[0]
    did, said, drafts = run(history=hist)
    assert not did["new"] and not drafts and not said, "the same failure is not drafted twice"


def test_a_failure_that_keeps_coming_back_is_escalated_with_a_fix_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    runs = [{"t": stamp(h), "code": 1, "tail": "drill FAILED"} for h in (70, 40, 10)]
    run(history={"continuity-drill": runs[:1]})
    run(history={"continuity-drill": runs[:2]})
    did, said, _ = run(history={"continuity-drill": runs})
    assert did["recurring"] == ["continuity-drill"] and "./securax autobuild" in said[0]


def test_a_recovery_is_announced_and_reports_reminders_and_itself_are_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    run(history={"daily-backup": [{"t": stamp(5), "code": 1}]})
    did, said, _ = run(history={"daily-backup": [{"t": stamp(5), "code": 1}, {"t": stamp(1), "code": 0}]})
    assert did["recovered"] == ["daily-backup"] and "green again" in said[0]
    did, _, drafts = run(history={"regwatch-digest": [{"t": stamp(1), "code": 1}], "checkin-nudge": [{"t": stamp(1), "code": 2}],
                                  "autopilot-learn": [{"t": stamp(1), "code": 1}]})
    assert not drafts and not did["new"]


def test_drills_pick_never_run_and_failed_first_and_every_drill_has_its_turn():
    cands = {c["id"] for c in ap.candidates()}
    assert {"resilience", "honesty", "github-down", "bad-change"} <= cands
    recent = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(NOW - 3600))
    hist = {c: [{"when": recent, "ok": True}] for c in cands}
    hist["github-down"] = [{"when": recent, "ok": False}]
    del hist["honesty"]
    first = [c["id"] for c in ap.pick(NOW, n=2, hist=hist)]
    assert first[0] == "honesty" and "github-down" in first


def test_a_much_slower_recovery_is_flagged_but_noise_is_not():
    past = [{"ok": True, "minutes": m} for m in (3.0, 3.2, 2.9, 3.1)]
    assert ap.slower(9.0, past) and not ap.slower(4.0, past) and not ap.slower(9.0, past[:2])


def test_the_trend_ignores_one_odd_reading():
    pts = [(d * 86400.0, 100.0 - d) for d in range(10)]
    pts[4] = (4 * 86400.0, 5.0)                                               # one wild reading
    assert abs(ap.theil_sen(pts) * 86400 - (-1.0)) < 0.05


def test_forecasts_warn_ahead_and_learn_first():
    day = 86400
    falling = [{"at": NOW - (9 - d) * day, "m": "disk_free_gb", "v": 19.0 - d * 1.5} for d in range(10)]
    res = {r["metric"]: r for r in ap.predict(falling, now=NOW)}
    assert res["disk_free_gb"]["state"] == "soon" and 0 < res["disk_free_gb"]["days"] <= 7
    assert res["ai_month_used_pct"]["state"] == "learning"
    flat = [{"at": NOW - (9 - d) * day, "m": "disk_free_gb", "v": 80.0} for d in range(10)]
    assert {r["metric"]: r for r in ap.predict(flat, now=NOW)}["disk_free_gb"]["state"] == "ok"


def test_a_forecast_warning_is_sent_at_most_once_a_day_and_samples_are_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    said = []
    for d in range(10):
        ap.forecast(say=lambda *_: None, alert=said.append, readings={"disk_free_gb": 14.0 - d * 1.5}, now=NOW - (9 - d) * 86400)
    n = len(said)
    ap.forecast(say=lambda *_: None, alert=said.append, readings={"disk_free_gb": 0.5}, now=NOW + 60)
    assert n >= 1 and any("free disk space" in s for s in said)
    assert len([s for s in said[n:] if "falls under" in s]) <= 1
    monkeypatch.setattr(ap, "KEEP_SAMPLES", 5)
    for i in range(20):
        ap.record({"latency_p95_s": 1.0}, now=NOW + i)
    assert len((tmp_path / "autopilot" / "metrics.jsonl").read_text().splitlines()) <= 5


def test_every_routine_the_autopilot_needs_is_scheduled():
    jobs = {j["id"]: j for j in json.loads((ROOT / "routines" / "jobs.json").read_text())}
    for jid, sub in (("autopilot-learn", "learn"), ("autopilot-drill", "drill"), ("autopilot-forecast", "forecast")):
        assert jobs[jid]["enabled"] and jobs[jid]["command"] == ["./securax", "autopilot", sub]


def test_a_nightly_drill_records_its_result_and_alerts_on_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    said = []
    rc = ap.drill(say=lambda *_: None, alert=said.append, runner=lambda c: (c["id"] != "resilience", "x"), now=NOW)
    log = [json.loads(x) for x in (tmp_path / "autopilot" / "drills.jsonl").read_text().splitlines()]
    assert len(log) == ap.DRILLS_PER_NIGHT and all("minutes" in r for r in log)
    assert (rc == 1) == any(r["id"] == "resilience" for r in log) and (bool(said) == (rc == 1))
