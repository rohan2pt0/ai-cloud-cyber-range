"""Your documents become Life OS Inbox items, read on this machine: a policy expiring soon with no nominee, a bank statement, a lapsed
policy and a file it cannot read. Fake text and a fake subprocess; no real document, no binary needed, nothing personal."""
import datetime as dt
import importlib.util
import json
import pathlib
import subprocess
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("lifedocs", ROOT / "governance" / "lifedocs.py")
ld = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ld)

NOW = dt.date(2026, 10, 22)
SOON = NOW + dt.timedelta(days=30)
POLICY_NO = "POL-ABCD-7781"
ACCOUNT_NO = "SBX-TEST-4455"

POLICY = f"""ACME Test General Insurance Co.
Policy Schedule
Policy No: {POLICY_NO}        Insured: Test Holder
Sum Assured : Rs. 5,00,000     Premium: Rs. 12,000
Policy Expiry Date : {SOON:%d/%m/%Y}
Nominee: Not registered
"""
BANK = f"""Example Test Bank
Statement of Account for the period 01-Sep-26 to 30-Sep-26
Account No : {ACCOUNT_NO}     IFSC: EXMP0000TST
Opening Balance 1,000.00    Closing Balance 2,000.00
Nominee Registered: Y
"""
LAPSED = """Old Test Life Insurance
Policy Number : POL-OLDX-2290
Premium due date: 05 Mar 2026
Sum Insured: 2,00,000
Nominee Name: Test Relative
"""


def fake_tools(texts, have=("pdftotext", "pdftoppm", "tesseract")):
    """A fake shutil.which and subprocess.run: pdftotext returns texts[file name]; OCR returns nothing."""
    def which(name):
        return "/usr/bin/" + name if name in have else None

    def run(cmd, capture_output=True, timeout=None, check=False):
        assert timeout and capture_output
        if cmd[0] not in have:
            raise FileNotFoundError(cmd[0])
        if cmd[0] == "pdftotext":
            return types.SimpleNamespace(returncode=0, stdout=texts.get(pathlib.Path(cmd[2]).name, "").encode())
        if cmd[0] == "pdftoppm":
            pathlib.Path(cmd[-1] + "-1.png").write_bytes(b"png")
            return types.SimpleNamespace(returncode=0, stdout=b"")
        return types.SimpleNamespace(returncode=0, stdout=texts.get("ocr", "").encode())
    return run, which


@pytest.fixture
def estate(tmp_path, monkeypatch):
    folder = tmp_path / "vault" / "life" / "docs"
    (folder / "insurance").mkdir(parents=True)
    texts = {"car-policy.pdf": POLICY, "sept-statement.pdf": BANK, "old-policy.pdf": LAPSED, "scan.pdf": ""}
    for name in texts:
        sub = folder / "insurance" if "policy" in name else folder
        (sub / name).write_bytes(b"%PDF-fake")
    run, which = fake_tools(texts, have=("pdftotext",))            # no OCR tools: the scan cannot be read
    monkeypatch.setattr(ld.subprocess, "run", run)
    monkeypatch.setattr(ld.shutil, "which", which)
    monkeypatch.setattr(ld, "today", lambda: NOW)
    monkeypatch.setattr(ld, "ROOT", tmp_path)
    monkeypatch.setattr(ld, "LIFE", tmp_path / "vault" / "life")
    monkeypatch.setattr(ld, "DOCS", folder)
    monkeypatch.setattr(ld, "OUT", tmp_path / "portal" / "inbox-import.json")
    return tmp_path


def test_classification_by_keywords():
    assert ld.classify(POLICY) == "insurance" and ld.classify(BANK) == "bank" and ld.classify(LAPSED) == "insurance"
    assert ld.classify("Government of India  Aadhaar  UIDAI  Date of Birth") == "identity"
    assert ld.classify("Income Tax Department  Permanent Account Number Card") == "identity"
    assert ld.classify("Folio No 77AB  NAV 12.3  Units allotted  mutual fund") == "investment"
    assert ld.classify("Registration Certificate  Chassis no  Pollution Under Control") == "vehicle"
    assert ld.classify("Loan Account  EMI  Outstanding principal") == "loan"
    assert ld.classify("A shopping list") == "other"


@pytest.mark.parametrize("s", ["21/11/2026", "21-11-2026", "21.11.2026", "21-11-26", "21 Nov 2026", "21-Nov-26", "21 November, 2026",
                               "2026-11-21", "Nov 21, 2026", "21st Nov 2026"])
