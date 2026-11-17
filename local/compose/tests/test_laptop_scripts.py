"""The laptop scripts never cost a person their data or their set-up by surprise (review ledger, slice 2).

teardown.sh is printed in GETTING-STARTED.md and the README as "stop everything", so it must keep every volume unless
the person asks to erase and types a word. Each test runs a COPY of the script in an empty folder with a fake `docker`
first on the path, so nothing real can be stopped or deleted.
"""
import os
import pathlib
import re
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEARDOWN = ROOT / "local/scripts/teardown.sh"


def _run(tmp_path, *args):
    """Run a copy of teardown.sh; return (result, the arguments the fake docker was called with)."""
    scripts = tmp_path / "local/scripts"
    scripts.mkdir(parents=True)
    (tmp_path / "local/compose").mkdir(parents=True)
    shutil.copy(TEARDOWN, scripts / "teardown.sh")
    fake = tmp_path / "bin"
    fake.mkdir()
    log = tmp_path / "docker.log"
    (fake / "docker").write_text(f'#!/bin/sh\necho "$@" >> "{log}"\n')
    (fake / "docker").chmod(0o755)
    env = {**os.environ, "PATH": f"{fake}:/usr/bin:/bin"}
    res = subprocess.run(["bash", str(scripts / "teardown.sh"), *args], capture_output=True, text=True, env=env,
                         stdin=subprocess.DEVNULL, timeout=30)
    return res, (log.read_text() if log.exists() else "")


def test_a_plain_teardown_keeps_every_volume(tmp_path):
    res, calls = _run(tmp_path)
    assert res.returncode == 0, res.stderr
    assert " down" in calls and "-v" not in calls.split(), calls
    assert "data is kept" in res.stdout


def test_erasing_needs_a_typed_word_and_a_terminal(tmp_path):
    res, calls = _run(tmp_path, "--erase-data")           # stdin is not a terminal here: nothing may be erased
    assert res.returncode == 1 and calls == "", (res.stdout, calls)
    assert "nothing was erased" in (res.stdout + res.stderr).lower()
    src = TEARDOWN.read_text()
    assert re.search(r'\[ "\$_word" = erase \]', src), "the erase path must compare a typed word, not a y/n"
    assert "./securax backup" in src, "the erase path offers the safe step (a backup) first"


def test_an_unknown_option_changes_nothing(tmp_path):
    res, calls = _run(tmp_path, "-v")
    assert res.returncode == 2 and calls == ""


def test_the_slice_names_no_particular_laptop():
    """The repository is public: a script or guide never names the owner's own machine."""
    for rel in ("GETTING-STARTED.md", "local/scripts/bootstrap-laptop.sh", "local/compose/docker-compose.yml"):
        assert "spectre" not in (ROOT / rel).read_text(encoding="utf-8").lower(), rel


def test_getting_started_points_at_nothing_a_person_does_not_have():
    text = (ROOT / "GETTING-STARTED.md").read_text(encoding="utf-8")
    assert "uploaded" not in text.lower(), "a guide must not send a person to a file that was never in the repository"


def test_the_dns_advice_never_overwrites_wsl_conf():
    """install.sh --docker writes systemd=true into /etc/wsl.conf; advice that overwrites the file undoes it."""
    cli = (ROOT / "securax").read_text(encoding="utf-8")
    assert "sudo tee /etc/wsl.conf" not in cli and "sudo tee -a /etc/wsl.conf" in cli


def test_server_setup_checks_its_files_before_it_changes_the_machine():
    src = (ROOT / "install.sh").read_text(encoding="utf-8")
    block = src[src.index('if [ "$SERVER" = 1 ]; then'):]
    first_change = block.index("apt-get")
    for needle in ('"Backup not found: $RESTORE"', '"Key file not found: $KEYFILE"', "cannot be used with --offline"):
        assert needle in block[:first_change], needle
    assert "sed -n '2,18p'" in src, "--help must show --no-start, --yes and the --server note too"
