"""governance/licences.json (doc 110): every image the estate runs is listed with its licence and what that licence lets SecuRAX
do once it is sold, so a fair-code or branding clause is never found after the first invoice."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
REG = json.loads((ROOT / "governance" / "licences.json").read_text("utf-8"))


def _images() -> set[str]:
    found = set()
    for f in (ROOT / "local" / "compose").glob("*.yml"):
        for m in re.finditer(r"^\s*image:\s*\"?([^\s\"]+)", f.read_text("utf-8"), re.M):
            ref = re.sub(r"^\$\{[A-Z_]+:-(.+)\}$", r"\1", m.group(1))       # ${VAR:-default} -> default
            found.add(re.split(r"[:@]", ref)[0])
    return found


def test_every_image_the_estate_runs_has_its_licence_listed():
    listed = {c["id"] for c in REG["components"]}
    missing = sorted(_images() - listed)
    assert not missing, f"add these to governance/licences.json with their licence and terms: {missing}"


def test_every_entry_says_what_selling_it_needs():
    for c in REG["components"] + REG["models"]:
        assert c["sell"] in ("ok", "conditions", "ask") and c["licence"] and c["terms"], c["id"]


def test_the_fair_code_and_branding_clauses_are_not_marked_free():
    by = {c["id"]: c["sell"] for c in REG["components"]}
    assert by["n8nio/n8n"] == "ask" and by["ghcr.io/open-webui/open-webui"] != "ok"
