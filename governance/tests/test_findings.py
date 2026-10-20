"""The findings register: one record per problem, a fix-by date from the severity, re-imports close what is gone, and a risk
acceptance always ends."""
import datetime as dt
import importlib.util
import json
import pathlib

import pytest

_s = importlib.util.spec_from_file_location("findings", pathlib.Path(__file__).resolve().parent.parent / "findings.py")
fd = importlib.util.module_from_spec(_s)
_s.loader.exec_module(fd)

D0 = dt.date(2026, 11, 2)


@pytest.fixture(autouse=True)
def _no_local_intel(monkeypatch):
    monkeypatch.setattr(fd, "epss_scores", lambda: {})                       # never read this machine's snapshots
    monkeypatch.setattr(fd, "kev_cves", lambda: set())
SLA = dict(fd.SLA)


def _sarif(results, tool="Trivy"):
    rules = [{"id": r[0], "properties": {"security-severity": r[1]}} for r in results]
    res = [{"ruleId": r[0], "message": {"text": f"{r[0]} in example-lib"}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": r[2]}}}]}
           for r in results]
    return {"runs": [{"tool": {"driver": {"name": tool, "rules": rules}}, "results": res}]}


def test_severity_words_numbers_and_levels():
    assert [fd.severity(x) for x in ("Critical", "HIGH", "Moderate", "error", "9.8", "5.0", "Informational", "")] == \
           ["critical", "high", "medium", "high", "critical", "medium", None, None]


def test_one_record_per_problem_and_reimport_closes_and_reopens():
    reg = {"findings": {}}
    scan = fd.from_sarif(_sarif([("CVE-2026-0001", "9.1", "app/req.txt"), ("CVE-2026-0002", "5.5", "app/req.txt")]))
    n = fd.merge(reg, scan + scan, D0, SLA, kev=set())
    assert n["new"] == 2 and n["seen"] == 2 and len(reg["findings"]) == 2           # the same scan twice is still two findings
    crit = next(f for f in reg["findings"].values() if f["cve"] == "CVE-2026-0001")
    assert crit["severity"] == "critical" and crit["due"] == "2026-11-09"
    later = fd.from_sarif(_sarif([("CVE-2026-0002", "5.5", "app/req.txt")]))
    n = fd.merge(reg, later, D0 + dt.timedelta(days=3), SLA, kev=set())
    assert n["fixed"] == 1 and crit["status"] == "fixed" and "no longer reported" in crit["fixed_by"]
    n = fd.merge(reg, scan, D0 + dt.timedelta(days=10), SLA, kev=set())
    assert n["reopened"] == 1 and crit["status"] == "open" and crit["due"] == "2026-11-19"   # a regression gets a fresh clock


def test_a_known_exploited_cve_is_critical_whatever_the_scanner_said():
    reg = {"findings": {}}
    fd.merge(reg, fd.from_sarif(_sarif([("CVE-2026-0003", "4.0", "img")])), D0, SLA, kev={"CVE-2026-0003"})
    f = next(iter(reg["findings"].values()))
    assert f["severity"] == "critical" and f["kev"] and f["due"] == "2026-11-09"


def test_another_tool_never_closes_this_tools_findings():
    reg = {"findings": {}}
    fd.merge(reg, fd.from_sarif(_sarif([("R1", "8", "a")], tool="Semgrep")), D0, SLA, kev=set())
    fd.merge(reg, fd.from_sarif(_sarif([("R2", "8", "b")], tool="Trivy")), D0, SLA, kev=set())
    assert all(f["status"] == "open" for f in reg["findings"].values())


def test_a_vapt_table_is_read_by_its_header_names(tmp_path):
    rows = [["VAPT report, example estate"], [], ["Sr", "Observation", "Risk Rating", "Affected Host", "CVE ID"],
            ["1", "Outdated TLS configuration", "Medium", "portal.example.test", ""],
            ["2", "Default credentials on admin console", "High", "10.0.0.5", ""],
            ["3", "Server banner disclosed", "Informational", "portal.example.test", ""]]
    got = fd.from_rows(rows, "vapt-q4")
    assert [g["severity"] for g in got] == ["medium", "high", None] and got[1]["asset"] == "10.0.0.5"
    csvf = tmp_path / "vapt.csv"
    csvf.write_text("\n".join(",".join(r) for r in rows[2:]))
    reg = {"findings": {}}
    n = fd.merge(reg, fd.read(csvf), D0, SLA, kev=set())
    assert n["new"] == 2 and n["skipped"] == 1


def test_acceptance_needs_a_reason_and_an_end_and_expires_by_itself():
    reg = {"findings": {}}
    fd.merge(reg, [{"source": "manual", "rule": "x", "title": "Weak cipher on a lab host", "severity": "high", "asset": "lab"}], D0, SLA, kev=set())
    fid = next(iter(reg["findings"].values()))["id"]
    with pytest.raises(ValueError):
        fd.accept(reg, fid, "", "2027-01-01", "owner", D0)
    with pytest.raises(ValueError):
        fd.accept(reg, fid, "isolated lab", "2028-06-01", "owner", D0)                # more than a year: decide again first
    f = fd.accept(reg, fid, "isolated lab, no data", "2026-12-31", "owner", D0)
    assert fd.status(f, D0) == "accepted" and fd.expiring(reg, dt.date(2026, 12, 20))
    assert fd.status(f, dt.date(2027, 1, 1)) == "overdue"                             # the end date passed and the fix-by date too
    with pytest.raises(KeyError):
        fd.find(reg, "F-nope")


def test_the_audit_summary(tmp_path):
    reg = {"findings": {}}
    fd.merge(reg, fd.from_sarif(_sarif([("A", "9.5", "x"), ("B", "7.5", "y"), ("C", "2", "z")])), D0, SLA, kev=set())
    ids = {f["title"][0]: f["id"] for f in reg["findings"].values()}
    fd.fixed(reg, ids["A"], D0 + dt.timedelta(days=5))                                  # inside 7 days
    fd.fixed(reg, ids["B"], D0 + dt.timedelta(days=40))                                 # outside 30 days
    s = fd.summary(reg, D0 + dt.timedelta(days=40))
    assert s["fixed"] == 2 and s["sla_met"] == 50 and s["open"]["low"] == 1 and s["overdue"] == 0
    p = tmp_path / "r.json"
    fd.save(reg, p)
    assert json.loads(p.read_text())["findings"] and (p.stat().st_mode & 0o077) == 0


def test_the_cockpit_lights_overdue_findings_so_the_phone_alert_sees_them(monkeypatch):
    sc = importlib.util.spec_from_file_location("cockpit_f", pathlib.Path(__file__).resolve().parent.parent / "cockpit.py")
    ck = importlib.util.module_from_spec(sc)
    sc.loader.exec_module(ck)
    reg = {"findings": {}}
    fd.merge(reg, [{"source": "manual", "rule": "a", "title": "Old", "severity": "high", "asset": "", "due": "2026-01-01"}], dt.date(2025, 12, 1), SLA, kev=set())
    stub = type("F", (), {"load": staticmethod(lambda: reg), "summary": staticmethod(fd.summary)})
    monkeypatch.setattr(ck, "_load", lambda name, rel: stub if "findings" in rel else None)
    c = ck.Collector({}, 0, "laptop", {})
    c.c_findings()
    m = c.metrics[0]
    assert m["id"] == "findings" and m["status"] == "red" and "1 overdue" in m["value"] and m["cmd"] == "./securax findings overdue"
    c2 = ck.Collector({}, 0, "laptop", {})
    monkeypatch.setattr(ck, "_load", lambda name, rel: type("E", (), {"load": staticmethod(lambda: {"findings": {}})}))
    c2.c_findings()
    assert c2.metrics == []                                                              # no register: nothing lit


def test_a_likely_exploited_cve_is_at_least_high_and_its_score_stays_current():
    reg = {"findings": {}}
    scan = fd.from_sarif(_sarif([("CVE-2026-0007", "5.0", "img"), ("CVE-2026-0008", "5.0", "img")]))
    fd.merge(reg, scan, D0, SLA, kev=set(), epss={"CVE-2026-0007": 0.62, "CVE-2026-0008": 0.03})
    by = {f["cve"]: f for f in reg["findings"].values()}
    assert by["CVE-2026-0007"]["severity"] == "high" and by["CVE-2026-0007"]["due"] == "2026-12-02"
    assert by["CVE-2026-0008"]["severity"] == "medium" and by["CVE-2026-0008"]["epss"] == 0.03
    fd.merge(reg, scan, D0 + dt.timedelta(days=1), SLA, kev=set(), epss={"CVE-2026-0007": 0.7, "CVE-2026-0008": 0.04})
    assert by["CVE-2026-0008"]["epss"] == 0.04 and fd.summary(reg, D0)["likely_open"] == 1
    assert "EPSS 70%" in fd._line(by["CVE-2026-0007"], D0)
