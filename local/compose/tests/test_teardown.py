"""teardown.sh stops the estate and keeps the person's data; erasing it is a separate, typed step (friction-by-consequence).
A stand-in `docker` and `kind` record what they were asked to do, so nothing real is stopped or erased."""
import os
import pathlib
import stat
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO / "local" / "scripts" / "teardown.sh"


def _run(tmp_path, *args, typed=""):
    log = tmp_path / "calls.log"
    for name in ("docker", "kind"):
        p = tmp_path / name
        p.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n')
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    r = subprocess.run(["bash", str(SCRIPT), *args], input=typed, capture_output=True, text=True, timeout=30,
                       env={"PATH": f"{tmp_path}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    return r, (log.read_text() if log.exists() else "")


def _compose(calls):
    return [ln for ln in calls.splitlines() if ln.startswith("docker compose")]


def test_a_plain_teardown_stops_everything_and_never_erases_a_volume(tmp_path):
    r, calls = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    (down,) = _compose(calls)
    assert down.split()[-1] == "down" and "-v" not in down.split() and "--volumes" not in down
    for profile in ("ai", "passwords", "online", "studio"):               # "stop everything" means the add-ons too
        assert f"--profile {profile}" in down
    assert "data is kept" in r.stdout and "securax up" in r.stdout          # ends on the one next step


def test_wipe_says_what_is_lost_offers_the_backup_first_and_needs_the_typed_word(tmp_path):
    for typed in ("", "y\n", "yes\n", "ERASE\n"):
        r, calls = _run(tmp_path, "--wipe", typed=typed)
        assert r.returncode == 0 and "Nothing was erased" in r.stdout
        assert calls == "", f"{typed!r} must stop before anything runs"
    assert "password vault" in r.stdout and "securax backup" in r.stdout
    r, calls = _run(tmp_path, "--wipe", typed="erase\n")
    assert _compose(calls)[0].split()[-2:] == ["down", "-v"]


def test_an_unknown_option_changes_nothing(tmp_path):
    r, calls = _run(tmp_path, "-v")
    assert r.returncode == 2 and calls == ""
