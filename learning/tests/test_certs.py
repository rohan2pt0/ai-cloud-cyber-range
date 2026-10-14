"""The certification planner respects prerequisites, money per year, carry-over and your progress; and says plainly where it waits."""
import datetime as dt
import importlib.util
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("certs", HERE / "certs.py")
cp = importlib.util.module_from_spec(spec)
sys.modules["certs"] = cp
spec.loader.exec_module(cp)
D = cp.load()
START = dt.date(2026, 11, 2)


def ids(p):
    return [r["id"] for r in p["rows"] if r["id"] != "practice"]


def test_data_is_consistent_and_every_price_has_a_source():
    known = {c["id"] for c in D["certs"]}
    for c in D["certs"]:
        assert c["source"].startswith("https://") and c["hours"] > 0 and c["usd"] > 0 and c["engine"] in D["engines"]
        assert set(c["after"]) <= known and set(c["needs"]) <= set(D["subscriptions"])
    assert set(D["subscriptions"]["offsec_unlimited"]["covers"]) <= known
    assert all(s["source"].startswith("https://") for s in D["subscriptions"].values())


@pytest.mark.parametrize("route", ["per-course", "unlimited"])
def test_no_cert_is_planned_before_its_prerequisites(route):
    order = ids(cp.plan(D, 30, 500000, START, route=route))
    for c in D["certs"]:
        if c["id"] in order:
            assert all(order.index(a) < order.index(c["id"]) for a in c["after"] if a in order), c["id"]


@pytest.mark.parametrize("carry", [True, False])
def test_spending_never_exceeds_the_budget(carry):
    p = cp.plan(D, 30, 500000, START, carry_over=carry, route="per-course")
    spend = [v["spent_inr"] for v in p["years"].values()]
    cap = int(500000 * 0.85)
    if carry:
        assert all(sum(spend[: i + 1]) <= cap * (i + 1) for i in range(len(spend)))
    else:
        assert all(s <= cap for s in spend)


def test_optional_and_passed_certs_are_left_out_and_replanning_starts_from_progress():
    base = ids(cp.plan(D, 30, 500000, START))
    assert "giac" not in base and "ejpt" not in base
    assert {"ejpt", "cwes", "giac"} <= set(ids(cp.plan(D, 30, 900000, START, include_optional=True)))
    after = ids(cp.plan(D, 30, 500000, START, passed={"cpts", "crtp"}))
    assert "cpts" not in after and "crtp" not in after and after[0] != "cpts"


def test_more_hours_finish_sooner_and_pace_scales_time():
    assert cp.plan(D, 40, 900000, START)["weeks"] < cp.plan(D, 15, 900000, START)["weeks"]
    slow, fast = cp.plan(D, 30, 2000000, START, pace=1.3), cp.plan(D, 30, 2000000, START, pace=0.8)
    assert fast["weeks"] < slow["weeks"]


def test_waiting_for_money_is_shown_as_a_practice_block_not_hidden():
    p = cp.plan(D, 30, 500000, START, route="per-course")
    gaps = [r for r in p["rows"] if r["id"] == "practice"]
    assert gaps and all(r["cost_inr"] == 0 for r in gaps)


def test_learn_unlimited_charges_once_for_the_certs_it_covers_and_needs_carry_over():
    u = cp.plan(D, 30, 500000, START, route="unlimited")
    covered = [r for r in u["rows"] if r["id"] in D["subscriptions"]["offsec_unlimited"]["covers"]]
    assert len(covered) == 4 and sum(1 for r in covered if r["cost_inr"] > 0) == 1          # the subscription is paid once
    assert len({r["plan_year"] for r in covered}) == 1                                     # all inside one paid year
    with pytest.raises(ValueError):
        cp.plan(D, 30, 500000, START, route="unlimited", carry_over=False)                 # ₹7 lakh never fits a ₹5 lakh year without saving


def test_best_route_picks_the_faster_plan():
    chosen, other = cp.best_route(D, 30, 500000, START)
    assert (chosen["weeks"], chosen["total_inr"]) <= (other["weeks"], other["total_inr"])


def test_an_impossible_budget_is_refused_with_the_reason():
    with pytest.raises(ValueError, match="cannot be afforded"):
        cp.plan(D, 30, 50000, START, route="per-course")
    with pytest.raises(ValueError):
        cp.plan(D, 0, 500000, START)


def test_circular_prerequisites_are_detected():
    bad = [{"id": "a", "after": ["b"]}, {"id": "b", "after": ["a"]}]
    with pytest.raises(ValueError, match="circular"):
        cp.ordered(bad, True)


def test_inr_uses_the_landed_multiplier():
    assert cp.inr(100, {"fx_usd_inr": 100, "landed_multiplier": 1.2}) == 12000


def test_mark_next_and_list_round_trip(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    assert cp.main(["next"]) == 0 and "CPTS" in capsys.readouterr().out
    assert cp.main(["mark", "cpts", "passed"]) == 0
    capsys.readouterr()
    assert cp.main(["next"]) == 0
    out = capsys.readouterr().out
    assert "CPTS" not in out.split("\n")[0] and "60%" in out and "./securax certs mark" in out
    assert json.loads((tmp_path / "s.json").read_text()) == {"cpts": "passed"}
    assert cp.main(["mark", "nope", "passed"]) == 2
    assert cp.main(["list"]) == 0 and "cpts" in capsys.readouterr().out


def test_cli_plan_prints_costs_years_and_the_route_comparison(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    assert cp.main(["plan", "--start", "2026-11-02"]) == 0
    out = capsys.readouterr().out
    assert "plan-year 1" in out and "compared:" in out and "Check the vendor" in out and "OffSec route" in out
    assert cp.main(["plan", "--start", "2026-11-02", "--json", "--route", "per-course"]) == 0
    assert json.loads(capsys.readouterr().out)["route"] == "per-course"
    assert cp.main(["plan", "--budget-inr", "10000", "--route", "per-course"]) == 1
