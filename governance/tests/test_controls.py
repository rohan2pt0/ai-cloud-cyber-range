"""The BFSI control library: a stdlib .xlsx import, tier profiles (the strictest-of-all ceiling), packs for new regulations,
the SecuRAX evidence map, and a navigator page with no script and no external request. Uses a small synthetic workbook."""
import html
import importlib.util
import json
import pathlib
import zipfile

_s = importlib.util.spec_from_file_location("controls", pathlib.Path(__file__).resolve().parent.parent / "controls.py")
ct = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ct)
ROOT = pathlib.Path(__file__).resolve().parents[2]

HEAD = ["Control ID", "Domain", "Sub-Domain", "Control Title", "Control Description", "Criticality Tier", "Threat (MITRE ATT&CK)",
        "RBI Primary Citation", "SEBI CSCRF", "Evidence Required", "Audit Test Procedure", "Remediation Action", "Owner Function",
        "Current Maturity (0-5)", "Target Maturity (0-5)", "Likelihood (1-5)", "Impact (1-5)", "Residual Risk", "SCB/PSB", "RRB", "Insurer/IRDAI"]
ROWS = [
    ["GOV-001", "GOV", "Policy", "Board policy", "d", "Critical", "-", "RBI-CSF 2016", "SEBI CSCRF", "minutes", "walkthrough", "draft it", "CISO", 2, 4, 4, 5, None, "MUST", "MUST", "MUST"],
    ["IAM-014", "IAM", "API Auth", "API authentication", "d", "High", "T1078", "RBI-ITGRC 2023", "-", "config", "test", "fix", "CISO", None, None, None, None, None, "MUST", "SHOULD", "MAY"],
    ["AUD-003", "AUD", "IRDAI Audit", "IRDAI ISMS audit", "d", "High", "-", "-", "-", "report", "review", "audit", "IA", None, None, None, None, None, "MAY", "N/A", "MUST"],
]


def _cell(ref, v):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return f'<c r="{ref}"><v>{v}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(str(v))}</t></is></c>'


def make_xlsx(path):
    cols = lambda i: (chr(65 + i) if i < 26 else "A" + chr(65 + i - 26))
    rows = [["MASTER CONTROL CATALOGUE"], ["sub"], HEAD] + ROWS
    xml = "".join(f'<row r="{r + 1}">' + "".join(_cell(f"{cols(i)}{r + 1}", v) for i, v in enumerate(row)) + "</row>" for r, row in enumerate(rows))
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook {ns}><sheets><sheet name="1. Cover &amp; Instructions" sheetId="1" r:id="rId1"/>'
                                      f'<sheet name="3. Master Catalogue" sheetId="2" r:id="rId2"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {ns}><sheetData>{_cell("A1", "WORKBOOK")}<row r="3">{_cell("A3", "v1.0 · test")}</row></sheetData></worksheet>'.replace(_cell("A1", "WORKBOOK"), '<row r="1">' + _cell("A1", "WORKBOOK") + "</row>"))
        z.writestr("xl/worksheets/sheet2.xml", f"<worksheet {ns}><sheetData>{xml}</sheetData></worksheet>")
        z.writestr("docProps/core.xml", "<cp:coreProperties><dc:creator>Somebody Personal</dc:creator></cp:coreProperties>")


def lib(tmp_path):
    x = tmp_path / "wb.xlsx"
    make_xlsx(x)
    data = ct.import_workbook(x)
    p = tmp_path / "library.json"
    p.write_text(json.dumps(data))
    return data, p


def test_import_reads_controls_classes_citations_and_your_scores_but_never_the_author(tmp_path):
    data, p = lib(tmp_path)
    assert [c["id"] for c in data["controls"]] == ["GOV-001", "IAM-014", "AUD-003"] and data["classes"] == ["SCB/PSB", "RRB", "Insurer/IRDAI"]
    g = data["controls"][0]
    assert g["citations"] == {"RBI Primary Citation": "RBI-CSF 2016", "SEBI CSCRF": "SEBI CSCRF"} and g["assessment"]["current"] == 2
    assert data["controls"][1]["mitre"] == "T1078" and data["controls"][2]["applicability"]["RRB"] == "N/A"
    assert "Somebody" not in p.read_text()                      # document properties (author) are never read


def test_ceiling_is_the_strictest_of_all_classes_and_dominance_names_what_scb_misses(tmp_path):
    data, _ = lib(tmp_path)
    assert [ct.ceiling(c) for c in data["controls"]] == ["MUST", "MUST", "MUST"]
    dom = ct.dominance(data)
    assert dom["RRB"] == [] and dom["Insurer/IRDAI"] == ["AUD-003"]      # complying with SCB/PSB alone misses the IRDAI audit


def test_a_pack_adds_a_new_regulation_without_code(tmp_path):
    _, p = lib(tmp_path)
    packs = tmp_path / "packs"
    packs.mkdir()
    (packs / "rbi-2027.json").write_text(json.dumps({"controls": [{"id": "ET-011", "domain": "ET", "title": "New AI rule", "tier": "Critical"}],
                                                     "citations": {"GOV-001": {"RBI Secondary Citation": "RBI 2027 circular"}}}))
    data = ct.load(p, packs)
    new = next(c for c in data["controls"] if c["id"] == "ET-011")
    assert new["pack"] == "rbi-2027.json" and ct.ceiling(new) == "MUST"
    assert next(c for c in data["controls"] if c["id"] == "GOV-001")["citations"]["RBI Secondary Citation"] == "RBI 2027 circular"


def test_state_prefers_your_score_then_securax_evidence_then_the_organisation(tmp_path):
    data, _ = lib(tmp_path)
    sx = {"IAM-014": {"status": "proven"}}
    gov, iam, aud = data["controls"]
    assert ct.state(gov, sx) == "far" and ct.state(iam, sx) == "proven" and ct.state(aud, sx) == "org"
    assert [c["id"] for c in ct.vital_gaps(data, ct.CEILING, sx)] == ["GOV-001", "AUD-003"]   # critical + scored risk first


def test_navigator_pages_have_no_script_no_external_request_and_one_page_per_class(tmp_path, monkeypatch):
    data, p = lib(tmp_path)
    monkeypatch.setattr(ct, "SXMAP", ROOT / "governance" / "controls" / "securax-map.json")
    pages = ct.write_navigator(ct.load(p, tmp_path / "none"), tmp_path / "portal" / "navigator.html")
    assert len(pages) == 1 + 1 + 3
    for pg in pages:
        t = pg.read_text()
        assert "<script" not in t and "http://" not in t.replace("http://www.w3.org", "") and "https://" not in t
    t = pages[0].read_text()
    assert "Master caution" in t and "Navigator" in t and "<svg" in t and "AUD-003" in t and "Insurer/IRDAI" in t


def test_every_securax_evidence_file_exists():
    sx = ct.sx_map()
    assert len(sx) >= 50
    missing = [(k, e) for k, v in sx.items() for e in v["evidence"] if not (ROOT / e).exists()]
    assert missing == [] and all(v["status"] in ("proven", "partial") for v in sx.values())
