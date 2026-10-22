"""Crown jewels and continuity: live checks become a ranked risk with the one next step, RPO is measured from real backups and
bundles, drills are timed and recorded, and the code survives without GitHub (a bundle that clones). Temp folders only."""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "governance"))
_c = importlib.util.spec_from_file_location("continuity", ROOT / "governance" / "continuity.py")
ct = importlib.util.module_from_spec(_c)
_c.loader.exec_module(ct)
sys.modules["continuity"] = ct
_j = importlib.util.spec_from_file_location("jewels", ROOT / "governance" / "jewels.py")
jw = importlib.util.module_from_spec(_j)
_j.loader.exec_module(jw)


def test_failing_checks_raise_a_single_point_of_failure_to_do_now_and_fixing_it_drops_it():
    cat = {"jewels": [{"id": "a", "name": "A", "why": "w", "impact": 5, "spof": True, "checks": ["x", "y"], "treat": "t", "command": "c", "scenario": "s"},
                      {"id": "b", "name": "B", "why": "w", "impact": 3, "spof": False, "checks": ["z"], "treat": "t", "command": "c", "scenario": "s"}]}
    bad = jw.assess(cat, {"x": (False, ""), "y": (None, ""), "z": (True, "")})
    assert [r["id"] for r in bad] == ["a", "b"] and bad[0]["priority"] == "DO NOW" and bad[0]["score"] == 30.0   # 5 x (1+2+1) x 1.5
    good = jw.assess(cat, {"x": (True, ""), "y": (True, ""), "z": (True, "")})
    assert good[0]["priority"] == "WATCH" and good[0]["score"] == 7.5


def test_every_jewel_check_exists_and_every_scenario_it_names_is_in_the_plan():
    cat = json.loads((ROOT / "governance" / "jewels.json").read_text())
    found = jw.checks()
    scen = {s["id"] for s in ct.load()}
    for j in cat["jewels"]:
        assert set(j["checks"]) <= set(found), j["id"]
        assert j["scenario"] in scen and j["command"].startswith("./securax "), j["id"]


def test_rpo_comes_from_the_real_backup_and_drills_are_timed_and_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))
    (tmp_path / "b").mkdir()
    assert ct.rpo_minutes("backup") is None                                   # nothing protects it yet
    f = tmp_path / "b" / "securax-20261020-010000.tar.gz.gpg"
    f.write_text("x")
    os.utime(f, (time.time() - 3 * 3600, time.time() - 3 * 3600))
    assert 170 < ct.rpo_minutes("backup") < 190
    plan = [{"id": "s1", "title": "T", "notice": "n", "rto_min": 5, "rpo_min": 60, "rpo_source": "backup", "steps": ["a"], "drill": "fake"}]
    assert ct.status(plan)[0]["ok"] is False                                   # 3 h old against a 1 h target, and never drilled
    out = []
    assert ct.drill("s1", plan, runner=lambda k: (True, "fine"), say=out.append) == 0 and "passed" in out[0]
    assert ct.last_drills()["s1"]["ok"] and ct.status(plan)[0]["rto_ok"] is True


def _repo(path: pathlib.Path, *extra: str) -> pathlib.Path:
    """A small whole repository with two commits (CI checks this one out shallow, so the test brings its own)."""
    def g(*a):
        subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *a], check=True, capture_output=True)
    path.mkdir()
    g("init", "-q", *extra)
    for n in ("1", "2"):
        (path / "securax").write_text(n)
        g("add", "-A")
        g("commit", "-qm", n)
    return path


def test_the_code_survives_without_github_a_bundle_that_clones(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))
    monkeypatch.setenv("MIRROR_REMOTES", "")
    repo = _repo(tmp_path / "r")
    assert ct.mirror(say=lambda *_: None, repo=repo) == 0 and (tmp_path / "b" / "repo-latest.bundle").exists()
    assert ct.rpo_minutes("repo", repo=repo) == 0.0                            # the bundle holds HEAD
    ok, note = ct.run_drill("repo-bundle", repo=repo)
    assert ok, note


def test_a_shallow_checkout_is_refused_rather_than_bundled_broken(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "b"))
    full = _repo(tmp_path / "full")
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{full}", str(tmp_path / "shallow")], check=True, capture_output=True)
    out = []
    assert ct.mirror(say=out.append, repo=tmp_path / "shallow") == 1 and "shallow" in out[0]
    assert not (tmp_path / "b" / "repo-latest.bundle").exists()


def test_mirror_setup_makes_a_key_then_saves_the_address_and_pushes_every_branch(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))
    monkeypatch.setenv("MIRROR_REMOTES", "")
    monkeypatch.setattr(ct, "ENVF", tmp_path / "env" / ".env")
    repo = _repo(tmp_path / "r")
    out = []
    if shutil.which("ssh-keygen"):
        assert ct.mirror_setup("", say=out.append, repo=repo) == 0
        assert ct.mirror_key().exists() and any("ssh-ed25519" in x for x in out) and any("Grant write permissions" in x for x in out)
    else:                                                                       # no traceback: a plain message and how to fix it
        assert ct.mirror_setup("", say=out.append, repo=repo) == 1 and "apt install openssh-client" in out[0]
    assert ct.mirror_setup("https://gitlab.example.invalid/x/y.git", say=out.append, repo=repo) == 2   # the HTTPS address is refused with a hint
    bare = tmp_path / "mirror.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    assert ct.mirror_setup(str(bare), say=out.append, repo=repo) == 0
    assert f"MIRROR_REMOTES={bare}" in ct.ENVF.read_text() and oct(ct.ENVF.stat().st_mode)[-3:] == "600"
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert head in subprocess.run(["git", "-C", str(bare), "rev-parse", "--all"], capture_output=True, text=True).stdout


