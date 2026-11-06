"""`./securax evolve` — the growth map (doc 128, principle `amoeba`). The estate ships as the simplest living form but
carries the DNA + a dormant rail to grow into its enterprise organism; evolve reads local conditions and shows what is
ready to grow, doing nothing on its own. No network; conditions are read locally."""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("evolve", ROOT / "governance" / "evolve.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


def test_the_principle_is_a_core_principle_and_in_agents():
    princ = json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]
    amoeba = next((p for p in princ if p["id"] == "amoeba"), None)
    assert amoeba and amoeba["core"] is True
    assert "amoeba" in amoeba["text"].lower() and "rail" in amoeba["text"].lower()
    agents = (ROOT / "AGENTS.md").read_text("utf-8")
    assert "amoeba" in agents.lower() and "governance/evolution.json" in agents


def test_every_capability_declares_amoeba_form_conditions_and_a_rail():
    evo = json.loads((ROOT / "governance" / "evolution.json").read_text("utf-8"))
    caps = evo["capabilities"]
    assert {"hunt", "crisis", "wargame", "gateway", "evolve"} <= set(caps)
    for cid, cap in caps.items():
        assert cap.get("organism"), f"{cid} must name its amoeba form"
        stages = cap["stages"]
        assert stages[0]["id"] == "amoeba" and stages[0]["have"] is True
        for st in stages[1:]:
            assert st.get("when"), f"{cid}/{st['id']} must name the conditions that trigger it"
            assert st.get("rail"), f"{cid}/{st['id']} must declare the dormant rail already built"
            assert st.get("actuation") in ("auto", "assisted")


def test_a_lone_amoeba_has_nothing_to_grow(monkeypatch, capsys):
    for k in ("GATEWAY_URL", "SECURAX_HUNT_MIRROR", "SECURAX_TEAMS", "SECURAX_TENANTS",
              "SECURAX_FLEET_SERVER", "VELOCIRAPTOR_SERVER", "SECURAX_LOAD_HIGH", "SECURAX_NODE_LOST"):
        monkeypatch.delenv(k, raising=False)
    cond = ev.conditions()
    assert cond["gateway"] is False and cond["internal_mirror"] is False and cond["teams"] is False
    # hunt's larger stages need a fleet server / mirror / teams — none set, so hunt stays an amoeba
    hunt = json.loads((ROOT / "governance" / "evolution.json").read_text("utf-8"))["capabilities"]["hunt"]
    assert ev._next_ready(hunt, cond) is None


def test_conditions_unlock_the_next_stage_and_the_rail_is_named(monkeypatch):
    monkeypatch.setenv("SECURAX_HUNT_MIRROR", "https://nexus.example.com")
    monkeypatch.setenv("SECURAX_TEAMS", "1")
    cond = ev.conditions()
    assert cond["internal_mirror"] is True and cond["teams"] is True
    hunt = json.loads((ROOT / "governance" / "evolution.json").read_text("utf-8"))["capabilities"]["hunt"]
    nxt = ev._next_ready(hunt, cond)
    assert nxt is not None and nxt["id"] == "organism" and nxt["rail"]


def test_trigger_evaluation_supports_numeric_node_thresholds():
    assert ev._met("nodes>1", {"nodes": 3}) is True
    assert ev._met("nodes>3", {"nodes": 3}) is False
    assert ev._met("teams", {"teams": True}) is True
    assert ev._met("teams", {"teams": False}) is False
    assert ev._met("unknown-signal", {}) is False


def test_evolve_is_read_only_and_runs_offline(monkeypatch, capsys):
    # the map prints and returns 0 without touching anything external
    monkeypatch.delenv("GATEWAY_URL", raising=False)
    assert ev.main([]) == 0
    out = capsys.readouterr().out
    assert "growth map" in out.lower()
    # an unknown capability is a clean error, not a crash
    assert ev.main(["does-not-exist"]) == 2