def test_dates_in_indian_formats(s):
    assert ld.parse_date("Valid till " + s) == dt.date(2026, 11, 21)


def test_the_date_nearest_each_label():
    text = "Issued on 01/01/2025\nPolicy End Date: 31-Dec-26\nMaturity Date\n15/08/2040\nValid upto 2027-03-01"
    assert ld.find_dates(text) == [("expiry", dt.date(2026, 12, 31)), ("maturity", dt.date(2040, 8, 15)), ("expiry", dt.date(2027, 3, 1))]
    assert ld.parse_date("31/02/2026") is None                      # no such day


def test_numbers_are_kept_masked_only():
    assert ld.find_number(POLICY) == "XXXX7781" and ld.find_number(BANK) == "XXXX4455"
    assert ld.find_number("Name TEST  PAN  ABCDE1234F") == "XXXX234F"
    assert ld.mask("AB-12") == "XXXXAB12" and ld.mask("A1") == "XXXX"
    assert ld.mask("TESTX9876") == "XXXX9876" and ld.mask("") == ""
    assert ld.find_cover(POLICY) == 500000


def test_nominee_states_and_no_names():
    assert ld.nominee_state(POLICY) == "absent"
    for absent in ("Nominee: -", "Nominee : NA", "Nominee Name: Nil", "No nominee on record"):
        assert ld.nominee_state(absent) == "absent", absent
    assert ld.nominee_state(LAPSED) == "present" and ld.nominee_state(BANK) == "present"
    assert ld.nominee_state("Policy schedule with no such line") == "unknown"


def test_items_rules_scores_and_vital(estate):
    rows, items = ld.scan(ld.DOCS)
    by = {(pathlib.PurePosixPath(r["file"]).stem, r["kind"], r["readable"]) for r in rows}
    assert by == {("car-policy", "insurance", True), ("sept-statement", "bank", True), ("old-policy", "insurance", True), ("scan", "unknown", False)}
    t = {x["t"]: x for x in items}
    renew = t[f"Renew insurance policy (car-policy) before {SOON.day} {SOON:%b} {SOON.year}"]
    assert renew["kind"] == "issue" and renew["area"] == "Insurance" and renew["due"] == (SOON - dt.timedelta(days=15)).isoformat()
    assert renew["score"] == 6.0
    nominee = next(x for x in items if x["t"].startswith("Add a nominee") and "car-policy" in x["t"])
    assert nominee["score"] == 3.0
    lapsed = next(x for x in items if x["t"].startswith("LAPSED?"))
    assert lapsed["due"] == NOW.isoformat() and lapsed["vital"] and lapsed["score"] == 9.0
    note = next(x for x in items if x["kind"] == "note")
    assert "lifeos readers" in note["t"] and note["area"] == "Documents"
    assert not any("sept-statement" in x["t"] for x in items)       # a statement with a nominee and no due date raises nothing
    for x in items:
        assert set(x) == {"id", "t", "kind", "area", "due", "next", "from", "vital", "score"}
        assert x["id"].startswith("ld-") and len(x["id"]) == 15 and x["from"] == "docs" and len(x["t"]) <= 200
    assert sum(x["vital"] for x in items) == 1                     # top 20% of three issues: one


def test_soon_is_due_today_when_closer_than_fifteen_days():
    row = {"file": "a.pdf", "kind": "vehicle", "dates": [{"role": "expiry", "date": (NOW + dt.timedelta(days=5)).isoformat()}],
           "number": "", "nominee": "unknown", "readable": True}
    [x] = ld.items_for(row, NOW)
    assert x["due"] == NOW.isoformat() and x["score"] == 2.5 and x["area"] == "Vehicle"
    row["dates"][0]["date"] = (NOW + dt.timedelta(days=200)).isoformat()
    assert ld.items_for(row, NOW) == []


