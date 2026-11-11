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


# ── one command ends with a running estate (owner, 2026-11-11: setup was still tedious) ──
def _stubs(tmp_path, sudo_rc=1):
    """A bin folder that makes the laptop path testable offline: git clone copies this checkout, docker has no compose,
    and sudo records what it was asked to run (and fails, so nothing real is installed)."""
    b = tmp_path / "bin"
    b.mkdir()
    (b / "git").write_text(f'#!/bin/bash\nif [ "$1" = clone ]; then d="${{@: -1}}"; mkdir -p "$d"; /usr/bin/git -C {ROOT} archive HEAD | tar -x -C "$d"; exit 0; fi\nexec /usr/bin/git "$@"\n')
    (b / "docker").write_text("#!/bin/bash\nexit 1\n")
    (b / "sudo").write_text(f'#!/bin/bash\necho "$@" >> {tmp_path}/sudo.log\nexit {sudo_rc}\n')
    for f in b.iterdir():
        f.chmod(0o755)
    return {"PATH": f"{b}:/usr/bin:/bin:/usr/local/bin", "SECURAX_REPO": "owner/repo"}


def test_without_docker_and_without_a_yes_it_asks_nothing_installs_nothing_and_says_the_one_next_step(tmp_path):
    r = _sh("--dir", str(tmp_path / "s"), home=tmp_path, env_extra=_stubs(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "install.sh\" --docker" in r.stdout and "securax up" in r.stdout
    assert not (tmp_path / "sudo.log").exists()                         # no tty, no --yes: never escalates by itself


def test_with_yes_it_installs_docker_through_the_shared_audited_path_and_fails_plainly(tmp_path):
    r = _sh("--yes", "--dir", str(tmp_path / "s"), home=tmp_path, env_extra=_stubs(tmp_path, sudo_rc=1))
    called = (tmp_path / "sudo.log").read_text()
    assert f"{tmp_path / 's'}/install.sh --docker" in called            # the local copy just cloned, never a second download
    assert r.returncode != 0 and "Docker did not install" in r.stderr


def test_docker_mode_is_root_only_and_installs_from_dockers_own_repository_for_the_sudo_user(tmp_path):
    stub = _stubs(tmp_path)                                               # docker without compose: "not installed"
    r = subprocess.run(["bash", str(ROOT / "install.sh"), "--docker"], capture_output=True, text=True, timeout=60,
                       env={"PATH": stub["PATH"], "HOME": str(tmp_path), "SECURAX_SERVER_DRYRUN": "1", "SUDO_USER": "fakeuser",
                            "SECURAX_REPO": "owner/repo"})
    if subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip() != "0":
        assert r.returncode != 0 and "runs as root" in r.stderr
        return
    out = r.stdout
    assert r.returncode == 0, r.stderr
    assert "download.docker.com" in out and "signed-by=/etc/apt/keyrings/docker.asc" in out
    assert "usermod -aG docker fakeuser" in out
    src = (ROOT / "install.sh").read_text()
    assert src.count("install_docker") == 3                            # one definition, used by --server and --docker
