import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("planner", ROOT / "finance" / "planner.py")
PL = importlib.util.module_from_spec(spec); sys.modules["planner"] = PL; spec.loader.exec_module(PL)
EX = ROOT / "finance" / "examples" / "sample-plan.json"


def test_example_loads_and_plans():
    inp = PL.load_inputs(str(EX))
    s = PL.plan(inp)
    assert s["working_years_left"] == 20 and s["retirement_years"] == 36
    assert s["corpus_needed_at_retirement"] > 0 and s["corpus_projected_at_retirement"] > 0
    assert s["status"] in ("SHORTFALL", "ON TRACK", "SURPLUS")


def test_projection_spans_horizon_with_phases():
    rows = PL.project(PL.load_inputs(str(EX)))
    assert rows[0]["age"] == 35 and rows[-1]["age"] == 90
    assert rows[0]["phase"] == "Working" and rows[-1]["phase"] == "Retired"
    # the car purchase at 45 shows up as a one-off that year, not before
    at45 = [r for r in rows if r["age"] == 45][0]
    assert at45["purchases"] > 0 and [r for r in rows if r["age"] == 44][0]["purchases"] == 0


def test_more_savings_shrinks_the_gap():
    inp = PL.load_inputs(str(EX))
    base = PL.plan(inp)["gap"]
    inp2 = json.loads(json.dumps(inp)); inp2["assets"][2]["monthly"] += 40000   # bigger equity SIP
    assert PL.plan(inp2)["gap"] < base


def test_required_sip_closes_gap():
    inp = PL.load_inputs(str(EX)); s = PL.plan(inp)
    if s["gap"] > 0:
        inp2 = json.loads(json.dumps(inp))
        inp2["assets"].append({"name": "extra", "value": 0, "monthly": s["extra_monthly_sip_to_close"], "return": inp["return_pre"], "counts": True})
        assert abs(PL.plan(inp2)["gap"]) <= abs(s["gap"]) * 0.1    # closed to within 10%


def test_upgrade_true_cost_exposes_lifestyle_creep():
    u = PL.upgrade_cost(5000, 35, 55, 90)
    # a 5k/month add-on should cost far more than the raw cash paid, once opportunity cost counts
    assert u["foregone_corpus_at_retirement"] > u["cash_paid_until_retirement"]
    assert u["extra_lump_needed_to_fund_in_retirement"] > 0 and "really costs" in u["verdict"]


def test_zero_return_does_not_divide_by_zero():
    inp = PL.load_inputs(str(EX)); inp["return_pre"] = 0.0
    for a in inp["assets"]:
        a["return"] = 0.0
    s = PL.plan(inp)          # must not raise
    assert s["corpus_projected_at_retirement"] >= 0
