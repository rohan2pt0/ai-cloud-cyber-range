"""Govern (doc 94): the catalog is complete, marks move coverage and maturity, a missing basic outranks a missing advanced
item, budgets scale with size and skip what is done, the team grows with size and tier, the Board report and the cockpit
card carry the 5W1H with no script or external address, and templates fill in the name without overwriting edits."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("govern", ROOT / "governance" / "govern.py")
gv = importlib.util.module_from_spec(_s)
_s.loader.exec_module(gv)
PROF = {"users": 2000, "endpoints": 2500, "apps": 40, "sites": 5, "coverage": "24x7"}


def test_every_capability_is_complete_and_its_template_exists():
    cat = gv.catalog()
    ids = [c["id"] for c in cat["capabilities"]]
    assert len(ids) == len(set(ids))
    for c in cat["capabilities"]:
        assert c["tier"] in gv.TIERS and c["domain"] in gv.DOMAINS and 1 <= c["impact"] <= 5, c["id"]
        assert c["why"] and c["how"] and c["owner"] and "cost" in c, c["id"]
        if c.get("template"):
            assert (gv.TEMPLATES / c["template"]).exists(), c["template"]
    for t in gv.TIERS:
        assert sum(c["tier"] == t for c in cat["capabilities"]) >= 5
    for d in gv.DOMAINS:
        assert any(c["domain"] == d and c["tier"] == "basic" for c in cat["capabilities"]), d


def test_marks_move_coverage_and_maturity():
    empty = gv.analyse({}, PROF)
    assert empty["maturity"][0] == 1 and empty["overall"]["basic"] == 0
    basics = {c["id"]: {"state": "done"} for c in gv.catalog()["capabilities"] if c["tier"] == "basic"}
    full = gv.analyse(basics, PROF)
    assert full["overall"]["basic"] == 100 and full["maturity"][0] == 3
    half = gv.analyse({k: {"state": "partial"} for k in basics}, PROF)
    assert half["overall"]["basic"] == 50


def test_a_missing_basic_comes_before_a_missing_advanced_item():
    a = gv.analyse({}, PROF)
    tiers = [g["tier"] for g in a["gaps"]]
    assert tiers[0] == "basic" and tiers.index("advanced") > tiers.index("standard") > 0
    assert all(set(gv.w5h(g)) == {"What", "Why", "Who", "When", "Where", "How", "How much"} for g in a["gaps"][:5])


def test_budgets_scale_with_size_and_skip_what_is_done():
    small = gv.analyse({}, {**PROF, "users": 200, "endpoints": 250, "apps": 5})["budget"]["basic"]["total"]
    big = gv.analyse({}, {**PROF, "users": 20000, "endpoints": 25000, "apps": 300})["budget"]["basic"]["total"]
    assert big[0] > small[0] and big[1] > small[1]
    before = gv.analyse({}, PROF)["budget"]["basic"]["tools_process"]
    after = gv.analyse({"tec-edr": {"state": "done"}}, PROF)["budget"]["basic"]["tools_process"]
    assert after[1] < before[1]
    for t in gv.TIERS[1:]:
        assert gv.analyse({}, PROF)["budget"][t]["total"][1] >= gv.analyse({}, PROF)["budget"]["basic"]["total"][1]


def test_the_team_grows_with_size_and_tier():
    def heads(tier, **kw):
        return sum(r["count"] for r in gv.team(tier, {**PROF, **kw}))
    assert heads("basic") < heads("standard") < heads("advanced")
    assert heads("standard", endpoints=25000, users=20000, apps=300) > heads("standard")
    adv = {r["id"]: r for r in gv.team("advanced", PROF)}
    assert adv["soc_l1"]["count"] == 5, "a 24x7 in-house seat needs about five people"
    assert "soc_l1" not in {r["id"] for r in gv.team("advanced", {**PROF, "coverage": "business"})}


def test_the_board_report_and_the_cockpit_card_carry_the_5w1h_safely():
    a = gv.analyse({}, {**PROF, "org": "Example Org <b>"})
    b = gv.board(a)
    assert "| # | What | Why | Who | When | Where | How | How much |" in b and "What we ask of management" in b
    card = gv.html_card(a)
    assert "Govern" in card and "<script" not in card and "http://" not in card and "https://" not in card
    assert "Maturity level 1 of 5" in card


def test_templates_fill_the_name_and_never_overwrite(tmp_path):
    made = gv.templates(tmp_path, "Example Org")
    assert len(made) == len(list(gv.TEMPLATES.iterdir()))
    pol = (tmp_path / "01-information-security-policy.md").read_text()
    assert "Example Org" in pol and "{{ORG}}" not in pol and "{{DATE}}" not in pol
    (tmp_path / "01-information-security-policy.md").write_text("edited")
    assert gv.templates(tmp_path, "Other") == [] and (tmp_path / "01-information-security-policy.md").read_text() == "edited"


def test_the_cli_keeps_answers_private(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    assert gv.main(["profile", "--users", "500", "--org", "Example Org"]) == 0
    assert gv.main(["mark", "tec-edr", "done", "--note", "all laptops"]) == 0
    assert gv.main(["mark", "no-such", "done"]) == 2
    assert gv.marks()["tec-edr"]["state"] == "done" and gv.profile()["users"] == 500
    assert (tmp_path / "govern.json").stat().st_mode & 0o077 == 0


def test_the_card_is_folded_and_shows_pictures_not_commands():
    a = gv.analyse({"tec-edr": {"state": "done"}}, PROF)
    card = gv.html_card(a)
    assert card.split("<details", 1)[1].startswith(" class='card panel' id='govern'>")   # folded: no 'open' on the panel
    assert "<svg" in card and "layer by layer" in card and "5W1H" in card and "./securax" not in card.split("</summary>", 1)[0]
    for svg in (gv.org_svg(a), gv.stack_svg(a)):
        assert svg.startswith("<svg") and "xmlns" not in svg and "<script" not in svg and "http" not in svg
    org = gv.org_svg(a, "standard")
    assert "CISO" in org and org.count("<rect") >= len(gv.team("standard", PROF))
    stack = gv.stack_svg(a)
    assert all(gv.short(c) in stack for c in gv.catalog()["capabilities"] if c["tier"] == "basic")


def test_the_pictures_export_as_standalone_svg(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    for cmd in ("org", "map"):
        out = tmp_path / f"{cmd}.svg"
        assert gv.main([cmd, "--out", str(out)]) == 0
        s = out.read_text()
        assert "<svg xmlns='http://www.w3.org/2000/svg' width='" in s and s.rstrip().endswith("</svg>")
