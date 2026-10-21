"""Every read-only command a user may type runs without a Python traceback and without a crash-level exit code, on a machine with
no estate running (the state CI and a new user start from). A traceback is the worst thing a non-expert can be shown."""
import os
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SAFE = ["help", "route fix the gateway", "brief fix the sync token check", "jewels", "continuity", "continuity show github-down",
        "online", "online status", "lifeos", "features", "lessons recent 3", "routines list", "rollback --check", "exercise list",
        "finish", "incident", "privacy check", "config check", "nodes", "channel", "online invite",
        "continuity tabletop"]


@pytest.mark.parametrize("cmd", SAFE)
def test_read_only_commands_never_crash(cmd, tmp_path):
    env = {**os.environ, "HOME": str(tmp_path), "SECURAX_HOME_DIR": str(tmp_path / "h"), "SECURAX_NO_OPEN": "1"}
    p = subprocess.run(["bash", str(ROOT / "securax"), *cmd.split()], cwd=ROOT, env=env, capture_output=True, text=True,
                       timeout=120, stdin=subprocess.DEVNULL)
    out = p.stdout + p.stderr
    assert "Traceback (most recent call last)" not in out, out[-1500:]
    assert "unknown command" not in out, out[-500:]
    assert p.returncode in (0, 1, 2), (p.returncode, out[-800:])        # 1 = something needs you, 2 = usage; never a crash
