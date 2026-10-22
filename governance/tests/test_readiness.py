"""governance/readiness.py (doc 106): one organisation's own readiness for any mapped regulation (RBI NBFC 2026 first). Only the chapter's items
apply; nothing unassessed counts as met; a 'met' needs evidence; every mark keeps who and when; the vital few put critical gaps
first; recurring duties go overdue on time; the board pack and the auditor's sheet are private and say what is sample data."""
import datetime as dt
import importlib.util
import json
import pathlib
import stat

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_readiness_t", ROOT / "governance" / "readiness.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)
NOW = dt.date(2026, 10, 22)


@pytest.fixture(autouse=True)
def _today(monkeypatch):
    monkeypatch.setenv("SECURAX_TODAY", NOW.isoformat())


def test_only_the_chapters_items_apply_and_every_layer_has_some():
    m = json.loads((ROOT / "governance" / "regmap-rbi-nbfc.json").read_text())
    for layer in rd.categories("rbi"):
        reqs = rd.requirements(layer)
        assert reqs and all(i["applies"] == "all" or layer in i["applies"] for i in reqs)
    assert len(rd.requirements("V")) > len(rd.requirements("III"))
    ids = {i["id"] for i in m["items"]}
    assert rd.CRITICAL_RBI <= ids and all(c[4] in ids for c in rd.CADENCES)       # every id the module names exists in the map


def test_nothing_unassessed_counts_as_met(tmp_path):
    a = rd.start("Fake NBFC One", "IV", tmp_path)
    s = rd.summary(a)
    assert s["score"] == 0 and s["assessed_pct"] == 0 and s["counts"]["unknown"] == s["in_scope"]
    html = rd.board_html(s)
    assert "not assessed" in html and "do not count as met" in html


def test_a_met_needs_evidence_and_every_mark_keeps_who_and_when(tmp_path):
    a = rd.start("Fake NBFC Two", "V", tmp_path)
    with pytest.raises(ValueError, match="needs the evidence"):
        rd.mark(a, "115-116", "met")
    with pytest.raises(KeyError):
        rd.mark(a, "15-17", "met", "x")                                          # a Chapter IV-only item is not in Chapter V
    rd.mark(a, "115-116", "met", "MFA on the admin console (fake)", "Head of IT", by="tester")
    m = a["marks"]["115-116"]
    assert m["by"] == "tester" and m["at"][:4] == str(dt.date.today().year) and m["evidence"]
    s = rd.summary(a)
    assert s["counts"]["met"] == 1 and s["score"] > 0


def test_the_vital_few_put_critical_gaps_first_and_late_ones_higher(tmp_path):
    a = rd.start("Fake NBFC Three", "V", tmp_path)
    for i in rd.requirements("V"):
        rd.mark(a, i["id"], "met", "fake evidence")
    rd.mark(a, "92-93", "gap")                                                   # not critical
    rd.mark(a, "115-116", "gap", due="2026-10-01")                               # critical and late
    rd.mark(a, "81-82", "gap")                                                   # critical
    v = [r["id"] for r in rd.summary(a, NOW)["vital"]]
    assert v[:3] == ["115-116", "81-82", "92-93"]
    assert [r["id"] for r in rd.summary(a, NOW)["late_actions"]] == ["115-116"]


def test_recurring_duties_go_overdue_on_time(tmp_path):
    a = rd.start("Fake NBFC Four", "V", tmp_path)
    a["done"] = {"va": (NOW - dt.timedelta(days=170)).isoformat(), "pt": (NOW - dt.timedelta(days=366)).isoformat()}
    by = {c["key"]: c for c in rd.cadences(a, NOW)}
    assert by["va"]["state"] == "soon" and by["pt"]["state"] == "overdue" and by["ciso-board"]["state"] == "never"
    assert "backup-test" not in by and "bcp-test" not in by and "bcp-test-critical" in by      # by chapter
    assert {c["key"] for c in rd.cadences(rd.start("Fake NBFC Five", "III", tmp_path), NOW)} == {"board-policy", "backup-test"}


def test_the_board_pack_and_sheet_are_private_and_label_sample_data(tmp_path):
    a = rd.demo(tmp_path)
    hp, cp = rd.report(a, tmp_path)
    for p in (hp, cp, tmp_path / f"{rd.slug(rd.DEMO_NAME)}.json"):
        assert stat.S_IMODE(p.stat().st_mode) == 0o600, p.name
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o700
    body = hp.read_text()
    assert "Sample data." in body and "not an audit opinion" in body
    assert "<script" not in body and "http://" not in body and "https://" not in body           # self-contained, offline
    rows = cp.read_text().splitlines()
    assert rows[0].startswith("para,requirement,status") and len(rows) == 1 + len(rd.requirements("V"))


def test_the_command_guides_a_first_time_user(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rd, "STORE", tmp_path)
    assert rd.main([]) == 1 and "readiness demo" in capsys.readouterr().out
    assert rd.main(["start", "Fake NBFC Six", "--layer", "IV"]) == 0
    out = capsys.readouterr().out
    assert "all not assessed" in out and "readiness mark" in out
    assert rd.main(["done", "Fake NBFC Six", "ciso-board", "2026-10-01"]) == 2                # Chapter V only
    assert rd.main(["done", "Fake NBFC Six", "va", "2030-01-01"]) == 2                        # never a future date
    assert rd.main(["done", "Fake NBFC Six", "va", "2026-10-01"]) == 0
    assert rd.main(["start", "Fake NBFC Six", "--layer", "IV"]) == 1                          # no silent overwrite


def test_any_mapped_regulation_works_on_the_same_engine(tmp_path, monkeypatch, capsys):
    a = rd.start("Fake Broker", "small", tmp_path, key="cscrf")                 # SEBI CSCRF, by category
    reqs = rd.requirements("small", "cscrf")
    assert reqs and all(i["applies"] == "all" or "small" in i["applies"] for i in reqs)
    assert len(reqs) < len(rd.requirements("mii", "cscrf"))
    rd.mark(a, reqs[0]["id"], "met", "fake evidence")
    s = rd.summary(a)
    assert s["score"] > 0 and not s["cadences"] and "CSCRF" in s["title"]
    assert "Recurring duties" not in rd.board_html(s)                          # no duties are invented for a map that sets none
    monkeypatch.setattr(rd, "STORE", tmp_path)
    assert rd.main(["start", "Fake UK Firm", "--map", "caf"]) == 0             # a map without categories needs none
    assert "all requirements" in capsys.readouterr().out
    assert rd.main(["start", "Fake Broker Two", "--map", "cscrf"]) == 2        # one with categories asks for it
    assert "--category is needed" in capsys.readouterr().out
    with pytest.raises(ValueError, match="category must be one of"):
        rd.start("Fake Broker Three", "IV", tmp_path, key="cscrf")
