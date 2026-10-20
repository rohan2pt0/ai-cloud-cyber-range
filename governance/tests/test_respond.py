"""Crisis response, end to end on this machine: permission is recorded first, the real collector runs from a 'USB', every
hash is checked on intake, IOCs from an advisory-style text are found in the evidence, tampering is caught, and nothing
private is written outside the case folder. All indicators below are made up (documentation ranges and fake names)."""
import datetime as dt
import importlib.util
import json
import pathlib
import subprocess

import pytest

_s = importlib.util.spec_from_file_location("respond", pathlib.Path(__file__).resolve().parent.parent / "respond.py")
rs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rs)
T0 = dt.datetime(2026, 11, 2, 9, 30, tzinfo=dt.timezone.utc)
ADVISORY = """TLP: AMBER   Example advisory EX-0001
IP Address
• 203[.]0[.]113[.]9
• 198[.]51[.]100[.]1–3
• 192[.]0[.]2[.]5, .7, .20–.21
Domain
• update-check[.]example
• cdn[.]bad-example[.]test
File name and hash
1   dropper_tool.jsp   aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
                       bbbbbbbbbbbbbbbbbbbb
2   cmd.exe            used by the attacker
Plain prose 10.0.0.1 is not an indicator.
"""


def test_permission_is_needed_before_working_for_someone_else(tmp_path):
    with pytest.raises(ValueError):
        rs.open_case("acme", "ransomware", org="Example Org", root=tmp_path)
    with pytest.raises(ValueError):
        rs.open_case("acme", "flood", root=tmp_path)
    cid = rs.open_case("acme", "ransomware", org="Example Org", authorised_by="Example CISO", scope="file servers, read-only", root=tmp_path, at=T0)
    assert cid == "IR-20261102-acme"
    ev = rs.custody(tmp_path / cid).events()
    assert ev[0]["data"]["authorised_by"] == "Example CISO" and (tmp_path / cid).stat().st_mode & 0o077 == 0


def test_advisory_style_indicators_are_read_with_ranges_wrapped_hashes_and_defanging(tmp_path):
    f = tmp_path / "ex.txt"
    f.write_text(ADVISORY)
    got = rs.extract_iocs(ADVISORY)
    assert got["ip"] == ["192.0.2.5", "192.0.2.7", "192.0.2.20", "192.0.2.21", "198.51.100.1", "198.51.100.2", "198.51.100.3", "203.0.113.9"]
    assert got["domain"] == ["cdn.bad-example.test", "update-check.example"]
    assert got["hash"] == ["a" * 44 + "b" * 20] and got["file"] == ["dropper_tool.jsp"]       # cmd.exe is Windows's own, not an indicator
    out = rs.ioc_import(f, "EX-0001", "amber", store=tmp_path / "iocs")
    assert json.loads(out.read_text())["tlp"] == "amber" and (out.stat().st_mode & 0o077) == 0
    with pytest.raises(ValueError):
        rs.ioc_import(f, "x", "purple", store=tmp_path / "iocs")


def test_collect_intake_triage_report_and_tamper_detection(tmp_path):
    cid = rs.open_case("lab", "compromise", root=tmp_path / "cases", at=T0)
    usb = rs.make_kit(cid, tmp_path / "usb", root=tmp_path / "cases")
    assert (usb / "CASE_ID").read_text().strip() == cid and (usb / "tools" / "README.txt").exists()
    r = subprocess.run(["sh", str(usb / "collect.sh"), "--quick"], capture_output=True, text=True, timeout=300)
    assert "Done." in r.stdout, r.stdout + r.stderr
    folder = next((usb / "evidence").iterdir())
    assert rs.check_manifest(folder)["ok"]
    (folder / "dns-like.txt").write_text("")                        # an extra file slipped in after sealing is caught too
    assert rs.check_manifest(folder)["unlisted"] == ["dns-like.txt"]
    (folder / "dns-like.txt").unlink()
    (folder / "processes.txt").write_text((folder / "processes.txt").read_text() + "\nroot 99 /tmp/.x/beacon --c2 203.0.113.9 update-check.example\n")
    assert rs.check_manifest(folder)["altered"] == ["processes.txt"]
    # re-seal as if collected that way, so the planted lines stand in for a real compromise
    subprocess.run(["sh", "-c", f"cd '{folder}' && find . -type f ! -name MANIFEST.sha256 ! -name collector.json -exec sha256sum {{}} \\; > MANIFEST.sha256"], check=True)
    got = rs.intake(cid, usb, handed_by="Example Officer", root=tmp_path / "cases")
    assert got[0]["ok"] and got[0]["handed_by"] == "Example Officer"
    assert rs.intake(cid, usb, root=tmp_path / "cases")[0]["skipped"]           # taking the same folder in twice is refused
    adv = tmp_path / "ex.txt"
    adv.write_text(ADVISORY)
    rs.ioc_import(adv, "EX-0001", "amber", store=tmp_path / "iocs")
    hits = rs.triage(cid, root=tmp_path / "cases", store=tmp_path / "iocs")
    whats = {h["what"] for h in hits}
    assert {"known-bad IP address", "known-bad domain", "program running from a temp or public folder"} <= whats
    rep = rs.report(cid, root=tmp_path / "cases").read_text()
    assert "TLP:AMBER" in rep and "203.0.113.9" in rep and "every evidence hash verify" in rep and "Example Officer" in rep
    assert rs.verify(cid, root=tmp_path / "cases") == []
    copy = tmp_path / "cases" / cid / "evidence" / folder.name / "processes.txt"
    copy.chmod(0o600)
    copy.write_text("cleaned")                                                     # someone edits the vault copy
    assert any("altered" in p for p in rs.verify(cid, root=tmp_path / "cases"))
    log = tmp_path / "cases" / cid / "custody.jsonl"
    lines = log.read_text().splitlines()
    log.write_text("\n".join(lines[:1] + lines[2:]) + "\n")                        # someone deletes a custody entry
    assert any("sequence broken" in p or "does not follow" in p for p in rs.verify(cid, root=tmp_path / "cases"))


def test_the_information_request_list_fits_the_kind_of_incident(tmp_path):
    cid = rs.open_case("pay", "fund-fraud", root=tmp_path, at=T0)
    rows = rs.requests_csv(cid, root=tmp_path).read_text().splitlines()
    assert rows[0].startswith("#,workstream") and any("maker and checker" in r for r in rows) and len(rows) == 1 + len(rs.REQUESTS) + 3
