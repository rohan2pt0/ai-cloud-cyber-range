"""One-command setup (no pasting): `routines install` leaves exactly one schedule line, for this folder."""
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]


def _stubs(tmp, crontab_text):
    b = tmp / "bin"
    b.mkdir()
    store = tmp / "crontab.txt"
    store.write_text(crontab_text)
    (b / "crontab").write_text(f'#!/bin/sh\nif [ "$1" = "-l" ]; then cat "{store}"; else cat > "{store}"; fi\n')
    (b / "pgrep").write_text("#!/bin/sh\nexit 0\n")                 # cron "running"
    for f in ("crontab", "pgrep"):
        (b / f).chmod(0o755)
    return b, store


def test_routines_install_replaces_stale_lines(tmp_path):
    stale = ("MAILTO=\"\"\n"
             "* * * * * cd /home/me/ai-cloud-cyber-range && ./securax routines run >> routines/.log 2>&1\n"
             "0 3 * * * echo keep-me\n")
    b, store = _stubs(tmp_path, stale)
    env = {**os.environ, "PATH": f"{b}:{os.environ['PATH']}"}
    r = subprocess.run([str(ROOT / "securax"), "routines", "install"], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [ln for ln in store.read_text().splitlines() if "securax routines run" in ln]
    assert lines == [f'* * * * * cd "{ROOT}" && ./securax routines run >> routines/.log 2>&1']
    assert "echo keep-me" in store.read_text() and 'MAILTO=""' in store.read_text()   # other jobs untouched
    assert "removed 1 line" in r.stdout


def test_routines_install_is_idempotent(tmp_path):
    b, store = _stubs(tmp_path, "")
    env = {**os.environ, "PATH": f"{b}:{os.environ['PATH']}"}
    for _ in range(2):
        subprocess.run([str(ROOT / "securax"), "routines", "install"], env=env, capture_output=True, text=True, timeout=60, check=True)
    assert sum("securax routines run" in ln for ln in store.read_text().splitlines()) == 1
