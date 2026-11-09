"""The first two delivery keys are read from git alone: how often we ship and how often a change needed a fix. No CI history."""
import datetime as dt
import importlib.util
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("delivery", ROOT / "governance" / "delivery.py")
dlv = importlib.util.module_from_spec(_s)
_s.loader.exec_module(dlv)


def _progress():
    spec = importlib.util.spec_from_file_location("progress", ROOT / "governance" / "progress.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(tmp_path):
    def g(*a, env=None):
        return subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, env=env)
    return g


def _commit(g, subject, days_ago):
    when = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S")
    g("commit", "--allow-empty", "-qm", subject, env={**os.environ, "GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when})


def test_ships_and_change_fail_rate_are_counted_from_merges(tmp_path):
    g = _git(tmp_path)
    g("init", "-q"), g("branch", "-M", "main")
    _commit(g, "Add a thing (#1)", 2)
    _commit(g, "Fix the thing (#2)", 4)
    _commit(g, "Revert the thing (#3)", 6)
    _commit(g, "Ship the hotfix (#4)", 8)
    _commit(g, "Improve docs (#5)", 10)
    _commit(g, "Fixture cleanup (#7)", 3)            # "fix" as a mere prefix: not a fix
    _commit(g, "plain commit", 12)                  # no PR marker: not a merge
    _commit(g, "Add an old thing (#6)", 40)         # older than 28 days: not counted
    d = dlv.compute(cwd=tmp_path)
    assert d["merges"] == 6 and d["fixed"] == 3
    assert d["ships_per_week"] == 1.5
    assert d["change_fail_rate"] == 0.5
    assert d["git_ok"] is True


def test_a_repo_with_no_merges_gives_zero_ships_and_no_crash(tmp_path):
    g = _git(tmp_path)
    g("init", "-q"), g("branch", "-M", "main")
    _commit(g, "plain commit", 1)
    d = dlv.compute(cwd=tmp_path)
    assert d["merges"] == 0 and d["ships_per_week"] == 0 and d["change_fail_rate"] == 0


def test_it_falls_back_to_head_when_there_is_no_main(tmp_path):
    g = _git(tmp_path)
    g("init", "-q"), g("branch", "-M", "trunk")
    _commit(g, "Add a thing (#1)", 1)
    assert dlv.compute(cwd=tmp_path)["merges"] == 1


def test_the_report_line_names_the_two_keys(tmp_path):
    g = _git(tmp_path)
    g("init", "-q"), g("branch", "-M", "main")
    _commit(g, "Add a thing (#1)", 1)
    _commit(g, "Fix the thing (#2)", 2)
    _commit(g, "Improve docs (#3)", 3)
    _commit(g, "Ship the thing (#4)", 4)
    assert _progress().delivery_line(cwd=tmp_path) == "Delivery: 1 ship a week, 25% needed a fix (last 4 weeks)"


def test_the_report_line_skips_silently_without_git(tmp_path):
    assert _progress().delivery_line(cwd=tmp_path) is None


def test_the_report_line_shows_zero_ships_when_git_is_present_but_nothing_merged(tmp_path):
    g = _git(tmp_path)
    g("init", "-q"), g("branch", "-M", "main")
    _commit(g, "plain commit", 1)
    assert _progress().delivery_line(cwd=tmp_path) == "Delivery: 0 ships a week, 0% needed a fix (last 4 weeks)"
