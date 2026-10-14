#!/usr/bin/env python3
"""CERTS — a certification path planner that fits YOUR hours and YOUR budget (data: learning/certs.json).

It turns "clear every serious offensive + AI certification" into a dated, costed sequence:
  * order follows shared skills (three engines: network/AD, web, AI) so each study hour counts towards several exams;
  * a cert starts only after its prerequisites, and only when the plan-year's budget (minus a retake reserve) can pay for it,
    including subscriptions (HTB Academy, Burp Pro) charged in each plan-year that uses them;
  * time = planning hours / (hours per week x efficiency), so a missed week does not break the plan;
  * your progress (`mark`) is kept in ~/.securax/certs-state.json and re-planning starts from where you are.

    ./securax certs plan [--hours 30] [--budget-inr 500000] [--start 2026-11-02] [--pace 1.0] [--with-optional] [--json]
    ./securax certs next                 this week's focus and where to practise
    ./securax certs mark cpts passed     (or: studying | booked | failed)
    ./securax certs list

Every price is a 14 Oct 2026 snapshot with a source link, several from third parties that disagree: check the vendor before you pay.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "certs.json"
STATES = ("studying", "booked", "passed", "failed")


def load(path: pathlib.Path = DATA) -> dict:
    return json.loads(path.read_text("utf-8"))


def state_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_CERTS_STATE") or pathlib.Path.home() / ".securax" / "certs-state.json")


def load_state() -> dict:
    try:
        return json.loads(state_path().read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(st: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2), "utf-8")


def inr(usd: float, d: dict) -> int:
    return int(round(usd * d["fx_usd_inr"] * d["landed_multiplier"], -2))


def ordered(certs: list[dict], include_optional: bool) -> list[dict]:
    """Strategic order (the order in the data file), but never before a prerequisite: a stable topological sort."""
    pool = [c for c in certs if include_optional or not c.get("optional")]
    ids = {c["id"] for c in pool}
    done: list[dict] = []
    seen: set[str] = set()
    while pool:
        nxt = next((c for c in pool if all(a in seen or a not in ids for a in c["after"])), None)
        if nxt is None:
            raise ValueError("circular prerequisites in certs.json: " + ", ".join(c["id"] for c in pool))
        done.append(nxt)
        seen.add(nxt["id"])
        pool.remove(nxt)
    return done


def cost_in_year(c: dict, d: dict, year: int, subs_paid: set[tuple[str, int]]) -> int:
    return inr(c["usd"], d) + sum(inr(d["subscriptions"][s]["usd"], d) for s in c["needs"] if (s, year) not in subs_paid)


def pick(todo: list[dict], done: set[str], d: dict, year: int, room: int, subs_paid: set) -> dict | None:
    """The first READY cert this plan-year can pay for, preferring one that uses a subscription already paid this year (use what you bought)."""
    ids = {c["id"] for c in todo} | done
    ready = [c for c in todo if all(x in done or x not in ids for x in c["after"]) and cost_in_year(c, d, year, subs_paid) <= room]
    paid = [c for c in ready if any((s, year) in subs_paid for s in c["needs"])]
    return (paid or ready or [None])[0]


def with_route(d: dict, route: str) -> dict:
    """route 'unlimited': the certs OffSec Learn Unlimited covers cost nothing individually and need the subscription instead."""
    if route != "unlimited":
        return d
    covers = set(d["subscriptions"]["offsec_unlimited"]["covers"])
    certs = [{**c, "usd": 0, "needs": [*c["needs"], "offsec_unlimited"]} if c["id"] in covers else c for c in d["certs"]]
    return {**d, "certs": certs}


def plan(d: dict, hours_week: float, budget_inr: int, start: dt.date, pace: float = 1.0, include_optional: bool = False,
         passed: set[str] | frozenset = frozenset(), efficiency: float = 0.85, reserve: float = 0.15, carry_over: bool = True, route: str = "per-course") -> dict:
    """Schedule certs one after another. Each plan-year (12 months from `start`) may spend budget x (1 - reserve), plus, with carry_over,
    what earlier years left unspent (money you saved is still yours). When nothing affordable is ready the plan waits for next year's
    budget, and that wait is shown as a practice block (free machines, retakes), never hidden."""
    if hours_week <= 0 or budget_inr <= 0:
        raise ValueError("hours per week and budget must be positive")
    d = with_route(d, route)
    weekly, base = hours_week * efficiency, int(budget_inr * (1 - reserve))
    todo = [c for c in ordered(d["certs"], include_optional) if c["id"] not in passed]
    spent: dict[int, int] = {}
    subs_paid: set[tuple[str, int]] = set()
    done, rows, week, idle_years = set(passed), [], 0.0, 0
    while todo:
        year = int(week // 52)
        room = base * (year + 1) - sum(spent.values()) if carry_over else base - spent.get(year, 0)
        c = pick(todo, done, d, year, room, subs_paid)
        if c is None:
            idle_years += 1
            if idle_years > 3:
                raise ValueError(f"'{todo[0]['id']}' cannot be afforded even after saving for 3 years at ₹{budget_inr:,}/year")
            nxt = (year + 1) * 52.0
            rows.append({"id": "practice", "name": "Practice block: free HTB/PG machines, retake buffer, rest", "engine": "-", "tier": 0, "hours": 0,
                         "start": (start + dt.timedelta(weeks=week)).isoformat(), "exam_by": (start + dt.timedelta(weeks=nxt)).isoformat(),
                         "plan_year": year + 1, "cost_inr": 0, "why": "the next certification needs next year's budget"})
            week = nxt
            continue
        idle_years = 0
        cost = cost_in_year(c, d, year, subs_paid)
        subs_paid.update((s, year) for s in c["needs"])
        spent[year] = spent.get(year, 0) + cost
        weeks = math.ceil(c["hours"] * pace / weekly)
        rows.append({"id": c["id"], "name": c["name"], "engine": c["engine"], "tier": c["tier"], "hours": round(c["hours"] * pace),
                     "start": (start + dt.timedelta(weeks=week)).isoformat(), "exam_by": (start + dt.timedelta(weeks=week + weeks)).isoformat(),
                     "plan_year": year + 1, "cost_inr": cost, "why": c["why"]})
        week += weeks
        done.add(c["id"])
        todo.remove(c)
    years = {y + 1: {"spent_inr": v, "budget_inr": budget_inr, "reserve_inr": budget_inr - v} for y, v in sorted(spent.items())}
    return {"rows": rows, "years": years, "weeks": math.ceil(week), "total_inr": sum(spent.values()), "route": route, "assumptions": {
        "hours_per_week": hours_week, "efficiency": efficiency, "effective_hours_per_week": round(weekly, 1), "pace": pace, "carry_over": carry_over,
        "fx_usd_inr": d["fx_usd_inr"], "landed_multiplier": d["landed_multiplier"], "retake_reserve": reserve}}


def best_route(d: dict, *args, **kw) -> tuple[dict, dict]:
    """Plan both OffSec routes; return (chosen, other): fewer weeks wins, then lower cost."""
    a = plan(d, *args, **kw, route="per-course")
    b = plan(d, *args, **kw, route="unlimited")
    return (a, b) if (a["weeks"], a["total_inr"]) <= (b["weeks"], b["total_inr"]) else (b, a)


def render_plan(p: dict, d: dict) -> str:
    a = p["assumptions"]
    out = [f"Plan: {a['hours_per_week']} h/week (≈{a['effective_hours_per_week']} effective), pace x{a['pace']}, "
           f"₹{a['fx_usd_inr']}/USD x{a['landed_multiplier']} landed (GST + card markup; see learning/certs.json)", ""]
    out.append(f"{'#':<3}{'certification':<52}{'engine':<12}{'study from':<12}{'exam by':<12}{'year':<6}{'₹ cost':>10}")
    out.append("-" * 107)
    i = 0
    for r in p["rows"]:
        i += r["id"] != "practice"
        label = f"{i:<3}" if r["id"] != "practice" else "   "
        out.append(f"{label}{r['name'][:51]:<52}{r['engine']:<12}{r['start']:<12}{r['exam_by']:<12}{r['plan_year']:<6}{r['cost_inr']:>10,}")
    out.append("")
    for y, v in p["years"].items():
        out.append(f"  plan-year {y}: ₹{v['spent_inr']:,} planned (budget ₹{v['budget_inr']:,} a year" + (", unspent money carries forward)" if a["carry_over"] else ")"))
    out.append(f"  OffSec route: {p['route']}   ·   total ₹{p['total_inr']:,}")
    out.append(f"  total: about {p['weeks']} weeks ({p['weeks'] / 52:.1f} years) for {sum(r['id'] != 'practice' for r in p['rows'])} certifications")
    out += ["", "Every price is a snapshot (checked " + d["checked"] + "); several sources disagree. Check the vendor's page before paying.",
            "Hours are estimates for a beginner: after your first exam, re-plan with --pace (e.g. 0.8 if you were faster, 1.3 if slower)."]
    return "\n".join(out) + "\n"


def next_focus(d: dict, st: dict) -> str:
    passed = {k for k, v in st.items() if v == "passed"}
    todo = [c for c in ordered(d["certs"], False) if c["id"] not in passed]
    if not todo:
        return "Every planned certification is marked passed. Re-plan with --with-optional, or add the next one to learning/certs.json.\n"
    c = todo[0]
    eng = d["engines"][c["engine"]]
    lines = [f"Now: {c['name']}  ({st.get(c['id'], 'not started')})", f"  why first: {c['why']}", f"  exam: {c['format']}",
             "", "This week (80/20 split of your hours):",
             "  60%  hands-on in the labs below (no video binge: do, fail, read, redo)",
             "  20%  notes + one practice report section (every OffSec/HTB exam is graded on the report too)",
             "  20%  redo yesterday's failures from memory (spaced repetition beats new material)", "", "Where to practise:"]
    lines += [f"  - {p}" for p in eng["practice"]]
    lines += ["", f"When you pass:  ./securax certs mark {c['id']} passed    (the plan moves on and re-dates itself)"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--hours", type=float, default=30)
    p.add_argument("--budget-inr", type=int, default=500000)
    p.add_argument("--start", default="")
    p.add_argument("--pace", type=float, default=1.0, help="multiply every hour estimate (0.8 faster, 1.3 slower)")
    p.add_argument("--with-optional", action="store_true", help="also schedule the optional ones (CWES, eJPT, GIAC)")
    p.add_argument("--route", default="best", choices=["best", "per-course", "unlimited"], help="OffSec 300-level: one course each, Learn Unlimited, or whichever is faster")
    p.add_argument("--no-carry-over", action="store_true", help="each year's unspent budget is lost (default: it carries forward)")
    p.add_argument("--json", action="store_true")
    sub.add_parser("next")
    sub.add_parser("list")
    m = sub.add_parser("mark")
    m.add_argument("id")
    m.add_argument("status", choices=STATES)
    a = ap.parse_args(argv)
    d = load()
    st = load_state()
    if a.cmd == "list":
        for c in d["certs"]:
            print(f"  {c['id']:<11}{'(optional) ' if c.get('optional') else ''}{c['name']}  — {st.get(c['id'], '')}")
        return 0
    if a.cmd == "mark":
        if a.id not in {c["id"] for c in d["certs"]}:
            print(f"unknown certification '{a.id}'. See: ./securax certs list")
            return 2
        st[a.id] = a.status
        save_state(st)
        print(f"{a.id}: {a.status}")
        return 0
    if a.cmd == "next":
        print(next_focus(d, st), end="")
        return 0
    start = dt.date.fromisoformat(a.start) if a.start else dt.date.today()
    args = (d, a.hours, a.budget_inr, start, a.pace, a.with_optional, {k for k, v in st.items() if v == "passed"})
    try:
        if a.route == "best":
            res, other = best_route(*args, carry_over=not a.no_carry_over)
        else:
            res, other = plan(*args, carry_over=not a.no_carry_over, route=a.route), None
    except ValueError as e:
        print("Cannot plan:", e)
        return 1
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    print(render_plan(res, d), end="")
    if other:
        print(f"  (compared: the {other['route']} route takes {other['weeks']} weeks for ₹{other['total_inr']:,}; this plan uses {res['route']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
