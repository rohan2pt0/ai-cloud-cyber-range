"""governance/lifebook.py (doc 104): a life workbook becomes Life OS actions. Sheets are recognised by their headers; every open
issue becomes one dated item; the vital fifth is marked; a secret written in a sheet is never copied, only reported; only the
household is checked for Aadhaar and PAN; an issue fixed since the last import is listed as resolved; other sources' items are
kept; the calendar file has two alarms per vital item; everything written is private. All names and numbers here are fake."""
import datetime as dt
import html
import importlib.util
import json
import pathlib
import stat
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_lifebook_t", ROOT / "governance" / "lifebook.py")
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)
TODAY = dt.date(2026, 10, 22)
SECRET = "pin-fake-4242"


def _serial(d: dt.date) -> int:
    return (d - dt.date(1899, 12, 30)).days


def _cell(ref, v):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return f'<c r="{ref}"><v>{v}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(str(v))}</t></is></c>'


def make_book(path, sheets: dict):
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    col = lambda i: chr(65 + i)  # noqa: E731
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f"<workbook {ns}><sheets>" + "".join(
            f'<sheet name="{html.escape(n)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, n in enumerate(sheets)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(
            f'<Relationship Id="rId{i + 1}" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(len(sheets))) + "</Relationships>")
        for i, rows in enumerate(sheets.values()):
            xml = "".join(f'<row r="{r + 1}">' + "".join(_cell(f"{col(c)}{r + 1}", v) for c, v in enumerate(row)) + "</row>" for r, row in enumerate(rows))
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", f"<worksheet {ns}><sheetData>{xml}</sheetData></worksheet>")


def book(tmp_path, register_nominee="N"):
    p = tmp_path / "The_Guiding_Map_test.xlsx"
    make_book(p, {
        "Master Register": [["One row per document (a note row above the table)"], [],
                            ["SL", "Category", "Owner", "Item / Document", "ID / Account No.", "MPIN / Pass", "Password Manager Entry? (Y/N)",
                             "Nominee Set? (Y/N)", "Expiry / Renewal Date"],
                            [1, "Banking", "Self", "Fake Savings Account", "ACC-FAKE-9911", SECRET, "N", register_nominee, None],
                            [2, "Insurance", "Family", "Fake Health Floater", "POL-FAKE-7781", "N/A", "Y", "Y", _serial(TODAY + dt.timedelta(days=40))],
                            [3, "Identity", "Self", "Fake Passport", "PP-FAKE-1", "", "N/A", "N/A", _serial(TODAY + dt.timedelta(days=400))]],
        "Nomination Tracker": [["note"], [], ["SL", "Asset / Account", "Institution", "Nominee Name", "Needs Update? (Y/N)"],
                               [1, "Fake Demat", "Fake Broker", "", "N"], [2, "Fake PPF", "Fake Bank", "Someone Fake", "Y"]],
        "Emergency Binder Checklist": [["note"], [], ["SL", "Item", "Included? (Y/N)"], [1, "Fake Will copy", "N"], [2, "Fake insurance list", "Y"]],
        "Credentials Vault": [["note"], [], ["SL", "Service / Portal", "Password Manager Entry? (Y/N)", "2FA Backup Codes Location"],
                              [1, "Fake Mail", "N", ""], [2, "Fake Tax Portal", "N", ""], [3, "Fake Bank App", "Y", "in the vault"]],
        "Personal Details": [["Sr", "Full Name", "Relation", "Relationship", "Aadhar Card Number", "PAN Card Number"],
                             [1, "Fake Self Person", "SELF", "Self", "AADH-FAKE", "NA"],
                             [2, "Fake Cousin Person", "PATERNAL", "Cousin Brother", "NA", "NA"]],
        "1. Certification": [["Sr. No.", "Certification", "Target Date", "Current Status"],
                             [1, "FAKE-CERT-A", _serial(TODAY - dt.timedelta(days=30)), "Not Started"],
                             [2, "FAKE-CERT-B", _serial(TODAY + dt.timedelta(days=90)), "Studying"],
                             [3, "FAKE-CERT-C", _serial(TODAY + dt.timedelta(days=90)), "Completed"]],
        "Master Roadmap": [["WBS NUMBER", "TASK TITLE", "DUE DATE", "PCT OF TASK COMPLETE"], ["1", "Fake task half done", None, 0.5], ["2", "Fake done task", None, 1]],
    })
    return p


def run(tmp_path, p, dry=False):
    return lb.run([p], today=TODAY, dry=dry, out=tmp_path / "inbox-import.json", life=tmp_path / "life")


def test_every_open_issue_becomes_one_dated_item_and_finished_ones_do_not(tmp_path):
    res = run(tmp_path, book(tmp_path))
    t = {i["t"] for i in res["items"]}
    assert "Set a nominee: Fake Savings Account (Self)" in t
    assert "Put the login for Fake Savings Account (Self) in the password manager" in t
    assert any(x.startswith("Renew before") and "Fake Health Floater" in x for x in t)          # within 90 days
    assert not any("Fake Passport" in x for x in t)                                              # 400 days away: not yet
    assert "No nominee recorded: Fake Demat" in t and "Update the nominee: Fake PPF" in t
    assert "Add to the emergency binder: Fake Will copy" in t and not any("Fake insurance list" in x for x in t)
    assert "Move 2 login(s) into the password manager" in t
    assert any(x.startswith("Late since") and "FAKE-CERT-A" in x for x in t) and "FAKE-CERT-B" in t and "FAKE-CERT-C" not in t
    assert "Fake task half done (50% done)" in t and not any("Fake done task" in x for x in t)
    assert all(i["due"] for i in res["items"] if i["kind"] == "issue")


def test_a_secret_in_a_sheet_is_reported_never_copied_and_numbers_never_leave(tmp_path):
    res = run(tmp_path, book(tmp_path))
    assert any(i["t"].startswith("Remove the PIN or password written in the workbook for Fake Savings Account") for i in res["items"])
    for f in (tmp_path / "inbox-import.json", tmp_path / "life" / "alarms.ics", tmp_path / "life" / "ledger.json"):
        body = f.read_text()
        assert SECRET not in body and "ACC-FAKE-9911" not in body and "POL-FAKE-7781" not in body and "AADH-FAKE" not in body, f.name


def test_only_the_household_is_checked_for_aadhaar_and_pan_and_na_counts_as_missing(tmp_path):
    t = [i["t"] for i in run(tmp_path, book(tmp_path))["items"] if i["area"] == "Identity"]
    assert t == ["PAN not on record for Self"]                         # the cousin is not checked; the self's NA PAN is missing


def test_the_vital_fifth_is_marked_and_secrets_and_nominees_come_first(tmp_path):
    items = run(tmp_path, book(tmp_path))["items"]
    vital = [i for i in items if i["vital"]]
    assert len(vital) == max(1, round(len(items) * 0.2))
    assert items[0]["t"].startswith("Remove the PIN") and all(i["score"] >= j["score"] for i, j in zip(items, items[1:]))


def test_a_fix_in_the_workbook_is_resolved_on_the_next_import_and_other_sources_are_kept(tmp_path):
    (tmp_path / "inbox-import.json").write_text(json.dumps({"items": [{"id": "keep-1", "t": "a Keep note", "from": "keep"}]}))
    first = run(tmp_path, book(tmp_path))
    nominee = [i["id"] for i in first["items"] if i["t"].startswith("Set a nominee: Fake Savings")][0]
    second = run(tmp_path, book(tmp_path, register_nominee="Y"))
    data = json.loads((tmp_path / "inbox-import.json").read_text())
    assert nominee in data["resolved"] and nominee in second["resolved"]
    assert any(x["id"] == "keep-1" for x in data["items"])               # another source's item survives
    assert len({x["id"] for x in data["items"]}) == len(data["items"])   # no duplicates


def test_the_calendar_has_two_alarms_per_vital_dated_item_and_everything_is_private(tmp_path):
    res = run(tmp_path, book(tmp_path))
    ics = (tmp_path / "life" / "alarms.ics").read_bytes().decode()
    vital = [i for i in res["items"] if i["vital"] and i["due"]]
    assert ics.count("BEGIN:VEVENT") == len(vital) and ics.count("BEGIN:VALARM") == 2 * len(vital)
    assert "TRIGGER:-P7D" in ics and "TRIGGER:-P1D" in ics and "\r\n" in ics
    assert all(len(line.encode()) <= 75 for line in ics.split("\r\n"))
    for f in (tmp_path / "inbox-import.json", tmp_path / "life" / "alarms.ics", tmp_path / "life" / "ledger.json"):
        assert stat.S_IMODE(f.stat().st_mode) == 0o600, f.name
    assert stat.S_IMODE((tmp_path / "life").stat().st_mode) == 0o700


def test_a_dry_run_writes_nothing(tmp_path):
    res = run(tmp_path, book(tmp_path), dry=True)
    assert res["items"] and not (tmp_path / "inbox-import.json").exists() and not (tmp_path / "life").exists()


def test_dates_are_read_in_the_forms_workbooks_use():
    assert lb.as_date(str(_serial(dt.date(2026, 11, 5)))) == dt.date(2026, 11, 5)
    assert lb.as_date("05-11-2026") == lb.as_date("05/11/2026") == lb.as_date("2026-11-05") == dt.date(2026, 11, 5)
    assert lb.as_date("not a date") is None and lb.as_date("") is None


def test_a_private_write_into_portal_keeps_the_dir_servable(tmp_path, monkeypatch):
    # The regression that took the Command Center offline: writing the private inbox-import.json used to chmod the whole
    # portal/ dir to 0700, so the nginx container (a different user) could no longer traverse it and every page 403'd.
    monkeypatch.setattr(lb, "ROOT", tmp_path)
    portal = tmp_path / "portal"
    portal.mkdir()
    portal.chmod(0o755)
    f = portal / "inbox-import.json"
    lb._private_write(f, '{"items": []}')
    assert stat.S_IMODE(f.stat().st_mode) == 0o600, "the private file itself is owner-only"
    assert (portal.stat().st_mode & 0o005) == 0o005, "portal/ stays world-traversable, or the Command Center 403s"


def test_a_private_write_into_the_vault_still_locks_that_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(lb, "ROOT", tmp_path)
    vault = tmp_path / "vault" / "life"
    vault.mkdir(parents=True)
    vault.chmod(0o755)
    f = vault / "ledger.json"
    lb._private_write(f, "{}")
    assert (vault.stat().st_mode & 0o077) == 0, "the private vault dir is still tightened to owner-only"
