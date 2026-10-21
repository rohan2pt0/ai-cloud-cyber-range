"""Venture (doc 96): break-even and payback count your time as a cost, unit economics are right, the plan is yours and private,
bad input is refused, and the stress-test prompt carries the real numbers and asks for unknowns to be marked."""
import importlib.util
import json
import os
import pathlib
import stat

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("venture", ROOT / "governance" / "venture.py")
vn = importlib.util.module_from_spec(_s)
_s.loader.exec_module(vn)


def _plan(**over):
    p = json.loads(json.dumps(vn.plan()))
    p.update(over)
    return p


def test_unit_economics_and_breakeven(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    p = _plan(churn_pct=5, fixed_month=3000, hours_month=40, hour_value=1500)
    p["tiers"] = {"pro": {"name": "Pro", "price": 1000, "var": 100, "conv_pct": 1, "cac": 1800}}
    u = vn.units(p)["pro"]
    assert u["cm"] == 900 and u["ltv"] == 18000 and u["ltv_cac"] == 10.0 and u["payback_months"] == 2.0
    b = vn.breakeven_users(p)
    assert b["cash"] == round(3000 / 900, 1) and b["with_time"] == round((3000 + 40 * 1500) / 900, 1)
    assert b["free_needed"] == round(b["with_time"] * 0.05 / 0.01)


def test_time_counts_as_investment_and_delays_payback(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    before = vn.analyse()
    assert vn.main(["log", "time", "100", "built the kit"]) == 0 and vn.main(["log", "money", "20000", "VPS"]) == 0
    after = vn.analyse()
    assert after["ledger"]["invested"] == 100 * after["plan"]["hour_value"] + 20000
    assert (after["payback_month"] or 999) >= (before["payback_month"] or 999)
    assert vn.main(["log", "revenue", "5000", "first customer"]) == 0
    assert vn.ledger()["invested"] == after["ledger"]["invested"] - 5000


def test_a_good_plan_breaks_even_and_a_bad_one_says_why(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    assert vn.main(["plan", "growth=2000", "churn_pct=2", "tiers.pro.conv_pct=3"]) == 0
    a = vn.analyse()
    assert a["breakeven_month"] and a["breakeven_with_time_month"] and not a["examples"]
    assert vn.main(["plan", "tiers.pro.price=100", "tiers.pro.var=150", "tiers.concierge.price=0"]) == 0
    mt = " ".join(vn.must_be_true(vn.analyse()))
    assert "does not cover its own running cost" in mt


def test_plan_is_private_and_refuses_unknown_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    assert vn.main(["plan", "hour_value=2500"]) == 0
    f = tmp_path / "venture.json"
    assert stat.S_IMODE(os.stat(f).st_mode) == 0o600 and vn.plan()["hour_value"] == 2500
    assert vn.main(["plan", "nonsense=1"]) == 2 and vn.main(["plan", "tiers.pro.colour=1"]) == 2
    assert vn.main(["log", "time", "-3"]) == 2 and vn.main(["log", "time", "lots"]) == 2
    assert vn.main(["plan", "tiers.founder.price=500"]) == 0 and "founder" in vn.plan()["tiers"]


def test_the_stress_test_prompt_carries_the_numbers(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    assert vn.main(["ask"]) == 0
    out = capsys.readouterr().out
    assert "Pre-mortem" in out and "unknown" in out and "Rs 999" in out and "GST" in out


def test_report_shows_leverage_and_dual_use(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    assert vn.main([]) == 0
    out = capsys.readouterr().out
    assert "Break-even" in out and "Platform leverage" in out and "example numbers" in out
    assert vn.main(["json"]) == 0
    j = json.loads(capsys.readouterr().out)
    assert j["dual_use"] and j["leverage"]["apps"] >= 2
