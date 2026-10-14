"""The CCSP map must be un-fudgeable: stale references, overclaims and a wrong outline shape all fail the check."""
import copy
import hashlib
import importlib.util
import json
import pathlib
import tarfile

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("ccsp", REPO / "governance" / "ccsp.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)
EV = importlib.util.spec_from_file_location("evidence", REPO / "local" / "compose" / "evidence.py")
ev = importlib.util.module_from_spec(EV)
EV.loader.exec_module(ev)


def topic(m, tid):
    return next(t for d in m["domains"] for t in d["topics"] if t["id"] == tid)


def test_the_shipped_map_is_consistent():
    assert cc.problems(cc.load()) == []


def test_outline_shape_is_isc2s():
    m = cc.load()
    assert {d["id"]: d["weight"] for d in m["domains"]} == cc.EXPECTED_WEIGHTS
    assert sum(len(d["topics"]) for d in m["domains"]) == 38


def test_a_stale_reference_is_caught():
    m = copy.deepcopy(cc.load())
    topic(m, "4.2")["evidence"].append("file:docs/does-not-exist.md")
    assert any("4.2" in p and "does not exist" in p for p in cc.problems(m))


def test_covered_on_documentation_alone_is_an_overclaim():
    m = copy.deepcopy(cc.load())
    t = topic(m, "4.2")
    t["evidence"] = [e for e in t["evidence"] if e.split(":")[0] not in cc.PROOF_KINDS] or ["file:BUILD-CONTRACT.md"]
    assert any("4.2" in p and "needs a journey or test" in p for p in cc.problems(m))


def test_gap_citing_evidence_and_partial_without_evidence_are_caught():
    m = copy.deepcopy(cc.load())
    topic(m, "2.6")["evidence"] = ["file:securax"]
    topic(m, "1.1")["evidence"] = []
    probs = cc.problems(m)
    assert any("2.6" in p for p in probs) and any("1.1" in p for p in probs)


def test_dropping_a_topic_or_changing_a_weight_is_caught():
    m = copy.deepcopy(cc.load())
    m["domains"][0]["topics"].pop()
    assert any("38" in p for p in cc.problems(m))
    m = copy.deepcopy(cc.load())
    m["domains"][0]["weight"] = 50
    assert any("weights" in p for p in cc.problems(m))


def test_coverage_math_is_weighted():
    m = {"domains": [
        {"id": 1, "name": "a", "weight": 75, "topics": [{"id": "1.1", "title": "x", "status": "covered", "note": "", "evidence": []}]},
        {"id": 2, "name": "b", "weight": 25, "topics": [{"id": "2.1", "title": "y", "status": "gap", "note": "", "evidence": []}]}]}
    assert cc.coverage(m)["overall_weighted_pct"] == 75.0
    assert cc.coverage(m)["backlog"][0]["id"] == "2.1"


def test_evidence_pack_carries_the_map_with_matching_checksums(tmp_path):
    out = tmp_path / "p.tgz"
    cc_art = ev.ccsp_artifacts()
    assert cc_art and 0 < cc_art[2] < 100
    ev.write_pack(str(out), {"x": 1}, "r", {"ccsp-coverage.json": cc_art[0], "ccsp-coverage.md": cc_art[1].encode()})
    with tarfile.open(out) as t:
        files = {m.name: t.extractfile(m).read() for m in t.getmembers()}
    assert {"ccsp-coverage.json", "ccsp-coverage.md", "SHA256SUMS"} <= set(files)
    for line in files["SHA256SUMS"].decode().splitlines():
        h, name = line.split("  ")
        assert hashlib.sha256(files[name]).hexdigest() == h
    assert json.loads(files["ccsp-coverage.json"])["integrity_problems"] == []
