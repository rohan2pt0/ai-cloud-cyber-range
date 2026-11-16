"""`./securax stop`, `restore`, `backup` and `setup` (review ledger, slice 4).

A stop of one add-on really stops it, and says so only when it did; a restore never empties a volume that a running
part still holds, and never takes a volume name from a file it cannot trust; a backup is never readable by others
while it is written; and no secret is ever made from the clock.

Each test runs a COPY of the CLI in a scratch folder with a pretend `docker`, so nothing here starts, stops or
restores anything real.
"""
import hashlib
import io
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLI = ROOT / "securax"

PRETEND_DOCKER = """#!/bin/sh
echo "docker $*" >> "$CALLS"
case "$1" in
  ps)   [ -n "$BUSY" ] && echo "{busy}"; exit 0 ;;
  stop) exit "${{STOP_EXIT:-0}}" ;;
  compose) exit "${{COMPOSE_EXIT:-0}}" ;;
esac
exit 0
"""


def _estate(tmp_path, env_text=""):
    """A scratch copy of the CLI with a settings file and a docker that only writes down how it was called."""
    home = tmp_path / "estate"
    (home / "local" / "compose").mkdir(parents=True)
    shutil.copy(CLI, home / "securax")
    shutil.copy(ROOT / "local" / "compose" / "tls-internal.yml", home / "local" / "compose" / "tls-internal.yml")
    (home / "local" / "compose" / ".env").write_text(env_text)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    tool = bindir / "docker"
    tool.write_text(PRETEND_DOCKER.format(busy="pretend-container"))
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    return home, bindir, tmp_path / "calls.log"


def _run(home, bindir, calls, *args, **extra):
    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}", CALLS=str(calls),
               SECURAX_NO_OPEN="1", SECURAX_HOME_DIR=str(home / "dot"), **extra)
    done = subprocess.run(["bash", str(home / "securax"), *args], capture_output=True, text=True, env=env,
                          stdin=subprocess.DEVNULL, timeout=60)
    return done, (calls.read_text() if calls.exists() else "")


def _branch(name):
    """The text of one top-level `case` branch of the CLI."""
    text = CLI.read_text(encoding="utf-8")
    start = re.search(rf"^  {name}\)", text, re.M)
    assert start, f"no '{name})' branch in securax"
    end = re.search(r"^    ;;$", text[start.end():], re.M)
    return text[start.start(): start.end() + end.end()]


def _tgz(member_names):
    blob = io.BytesIO()
    with tarfile.open(fileobj=blob, mode="w:gz") as tar:
        for name in member_names:
            info = tarfile.TarInfo(name)
            info.size = 2
            tar.addfile(info, io.BytesIO(b"x\n"))
    return blob.getvalue()


