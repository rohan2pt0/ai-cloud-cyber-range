"""`routines prune`: a routine has to earn its place. Failing, found-nothing, duplicate and never-ran routines are named
with the command to act; guards are never suggested for pruning; switching one off stays on this machine."""
import datetime as dt
import json

from routines import prune
from routines import scheduler as s

NOW = dt.datetime(2026, 11, 20, 12, 0)


def _runs(n, code=0, found=False, every_days=7):
    return [{"t": (NOW - dt.timedelta(days=every_days * i)).strftime("%Y-%m-%dT%H:%M"), "code": code, "found": found} for i in range(n)][::-1]


def _job(jid, cmd, kind):
    return s.Job(jid, "0 9 * * 1", cmd, "", True, kind)


def test_each_kind_of_dead_weight_is_named_with_the_fix():
    jobs = [_job("brief", ["./securax", "doctor"], "report"), _job("nudge", ["./securax", "doctor"], "nudge"),
            _job("broken", ["x"], "guard"), _job("quiet-guard", ["./securax", "backup"], "guard"),
            _job("useful", ["./securax", "demo"], "report"), _job("ghost", ["./securax", "y"], "nudge")]
    hist = {"brief": _runs(4), "nudge": _runs(4), "broken": _runs(3, code=1), "quiet-guard": _runs(7),             # 42 days of history
            "useful": _runs(3) + _runs(1, found=True)}
    got = {i["id"]: i for i in prune.review(jobs, hist, NOW)}
    assert got["broken"]["verdict"] == "failing" and "routines off broken" in got["broken"]["fix"]
    assert got["brief"]["verdict"] == "nothing" and "4 runs" in got["brief"]["why"]
    assert got["nudge"]["verdict"] == "duplicate" and "same command as brief" in got["nudge"]["why"]
    assert "quiet-guard" not in got and "useful" not in got           # a silent guard is a working guard; a report that found something stays
    assert got["ghost"]["verdict"] == "never" and "routines install" in got["ghost"]["fix"]


def test_a_new_estate_is_not_judged_before_it_has_history():
    jobs = [_job("brief", ["./securax", "doctor"], "report"), _job("ghost", ["./securax", "y"], "nudge")]
    assert prune.review(jobs, {"brief": _runs(2)}, NOW) == []


def test_runs_are_recorded_with_whether_they_found_anything_and_switch_off_is_local(tmp_path, monkeypatch):
    h = tmp_path / ".history.json"
    s.record_run("brief", 0, "✔ all fine", "2026-11-01T09:00", h)
    s.record_run("brief", 0, "✗ backup is 9 days old", "2026-11-08T09:00", h)
    got = json.loads(h.read_text())["brief"]
    assert [r["found"] for r in got] == [False, True]
    off = tmp_path / ".off.json"
    monkeypatch.setattr(s, "DEFAULT_OFF", off)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(json.dumps([{"id": "brief", "cron": "0 9 * * 1", "command": ["true"], "kind": "report"}]))
    s.set_off("brief", True)
    assert s.parse_jobs(jobs_file)[0][0].enabled is False
    s.set_off("brief", False)
    assert s.parse_jobs(jobs_file)[0][0].enabled is True


def test_the_shipped_routines_all_have_a_kind_and_guards_cover_the_safety_nets():
    jobs, errors = s.parse_jobs()
    assert not errors
    kinds = {j.id: j.kind for j in jobs}
    for guard in ("nightly-update", "weekly-backup", "offsite-restore-drill", "andon", "regwatch"):
        assert kinds[guard] == "guard"
