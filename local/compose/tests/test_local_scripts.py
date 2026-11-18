"""The scripts in local/scripts and the advice the CLI prints must never cost a person their data or read a failure as a pass
(review ledger, slice 2). The teardown tests run the real script against a fake docker that only records its arguments."""
import os
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "local" / "scripts"


def _teardown(tmp_path, *args):
    """Run teardown.sh with a docker and a kind that write their arguments to a file and do nothing else."""
    fake = tmp_path / "bin"
    fake.mkdir(exist_ok=True)
    log = tmp_path / "calls.log"
    for name in ("docker", "kind"):
        tool = fake / name
        tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n')
        tool.chmod(0o755)
    env = {"PATH": f"{fake}:/usr/bin:/bin", "HOME": str(tmp_path)}
    run = subprocess.run(["bash", str(SCRIPTS / "teardown.sh"), *args], capture_output=True, text=True, env=env,
                         stdin=subprocess.DEVNULL, timeout=60)
    return run, (log.read_text() if log.exists() else "")


def test_teardown_keeps_the_data_by_default(tmp_path):
    run, calls = _teardown(tmp_path)
    assert run.returncode == 0, run.stderr
    down = [line for line in calls.splitlines() if line.startswith("docker compose") and " down" in line]
    assert down, calls
    assert not any(re.search(r"\s(-v|--volumes)(\s|$)", line) for line in down), down
    assert "data is kept" in run.stdout


def test_teardown_erase_needs_a_person_and_deletes_nothing_without_one(tmp_path):
    run, calls = _teardown(tmp_path, "--erase")          # stdin is not a terminal here
    assert run.returncode == 1 and "Nothing was deleted" in run.stderr
    assert "docker" not in calls, calls
    assert "./securax backup" in run.stdout, "the safe step is offered first"


def test_teardown_refuses_an_option_it_does_not_know(tmp_path):
    run, calls = _teardown(tmp_path, "-v")
    assert run.returncode == 2 and calls == ""


def test_teardown_erase_asks_for_a_typed_word():
    text = (SCRIPTS / "teardown.sh").read_text()
    assert '[ "$_word" = "ERASE" ]' in text
    assert text.index("Type ERASE") < text.index("VOLS=(-v)"), "the question comes before the volumes are named for deletion"


def test_the_admission_test_passes_only_on_a_denial():
    text = (SCRIPTS / "kind-up.sh").read_text()
    assert re.search(r"elif grep -qi 'denied' \"\$ERR\"; then\s+log \"  PASS", text), "PASS must follow proof of a denial"
    assert "nothing was proven" in text


def test_no_script_writes_to_a_fixed_name_in_tmp():
    for script in sorted(SCRIPTS.glob("*.sh")):
        fixed = re.findall(r"[>o] ?/tmp/[A-Za-z_.-]+", script.read_text())
        assert not fixed, f"{script.name}: use mktemp, not {fixed}"


def test_bootstrap_stops_when_the_gateway_never_answered():
    text = (SCRIPTS / "bootstrap-laptop.sh").read_text()
    assert text.index("did not answer within a minute") < text.index("5/6 Smoke test")


def test_nothing_tells_a_person_to_overwrite_wsl_conf():
    """install.sh --docker writes the line that starts Docker into /etc/wsl.conf; advice that overwrites the file undoes it."""
    files = [ROOT / "securax", ROOT / "install.sh", ROOT / "install.ps1", *ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md"),
             *SCRIPTS.glob("*.sh")]
    bad = []
    for f in files:
        if f.name == "review-ledger.md" or not f.is_file():
            continue
        for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            if re.search(r"tee /etc/wsl\.conf|[^>]> ?/etc/wsl\.conf", line):
                bad.append(f"{f.relative_to(ROOT)}:{n}")
    assert not bad, bad


def test_getting_started_names_no_file_a_person_does_not_have():
    text = (ROOT / "GETTING-STARTED.md").read_text()
    assert "uploaded" not in text, "a person cannot open a file that was only ever uploaded to a chat"
    assert os.access(SCRIPTS / "teardown.sh", os.X_OK)
