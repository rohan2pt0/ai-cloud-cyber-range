"""The honesty score keeps a short history, and the cockpit shows it, so a drop after a model change shows at a glance (doc 89)."""
import importlib.util
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


honesty = _load("honesty_under_test", "governance/honesty.py")
cockpit = _load("cockpit_under_test_honesty", "governance/cockpit.py")


def _res(passed, probes=7, answered=None, model="test-model"):
    return {"model": model, "probes": probes, "answered": probes if answered is None else answered, "passed": passed, "rows": []}


def test_history_is_bounded_to_52_newest_last(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    for i in range(60):
        assert honesty.record(_res(i % 8, model=f"m{i}"))
    lines = (tmp_path / "honesty.jsonl").read_text("utf-8").splitlines()
    assert len(lines) == 52
    rows = honesty.history(100)
    assert len(rows) == 52 and rows[-1]["model"] == "m59" and rows[0]["model"] == "m8"
    assert set(rows[-1]) == {"ts", "model", "passed", "probes"}
    assert [r["model"] for r in honesty.history(2)] == ["m58", "m59"]
    assert not list(tmp_path.glob("*.tmp"))


def test_a_run_with_no_answer_is_not_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    assert honesty.record(_res(0, answered=0)) is False
    assert honesty.history() == []


def test_a_failing_write_does_not_raise(tmp_path, monkeypatch):
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x")
    monkeypatch.setenv("SECURAX_HOME_DIR", str(blocker / "home"))      # its parent is a file: mkdir must fail
    assert honesty.record(_res(7)) is False
    assert honesty.history() == []


def test_main_still_exits_by_the_score_when_history_cannot_be_written(tmp_path, monkeypatch):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    monkeypatch.setenv("SECURAX_HOME_DIR", str(blocker / "home"))
    monkeypatch.setattr(honesty, "run", lambda *a, **k: _res(7))
    assert honesty.main(["--json"]) == 0


def test_garbage_lines_are_skipped(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    (tmp_path / "honesty.jsonl").write_text("not json\n" + json.dumps({"ts": "t", "model": "m", "passed": 5, "probes": 7}) + "\n[1]\n")
    assert [r["passed"] for r in honesty.history()] == [5]


def _metric(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))

    def no_network(*a, **k):
        raise AssertionError("the honesty lamp must not call the network")
    monkeypatch.setattr(cockpit.urllib.request, "urlopen", no_network)
    c = cockpit.Collector({}, time.time(), "personal", {}, fast=True)
    c.c_honesty()
    [m] = [m for m in c.metrics if m["id"] == "honesty"]
    assert m["label"] == "AI honesty" and m["importance"] == 2 and not m["urgent"]
    return m


def test_cockpit_unknown_when_never_checked(tmp_path, monkeypatch):
    m = _metric(tmp_path, monkeypatch)
    assert m["status"] == "unknown" and m["value"] == "not checked yet"
    assert m["action"] == "Check the AI refuses to guess" and m["cmd"] == "./securax ai honesty"


def test_cockpit_green_when_all_honest(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    honesty.record(_res(7))
    m = _metric(tmp_path, monkeypatch)
    assert m["status"] == "green" and m["value"] == "7/7 honest" and m["action"] == ""


def test_cockpit_amber_on_a_drop_and_names_the_last_score(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    honesty.record(_res(7))
    honesty.record(_res(6))
    m = _metric(tmp_path, monkeypatch)
    assert m["status"] == "amber" and m["value"] == "6/7 honest (was 7/7)" and m["action"]


def test_cockpit_amber_below_full_score_without_a_drop(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    honesty.record(_res(5))
    honesty.record(_res(5))
    m = _metric(tmp_path, monkeypatch)
    assert m["status"] == "amber" and m["value"] == "5/7 honest"


def test_cockpit_red_below_half(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    honesty.record(_res(7))
    honesty.record(_res(3))
    m = _metric(tmp_path, monkeypatch)
    assert m["status"] == "red" and m["value"] == "3/7 honest (was 7/7)" and not m["urgent"]


def test_honesty_is_not_a_primary_instrument():
    assert "honesty" not in cockpit.PRIMARY
