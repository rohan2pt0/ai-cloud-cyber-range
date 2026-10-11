"""Routines scheduler — cron matching, due-selection, de-dup and safe execution. All offline."""
import time

import pytest

from routines import scheduler as s


def _t(y=2026, mo=10, d=12, hh=7, mm=45):
    # 2026-10-12 is a Monday.
    return time.struct_time((y, mo, d, hh, mm, 0, time.strptime(f"{y}-{mo}-{d}", "%Y-%m-%d").tm_wday, 0, -1))


# ---- cron field parsing ----------------------------------------------------------------------
def test_parse_field_forms():
    assert s._parse_field("*", 0, 59) == set(range(60))
    assert s._parse_field("*/15", 0, 59) == {0, 15, 30, 45}
    assert s._parse_field("1-5", 0, 23) == {1, 2, 3, 4, 5}
    assert s._parse_field("1,3,5", 0, 59) == {1, 3, 5}
    assert s._parse_field("10-20/5", 0, 59) == {10, 15, 20}


def test_parse_field_rejects_garbage():
    for bad in ["", "99", "5-2", "1--2", "a", "*/0", "70"]:
        with pytest.raises(ValueError):
            s._parse_field(bad, 0, 59)


def test_cron_requires_five_fields():
    with pytest.raises(ValueError):
        s.cron_matches("* * * *", _t())


# ---- cron matching ---------------------------------------------------------------------------
def test_cron_matches_weekday_morning():
    assert s.cron_matches("45 7 * * 1-5", _t(hh=7, mm=45))       # Mon 07:45 -> yes
    assert not s.cron_matches("45 7 * * 1-5", _t(hh=7, mm=46))   # wrong minute
    assert not s.cron_matches("45 7 * * 1-5", _t(d=11))          # Sunday -> no


def test_cron_sunday_is_zero_and_seven():
    sunday = _t(d=11)  # 2026-10-11 is a Sunday
    assert s.cron_matches("0 20 * * 0", _t(d=11, hh=20, mm=0))
    assert s.cron_matches("0 20 * * 7", _t(d=11, hh=20, mm=0))   # 7 also means Sunday
    assert sunday.tm_wday == 6


def test_cron_dom_or_dow_when_both_restricted():
    # "0 0 13 * 5" fires on the 13th OR any Friday (cron OR-semantics).
    assert s.cron_matches("0 0 13 * 5", _t(d=13, hh=0, mm=0))      # the 13th (a Tuesday) -> yes
    # 2026-10-16 is a Friday:
    assert s.cron_matches("0 0 13 * 5", _t(d=16, hh=0, mm=0))      # a Friday -> yes
    assert not s.cron_matches("0 0 13 * 5", _t(d=15, hh=0, mm=0))  # neither -> no


def test_cron_both_wildcard_is_and():
    assert s.cron_matches("0 0 12 10 *", _t(mo=10, d=12, hh=0, mm=0))
    assert not s.cron_matches("0 0 12 11 *", _t(mo=10, d=12, hh=0, mm=0))


# ---- load / validate -------------------------------------------------------------------------
def _write_jobs(tmp_path, data):
    import json
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps(data))
    return p


def test_load_rejects_shell_string_command(tmp_path):
    p = _write_jobs(tmp_path, [{"id": "x", "cron": "* * * * *", "command": "rm -rf /"}])
    with pytest.raises(ValueError):
        s.load_jobs(p)


def test_load_rejects_duplicate_ids(tmp_path):
    p = _write_jobs(tmp_path, [
        {"id": "x", "cron": "* * * * *", "command": ["a"]},
        {"id": "x", "cron": "* * * * *", "command": ["b"]},
    ])
    with pytest.raises(ValueError):
        s.load_jobs(p)


def test_load_validates_cron_upfront(tmp_path):
    p = _write_jobs(tmp_path, [{"id": "x", "cron": "bad cron", "command": ["a"]}])
    with pytest.raises(ValueError):
        s.load_jobs(p)