# ------------------------------------------------------------------------------------------- tabletop exercises (doc 88)
def _tt_env(tmp_path, monkeypatch):
    monkeypatch.setattr(ct, "ENVF", tmp_path / "no.env")
    for k in ("SECURAX_NOTIFY_NTFY", "SECURAX_NOTIFY_WEBHOOK", "ALERT_WEBHOOK", "SECURAX_BACKUP_KEYFILE", "SECURAX_OFFSITE_DIR",
              "SYNC_PEERS", "MIRROR_REMOTES", "AI_BUDGET_DAY_TOKENS", "AI_BUDGET_MONTH_TOKENS"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))


def test_every_tabletop_inject_is_complete_and_names_a_real_check_and_command():
    known = {"alerts", "depth", "encrypted", "offsite", "offsite_offline", "drilled", "allowance", "known_good", "peers", "sync",
             "mirror", "replicas", "killswitch", "ai_clock"}
    scen = {s["id"] for s in ct.load()}
    help_text = subprocess.run(["bash", str(ROOT / "securax"), "help"], capture_output=True, text=True).stdout
    for ex in ct.exercises():
        assert ex["scenario"] in scen and ex["injects"]
        for inj in ex["injects"]:
            assert {"at", "phase", "event", "ask", "expect", "fix"} <= inj.keys(), inj
            assert inj.get("check") is None or inj["check"] in known, inj["check"]
            cmd = inj["fix"].split("./securax ", 1)[1].split()[0] if "./securax " in inj["fix"] else ""
            assert not cmd or cmd in help_text, f"the fix names a command help does not list: {cmd}"


def test_an_unprepared_machine_fails_the_ransomware_tabletop_with_a_fix_for_each_gap(tmp_path, monkeypatch):
    _tt_env(tmp_path, monkeypatch)
    said = []
    rc = ct.tabletop("ransomware", answers="", say=said.append)
    assert rc == 1
    reports = list((tmp_path / "h" / "continuity" / "tabletops").glob("ransomware-*.md"))
    text = reports[0].read_text()
    assert "## Gaps and fixes" in text and "./securax protect" in text and "not answered" in text
    assert ct.last_tabletops()["ransomware"]["gaps"] == 10


def test_a_check_the_machine_can_prove_overrides_a_yes(tmp_path, monkeypatch):
    _tt_env(tmp_path, monkeypatch)
    rc = ct.tabletop("ransomware", answers="y" * 20, say=lambda *_: None)
    gaps = ct.last_tabletops()["ransomware"]["gaps"]
    assert rc == 1 and gaps == 5, "answering yes cannot pass an inject the machine proves false (alerts, depth, key, copies, drill)"


def test_a_prepared_machine_passes(tmp_path, monkeypatch):
    _tt_env(tmp_path, monkeypatch)
    b, off = tmp_path / "b", tmp_path / "off"
    b.mkdir()
    off.mkdir()
    old, new = b / "securax-20260101-010101.tar.gz.gpg", b / "securax-20260102-010101.tar.gz.gpg"
    for f in (old, new, off / new.name):
        f.write_bytes(b"x")
    os.utime(old, (time.time() - 10 * 86400,) * 2)
    key = tmp_path / "k"
    key.write_text("k")
    monkeypatch.setenv("ALERT_WEBHOOK", "http://127.0.0.1:9/alert")
    monkeypatch.setenv("SECURAX_BACKUP_KEYFILE", str(key))
    monkeypatch.setenv("SECURAX_OFFSITE_DIR", str(off))
    (tmp_path / "h" / "continuity").mkdir(parents=True)
    (tmp_path / "h" / "continuity" / "offline.log").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + " offline x\n")
    ct.drills_path().write_text(json.dumps({"id": "data-lost", "when": time.strftime("%Y-%m-%dT%H:%M:%S"), "ok": True, "minutes": 3}) + "\n")
    rc = ct.tabletop("ransomware", answers="yyyyy", say=lambda *_: None)
    assert rc == 0 and ct.last_tabletops()["ransomware"]["gaps"] == 0


def test_after_action_reports_are_bounded(tmp_path, monkeypatch):
    _tt_env(tmp_path, monkeypatch)
    for _ in range(ct.KEEP_REPORTS + 3):
        ct.tabletop("node-lost", answers="", say=lambda *_: None)
        time.sleep(0.01)
    assert len(list((tmp_path / "h" / "continuity" / "tabletops").glob("*.md"))) <= ct.KEEP_REPORTS
    assert ct.tabletop("no-such", say=lambda *_: None) == 2