def _backup_file(tmp_path, volume_names, vault_members=None):
    """A pretend backup: one small archive per volume name, and the checksums `restore` asks for."""
    inner = {}
    if vault_members:
        inner["vault.tgz"] = _tgz(vault_members)
    for name in volume_names:
        blob = io.BytesIO()
        with tarfile.open(fileobj=blob, mode="w:gz"):
            pass
        inner[f"vol-{name}.tgz"] = blob.getvalue()
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  ./{fname}\n" for fname, data in inner.items())
    inner["SHA256SUMS"] = sums.encode()
    out = tmp_path / "pretend-backup.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        for fname, data in inner.items():
            info = tarfile.TarInfo(f"./{fname}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return out


# ---- stop ------------------------------------------------------------------------------------------------------------

def test_stop_names_only_services_that_exist(tmp_path):
    """Without internal TLS there is no sidecar; naming one makes compose stop nothing at all."""
    home, bindir, calls = _estate(tmp_path, "SECURAX_OPTIONAL=docs flows\n")
    done, log = _run(home, bindir, calls, "stop", "docs")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "stop anythingllm" in log
    assert "-tls" not in log, "`stop` named a TLS sidecar that no compose file defines, so nothing would stop"


def test_stop_names_the_sidecar_when_internal_tls_is_on(tmp_path):
    home, bindir, calls = _estate(tmp_path, "COMPOSE_FILE=docker-compose.yml:tls.yml:tls-internal.yml\nTLS_INTERNAL=1\n")
    _, log = _run(home, bindir, calls, "stop", "docs")
    assert "stop anythingllm anythingllm-tls" in log


def test_stop_never_names_a_sidecar_the_overlay_does_not_define(tmp_path):
    """The password manager has no sidecar: with internal TLS on, naming one stopped (and started) nothing."""
    home, bindir, calls = _estate(tmp_path, "COMPOSE_FILE=docker-compose.yml:tls.yml:tls-internal.yml\nTLS_INTERNAL=1\n")
    done, log = _run(home, bindir, calls, "stop", "passwords")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "stop vaultwarden" in log and "vaultwarden-tls" not in log
    assert 'has_sidecar "$_s"' in _branch("start"), "`start` must ask the same question before it names a sidecar"


def test_stop_says_the_data_is_kept_and_forgets_the_add_on(tmp_path):
    home, bindir, calls = _estate(tmp_path, "SECURAX_OPTIONAL=docs flows\n")
    done, _ = _run(home, bindir, calls, "stop", "docs")
    assert "data is kept" in done.stdout
    assert "./securax start docs" in done.stdout, "the stop ends on the one next step"
    assert "SECURAX_OPTIONAL=flows" in (home / "local" / "compose" / ".env").read_text()


def test_a_stop_that_failed_says_so_and_remembers_the_add_on(tmp_path):
    home, bindir, calls = _estate(tmp_path, "SECURAX_OPTIONAL=docs flows\n")
    done, _ = _run(home, bindir, calls, "stop", "docs", COMPOSE_EXIT="1")
    assert done.returncode == 1
    assert "Could not stop" in done.stdout
    assert "./securax why" in done.stdout
    assert "SECURAX_OPTIONAL=docs flows" in (home / "local" / "compose" / ".env").read_text(), \
        "a part that is still running must not be forgotten: the next `up` would not bring it back"


# ---- restore ---------------------------------------------------------------------------------------------------------

def test_restore_refuses_a_volume_name_it_cannot_trust(tmp_path):
    """The name comes from a file inside the backup and goes into a shell line: only plain volume names pass."""
    home, bindir, calls = _estate(tmp_path)
    bad = _backup_file(tmp_path, ["fine_data", "x;touch pwned"])
    done, log = _run(home, bindir, calls, "restore", str(bad), "--yes")
    assert done.returncode == 1
    assert "Nothing was changed" in done.stdout
    assert "docker run" not in log, "a volume was emptied before every name in the backup was checked"
    assert " down" not in log, "the estate was stopped for a backup that was then refused"


def test_restore_refuses_a_file_that_would_write_into_the_code_folder(tmp_path):
    """The private registers unpack next to the code; a member outside vault/ could replace the CLI itself."""
    home, bindir, calls = _estate(tmp_path)
    bad = _backup_file(tmp_path, ["fine_data"], vault_members=["vault/ok.json", "securax"])
    before = (home / "securax").read_bytes()
    done, log = _run(home, bindir, calls, "restore", str(bad), "--yes")
    assert done.returncode == 1
    assert "Nothing was changed" in done.stdout
    assert "docker run" not in log and " down" not in log
    assert (home / "securax").read_bytes() == before


def test_restore_never_empties_a_volume_a_running_part_still_holds(tmp_path):
    home, bindir, calls = _estate(tmp_path)
    good = _backup_file(tmp_path, ["fine_data"])
    done, log = _run(home, bindir, calls, "restore", str(good), "--yes", BUSY="1", STOP_EXIT="1")
    assert done.returncode == 1
    assert "ps -q --filter volume=fine_data" in log
    assert "docker stop pretend-container" in log
    assert "docker run" not in log, "the volume was emptied under a container that was still running"
    assert "./securax down" in done.stdout


def test_restore_checks_who_holds_a_volume_before_it_empties_it():
    text = _branch("restore")
    assert text.index("--filter \"volume=$V\"") < text.index("find /v -mindepth 1 -delete")


# ---- backup and setup ------------------------------------------------------------------------------------------------

def test_a_backup_is_never_readable_by_others_while_it_is_written():
    text = _branch("backup")
    mask = re.search(r"^    umask 077\b", text, re.M)
    assert mask and mask.start() < text.index('mkdir -p "$DEST"'), \
        "the backup holds the keys: set the mask before its folder and file are made, not a chmod afterwards"


def test_no_command_is_printed_with_a_placeholder_for_the_backup_file():
    for name in ("backup", "restore"):
        for line in _branch(name).splitlines():
            if line.lstrip().startswith("#"):
                continue
            assert "restore <file>" not in line and "restore FILE" not in line, \
                f"`{name}` prints a command a person cannot run as written: {line.strip()[:120]}"


def test_no_secret_is_made_from_the_clock():
    text = CLI.read_text(encoding="utf-8")
    assert not re.search(r"date \+%s%N \| sha256sum", text), \
        "a token or password made from the time can be guessed: use /dev/urandom when openssl is missing"
