"""The CISO's ready reckoner (doc 94 §8): every capability and role in the catalog has a complete, sourced entry with at
least three options; every box in the cockpit's stack and organogram opens its page; the pages carry no script and link
out only to their sources; the RFP pack has every section; the terminal card answers by id and suggests on a near miss."""
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rk = load("securax_reckoner_t", "governance/reckoner.py")
gv = load("securax_govern_t", "governance/govern.py")


def test_every_capability_and_role_has_a_complete_sourced_entry():
    assert rk.problems() == []


def test_every_box_opens_its_page_and_the_pages_carry_no_script(tmp_path):
    a = gv.analyse({}, {"users": 2000, "endpoints": 2500, "apps": 40, "sites": 5, "coverage": "24x7"})
    stack, org = gv.stack_svg(a, link="reckoner/"), gv.org_svg(a, "advanced", link="reckoner/")
    caps = {c["id"] for c in gv.catalog()["capabilities"]}
    assert set(re.findall(r"href='reckoner/([a-z0-9-]+)\.html'", stack)) == caps
    roles = set(re.findall(r"href='reckoner/role-([a-z0-9_]+)\.html'", org))
    assert {"ciso", "pmo", "soc_l2"} <= roles
    assert "href=" not in gv.stack_svg(a, standalone=True)              # a file for a deck carries no dead links
    n = rk.build(tmp_path)
    assert n == len(caps) + len(gv.catalog()["roles"]) + 1
    for p in tmp_path.glob("*.html"):
        page = p.read_text()
        assert "<script" not in page, p.name
        for href in re.findall(r"href='([^']+)'", page):
            assert href.startswith(("https://", "../cockpit.html", "index.html", "rfp/", "role-")) or href.endswith(".html"), (p.name, href)
    for rid in roles:
        assert (tmp_path / f"role-{rid}.html").exists()


def test_the_rfp_pack_has_every_section(tmp_path):
    out = tmp_path / "rfp.md"
    assert rk.main(["rfp", "tec-edr", "--out", str(out), "--org", "Example Org"]) == 0
    text = out.read_text()
    for h in ("Scope of work", "Mandatory technical specifications", "Sizing", "Architecture and placement", "Service levels",
              "Evaluation criteria", "Contract clauses", "Commercial format"):
        assert h in text, h
    assert "Example Org" in text and "[to be completed]" not in text.split("## 11.")[0]
    assert rk.main(["rfp", "no-such-thing"]) == 2


def test_the_terminal_card_answers_by_id_and_suggests_on_a_near_miss(capsys):
    assert rk.main(["reckon", "tec-edr"]) == 0 and "Options:" in capsys.readouterr().out
    assert rk.main(["reckon", "soc_l2"]) == 0 and "Must have:" in capsys.readouterr().out
    assert rk.main(["reckon", "edr"]) == 2 and "tec-edr" in capsys.readouterr().out
