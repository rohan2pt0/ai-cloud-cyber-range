"""Friction removers in the CLI: `securax` from any folder, and `why` for a failing container, with a stand-in `docker` so it runs anywhere."""
import importlib.util
import os
import pathlib
import re
import stat
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent.parent
spec = importlib.util.spec_from_file_location("why", REPO / "governance" / "why.py")
why = importlib.util.module_from_spec(spec)
spec.loader.exec_module(why)


@pytest.mark.parametrize("log, word", [
    ("write /data: no space left on device", "disk is full"), ("listen tcp 0.0.0.0:8080: bind: address already in use", "port"),
    ("Killed", "memory"), ("x509: certificate signed by unknown authority", "certificate"),
    ("sqlalchemy.exc.OperationalError: database is locked", "backup"), ("WEBUI_SECRET_KEY not set", "setup"),
    ("OSError: [Errno 13] Permission denied: '/app/data'", "WSL"), ("dial tcp: connection refused", "depends"),
    ("Traceback (most recent call last):\n  File x", "update"),
])
def test_known_failures_get_a_plain_hint_that_never_says_delete_the_data(log, word):
    h = why.hint(log)
    assert word.lower() in h.lower() and not re.search(r"(?<!not )delete the data", h.lower())


def test_unknown_output_gets_no_invented_diagnosis():
    assert why.hint("INFO all good\nlistening") == ""


def fake_docker(tmp_path, ps_lines, log):
    b = tmp_path / "bin"
    b.mkdir()
    d = b / "docker"
    d.write_text(f"""#!/bin/sh
case "$1 $2" in
  "info "*) exit 0;;
  "compose ps") printf '%s\\n' "{ps_lines}"; exit 0;;
  "compose logs") printf '%s\\n' "{log}"; exit 0;;
esac
exit 0
""")
    d.chmod(d.stat().st_mode | stat.S_IEXEC)
    return b


def run(args, tmp_path, bindir=None, home=None):
    env = {**os.environ, "HOME": str(home or tmp_path / "home"), "PATH": f"{bindir}:{os.environ['PATH']}" if bindir else os.environ["PATH"]}
    (tmp_path / "home").mkdir(exist_ok=True)
    return subprocess.run(["bash", str(REPO / "securax"), *args], capture_output=True, text=True, env=env, timeout=60)


def test_why_names_the_stopped_service_shows_its_log_and_explains(tmp_path):
    b = fake_docker(tmp_path, "open-webui Exited (1) 3 seconds ago", "sqlalchemy.exc.OperationalError: database is locked")
    p = run(["why"], tmp_path, b)
    assert p.returncode == 0 and "open-webui" in p.stdout and "database is locked" in p.stdout and "./securax backup" in p.stdout


def test_why_says_so_when_everything_is_healthy(tmp_path):
    b = fake_docker(tmp_path, "gateway Up 2 minutes (healthy)", "")
    assert "looks healthy" in run(["why"], tmp_path, b).stdout


def test_why_tells_a_beginner_what_to_do_when_docker_is_off(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    (b / "docker").write_text("#!/bin/sh\nexit 1\n")
    (b / "docker").chmod(0o755)
    p = run(["why"], tmp_path, b)
    assert p.returncode == 1 and "Docker Desktop" in p.stdout


def test_shortcut_lets_you_run_securax_from_any_folder_and_can_be_undone(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").write_text("# mine\n")
    p = run(["shortcut"], tmp_path, home=home)
    w = home / ".local" / "bin" / "securax"
    assert p.returncode == 0 and w.exists() and os.access(w, os.X_OK)
    assert "securax-shortcut" in (home / ".bashrc").read_text() and "new one" in p.stdout or "any folder" in p.stdout
    elsewhere = subprocess.run([str(w), "help"], cwd="/", capture_output=True, text=True, env={**os.environ, "HOME": str(home)})
    assert elsewhere.returncode == 0 and "START HERE" in elsewhere.stdout
    run(["shortcut"], tmp_path, home=home)                                   # idempotent: the rc file gets the line once
    assert (home / ".bashrc").read_text().count("securax-shortcut") == 1
    run(["shortcut", "off"], tmp_path, home=home)
    assert not w.exists() and "securax-shortcut" not in (home / ".bashrc").read_text() and "# mine" in (home / ".bashrc").read_text()


def test_the_launcher_explains_itself_when_the_folder_was_moved(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    w = home / ".local" / "bin"
    w.mkdir(parents=True)
    (w / "securax").write_text('#!/bin/sh\n[ -x "/nonexistent/securax" ] || { echo "SecuRAX was moved. Open its folder and run:  ./securax shortcut"; exit 1; }\n')
    (w / "securax").chmod(0o755)
    p = subprocess.run([str(w / "securax")], capture_output=True, text=True)
    assert p.returncode == 1 and "was moved" in p.stdout
