"""The incident clock: deadlines are computed for every regulator at once, filings are judged on time/late, the log is tamper-evident,
and regulators are data (so any jurisdiction can be added without code)."""
import hashlib
import importlib.util
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("incident", REPO / "governance" / "incident.py")
inc = importlib.util.module_from_spec(spec)
sys.modules["incident"] = inc
spec.loader.exec_module(inc)

DETECTED = "2026-10-14T09:30+05:30"                      # = 04:00Z
T0 = datetime(2026, 10, 14, 4, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "inc"))
    monkeypatch.delenv("SECURAX_REGULATORS_DIR", raising=False)
    monkeypatch.setenv("SECURAX_TZ", "Asia/Kolkata")
    return tmp_path


def open_case(regs="rbi-nbfc,sebi-cscrf,cert-in", **kw):
    args = ["open", "Ransomware on FS01", "--regulators", regs, "--detected", DETECTED, "--severity", "high"]
    for k, v in kw.items():
        args += [f"--{k}", v]
    assert inc.main(args, now=T0 + timedelta(minutes=1)) == 0
    return inc.cases()[0]


def dl(case, now):
    return {(d["regulator"], d["obligation"]): d for d in inc.deadlines(case.state(), inc.load_regulators(), now)}


def test_every_shipped_regulator_definition_is_well_formed():
    regs = inc.load_regulators()
    assert {"rbi-nbfc", "sebi-cscrf", "cert-in"} <= set(regs)
    for r in regs.values():
        assert inc.regulator_problems(r) == [], r["id"]


def test_the_verified_rules_are_the_ones_read_from_primary_text_and_the_rest_say_so():
    regs = inc.load_regulators()
    assert {i for i, r in regs.items() if r["verified"]} == {"cert-in", "rbi-nbfc", "sebi-cscrf"}
    for i in ("rbi-bank", "irdai", "dpdp"):
        assert not regs[i]["verified"] and "UNVERIFIED" in json.dumps(regs[i])


def test_deadlines_for_all_regulators_start_at_detection_not_at_opening():
    c = open_case()
    d = dl(c, T0 + timedelta(hours=1))
    assert d[("rbi-nbfc", "daksh")]["due"] == "2026-10-14T10:00:00Z"            # 09:30 IST + 6 h = 15:30 IST
    assert d[("sebi-cscrf", "sebi-6h")]["due"] == "2026-10-14T10:00:00Z"
    assert d[("sebi-cscrf", "sebi-portal")]["due"] == "2026-10-15T04:00:00Z"    # + 24 h
    assert d[("cert-in", "cert-in-6h")]["due"] == "2026-10-14T10:00:00Z"
    assert all(x["status"] in ("open", "conditional") for x in d.values())


def test_status_turns_overdue_exactly_after_the_deadline():
    c = open_case("rbi-nbfc")
    assert dl(c, T0 + timedelta(hours=6))[("rbi-nbfc", "daksh")]["status"] == "open"
    assert dl(c, T0 + timedelta(hours=6, seconds=1))[("rbi-nbfc", "daksh")]["status"] == "overdue"


def test_filing_is_judged_on_time_or_late(capsys):
    c = open_case("rbi-nbfc")
    inc.main(["file", c.id, "--regulator", "rbi-nbfc", "--obligation", "daksh", "--reference", "DK-1", "--at", "2026-10-14T14:00+05:30"], now=T0 + timedelta(hours=5))
    assert dl(c, T0 + timedelta(hours=9))[("rbi-nbfc", "daksh")]["status"] == "on_time"
    inc.main(["file", c.id, "--regulator", "rbi-nbfc", "--obligation", "cert-in", "--reference", "CI-1", "--at", "2026-10-14T16:00+05:30"], now=T0 + timedelta(hours=7))
    assert dl(c, T0 + timedelta(hours=9))[("rbi-nbfc", "cert-in")]["status"] == "late"
    assert "LATE" in capsys.readouterr().out


def test_due_exit_codes_for_cron_and_n8n(capsys):
    open_case("rbi-nbfc")
    assert inc.main(["due", "--within", "1"], now=T0 + timedelta(hours=1)) == 0
    assert inc.main(["due", "--within", "1"], now=T0 + timedelta(hours=5, minutes=30)) == 1
    assert inc.main(["due"], now=T0 + timedelta(hours=7)) == 2
    assert "OVERDUE" in capsys.readouterr().out


def test_follow_up_obligations_chain_from_an_earlier_filing(tmp_path, monkeypatch):
    d = tmp_path / "regs"
    d.mkdir()
    (d / "x.json").write_text(json.dumps({"id": "xreg", "name": "X", "verified": True, "verified_on": "2026-01-01", "obligations": [
        {"id": "first", "label": "first", "from": "detection", "within_hours": 2, "channel": "c"},
        {"id": "update", "label": "update", "from": "after:first", "within_hours": 24, "channel": "c"}], "periodic": []}))
    monkeypatch.setenv("SECURAX_REGULATORS_DIR", str(d))
    c = open_case("xreg")
    assert dl(c, T0)[("xreg", "update")]["status"] == "waiting"
    inc.main(["file", c.id, "--regulator", "xreg", "--obligation", "first", "--reference", "r", "--at", "2026-10-14T10:00+05:30"], now=T0 + timedelta(hours=2))
    assert dl(c, T0 + timedelta(hours=3))[("xreg", "update")]["due"] == "2026-10-15T04:30:00Z"      # 24 h after the filing at 04:30Z