def test_shipped_example_jobs_are_valid():
    import pathlib
    ex = pathlib.Path(s.__file__).resolve().parent / "examples" / "jobs.json"
    jobs = s.load_jobs(ex)
    assert any(j.id == "morning-brief" for j in jobs)
    assert all(isinstance(j.command, list) and j.command for j in jobs)


# ---- due + run -------------------------------------------------------------------------------
def test_due_skips_disabled_and_dedups(tmp_path):
    p = _write_jobs(tmp_path, [
        {"id": "on", "cron": "45 7 * * *", "command": ["x"]},
        {"id": "off", "cron": "45 7 * * *", "command": ["y"], "enabled": False},
    ])
    jobs = s.load_jobs(p)
    now = _t(hh=7, mm=45)
    due = s.due_jobs(jobs, now)
    assert [j.id for j in due] == ["on"]
    # already ran this minute -> not due again
    stamp = time.strftime("%Y-%m-%dT%H:%M", now)
    assert s.due_jobs(jobs, now, {"on": stamp}) == []


def test_run_due_executes_only_due_and_records_state(tmp_path):
    p = _write_jobs(tmp_path, [
        {"id": "a", "cron": "45 7 * * *", "command": ["echo", "a"]},
        {"id": "b", "cron": "0 9 * * *", "command": ["echo", "b"]},
    ])
    ran = []
    state = {}
    res = s.run_due(_t(hh=7, mm=45), jobs_path=p,
                    runner=lambda cmd: (ran.append(cmd) or (0, "ok")),
                    read_state=lambda: state, write_state=lambda st: state.update(st))
    assert [r["id"] for r in res] == ["a"]
    assert ran == [["echo", "a"]]              # only the due job ran
    assert state.get("a")                      # state recorded for de-dup

    # second run in the SAME minute: nothing runs again
    ran.clear()
    res2 = s.run_due(_t(hh=7, mm=45), jobs_path=p,
                     runner=lambda cmd: (ran.append(cmd) or (0, "ok")),
                     read_state=lambda: dict(state), write_state=lambda st: state.update(st))
    assert res2 == [] and ran == []


def test_cron_dow_seven_in_list_and_range():
    # 7 means Sunday anywhere in a field (not only as a bare '7') — regression for the review find.
    assert s.cron_matches("0 20 * * 0,7", _t(d=11, hh=20, mm=0))   # Sunday via the 7
    assert s.cron_matches("0 9 * * 1-7", _t(d=12, hh=9, mm=0))     # Monday within 1-7
    assert s.cron_matches("0 9 * * 1-7", _t(d=11, hh=9, mm=0))     # 1-7 folds 7->0, includes Sunday


def test_one_bad_job_does_not_disable_the_healthy_ones(tmp_path):
    p = _write_jobs(tmp_path, [
        {"id": "good", "cron": "45 7 * * *", "command": ["echo", "ok"]},
        {"id": "bad", "cron": "this is not cron", "command": ["x"]},
        {"id": "nocmd", "cron": "* * * * *"},
    ])
    # strict load surfaces the errors (used by the CLI `list`):
    with pytest.raises(ValueError):
        s.load_jobs(p)
    # but run_due is tolerant: the healthy job still fires, the bad ones are reported, not fatal.
    ran = []
    res = s.run_due(_t(hh=7, mm=45), jobs_path=p,
                    runner=lambda c: (ran.append(c) or (0, "ok")),
                    read_state=lambda: {}, write_state=lambda st: None)
    ids = {r["id"] for r in res}
    assert "good" in ids and "(config)" in ids
    assert ran == [["echo", "ok"]]


def test_run_due_survives_a_job_crash(tmp_path):
    p = _write_jobs(tmp_path, [{"id": "boom", "cron": "* * * * *", "command": ["x"]}])

    def boom(cmd):
        raise RuntimeError("kaboom")

    res = s.run_due(_t(), jobs_path=p, runner=boom,
                    read_state=lambda: {}, write_state=lambda st: None)
    assert res[0]["exit_code"] == 1 and "kaboom" in res[0]["output_tail"]
