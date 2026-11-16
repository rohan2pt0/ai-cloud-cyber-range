"""Review slice 2 (docs/specs/review-ledger.md): what the installer and the older local scripts must never do again.

Nothing here starts Docker, a cluster or a download: `teardown.sh` runs against fake `docker` and `kind` programs that
only write down how they were called, and the rest reads the script text."""
import os
import re
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEARDOWN = ROOT / "local" / "scripts" / "teardown.sh"


def _fakes(tmp_path):
    """A PATH whose docker and kind only record their arguments."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "calls.log"
    for name in ("docker", "kind"):
        prog = bindir / name
        prog.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n')
        prog.chmod(prog.stat().st_mode | stat.S_IXUSR)
    return {"PATH": f"{bindir}:{os.environ['PATH']}", "HOME": str(tmp_path)}, log


def _teardown(tmp_path, *args, typed=""):
    env, log = _fakes(tmp_path)
    run = subprocess.run(["bash", str(TEARDOWN), *args], input=typed, capture_output=True, text=True, env=env, timeout=30)
    return run, (log.read_text() if log.exists() else "")


def test_teardown_keeps_the_data_by_default(tmp_path):
    run, calls = _teardown(tmp_path)
    assert run.returncode == 0, run.stderr
    down = [line for line in calls.splitlines() if line.startswith("docker compose")]
    assert down and " down" in down[0], calls
    assert "-v" not in down[0].split(), "a plain teardown must never delete the data volumes"
    assert "data is kept" in run.stdout


def test_teardown_erases_only_after_the_typed_word(tmp_path):
    run, calls = _teardown(tmp_path, "--erase", typed="y\n")
    assert run.returncode == 0
    assert "docker" not in calls, "anything but the typed word must stop nothing and delete nothing"
    assert "nothing was deleted" in run.stdout.lower()
    assert "./securax backup" in run.stdout, "the safe step is offered first"


def test_teardown_erases_with_the_typed_word(tmp_path):
    run, calls = _teardown(tmp_path, "--erase", typed="ERASE\n")
    assert run.returncode == 0, run.stderr
    assert "-v" in calls.split(), calls


def test_teardown_refuses_an_option_it_does_not_know(tmp_path):
    run, calls = _teardown(tmp_path, "-v")
    assert run.returncode == 2
    assert calls == ""


def test_the_docs_do_not_call_an_erase_a_stop():
    for name in ("GETTING-STARTED.md", "README.md"):
        for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
            if "teardown.sh" in line and "stop everything" in line:
                assert "keep your data" in line, f"{name}: {line.strip()}"


def test_the_server_firewall_lets_in_the_port_ssh_really_uses():
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "sshd -T" in text, "ask sshd which ports it listens on before the firewall goes on"
    enable = [line for line in text.splitlines() if "ufw --force enable" in line and line.lstrip().startswith("elif")]
    assert enable and "_ufw_ssh" in enable[0], "the firewall is switched on only after every SSH port is allowed"


def test_the_server_checks_the_backup_before_it_changes_the_machine():
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    server = text[text.index('if [ "$SERVER" = 1 ]; then'):]
    assert server.index("Backup not found") < server.index("apt-get update"), "a typo in --restore must cost nothing"


def test_no_network_ends_the_stable_install_with_a_plain_reason():
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    want = next(line for line in text.splitlines() if line.strip().startswith('WANT="$(curl'))
    assert want.rstrip().endswith('|| true)"'), "under pipefail a failed look-up must not end the script before its message"
    for clone in re.findall(r"git clone --quiet[^\n]*\n[^\n]*", text):
        assert "|| die" in clone, "a failed download says what happened and the next step"


def test_no_script_writes_to_a_fixed_name_in_tmp():
    for path in sorted((ROOT / "local" / "scripts").glob("*.sh")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not re.search(r"[>o] ?/tmp/[a-z_]+\.[a-z]+", line), f"{path.name}:{n} use mktemp, not a fixed name in /tmp"


def test_the_wsl_dns_advice_adds_to_wsl_conf_and_never_replaces_it():
    """install.sh --docker writes `systemd=true` into /etc/wsl.conf; advice that overwrites the file stops Docker starting."""
    for rel in ("securax", "docs/securax/121-DRIVE-HOME.md"):
        for line in (ROOT / rel).read_text(encoding="utf-8").splitlines():
            if "generateResolvConf" in line and "tee" in line:
                assert "tee -a /etc/wsl.conf" in line, f"{rel}: {line.strip()[:120]}"


def test_a_port_clash_names_the_tool_for_this_system():
    text = (ROOT / "securax").read_text(encoding="utf-8")
    block = text[text.index("already used by another program (or an old copy"):][:1400]
    assert "netstat -ano" in block and "lsof -nP" in block and "ss -ltnp" in block