def test_a_new_regulator_needs_no_code_and_a_bad_one_is_reported(tmp_path, monkeypatch):
    d = tmp_path / "regs"
    d.mkdir()
    (d / "bad.json").write_text(json.dumps({"id": "bad", "name": "Bad", "verified": True, "obligations": [{"id": "a", "label": "a", "from": "nowhere", "within_hours": -1, "channel": "c"}]}))
    monkeypatch.setenv("SECURAX_REGULATORS_DIR", str(d))
    probs = inc.regulator_problems(inc.load_regulators()["bad"])
    assert any("from" in p for p in probs) and any("within_hours" in p for p in probs) and any("without a date" in p for p in probs)


def test_unknown_regulator_is_refused(capsys):
    assert inc.main(["open", "t", "--regulators", "nope"], now=T0) == 2
    assert "unknown regulator" in capsys.readouterr().out


def test_unverified_rules_are_flagged_every_time(capsys):
    open_case("dpdp")
    out = capsys.readouterr().out
    assert "NOT verified" in out and "unverified rule" in out


def test_role_specific_and_conditional_obligations():
    plain = open_case("sebi-cscrf")
    d = dl(plain, T0)
    assert ("sebi-cscrf", "exchange-6h") not in d                       # not a stock broker: not shown
    assert d[("sebi-cscrf", "other-24h")]["status"] == "conditional"    # only if the incident is outside CERT-In's directions
    inc.main(["set", plain.id, "applies:sebi-cscrf/other-24h=yes"], now=T0)
    assert dl(plain, T0)[("sebi-cscrf", "other-24h")]["status"] == "open"


def test_stock_broker_role_adds_the_exchange_report():
    c = open_case("sebi-cscrf", roles="stock-broker")
    assert dl(c, T0)[("sebi-cscrf", "exchange-6h")]["due"] == "2026-10-14T10:00:00Z"


def test_the_rule_in_force_at_opening_is_frozen_in_the_case(tmp_path, monkeypatch):
    d = tmp_path / "regs"
    d.mkdir()
    src = json.loads((REPO / "governance" / "regulators" / "cert-in.json").read_text())
    monkeypatch.setenv("SECURAX_REGULATORS_DIR", str(d))
    c = open_case("cert-in")
    src["obligations"][0]["within_hours"] = 1
    (d / "cert-in.json").write_text(json.dumps(src))                      # a later edit must not move this case's deadline
    assert dl(c, T0)[("cert-in", "cert-in-6h")]["due"] == "2026-10-14T10:00:00Z"


def test_log_is_tamper_evident(tmp_path):
    c = open_case("rbi-nbfc")
    inc.main(["set", c.id, "impact=3 branches"], now=T0)
    inc.main(["note", c.id, "contained"], now=T0)
    assert c.verify() == []
    lines = c.path.read_text().splitlines()
    c.path.write_text("\n".join([lines[0], lines[1].replace("3 branches", "none"), lines[2]]) + "\n")
    assert any("altered" in p for p in c.verify())
    c.path.write_text("\n".join([lines[0], lines[2]]) + "\n")                 # an entry removed
    assert c.verify()
    c.path.write_text("\n".join(lines) + "\n")
    assert c.verify() == []


def test_draft_lists_what_is_still_missing_and_fills_what_is_known(capsys):
    c = open_case("rbi-nbfc")
    inc.main(["set", c.id, "systems_affected=FS01", "entity_name=Acme Finance"], now=T0)
    capsys.readouterr()
    inc.main(["draft", c.id, "--regulator", "rbi-nbfc", "--obligation", "daksh"], now=T0)
    out = capsys.readouterr().out
    assert "Name of the regulated entity: Acme Finance" in out and "FS01" in out and "<<MISSING: Contact person" in out
    assert "14 Oct 2026 09:30 IST" in out and "daksh.rbi.org.in" in out


def test_time_zone_is_configurable_for_other_jurisdictions(monkeypatch):
    monkeypatch.setenv("SECURAX_TZ", "Asia/Singapore")
    assert "12:00" in inc.local(T0)                                          # 04:00Z is noon in Singapore


def test_quarterly_rollup_dates_and_membership(capsys):
    open_case("sebi-cscrf")                                               # detected 14 Oct 2026 = Q4
    capsys.readouterr()
    assert inc.main(["rollup", "--regulator", "sebi-cscrf", "--period", "2026Q3"], now=T0) == 0
    out = capsys.readouterr().out
    assert "Due 15 Oct 2026 23:59 IST" in out and "Incidents detected in the period: 0" in out
    inc.main(["rollup", "--regulator", "sebi-cscrf", "--period", "2026Q4"], now=T0)
    assert "Incidents detected in the period: 1" in capsys.readouterr().out
    assert inc.main(["rollup", "--regulator", "rbi-nbfc", "--period", "2026Q3"], now=T0) == 2     # no quarterly report defined


def test_seal_hashes_and_records_the_evidence(tmp_path, capsys):
    c = open_case("rbi-nbfc")
    f = tmp_path / "gateway.log"
    f.write_text("audit line\n")
    inc.main(["seal", c.id, "--evidence", str(f), "--out", str(tmp_path / "ev")], now=T0)
    man = json.loads((tmp_path / "ev" / "MANIFEST.json").read_text())
    assert man["files"][0]["sha256"] == hashlib.sha256(b"audit line\n").hexdigest()
    assert c.state()["evidence"] and c.verify() == []
    assert inc.main(["seal", c.id, "--evidence", str(tmp_path / "missing")], now=T0) == 2
