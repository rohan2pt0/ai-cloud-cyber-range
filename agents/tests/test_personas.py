import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pers", ROOT / "agents" / "personas.py")
P = importlib.util.module_from_spec(spec); sys.modules["pers"] = P; spec.loader.exec_module(P)


def test_roster_has_the_core_specialists():
    keys = {a["key"] for a in P.list_agents()}
    for must in ["legal", "finance", "cfo", "cto", "ciso", "tax", "dietician", "coach", "engineer"]:
        assert must in keys, must


def test_roster_covers_the_vital_life_domains():
    # 80/20 completeness beyond the first ask: health, mind, relationships, money-adjacent, continuity
    keys = {a["key"] for a in P.list_agents()}
    for must in ["doctor", "mind", "relationship", "parenting", "insurance", "realestate",
                 "estate", "negotiation", "eldercare", "learning", "travel", "home"]:
        assert must in keys, must
    assert len(keys) >= 24


def test_every_agent_carries_the_anti_hallucination_contract():
    for k in P.PERSONAS:
        msgs = P.build_messages(k, "test question")
        sysmsg = msgs[0]["content"]
        assert "Never guess" in sysmsg or "never invent" in sysmsg.lower()
        # first-draft, not final: must point to a human professional (except the chef, consult '—')
        assert "FIRST opinion" in sysmsg and "confirm with" in sysmsg


def test_messages_are_grounded_and_role_specific():
    msgs = P.build_messages("ciso", "How do I phase zero-trust?", context="I run a home lab.")
    assert msgs[0]["role"] == "system" and "chief information security officer" in msgs[0]["content"]
    assert "CONTEXT" in msgs[1]["content"] and "zero-trust" in msgs[1]["content"]


def test_stealth_no_network_without_gateway(monkeypatch):
    monkeypatch.delenv("GATEWAY_URL", raising=False)
    out = P.ask_agent("finance", "How much emergency fund?")
    assert "answer" not in out                 # nothing is called unless a gateway is configured
    assert out["agent"] == "finance" and out["messages"]


def test_unknown_agent_rejected():
    try:
        P.build_messages("wizard", "hi")
        assert False, "should have raised"
    except KeyError:
        pass


def test_engineer_is_the_credit_saver():
    # the SecuRAX-engineer persona exists so the system can enhance itself on local/free models
    out = P.ask_agent("engineer", "Add a dark-mode toggle to the portal")
    assert out["name"] == "SecuRAX Engineer" and out["messages"]