def test_outputs_merge_mask_ics_and_modes(estate):
    out = ld.OUT
    out.parent.mkdir(parents=True)
    out.write_text(json.dumps({"items": [{"id": "keep-1", "t": "Fix the lock", "from": "keep"},
                                         {"id": "ld-oldoldoldold", "t": "gone now", "from": "docs"}], "resolved": ["wb-9"]}))
    assert ld.main([]) == 0
    j = json.loads(out.read_text())
    assert [x["id"] for x in j["items"]][0] == "keep-1" and all(x["from"] == "docs" for x in j["items"][1:])
    assert j["resolved"] == ["wb-9", "ld-oldoldoldold"]
    life = estate / "vault" / "life"
    reg = json.loads((life / "docs-register.json").read_text())
    car = next(r for r in reg["documents"] if r["file"] == "insurance/car-policy.pdf")
    assert car["number"] == "XXXX7781" and car["nominee"] == "absent" and car["dates"] == [{"role": "expiry", "date": SOON.isoformat()}]
    raw = (life / "docs-alarms.ics").read_bytes()
    assert raw.count(b"BEGIN:VEVENT") == 3 and raw.count(b"BEGIN:VALARM") == 6
    assert raw.count(b"TRIGGER:-P7D") == 3 and raw.count(b"TRIGGER:-P1D") == 3
    assert b"\n" not in raw.replace(b"\r\n", b"") and all(len(ln) <= 75 for ln in raw.split(b"\r\n"))
    ids = [x["id"] for x in j["items"] if x.get("kind") == "issue"]
    assert all(f"UID:{i}".encode() in raw for i in ids)
    for f in (out, life / "docs-register.json", life / "docs-alarms.ics"):
        assert oct(f.stat().st_mode & 0o777) == "0o600", f
        text = f.read_text()
        for full in (POLICY_NO, ACCOUNT_NO, "POL-OLDX-2290", "POLABCD7781", "Test Relative", "Test Holder"):
            assert full not in text, (full, f)
    assert oct(life.stat().st_mode & 0o777) == "0o700"
    again = json.loads(out.read_text())
    assert ld.main([]) == 0 and json.loads(out.read_text())["items"] == again["items"]      # the same run twice: the same items


def test_dry_run_writes_nothing_and_json_is_masked(estate, capsys):
    assert ld.main(["--dry-run"]) == 0
    said = capsys.readouterr().out
    assert "Nothing written" in said and "LAPSED?" in said and "could not be read" in said
    assert not ld.OUT.exists() and not (estate / "vault" / "life" / "docs-register.json").exists()
    assert ld.main(["--dry-run", "--json"]) == 0
    dumped = capsys.readouterr().out
    assert json.loads(dumped)["documents"] and POLICY_NO not in dumped and ACCOUNT_NO not in dumped


def test_the_default_folder_is_made_private(estate, capsys):
    import shutil
    shutil.rmtree(ld.DOCS)
    assert ld.main([]) == 0 and ld.DOCS.is_dir() and oct(ld.DOCS.stat().st_mode & 0o777) == "0o700"
    assert "Made vault/life/docs/" in capsys.readouterr().out


def test_missing_readers_degrade_to_could_not_read(tmp_path):
    for name in ("a.pdf", "b.jpg"):
        (tmp_path / name).write_bytes(b"x")
    run, which = fake_tools({}, have=())
    rows, items = ld.scan(tmp_path, NOW, run, which)
    assert [r["why"] for r in rows] == [ld.INSTALL, ld.INSTALL] and [x["kind"] for x in items] == ["note", "note"]

    def broken(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)
    assert ld.extract(tmp_path / "b.jpg", broken, lambda n: "/usr/bin/" + n)[1].startswith("could not read: no text found")


def test_a_scan_is_read_with_ocr(tmp_path):
    (tmp_path / "id.pdf").write_bytes(b"x")
    run, which = fake_tools({"id.pdf": "", "ocr": "Government of India  Aadhaar  UIDAI  Date of Birth 01/01/1990  " * 2})
    text, why = ld.extract(tmp_path / "id.pdf", run, which)
    assert why == "" and ld.classify(text) == "identity"


def test_ics_escapes_and_folds():
    item = {"id": "ld-abcdefabcdef", "t": "Renew; this, now\\" + " long" * 30 + " é", "kind": "issue", "due": "2026-11-06", "next": "a\nb"}
    raw = ld.ics([item], dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc)).encode()
    assert b"Renew\\; this\\, now\\\\" in raw and b"DESCRIPTION:a\\nb" in raw and b"\r\n " in raw
    assert all(len(ln) <= 75 for ln in raw.split(b"\r\n")) and raw.decode().count("é") == 3                # the summary and both alarms


# -- the papers are the input (doc 104): a guided list, any format, the figures read --------------------------------------------

F16PAPER = ("FORM NO. 16 under section 203 for tax deducted at source on salary (section 192)\nTAN of the deductor: FAKE-TAN\n"
          "Gross Salary   Rs. 18,50,000.00\nTotal taxable income  16,25,000\nTotal tax deducted    2,95,400\n")
