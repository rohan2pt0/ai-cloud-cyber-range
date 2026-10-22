"""The regulatory gap maps must be un-fudgeable: stale references, overclaims and a missing 'next step' all fail the check."""
import copy
import importlib.util
import json
import pathlib
import tarfile

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("regmap", REPO / "governance" / "regmap.py")
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)
ESPEC = importlib.util.spec_from_file_location("evidence", REPO / "local" / "compose" / "evidence.py")
ev = importlib.util.module_from_spec(ESPEC)
ESPEC.loader.exec_module(ev)


def item(m, id_):
    return next(i for i in m["items"] if i["id"] == id_)


def test_shipped_maps_are_consistent():
    for k in rm.MAPS:
        assert rm.problems(rm.load(k)) == [], k


def test_the_source_texts_are_cited_with_a_date_and_a_caveat():
    for k in rm.MAPS:
        s = rm.load(k)["source"]
        assert s["read_on"] and s["caveat"] and s["url"].startswith("https://")


def test_a_stale_reference_is_caught():
    m = copy.deepcopy(rm.load("rbi"))
    item(m, "111")["evidence"].append("file:docs/none.md")
    assert any("111" in p and "does not exist" in p for p in rm.problems(m))


def test_supported_on_documentation_alone_is_an_overclaim():
    m = copy.deepcopy(rm.load("rbi"))
    item(m, "111")["evidence"] = ["file:docs/securax/27-INCIDENT-RUNBOOK.md"]
    assert any("111" in p and "journey or test" in p for p in rm.problems(m))


def test_gap_with_evidence_and_partial_without_next_step_are_caught():
    m = copy.deepcopy(rm.load("rbi"))
    gap = next(i for i in m["items"] if i["status"] == "gap")
    gap["evidence"] = ["file:securax"]
    item(m, "18")["next"] = ""
    probs = rm.problems(m)
    assert any(p.startswith(gap["id"] + ":") for p in probs) and any(p.startswith("18:") for p in probs)


def test_entity_obligations_are_never_counted_as_covered():
    m = copy.deepcopy(rm.load("rbi"))
    before = rm.coverage(m)["software_scope_coverage_pct"]
    for i in m["items"]:
        if i["status"] == "entity":
            i["evidence"] = ["cmd:evidence"]            # even citing evidence must not change the software-scope score
    assert rm.coverage(m)["software_scope_coverage_pct"] == before


def test_coverage_math_and_category_filter():
    m = {"categories": {"a": "A", "b": "B"}, "items": [
        {"id": "1", "title": "", "applies": "all", "status": "supported", "note": "", "evidence": [], "next": "", "priority": ""},
        {"id": "2", "title": "", "applies": ["a"], "status": "gap", "note": "", "evidence": [], "next": "x", "priority": "high"},
        {"id": "3", "title": "", "applies": ["b"], "status": "entity", "note": "", "evidence": [], "next": "", "priority": ""}]}
    assert rm.coverage(m)["software_scope_coverage_pct"] == 50.0
    assert rm.coverage(m, "a")["software_scope_coverage_pct"] == 50.0
    assert rm.coverage(m, "b")["software_scope_coverage_pct"] == 100.0 and rm.coverage(m, "b")["entity_items"] == 1


def test_committed_reports_match_the_maps():
    for k, name in (("rbi", "rbi-nbfc-gap-assessment.md"), ("cscrf", "sebi-cscrf-gap-assessment.md"), ("mit-ai-risk", "mit-ai-risk-assessment.md"),
                    ("nist-ai-600-1", "nist-ai-600-1-assessment.md"), ("pqc", "pqc-readiness-assessment.md"),
                    ("owasp-ai", "owasp-llm-agentic-assessment.md"), ("free-ai", "rbi-free-ai-assessment.md")):
        m = rm.load(k)
        assert (REPO / "docs" / "securax" / "regulatory" / name).read_text("utf-8").rstrip() == rm.render_md(k, m, None, rm.problems(m)).rstrip(), \
            f"regenerate with: ./securax comply {k} --md > docs/securax/regulatory/{name}"


def test_evidence_pack_carries_both_assessments(tmp_path):
    comp = ev.compliance_artifacts()
    assert comp and {"compliance-rbi.md", "compliance-cscrf.md", "compliance-summary.json"} <= set(comp[0])
    out = tmp_path / "p.tgz"
    ev.write_pack(str(out), {"x": 1}, "r", comp[0])
    with tarfile.open(out) as t:
        names = set(t.getnames())
    assert {"compliance-rbi.md", "compliance-cscrf.md", "SHA256SUMS"} <= names
    assert json.loads(comp[0]["compliance-summary.json"])["rbi"]["integrity_problems"] == []
