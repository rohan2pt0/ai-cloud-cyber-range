"""The estate map: built from the estate's own declarations, one self-contained HTML, every component on its platform (doc 113)."""
import importlib.util
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("estate_map", REPO / "tools" / "estate_map.py")
em = importlib.util.module_from_spec(spec)
spec.loader.exec_module(em)

DATA = em.load(REPO)
G = em.graph(DATA)


def test_every_declared_component_is_a_node():
    comp_ids = {"cmp:" + c for c in DATA["suite"]["components"]}
    got = {n["id"] for n in G["nodes"] if n["kind"] == "component"}
    assert got == comp_ids, "every component in suite.json must appear once on the map"


def test_every_platform_service_is_a_hub():
    svc_ids = {"svc:" + s for s in DATA["suite"]["services"]}
    got = {n["id"] for n in G["nodes"] if n["kind"] == "service"}
    assert got == svc_ids


def test_edges_match_the_declared_uses():
    # an edge for every (component uses service) pair, and no stray edges.
    want = set()
    for cid, c in DATA["suite"]["components"].items():
        for s in c.get("uses", []):
            if s in DATA["suite"]["services"]:
                want.add(("cmp:" + cid, "svc:" + s))
    got = {(e["s"], e["t"]) for e in G["edges"]}
    assert got == want and len(G["edges"]) == len(want)


def test_components_carry_their_human_facing_detail():
    feats = {f["id"]: f for f in DATA["features"]["features"]}
    for n in G["nodes"]:
        if n["kind"] == "component":
            cid = n["id"].split(":", 1)[1]
            assert n["name"] == feats[cid]["name"], f"{cid} should show its feature name"


def test_build_is_one_self_contained_offline_html():
    out = em.build(REPO)
    assert out.lstrip().startswith("<!doctype html>")
    # no external resource load — it must work offline, from the filesystem (the SVG XML namespace URL is not a fetch).
    assert "cdn" not in out.lower()
    assert "<script src" not in out.lower() and "<link" not in out.lower()
    assert 'src="http' not in out.lower() and 'href="http' not in out.lower()
    assert "fetch(" not in out and "XMLHttpRequest" not in out
    # the data is embedded and parseable, and closes no tag it should not.
    m = re.search(r'<script id="data"[^>]*>(.*?)</script>', out, re.S)
    assert m, "the baked data block must be present"
    blob = json.loads(m.group(1).replace("<\\/", "</"))
    assert len(blob["nodes"]) == len(G["nodes"]) and blob["edges"]


def test_dark_and_light_theme_declared():
    out = em.build(REPO)
    assert "--bg:" in out and "prefers-color-scheme: light" in out      # readable in both, per the design standard
