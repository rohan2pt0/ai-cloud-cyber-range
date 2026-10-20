"""Crown jewels and continuity: live checks become a ranked risk with the one next step, RPO is measured from real backups and
bundles, drills are timed and recorded, and the code survives without GitHub (a bundle that clones). Temp folders only."""
import importlib.util
import json
import os
import pathlib
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


def test_the_code_survives_without_github_a_bundle_that_clones(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "h"))
    monkeypatch.setenv("MIRROR_REMOTES", "")
    assert ct.mirror(say=lambda *_: None) == 0 and (tmp_path / "b" / "repo-latest.bundle").exists()
    assert ct.rpo_minutes("repo") == 0.0                                       # the bundle holds HEAD
    ok, note = ct.run_drill("repo-bundle")
    assert ok, note
