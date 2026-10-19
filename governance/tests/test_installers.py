"""install.sh does exactly what doc 75 says: refuses a tampered archive, never touches an existing folder, and needs no
repository name baked in when it runs from a clone."""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _sh(*args, home, env_extra=None):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(home), **(env_extra or {})}
    return subprocess.run(["bash", str(ROOT / "install.sh"), *args], capture_output=True, text=True, env=env, timeout=120)


def _release(tmp_path):
    arc = tmp_path / "securax-9.9.9.tar.gz"
    subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar.gz", "--prefix=securax-9.9.9/", "-o", str(arc), "HEAD"], check=True)
    digest = subprocess.run(["sha256sum", arc.name], cwd=tmp_path, capture_output=True, text=True, check=True).stdout
    (tmp_path / "SHA256SUMS").write_text(digest)
    return arc


def test_offline_install_checks_the_checksum_first(tmp_path):
    arc = _release(tmp_path)
    ok = _sh("--offline", str(arc), "--dir", str(tmp_path / "good"), home=tmp_path)
    assert ok.returncode == 0, ok.stderr
    assert "checksum matches" in ok.stdout and (tmp_path / "good" / "securax").exists()
    with arc.open("ab") as f:
        f.write(b"tampered")
    bad = _sh("--offline", str(arc), "--dir", str(tmp_path / "bad"), home=tmp_path)
    assert bad.returncode != 0 and "Checksum mismatch" in bad.stderr and not (tmp_path / "bad").exists()


def test_an_existing_folder_is_never_changed(tmp_path):
    (tmp_path / "securax").mkdir()
    r = _sh("--dir", str(tmp_path / "securax"), home=tmp_path)
    assert r.returncode != 0 and "./securax update" in r.stderr


def test_the_tracked_installers_carry_a_placeholder_not_a_name():
    for name in ("install.sh", "install.ps1"):
        assert "{{REPO_SLUG}}" in (ROOT / name).read_text()


def test_restore_checks_the_backup_before_installing_and_says_the_next_step(tmp_path):
    bad = _sh("--restore", str(tmp_path / "missing.tar.gz"), "--dir", str(tmp_path / "r0"), home=tmp_path)
    assert bad.returncode != 0 and "Backup not found" in bad.stderr and not (tmp_path / "r0").exists()
    enc = tmp_path / "securax-x.tar.gz.gpg"
    enc.write_bytes(b"x")
    nokey = _sh("--restore", str(enc), "--dir", str(tmp_path / "r1"), home=tmp_path)
    assert nokey.returncode != 0 and "--keyfile" in nokey.stderr
    backup = tmp_path / "securax-20261101-0930.tar.gz"
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "MANIFEST").write_text("securax test backup\n")
    subprocess.run(["tar", "czf", str(backup), "-C", str(tmp_path / "data"), "."], check=True)
    arc = _release(tmp_path)
    ok = _sh("--offline", str(arc), "--restore", str(backup), "--dir", str(tmp_path / "r2"), home=tmp_path,
             env_extra={"PATH": "/usr/bin:/bin"})
    assert ok.returncode == 0 and (tmp_path / "r2" / "securax").exists()
    assert "./securax restore" in ok.stdout or "Restoring your data" in ok.stdout      # without Docker: the exact command to run later
