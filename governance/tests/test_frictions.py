"""ask-by-frequency (owner, 2026-11-11): every friction a person meets is written down with its fix; open ones carry a due date."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_the_friction_log_is_well_formed():
    items = json.loads((ROOT / "governance" / "frictions.json").read_text("utf-8"))["frictions"]
    ids = [f["id"] for f in items]
    assert len(ids) == len(set(ids)), "each friction has its own id"
    for f in items:
        for k in ("id", "seen", "where", "friction", "fix", "state"):
            assert f.get(k), f"{f.get('id')} names {k}"
        assert f["state"] in ("open", "fixed", "accepted"), f["id"]
        if f["state"] == "open":
            assert f.get("due"), f"open friction {f['id']} has a due date"


def test_ask_by_frequency_is_core_and_agents_have_it():
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    assert princ["ask-by-frequency"]["core"] is True and "asked once" in princ["ask-by-frequency"]["text"]
    agents = (ROOT / "AGENTS.md").read_text("utf-8").split("## 1. Pick the tier")[0]
    assert "(`ask-by-frequency`" in agents and "governance/frictions.json" in agents
