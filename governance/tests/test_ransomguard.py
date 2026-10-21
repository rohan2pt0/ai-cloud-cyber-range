"""Ransomware cannot poison the backups (doc 88): encrypted data is recognised, its backup is marked -SUSPECT and deletes
nothing, retention keeps weeks and months (never only the last 7 nights), restores and drills pick the newest CLEAN copy, the
restore twin opens a backup as working data, and a drill with nothing to restore fails instead of passing. Temp folders only."""
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import tarfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("ransomguard", ROOT / "governance" / "ransomguard.py")
rg = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rg)


def _vault(root: pathlib.Path, n: int = 6) -> pathlib.Path:
    v = root / "vault" / "registers"
    v.mkdir(parents=True)
    for i in range(n):
        (v / f"r{i}.json").write_text(json.dumps({"id": f"R-{i}", "title": "Fake risk"}))
    (v / "notes.md").write_text("# Fake notes\n")
    (root / "vault" / "README.txt").write_text("what this folder is\n")
    return root / "vault"


def _encrypt(f: pathlib.Path) -> None:
    f.write_bytes(os.urandom(256))


def test_a_normal_vault_is_clean_and_an_encrypted_one_is_suspect(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))
    v = _vault(tmp_path)
    (v / "~$Book.xlsx").write_bytes(b"lock file, not a zip")                # Office lock files are not damage
    assert rg.check(tmp_path)["suspect"] is False
    _encrypt(v / "registers" / "r0.json")                                    # one damaged file is not ransomware
    assert rg.check(tmp_path)["suspect"] is False
    for f in (v / "registers").glob("*.json"):
        _encrypt(f)
    res = rg.check(tmp_path)
    assert res["suspect"] and any("no longer open" in r for r in res["reasons"])


def test_the_canary_catches_it_even_when_the_vault_is_almost_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))
    made = rg.plant(tmp_path)
    assert len(made) == 2 and rg.check(tmp_path)["suspect"] is False
    _encrypt(tmp_path / "vault" / rg.CANARY_NAME)
    assert "canary" in rg.check(tmp_path)["reasons"][0]
    (tmp_path / "vault" / rg.CANARY_NAME).unlink()                         # deleted after it was planted: evidence, not re-planted
    assert rg.check(tmp_path)["suspect"] and not (tmp_path / "vault" / rg.CANARY_NAME).exists()


def test_ransom_notes_and_endings_are_flagged_but_a_readme_is_not(tmp_path):
    v = _vault(tmp_path)
    assert rg.scan([v])["suspect"] is False
    (v / "HOW_TO_DECRYPT_FILES.txt").write_text("pay")
    assert rg.scan([v])["notes"]
    (v / "HOW_TO_DECRYPT_FILES.txt").unlink()
    (v / "registers" / "r1.json.locked").write_bytes(b"x")
    assert rg.scan([v])["endings"]


def _files(folder: pathlib.Path, days: int, suspect_last: int = 0) -> list[pathlib.Path]:
    folder.mkdir(parents=True, exist_ok=True)
    now, out = time.time(), []
    for d in range(days):
        t = time.localtime(now - d * 86400)
        tag = "-SUSPECT" if d < suspect_last else ""
        f = folder / f"securax-{time.strftime('%Y%m%d-%H%M%S', t)}{tag}.tar.gz.gpg"
        f.write_bytes(b"x")
        out.append(f)
    return out


def test_retention_keeps_weeks_and_months_not_just_the_last_week(tmp_path):
    _files(tmp_path, 100)
    gone = rg.prune(tmp_path, keep=7)
    left = rg.backups(tmp_path)
    ages = [(time.time() - rg.when(f)) / 86400 for f in left]
    assert gone and len(left) <= 7 + 4 + 3
    assert max(ages) > 50, "a copy from months back survives: a week of silent damage cannot rotate the last clean copy out"
    assert sum(a < 7 for a in ages) == 7


def test_a_suspect_streak_never_rotates_the_clean_copies_out(tmp_path):
    _files(tmp_path, 12, suspect_last=8)                                     # 8 nights of encrypted data, newest first
    rg.prune(tmp_path, keep=7)
    left = rg.backups(tmp_path)
    clean = [f for f in left if not rg.suspect(f)]
    assert len(clean) == 4, "every clean copy stays: the newest 7 CLEAN ones are kept, suspect ones do not count"
    assert sum(rg.suspect(f) for f in left) == rg.MAX_SUSPECT
    assert rg.pick(tmp_path) == clean[0] and not rg.suspect(rg.pick(tmp_path))


def test_pick_skips_suspect_and_can_insist_on_encrypted(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "securax-20260101-010101.tar.gz").write_bytes(b"x")
    (b / "securax-20260102-010101.tar.gz.gpg").write_bytes(b"x")
    (a / "securax-20260103-010101-SUSPECT.tar.gz").write_bytes(b"x")
    assert rg.pick(a, b).name == "securax-20260102-010101.tar.gz.gpg"
    assert rg.pick(a, encrypted_only=True) is None


def _staged(tmp: pathlib.Path, db_ok: bool = True, env: bool = True, vault_bad: bool = False) -> pathlib.Path:
    st = tmp / "stage"
    st.mkdir(parents=True)
    vol = tmp / "vol"
    vol.mkdir()
    db = vol / "webui.db"
    con = sqlite3.connect(db)
    con.execute("create table t(x)")
    con.executemany("insert into t values (?)", [(i,) for i in range(500)])
    con.commit()
    con.close()
    if not db_ok:
        raw = bytearray(db.read_bytes())
        raw[4096:8192] = os.urandom(4096)                                     # a damaged page
        db.write_bytes(bytes(raw))
    with tarfile.open(st / "vol-range_openwebui.tgz", "w:gz") as tf:
        tf.add(db, arcname="./webui.db")
    v = _vault(tmp / "src")
    (v / rg.CANARY_NAME).write_text(rg.CANARY_TEXT)
    if vault_bad:
        for f in (v / "registers").glob("*.json"):
            _encrypt(f)
    with tarfile.open(st / "vault.tgz", "w:gz") as tf:
        tf.add(v, arcname="vault")
    if env:
        (st / "env").write_text("GEMINI_API_KEY=fake-value\n")
    return st


