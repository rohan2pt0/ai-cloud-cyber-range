"""The learning layer: MITRE ATT&CK, D3FEND and ATLAS tags that are real and checked, coverage a learner can study,
personal players with XP, levels and badges earned only from judged work, and skill tracks."""
import json
import pathlib
import sys
import threading

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from exercise import engine, frameworks, portal, progress, scenario  # noqa: E402
from exercise.tests.test_portal import call  # noqa: E402


def test_the_catalogue_holds_official_names_and_links():
    c = frameworks.load()
    assert c["versions"]["attack"] and c["versions"]["atlas"] and all(c[k] for k in frameworks.KINDS)
    assert c["attack"]["T1078.001"]["name"] == "Default Accounts" and "initial-access" in c["attack"]["T1078.001"]["tactics"]
    assert c["d3fend"]["D3-MFA"]["name"] == "Multi-factor Authentication" and c["d3fend"]["D3-MFA"]["tactic"] == "Harden"
    assert c["atlas"]["AML.T0051"]["name"] == "LLM Prompt Injection" and c["atlas"]["AML.M0020"]["name"] == "Generative AI Guardrails"
    assert frameworks.url("T1021.004") == "https://attack.mitre.org/techniques/T1021/004/"
    assert frameworks.url("AML.M0020") == "https://atlas.mitre.org/mitigations/AML.M0020"
    assert frameworks.url("D3-SPP").startswith("https://d3fend.mitre.org/technique/d3f:")
    ids = [i for t in json.loads((ROOT / "exercise" / "tracks.json").read_text())["tracks"] for i in t["ids"]]
    assert frameworks.unknown(ids) == [] and frameworks.unknown(["T9999", "D3-NOPE", "hello"]) == ["T9999", "D3-NOPE", "hello"]


def test_a_scenario_with_an_unknown_tag_is_refused(tmp_path):
    raw = json.loads(scenario.SAMPLE.read_text())
    raw["tasks"][0]["attack"].append("T9999")
    f = tmp_path / "s.json"
    f.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="T9999 is not a known"):
        scenario.load(f, 2)


@pytest.fixture
def game(tmp_path):
    tokens = engine.Game.create(tmp_path / "g", team=6)
    g = engine.Game(tmp_path / "g")
    g.start()
    g.set_meta("started", str(float(g.meta("started")) - 170 * 60))       # attack phase, every task open
    return g, tokens


def test_coverage_shows_met_detected_and_applied(game):
    g, _ = game
    with pytest.raises(ValueError):
        g.attack(6, "red", "www", "x", techniques=["D3-MFA"])                # a defence is not an attack technique
    g.attack(6, "red", "www", "Defaced the site", techniques=["T1491.002", "T1078.001"])
    with pytest.raises(ValueError):
        g.file_incident(6, "blue-6", {"target": "www", "chronology": "x", "techniques": ["T0000"]})
    i = g.file_incident(6, "blue-6", {"target": "www", "chronology": "10:02 defaced", "techniques": ["T1491.002", "T1078.001"], "defences": ["D3-CRO", "D3-FIM"]})
    c = {r["id"]: r for r in frameworks.coverage(g, 6)["rows"]}
    assert c["T1491.002"]["met"] and not c["T1491.002"]["detected"]                 # reported, not yet accepted
    g.judge(i, "white", 15, "accepted")
    cov = frameworks.coverage(g, 6)
    c = {r["id"]: r for r in cov["rows"]}
    assert c["T1491.002"]["detected"] and c["D3-CRO"]["applied"] and c["AML.T0051"]["met"]   # the AI task's ATLAS tags count as met
    groups = {x["group"] for x in cov["groups"]["attack"]}
    assert {"impact", "initial-access"} <= groups and "Harden" in {x["group"] for x in cov["groups"]["d3fend"]}
    assert "Framework coverage (MITRE ATT&CK, D3FEND, ATLAS)" in g.after_action(6)


def test_players_earn_xp_and_badges_only_from_judged_work(game):
    g, _ = game
    with pytest.raises(ValueError):
        g.add_player(6, "<script>")
    g.add_player(6, "Asha")
    with pytest.raises(ValueError):
        g.add_player(6, "Asha")
    g.add_player(6, "Ben")
    me = "blue-6:Asha"
    sub = g.submit_task(6, me, "p1-endpoints", "plan")
    assert progress.players(g, 6)[0]["xp"] == 0                                # submitted, not judged: nothing yet
    g.judge(sub, "white", 40, "accepted")
    for target, techs in (("www", ["T1491.002"]), ("dns1", ["T1078.001"]), ("ws3-1", ["T1053.003"])):
        i = g.file_incident(6, me, {"target": target, "chronology": "seen", "techniques": techs,
                                    "defences": ["D3-SPP", "D3-MFA", "D3-CRO", "D3-ACH", "D3-SU"]})
        g.judge(i, "white", 10, "accepted")
    for item in ("t0-inventory", "t0-passwords"):
        g.plan_mark(6, me, item, "done")
    i = g.file_incident(6, "blue-6:Ben", {"target": "www", "chronology": "x", "techniques": ["AML.T0051"]})
    g.judge(i, "white", 0, "rejected")
    p = {x["player"]: x for x in progress.players(g, 6)}
    assert p["Asha"]["xp"] == 40 + 30 + 20 and p["Asha"]["level"]["name"] == "Recruit" and p["Asha"]["level"]["next"] == "Analyst"
    assert {b["name"] for b in p["Asha"]["badges"]} == {"First detection", "Tactician", "Hardener"}
    assert p["Ben"]["xp"] == 0 and p["Ben"]["badges"] == []                     # a rejected report earns nothing
    assert progress.level(260)["name"] == "Defender" and progress.level(5000)["next"] is None
    t = {x["id"]: x for x in progress.tracks(g, 6)}
    assert t["identity-ad"]["progress_pct"] > 0 and t["ai-systems"]["progress_pct"] == 0 and "CRTP" in " ".join(t["identity-ad"]["certifications"])


def test_personal_tokens_through_the_portal(game):
    g, tokens = game
    srv = portal.serve(g, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        tok = g.add_player(6, "Chen")
        me = call(base, "/api/me", tok)[1]
        assert me["role"] == "blue" and me["team"] == 6 and me["player"] == "Chen"
        assert call(base, "/api/tasks/p1-network/submit", tok, {"answer": "x"})[0] == 200
        assert g.submissions(6, "task")[0]["actor"] == "blue-6:Chen"                 # credited to the person
        red_cat = call(base, "/api/catalogue", tokens["red"])[1]
        assert red_cat and not any(i["kind"] == "d3fend" for i in red_cat)
        assert call(base, "/api/progress", tokens["red"])[0] == 403
        assert call(base, "/api/progress", tok)[1]["me"] == "Chen"
        assert call(base, "/api/players", tokens["white"])[1] == {"players": ["Chen"]} and call(base, "/api/players", tok)[0] == 403
        assert call(base, "/api/attack", tokens["red"], {"target": "www", "objective": "x", "techniques": ["T1491.002"]})[0] == 200
        assert call(base, "/api/frameworks", tok)[1]["counts"]["met"] >= 1
    finally:
        srv.shutdown()
