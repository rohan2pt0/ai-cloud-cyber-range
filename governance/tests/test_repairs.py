"""Repairs: every problem from every register in one list, each with its fix; setup steps are not repairs."""
import datetime as dt
import importlib.util
import json
import pathlib

_s = importlib.util.spec_from_file_location("repairs", pathlib.Path(__file__).resolve().parent.parent / "repairs.py")
rp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rp)


def test_one_list_from_the_snapshot_and_the_registers(tmp_path, monkeypatch):
    snap = tmp_path / "cockpit.json"
    snap.write_text(json.dumps({"ts": 1, "metrics": [
        {"label": "Latest backup", "value": "none yet", "status": "red", "area": "Recover", "why": "the only way back", "cmd": "./securax backup"},
        {"label": "TLS", "value": "plain HTTP", "status": "amber", "area": "Protect", "why": "", "action": "Turn it on"},
        {"label": "Gateway", "value": "up", "status": "green", "area": "Run", "why": ""}]}))
    late = {"id": "F-abc123", "due": "2026-01-01", "title": "Example overdue finding", "severity": "high", "kev": True, "asset": "lab"}
    monkeypatch.setattr(rp, "_findings", lambda: [{"level": "act", "area": "Findings", "title": late["id"] + " overdue", "why": "", "fix": "./securax findings fixed F-abc123"}])
    monkeypatch.setattr(rp, "_risks", lambda: [])
    def _routines():
        raise RuntimeError("no history")
    monkeypatch.setattr(rp, "_routines", _routines)
    rep = rp.collect(snap)
    assert [i["level"] for i in rep["items"]] == ["act", "act", "schedule"]          # today's first; green readings are not repairs
    assert {i["fix"] for i in rep["items"]} >= {"./securax backup", "Turn it on", "./securax findings fixed F-abc123"}
    assert rep["act"] == 2 and rep["errors"] == ["routines: RuntimeError"]            # a broken source is named, not silently dropped
    assert rp.summary(rep) == {"count": 3, "act": 2, "top": rep["items"][0]["title"]}


def test_overdue_findings_and_ending_acceptances_come_with_their_command(monkeypatch):
    fd = rp._mod("securax_findings_t", "governance/findings.py")
    reg = {"findings": {}}
    fd.merge(reg, [{"source": "manual", "rule": "a", "title": "Old finding", "severity": "high", "asset": "", "due": "2026-01-01"},
                   {"source": "manual", "rule": "b", "title": "Lab finding", "severity": "low", "asset": ""}], dt.date(2025, 12, 1), kev=set())
    lab = next(f for f in reg["findings"].values() if f["title"] == "Lab finding")
    fd.accept(reg, lab["id"], "isolated lab", (dt.date.today() + dt.timedelta(days=5)).isoformat(), "owner")
    monkeypatch.setattr(rp, "_mod", lambda *a: type("M", (), {"load": staticmethod(lambda: reg), "overdue": staticmethod(fd.overdue),
                                                             "expiring": staticmethod(fd.expiring)}))
    got = rp._findings()
    assert got[0]["level"] == "act" and "findings fixed" in got[0]["fix"]
    assert got[1]["level"] == "schedule" and "decide again" in got[1]["fix"]
