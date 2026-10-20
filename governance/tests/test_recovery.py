"""`./securax rollback`: working versions are recorded and pinned, the way back is safe (stash, backup, pin), a version that
does not start sends you back where you were, and the record stays bounded. A throwaway git repo and a fake estate."""
import importlib.util
import json
import pathlib
import subprocess
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("recovery", ROOT / "governance" / "recovery.py")
rc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rc)


def sh(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "estate"
    r.mkdir()
    sh(r, "init", "-q", "-b", "main")
    sh(r, "config", "user.email", "t@example.invalid")
    sh(r, "config", "user.name", "t")
    commits = []
    for v in ("0.1.0", "0.2.0", "0.3.0"):
        (r / "VERSION").write_text(v + "\n")
        (r / "app.txt").write_text(f"app {v}\n")
        sh(r, "add", "-A")
        sh(r, "commit", "-q", "-m", v)
        commits.append(sh(r, "rev-parse", "HEAD"))
    sh(r, "tag", "v0.1.0", commits[0])
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "home"))
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "backups"))
    (tmp_path / "backups").mkdir()
    return r, commits


class Estate:
    """A pretend estate: `up` works unless the checked-out VERSION is in `broken`; records every command."""

    def __init__(self, repo, broken=()):
        self.repo, self.broken, self.calls, self.up = repo, set(broken), [], False

    def __call__(self, *args, root=None, timeout=0):
        self.calls.append(args)
        if args[0] == "up":
            self.up = (self.repo / "VERSION").read_text().strip() not in self.broken
            return (0 if self.up else 1), "up"
        if args[0] == "down":
            self.up = False
        if args[0] == "ready":
            return (0 if self.up else 1), "READY" if self.up else "NOT READY"
        return 0, f"{args[0]} done\n✔ backup written"

    def ready(self, root=None, run=None):
        return self.up


def record_each(r, commits, now0=None):
    now0 = now0 or time.time() - 30 * 86400
    for i, c in enumerate(commits):
        sh(r, "checkout", "-q", c)
        rc.record("up", root=r, now=now0 + i * 86400)
    sh(r, "checkout", "-q", "main")


def test_working_versions_are_recorded_pinned_and_bounded(repo, monkeypatch):
    r, commits = repo
    t0 = time.time() - 30 * 86400
    record_each(r, commits, now0=t0)
    assert rc.record("up", root=r, now=t0 + 2 * 86400 + 60) is None          # same version, a minute later: not again
    rows = rc.load()
    assert [x["version"] for x in rows] == ["0.1.0", "0.2.0", "0.3.0"] and all(x["commit"] for x in rows)
    refs = sh(r, "for-each-ref", "--format=%(objectname)", "refs/securax/good/").split()
    assert sorted(refs) == sorted(commits)                                            # each one pinned in git
    monkeypatch.setattr(rc, "KEEP", 2)
    sh(r, "checkout", "-q", commits[0])
    rc.record("up", root=r, now=t0 + 10 * 86400)
    assert len(rc.load()) == 2 and len(sh(r, "for-each-ref", "refs/securax/good/").splitlines()) == 2   # the record and pins stay bounded


def test_choosing_where_to_go_back_to(repo):
    r, commits = repo
    record_each(r, commits)
    rows = rc.load()
    assert rc.resolve(None, rows, root=r)["commit"] == commits[1]                    # newest working version older than HEAD
    assert rc.resolve("3", rows, root=r)["commit"] == commits[0]
    assert rc.resolve("v0.1.0", rows, root=r)["version"] == "0.1.0"
    with pytest.raises(ValueError):
        rc.resolve("9", rows, root=r)
    with pytest.raises(ValueError):
        rc.resolve("nope", rows, root=r)
    with pytest.raises(ValueError, match="No working version"):
        rc.resolve(None, [], root=r)


def test_going_back_keeps_edits_backs_up_and_can_come_forward(repo):
    r, commits = repo
    record_each(r, commits)
    (r / "app.txt").write_text("my unsaved edit\n")
    est = Estate(r)
    est.up = True
    out = []
    code = rc.go(rc.resolve(None, rc.load(), root=r), root=r, run=est, ready=est.ready, say=out.append)
    assert code == 0 and sh(r, "rev-parse", "HEAD") == commits[1] and (r / "VERSION").read_text().strip() == "0.2.0"
    assert ("backup",) in est.calls and est.calls.index(("backup",)) < est.calls.index(("up",))   # data backed up before the switch
    assert "securax-rollback-" in sh(r, "stash", "list")                             # the unsaved edit is kept, not lost
    assert sh(r, "for-each-ref", "--format=%(objectname)", "refs/securax/before-rollback/") == commits[2]
    assert any("healthy" in x for x in out) and rc.load()[-1]["reason"] == "rollback"
    assert rc.latest(root=r, run=est, ready=est.ready, say=out.append) == 0
    assert sh(r, "rev-parse", "--abbrev-ref", "HEAD") == "main" and sh(r, "rev-parse", "HEAD") == commits[2]


def test_a_version_that_does_not_start_sends_you_back(repo):
    r, commits = repo
    record_each(r, commits)
    est = Estate(r, broken={"0.2.0"})
    est.up = True
    out = []
    code = rc.go(rc.resolve("2", rc.load(), root=r), root=r, run=est, ready=est.ready, say=out.append)
    assert code == 3 and sh(r, "rev-parse", "--abbrev-ref", "HEAD") == "main" and sh(r, "rev-parse", "HEAD") == commits[2]
    assert est.up and any("Returning to where you were" in x for x in out)


def test_with_data_restores_the_backup_of_that_time_and_check_finds_gaps(repo, tmp_path):
    r, commits = repo
    b = tmp_path / "backups" / "securax-20260101.tar.gz"
    b.write_text("pretend backup")
    record_each(r, commits)
    est = Estate(r)
    est.up = True
    target = rc.resolve("2", rc.load(), root=r)
    assert target["backup"] == str(b)
    assert rc.go(target, with_data=True, root=r, run=est, ready=est.ready, say=lambda *_: None) == 0
    assert ("restore", str(b), "--yes") in est.calls
    assert rc.check(rc.load(), root=r) == []
    b.unlink()
    assert any("backup" in p and "gone" in p for p in rc.check(rc.load(), root=r))


def test_the_command_line_lists_and_asks_first(repo, monkeypatch, capsys):
    r, commits = repo
    record_each(r, commits)
    monkeypatch.setattr(rc, "ROOT", r)
    monkeypatch.setattr(rc, "git", lambda *a, root=r, check=False: (lambda p: (p.returncode, p.stdout.strip()))(
        subprocess.run(["git", "-C", str(r), *a], capture_output=True, text=True)))
    assert rc.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "v0.3.0" in out and "running now" in out and out.index("v0.3.0") < out.index("v0.1.0")
    assert rc.main([]) == 2 and "add --yes" in capsys.readouterr().out               # never acts without being told to
    assert sh(r, "rev-parse", "HEAD") == commits[2]
    assert json.loads(rc.ledger_path().read_text().splitlines()[0])["version"] == "0.1.0"