STMT = "Statement of Account\nSavings Account IFSC FAKE-IFSC\nTotal Credits 19,10,000.00\nTotal Debits 14,60,500.00\nClosing Balance 5,69,500.00\n"


def _docx(path, text):
    import zipfile
    body = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in text.splitlines())
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", f'<w:document xmlns:w="w"><w:body>{body}</w:body></w:document>')


def test_form16_and_a_statement_in_any_format_give_the_first_numbers(tmp_path):
    _docx(tmp_path / "salary-paper.docx", F16PAPER)
    (tmp_path / "statement.csv").write_text(STMT)
    rows, _ = ld.scan(tmp_path, now=dt.date(2026, 10, 22))
    kinds = {r["file"]: r["kind"] for r in rows}
    assert kinds == {"salary-paper.docx": "form16", "statement.csv": "bank"}
    f = ld.papers(rows)["figures"]
    assert f["gross_income"] == 1850000 and f["tax_paid"] == 295400 and f["money_out"] == 1460500 and f["saving_rate_pct"] == 21


def test_the_guided_list_asks_for_what_is_missing_and_the_ask_goes_once_the_paper_is_in(tmp_path):
    out, life = tmp_path / "inbox-import.json", tmp_path / "life"
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "statement.txt").write_text(STMT)
    rows, items = ld.scan(tmp_path / "d", now=dt.date(2026, 10, 22))
    ld.write_all(rows, items, out, life)
    data = json.loads(out.read_text())
    asks = [x for x in data["items"] if x["id"].startswith("ld-paper-")]
    assert "ld-paper-form16" in {x["id"] for x in asks} and "ld-paper-bank" not in {x["id"] for x in asks}
    assert sum(1 for x in asks if x["vital"]) == 3 and all("./securax lifeos docs" in x["next"] for x in asks)
    assert [c["key"] for c in data["papers"]["checklist"] if c["have"]] == ["bank"]
    (tmp_path / "d" / "f16.txt").write_text(F16PAPER)
    rows, items = ld.scan(tmp_path / "d", now=dt.date(2026, 10, 22))
    assert "ld-paper-form16" in ld.write_all(rows, items, out, life)          # resolved: the Life OS ticks the ask off
    body = out.read_text()
    assert "FAKE-TAN" not in body and "FAKE-IFSC" not in body                 # totals only, never an identifier


def test_papers_prints_the_guided_list(tmp_path, capsys):
    assert ld.guide(tmp_path / "none") == 0
    out = capsys.readouterr().out
    assert "Your papers (0 of" in out and "Form 16" in out and "CDSL or NSDL" in out


# ---- Phase 3: forgiving import for a non-technical owner ---------------------------------------------------------------
def _which(present):
    return lambda name: ("/usr/bin/" + name) if name in present else None


def test_install_cmd_matches_the_package_manager():
    assert "apt install poppler-utils tesseract-ocr" in ld.install_cmd(_which({"apt-get"}))
    assert ld.install_cmd(_which({"brew"})) == "brew install poppler tesseract"
    assert "dnf install" in ld.install_cmd(_which({"dnf"}))
    assert "package manager" in ld.install_cmd(_which(set()))          # unknown OS: plain words, never a wrong guess


def test_readers_names_only_what_is_missing():
    r = ld.readers(_which({"pdftotext", "pdftoppm"}))                  # poppler present, tesseract not
    assert r["poppler"] and not r["tesseract"] and r["missing"] == ["tesseract"] and not r["all"]
    assert ld.readers(_which({"pdftotext", "pdftoppm", "tesseract"}))["all"]


def test_readers_cmd_installs_only_on_request(capsys):
    calls = []

    def run(cmd):
        calls.append(cmd)
        return 0
    ld.readers_cmd(install=False, run=run, which=_which(set()))
    assert calls == [] and "readers --install" in capsys.readouterr().out    # shows how, runs nothing
    ld.readers_cmd(install=True, run=run, which=_which({"apt-get"}))
    assert calls and "poppler-utils" in " ".join(calls[0])                   # --install actually runs the installer


def test_an_empty_folder_points_at_documents_you_already_have(tmp_path, monkeypatch, capsys):
    empty = tmp_path / "docs"
    empty.mkdir()
    monkeypatch.setattr(ld, "found_elsewhere", lambda: [(tmp_path / "Downloads", 3)])
    ld.main(["docs", str(empty)])
    out = capsys.readouterr().out
    assert "already have documents" in out and "Downloads" in out and "./securax lifeos docs" in out
