"""The risk register: V/T/R and treatment-plan workbooks import by HEADER NAME (two-row headers included), treatment plans join
by reference, risks link to library controls, overdue treatments are found, and the CII self-check follows the four tests."""
import datetime as dt
import html
import importlib.util
import pathlib
import zipfile

_s = importlib.util.spec_from_file_location("risks", pathlib.Path(__file__).resolve().parent.parent / "risks.py")
rk = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rk)
NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def _sheet(rows):
    col = lambda i: chr(65 + i) if i < 26 else "A" + chr(65 + i - 26)
    cell = lambda ref, v: "" if v is None else (f'<c r="{ref}"><v>{v}</v></c>' if isinstance(v, (int, float))
                                                else f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(str(v))}</t></is></c>')
    return f"<worksheet {NS}><sheetData>" + "".join(f'<row r="{i + 1}">' + "".join(cell(f"{col(j)}{i + 1}", v) for j, v in enumerate(r)) + "</row>"
                                                  for i, r in enumerate(rows)) + "</sheetData></worksheet>"


def workbook(path, sheets):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f"<workbook {NS}><sheets>" + "".join(f'<sheet name="{n}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, n in enumerate(sheets)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Target="worksheets/s{i + 1}.xml"/>' for i in range(len(sheets))) + "</Relationships>")
        for i, rows in enumerate(sheets.values()):
            z.writestr(f"xl/worksheets/s{i + 1}.xml", _sheet(rows))


def test_vtr_two_row_header_imports_scores_and_links_to_controls(tmp_path):
    f = tmp_path / "vtr.xlsx"
    workbook(f, {"Riskwise_Risk_Register": [
        ["REGISTER"],
        ["SN", "RISK ID", "RISK PERSPECTIVE", "ASSET/PROCESS", "RISK CATEGORY", "RISK DESCRIPTION (THREAT)", "IMPACT ASSESSMENT", "LIKELIHOOD ASSESSMENT", None, "INHERENT RISK (IR)", "RISK TREATMENT PLAN"],
        [None, None, None, None, None, None, "Impact Value", "LIKELIHOOD", "LIKELIHOOD SCORE", "IR SCORE (LIKELIHOOD X IMPACT)", "Risk Status", "Target Date", "Risk Owner"],
        [1, "R-1", "Organisational", "Vendor images", "Third-Party and Supply Chain", "Backdoors in vendor-supplied images", 4, "Almost certain", 5, 20, "Open", "2026-01-31", "CISO"],
        [2, "R-2", "Information systems", "Branch PCs", "Malware", "Outdated antivirus definitions", 3, "Likely", 3, 9, "Closed", "2026-01-31", "IT"],
    ]})
    rs = rk.import_file(f)
    a, b = rs
    assert a["id"] == "R-1" and a["inherent"] == 20 and a["inherent_rating"] == "critical" and "TP-005" in a["controls"]
    assert "EP-003" in b["controls"] and not rk.is_open(b)
    assert [r["id"] for r in rk.overdue(rs, dt.date(2026, 3, 1))] == ["R-1"]               # the closed one is not overdue
    assert rk.control_pressure(rs).get("TP-005") == 20 and "EP-003" not in rk.control_pressure(rs)


def test_assessment_and_treatment_plan_sheets_join_by_reference(tmp_path):
    f = tmp_path / "rtp.xlsx"
    workbook(f, {
        "Risk Assessment": [["Risk Identification"], ["x"], ["y"],
                            ["Department", "Sr. No.", "Business Process name", "Associated Assets", "Risk Description", "Vulnerability", "Threat",
                             "Probability of threat", "Overall Impact", "Inherent Risk Score", "Treatment Type", "Risk Owner", "Risk treatment #"],
                            ["IT", 1, "Backups", "File servers", "No restore testing", "Untested backups", "Data loss", 4, 4, 16, "Reduce", "Head IT", "RTP-1"]],
        "Treatment Plan": [["Risk Treatment"], ["Reference #", "Treatment Type", "Treatment Plan", "Status", "Person responsible", "Planned End Date", "Actual End Date"],
                           ["RTP-1", "Reduce", "Quarterly restore test", "In progress", "Ops", "30th August 2025", None]]})
    (r,) = rk.import_file(f)
    assert r["inherent"] == 16 and r["status"] == "In progress" and r["due"] == "2025-08-30" and r["owner"] == "Ops"
    assert "BCP-003" in r["controls"] and rk.is_open(r)


def test_dates_are_read_in_the_forms_registers_use():
    assert rk._date(45000) == "2023-03-15" and rk._date("3rd October 2019") == "2019-10-03" and rk._date("2025-05-07 00:00:00") == "2025-05-07"
    assert rk._date("someday") == ""


def test_cii_self_check_follows_the_four_tests():
    assert rk.cii_verdict({"customers": True, "dependency": True}).startswith("LIKELY CII")
    assert rk.cii_verdict({"timeframe": True}).startswith("POSSIBLY CII")
    assert rk.cii_verdict({}).startswith("UNLIKELY CII")
