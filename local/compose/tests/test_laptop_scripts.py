"""The laptop scripts and the installer, held where the review found them wrong (review ledger, slice 2).

Nothing here needs Docker: `docker` and `kind` are stand-ins that only write down what they were asked to do.
"""
import os
import re
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEARDOWN = ROOT / "local" / "scripts" / "teardown.sh"


def _teardown(tmp_path, *args, typed=""):
    """Run teardown.sh with stand-in tools first on the PATH; return (what docker was asked, what was printed)."""
    log = tmp_path / "asked.log"
    for tool in ("docker", "kind"):
        fake = tmp_path / tool
        fake.write_text('#!/bin/sh\necho "%s $*" >> "%s"\n' % (tool, log))
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ, PATH=f"{tmp_path}:/usr/bin:/bin")
    done = subprocess.run(["bash", str(TEARDOWN), *args], input=typed, capture_output=True, text=True, env=env, timeout=30)
    asked = log.read_text() if log.exists() else ""
    return asked, done.stdout + done.stderr, done.returncode


def _deletes_volumes(asked):
    return bool(re.search(r"docker compose .* down .*(-v\b|--volumes)", asked))


def test_teardown_keeps_the_data_by_default(tmp_path):
    asked, said, code = _teardown(tmp_path)
    assert code == 0 and "docker compose" in asked and " down" in asked
    assert not _deletes_volumes(asked), "a plain teardown must never delete a data volume"
    assert "data is kept" in said


def test_erase_needs_the_typed_word(tmp_path):
    for typed in ("", "y\n", "yes\n", "ERASE\n"):
        asked, said, _ = _teardown(tmp_path, "--erase", typed=typed)
        assert not _deletes_volumes(asked), f"typed {typed!r} must not delete anything"
        assert "Nothing deleted" in said
        (tmp_path / "asked.log").unlink()


def test_erase_says_what_is_lost_and_offers_the_backup_first(tmp_path):
    asked, said, code = _teardown(tmp_path, "--erase", typed="erase\n")
    assert code == 0 and _deletes_volumes(asked)
    assert "cannot be undone" in said and "./securax backup" in said
    assert said.index("./securax backup") < said.index("Type  erase")


def test_an_unknown_option_stops_before_anything_runs(tmp_path):
    asked, said, code = _teardown(tmp_path, "-v")
    assert code == 1 and asked == "" and "Unknown option" in said


def test_the_installer_reaches_its_own_message_when_the_release_lookup_fails():
    # under `set -euo pipefail` a failed command substitution in an assignment ends the script with no message
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "url_effective" in ln)
    assert "|| true)" in line
    assert "Could not find the newest release" in text


def test_the_installer_help_shows_every_header_line():
    text = (ROOT / "install.sh").read_text(encoding="utf-8").splitlines()
    last = next(i for i, ln in enumerate(text, 1) if i > 1 and not ln.startswith("#")) - 1
    shown = int(re.search(r"sed -n '2,(\d+)p' \"\$0\"", "\n".join(text)).group(1))
    assert shown == last, f"--help prints lines 2 to {shown}, the header ends at line {last}"


def test_no_advice_replaces_wsl_conf():
    # install.sh --docker writes the line that starts Docker into /etc/wsl.conf; advice that overwrites the file undoes it
    for rel in ("securax", "docs/securax/121-DRIVE-HOME.md", "install.sh", "local/scripts/wsl-setup.sh"):
        for ln in (ROOT / rel).read_text(encoding="utf-8").splitlines():
            assert not re.search(r"tee /etc/wsl\.conf|[^>]> ?/etc/wsl\.conf", ln), f"{rel}: {ln.strip()[:90]}"


def test_a_pasted_key_is_never_echoed():
    text = (ROOT / "securax").read_text(encoding="utf-8")
    reads = [ln for ln in text.splitlines() if re.search(r"\bread\b.*\bGK\b", ln)]
    assert reads and all(re.search(r"read -r?s", ln) for ln in reads)


def test_the_admission_check_passes_only_on_a_policy_refusal():
    text = (ROOT / "local" / "scripts" / "kind-up.sh").read_text(encoding="utf-8")
    assert re.search(r"grep -qiE 'kyverno\|admission webhook'", text)
    assert "the policy was not tested" in text


def test_the_scripts_use_no_fixed_temp_file():
    for name in ("kind-up.sh", "bootstrap-laptop.sh", "teardown.sh", "daily-driver-up.sh"):
        text = (ROOT / "local" / "scripts" / name).read_text(encoding="utf-8")
        assert not re.search(r"/tmp/[A-Za-z_]", text), f"{name} writes to a fixed name in /tmp: use mktemp"


def test_getting_started_points_at_nothing_a_person_does_not_have():
    text = (ROOT / "GETTING-STARTED.md").read_text(encoding="utf-8")
    assert "uploaded" not in text, "a file the owner once uploaded is not in the repository"
