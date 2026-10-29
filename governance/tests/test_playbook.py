"""Incident-response playbooks (./securax playbook): the library is well-formed, a run ticks through its steps, a retro
cannot close while critical steps are open (unless forced), and closing writes a real postmortem seeded with the run's
timeline. Keeps the IR workflow honest: you cannot mark an incident "handled" with the critical steps undone."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pb = _load("playbook", "governance/playbook.py")


def test_library_is_well_formed():
    lib = pb.library()
    assert {"ransomware", "data-exfiltration", "zero-day"} <= set(lib)
    for name, p in lib.items():
        assert p["name"] and p["scenario"] and p["steps"], name
        ids = [s["id"] for s in p["steps"]]
        assert len(ids) == len(set(ids)), f"{name}: duplicate step ids"
        for s in p["steps"]:
            assert s["phase"] in pb.PHASES, f"{name}/{s['id']}: unknown phase {s['phase']}"
            assert s["title"] and s["how"], f"{name}/{s['id']}: missing title/how"
        assert any(s.get("critical") for s in p["steps"]), f"{name}: no critical step"


def test_a_run_ticks_through_its_steps(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "RUNS", tmp_path / "runs")
    run = pb.start("zero-day", "a CVE under exploitation")
    assert run["playbook"] == "zero-day" and run["steps"] and not run["closed_at"]
    first = run["steps"][0]["id"]
    pb.mark(run["id"], first, by="analyst")
    reloaded = pb.load_run(run["id"])
    step = next(s for s in reloaded["steps"] if s["id"] == first)
    assert step["done_at"] and step["by"] == "analyst"
    pr = pb.progress(reloaded)
    assert pr["done"] == 1 and pr["total"] == len(reloaded["steps"])


def test_an_unknown_scenario_or_step_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "RUNS", tmp_path / "runs")
    try:
        pb.start("not-a-scenario", "x"); raise AssertionError("expected KeyError")
    except KeyError as e:
        assert "unknown playbook" in str(e)
    run = pb.start("ransomware", "x")
    try:
        pb.mark(run["id"], "no-such-step"); raise AssertionError("expected KeyError")
    except KeyError as e:
        assert "no step" in str(e)


def test_retro_refuses_while_critical_steps_are_open_then_writes_a_postmortem(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(pb, "ROOT", tmp_path)                       # keep the postmortem the retro writes out of the repo
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "postmortem.py").write_text((ROOT / "governance" / "postmortem.py").read_text("utf-8"))
    run = pb.start("ransomware", "test event")
    try:
        pb.retro(run["id"]); raise AssertionError("expected RuntimeError")
    except RuntimeError as e:
        assert "critical steps are still open" in str(e)
    out = pb.retro(run["id"], force=True)
    assert out["postmortem"] and (tmp_path / out["postmortem"]).exists()
    assert pb.load_run(run["id"])["closed_at"]