def test_the_restore_twin_opens_a_good_backup_as_working_data(tmp_path):
    res = rg.verify(_staged(tmp_path))
    assert res["ok"], res["problems"]
    assert res["volumes"] == 1 and res["databases"] == 1 and res["scan"]["canaries"] == 1


def test_the_twin_finds_a_damaged_database_a_lost_env_and_an_encrypted_vault(tmp_path):
    assert any("integrity" in p for p in rg.verify(_staged(tmp_path / "1", db_ok=False))["problems"])
    assert any(".env" in p for p in rg.verify(_staged(tmp_path / "2", env=False))["problems"])
    assert any("encrypted" in p for p in rg.verify(_staged(tmp_path / "3", vault_bad=True))["problems"])


def test_the_twin_refuses_an_archive_that_escapes_its_folder(tmp_path):
    st = tmp_path / "stage"
    st.mkdir()
    with tarfile.open(st / "vol-evil.tgz", "w:gz") as tf:
        data = b"owned"
        ti = tarfile.TarInfo("../../escaped.txt")
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
    (st / "env").write_text("X=1\n")
    res = rg.verify(st)
    assert not res["ok"] and not (tmp_path / "escaped.txt").exists()


# ------------------------------------------------------------------------------------- the real CLI, on an isolated copy
def _estate(tmp: pathlib.Path) -> tuple[pathlib.Path, dict]:
    r = tmp / "r"
    (r / "local" / "compose").mkdir(parents=True)
    shutil.copy(ROOT / "securax", r / "securax")
    shutil.copy(ROOT / "VERSION", r / "VERSION")
    shutil.copytree(ROOT / "governance", r / "governance", ignore=shutil.ignore_patterns("tests", "__pycache__"))
    (r / "local" / "compose" / ".env").write_text("GEMINI_API_KEY=fake-value\n")
    _vault(r)
    nodock = tmp / "bin"
    nodock.mkdir()
    (nodock / "docker").write_text("#!/bin/sh\nexit 1\n")                  # never touch a real Docker daemon from a unit test
    (nodock / "docker").chmod(0o755)
    env = {**os.environ, "PATH": f"{nodock}:{os.environ['PATH']}", "HOME": str(tmp), "SECURAX_HOME_DIR": str(tmp / "h"),
           "SECURAX_BACKUP_DIR": str(tmp / "b"), "SECURAX_NO_OPEN": "1", "SECURAX_OFFSITE_DIR": "", "ALERT_WEBHOOK": "",
           "SECURAX_BACKUP_KEYFILE": ""}
    return r, env


def _run(r: pathlib.Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(r / "securax"), *args], cwd=r, env=env, capture_output=True, text=True, timeout=120,
                          stdin=subprocess.DEVNULL)


def test_a_drill_with_nothing_to_restore_fails_instead_of_passing(tmp_path):
    r, env = _estate(tmp_path)
    p = _run(r, env, "backup", "drill")
    assert p.returncode == 1 and "no clean backup" in p.stdout


def test_ransomware_night_end_to_end_on_the_real_cli(tmp_path):
    r, env = _estate(tmp_path)
    assert _run(r, env, "backup").returncode == 0
    p = _run(r, env, "backup", "drill")
    assert p.returncode == 0 and "restore twin" in p.stdout and "NOT off-site" in p.stdout, p.stdout + p.stderr
    clean = rg.pick(tmp_path / "b")
    for f in (r / "vault" / "registers").glob("*.json"):                   # the attack
        _encrypt(f)
    _encrypt(r / "vault" / rg.CANARY_NAME)
    time.sleep(1.1)                                                          # a new timestamp in the file name
    p = _run(r, env, "backup")
    assert p.returncode == 3 and "RANSOMWARE SUSPECTED" in p.stdout, p.stdout + p.stderr
    names = sorted(f.name for f in (tmp_path / "b").iterdir())
    assert len(names) == 2 and sum("-SUSPECT" in n for n in names) == 1 and clean.name in names
    p = _run(r, env, "backup", "drill")
    assert p.returncode == 0 and clean.name in p.stdout, "the drill proves the CLEAN copy, not the newest one"
    p = _run(r, env, "restore", "latest", "--yes")
    assert f"Restoring the newest clean backup: {clean}" in p.stdout, p.stdout + p.stderr
    assert json.loads((r / "vault" / "registers" / "r0.json").read_text())["id"] == "R-0", "the vault is readable again"
    assert list(r.glob("vault.pre-restore-*")), "the encrypted vault is kept aside as evidence, never overwritten"


def test_files_windows_writes_are_not_mistaken_for_encryption(tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    (v / "bom.json").write_bytes('﻿{"id": "R-1"}'.encode("utf-8"))           # Notepad's UTF-8 with a byte-order mark
    (v / "excel.csv").write_bytes("Name,Café,€5\r\n".encode("cp1252"))          # Excel's default CSV
    (v / "unicode.txt").write_bytes("a\tb\r\n".encode("utf-16"))                 # Excel's "Unicode text"
    (v / "half.json").write_bytes(b'{"id": ')                                    # malformed, but not encrypted
    (v / "empty.json").write_bytes(b"")
    res = rg.scan([v])
    assert res["suspect"] is False and res["unreadable"] == [], res
