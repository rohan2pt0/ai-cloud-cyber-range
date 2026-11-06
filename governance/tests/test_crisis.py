"""`./securax crisis` — multi-agency crisis coordination (doc 125). The templates are generic (no real
organisation, person or case), a requisition tracks done/pending/overdue against its deadline, and the
response pack is generated from the run. No network."""
import csv
import datetime
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("crisis", ROOT / "governance" / "crisis.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)
NOW = datetime.datetime(2026, 11, 6, 6, 0, tzinfo=datetime.timezone.utc)


def test_templates_are_present_and_generic():
    data = cr.lib()
    owners = data["owners"]
    assert set(data["requisitions"]) >= {"le-production-notice", "sectoral-cert-forensics", "regulator-incident-report"}
    for t in data["requisitions"].values():
        assert t["tier"] in ("state", "national", "global")
        assert t["sections"]
        for s in t["sections"]:
            assert s["owner"] in owners and s["items"]
            for i in s["items"]:
                assert i["q"] and i["record"]
    # deliberately generic: the shipped library names no real organisation or regulator
    blob = (ROOT / "governance" / "crisis.json").read_text("utf-8")
    for banned in ("Central Bank", "Maharashtra", "CERT-In", "RBI", "SEBI", "Belapur"):
        assert banned not in blob, f"the generic library must not name {banned!r}"


def test_the_ready_documents_exist_and_use_placeholders():
    docs = {p.stem for p in (ROOT / "governance" / "crisis-templates").glob("*.md")}
    assert {"forensic-tool-exception", "chain-of-custody", "forensic-collection-sop",
            "agency-cover-letter", "duty-roster"} <= docs
    # the fill-in forms carry placeholders; the SOP is a procedure (checked separately)
    for name in ("forensic-tool-exception", "chain-of-custody", "agency-cover-letter", "duty-roster"):
        text = (ROOT / "governance" / "crisis-templates" / f"{name}.md").read_text("utf-8")
        assert "<" in text and ">" in text, f"{name} should be a fill-in template with placeholders"
    sop = (ROOT / "governance" / "crisis-templates" / "forensic-collection-sop.md").read_text("utf-8")
    assert "SHA-256" in sop and "volatil" in sop.lower()


def test_a_requisition_tracks_progress_and_deadline(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_CRISIS_DIR", str(tmp_path))
    assert cr.main(["new", "le-production-notice", "--agency", "State Cyber Police", "--ref", "N/2026/1", "--due", "48h"], now=NOW) == 0
    run = cr.runs()[0]
    cid = run["id"]
    n_items = sum(len(s["items"]) for s in run["sections"])
    assert n_items > 50 and len(run["sections"]) == 13      # the production notice is the big 80/20

    # mark one done, one not-applicable
    cr.main(["set", cid, "1.1", "--done", "--evidence", "org-chart.pdf"], now=NOW)
    cr.main(["set", cid, "1.3", "--na"], now=NOW)
    run = cr.load_run(cid)
    got = {i["id"]: i for s in run["sections"] for i in s["items"]}
    assert got["1.1"]["status"] == "done" and got["1.1"]["evidence"] == "org-chart.pdf"
    assert got["1.3"]["status"] == "na"

    # assigning a section re-owns its items
    cr.main(["assign", cid, "makers", "--to", "Payments SPOC"], now=NOW)
    run = cr.load_run(cid)
    makers = next(s for s in run["sections"] if s["id"] == "makers")
    assert makers["spoc"] == "Payments SPOC" and all(i["owner"] == "Payments SPOC" for i in makers["items"])

    # before the deadline: still open, not overdue (exit 0 or 1, never the overdue 2)
    assert cr.main(["status", cid], now=NOW + datetime.timedelta(hours=1)) in (0, 1)
    # past the deadline with items still pending: overdue (exit 2)
    assert cr.main(["status", cid], now=NOW + datetime.timedelta(hours=49)) == 2


def test_the_response_pack_is_generated(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_CRISIS_DIR", str(tmp_path))
    cr.main(["new", "sectoral-cert-forensics", "--agency", "Sectoral CERT", "--ref", "C/9"], now=NOW)
    cid = cr.runs()[0]["id"]
    cr.main(["set", cid, "r.1", "--done", "--evidence", "report.pdf"], now=NOW)
    assert cr.main(["pack", cid], now=NOW) == 0
    pack = tmp_path / cid / "pack"
    assert (pack / "cover-letter.md").exists() and (pack / "response-register.md").exists()
    # the cover letter was filled with the agency and ref; the register lists the provided item
    cover = (pack / "cover-letter.md").read_text("utf-8")
    assert "Sectoral CERT" in cover and "C/9" in cover
    with open(pack / "response-register.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    r1 = next(r for r in rows if r["item"] == "r.1")
    assert r1["status"] == "provided" and r1["evidence"] == "report.pdf"
