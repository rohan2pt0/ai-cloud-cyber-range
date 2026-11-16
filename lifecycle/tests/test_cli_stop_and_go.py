"""`./securax down` and the closing words of `./securax go` (review ledger, slice 3).

Stopping keeps every volume and stops the parts that have a profile of their own; a stop that failed says so in plain
words; and `go` never says "running again" or "just opened" when that did not happen.
"""
import os
import pathlib
import re
import stat
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLI = ROOT / "securax"


def _down(tmp_path, docker_exit=0):
    """Run `securax down` with a docker that only writes down how it was called."""
    log = tmp_path / "calls.log"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    tool = bindir / "docker"
    tool.write_text(f'#!/bin/sh\necho "docker $*" >> "{log}"\nexit {docker_exit}\n')
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}", SECURAX_NO_OPEN="1")
    done = subprocess.run(["bash", str(CLI), "down"], capture_output=True, text=True, env=env, timeout=60)
    return done, (log.read_text() if log.exists() else "")


def _branch(name):
    """The text of one top-level `case` branch of the CLI."""
    text = CLI.read_text(encoding="utf-8")
    start = re.search(rf"^  {name}\)", text, re.M)
    assert start, f"no '{name})' branch in securax"
    end = re.search(r"^    ;;$", text[start.end():], re.M)
    return text[start.start(): start.end() + end.end()]


def test_down_keeps_every_volume_and_says_so(tmp_path):
    done, calls = _down(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert " down" in calls
    assert " -v" not in calls and "--volumes" not in calls, "a stop must never delete volumes"
    assert "Your data is kept" in done.stdout
    assert "./securax up" in done.stdout, "the stop ends on the one next step"


def test_down_stops_the_parts_with_a_profile_of_their_own(tmp_path):
    _, calls = _down(tmp_path)
    for profile in ("ai", "passwords", "online"):
        assert f"--profile {profile}" in calls, f"`down` left the '{profile}' services running"


def test_a_stop_that_failed_says_so(tmp_path):
    done, _ = _down(tmp_path, docker_exit=1)
    assert done.returncode == 1
    assert "Could not stop everything" in done.stdout
    assert "Stopped. Your data is kept" not in done.stdout
    assert "./securax why" in done.stdout


def test_no_branch_of_the_cli_removes_volumes_with_compose():
    text = CLI.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "compose" in line and re.search(r"\bdown\b", line):
            assert not re.search(r"\s(-v|--volumes)(\s|$)", line.split("#")[0]), line.strip()[:120]
    assert "volume rm" not in text and "volume prune" not in text


def test_go_tells_a_rollback_from_a_failed_update():
    go = _branch("go")
    assert '_urc" = 3' in go, "`update` exits 3 after a rollback and 1 when nothing runs: `go` must not use one sentence for both"
    assert go.count("previous version is running again") == 1


def test_go_says_opened_only_when_something_opened_it():
    go = _branch("go")
    said = go.index("The app just opened in your browser")
    opener = go.rindex("if ( command -v powershell.exe", 0, said)
    assert "|| true" not in go[opener:said], "an opener that failed must not be followed by 'just opened'"
    assert "open \"$LAPLINK\"" in go[opener:said], "a Mac has `open`, not xdg-open"
    assert "./securax sync-link" in go[said:said + 400]
