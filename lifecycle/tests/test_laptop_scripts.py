"""The laptop scripts and the first page a newcomer reads (review ledger, slice 2).

Stopping must never delete a person's data; erasing needs a typed word; the installer's help is whole; and the
getting-started page names no file the person does not have.
"""
import os
import pathlib
import stat
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEARDOWN = ROOT / "local" / "scripts" / "teardown.sh"


def _fake_tools(tmp_path):
    """A docker and a kind that only write down how they were called."""
    log = tmp_path / "calls.log"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name in ("docker", "kind"):
        tool = bindir / name
        tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n')
        tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")
    return env, log


def _run(tmp_path, *args, typed=""):
    env, log = _fake_tools(tmp_path)
    done = subprocess.run(["bash", str(TEARDOWN), *args], input=typed, capture_output=True, text=True, env=env, timeout=60)
    return done, (log.read_text() if log.exists() else "")


def test_stopping_keeps_every_volume(tmp_path):
    done, calls = _run(tmp_path)
    assert done.returncode == 0, done.stderr
    assert "compose" in calls and " down" in calls
    assert " -v" not in calls, "a plain stop must never delete volumes"
    assert "your data is kept" in done.stdout


def test_erase_needs_the_typed_word(tmp_path):
    done, calls = _run(tmp_path, "--erase", typed="y\n")
    assert done.returncode == 1
    assert "nothing was erased" in done.stdout
    assert "down" not in calls, "a wrong word must stop before anything is touched"


def test_erase_says_what_is_lost_and_offers_the_backup_first(tmp_path):
    done, calls = _run(tmp_path, "--erase", typed="ERASE\n")
    assert done.returncode == 0, done.stderr
    assert "password vault" in done.stdout and "./securax backup" in done.stdout
    assert " down -v" in calls


def test_an_unknown_option_changes_nothing(tmp_path):
    done, calls = _run(tmp_path, "-v")
    assert done.returncode == 2 and calls == ""


def test_the_installer_help_is_whole():
    done = subprocess.run(["bash", str(ROOT / "install.sh"), "--help"], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert "It never changes an existing folder" in done.stdout
    assert "--server is the one exception" in done.stdout


def test_the_installer_claims_an_open_page_only_when_it_opened():
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert 'say "✔ Done. Your Command Center is open.' not in text
    assert "securax open" in text


def test_getting_started_names_only_files_that_exist():
    text = (ROOT / "GETTING-STARTED.md").read_text(encoding="utf-8")
    assert "uploaded" not in text, "a newcomer has no uploaded file: name something in the repository"
    for name in ("portal/index.html", "docs/demo-runbook.md", "docs/securax/05-ROADMAP.md", "WINDOWS-QUICKSTART.md"):
        assert name in text and (ROOT / name).exists(), name
