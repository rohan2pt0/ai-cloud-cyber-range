#!/usr/bin/env python3
"""Future Financial Planner — sovereign, estate-native retirement-corpus engine (India).

A from-scratch, offline reimplementation of the "Future Financial Planner" spreadsheet so you
can keep using it WITHOUT the friction of a fragile .xlsx — and so your real numbers never leave
your machine (the repo ships only a neutral EXAMPLE). It answers the three questions the sheet
answers:

  1. How big a corpus must exist at retirement to fund the rest of your life?
  2. What will your current assets + SIPs actually grow to by then?
  3. What extra monthly SIP closes the gap (or how big is your surplus)?

Plus the lifestyle "upgrade" true-cost: what a small recurring add-on really costs over a life.

Inputs are YOUR numbers (kept local — JSON here, or your own .xlsx via load_xlsx). Pure standard
library; Indian context (₹, inflation, pre/post-retirement returns). The finance/CFO advisors
(agents/) can reason over this engine's output; the Guiding Map wealth engine mirrors its gates.
"""
from __future__ import annotations

import argparse
import json
import pathlib


def _fv_annuity(annual: float, years: int, r: float) -> float:
    """Future value of `annual` invested at the end of each year for `years` at rate r."""
    if years <= 0:
        return 0.0
    if abs(r) < 1e-9:
        return annual * years
    return annual * (((1 + r) ** years - 1) / r)


def project(inp: dict) -> list[dict]:
    """Year-by-year engine: for each year, the real cash picture (today→plan horizon)."""
    age0 = int(inp["age"]); R = int(inp["retire_age"]); end = int(inp["plan_until"])
    y0 = int(inp.get("start_year", 2026))
    infl = float(inp.get("inflation", 0.06))
    rows = []
    for a in range(age0, end + 1):
        n = a - age0
        retired = a >= R
        # recurring expenses, each inflated by its own rate, continuing per post-retirement %
        exp = 0.0
        for e in inp.get("expenses", []):
            starts = e.get("starts_age") or age0
            ends = e.get("ends_age") or end
            if a < starts or a > ends:
                continue
            i = float(e.get("infl", infl))
            amt = float(e.get("monthly", 0)) * 12 * (1 + i) ** n
            if retired:
                amt *= float(e.get("post_ret_pct", 1.0))
            exp += amt
        # one-off purchases funded in the year they happen (nominal at that age)
        buy = 0.0
        for p in inp.get("purchases", []):
            if (p.get("at_age") or -1) == a:
                i = float(p.get("infl", infl))
                nominal = float(p.get("cost_today", 0)) * (1 + i) ** (a - age0)
                buy += nominal * float(p.get("funded_pct", 1.0))
        # income active this year (passive/job), each grown from today
        inc = 0.0
        for s in inp.get("income_post", []):
            starts = s.get("starts_age") or R
            ends = s.get("ends_age") or end
            if a < starts or a > ends:
                continue
            g = float(s.get("growth", 0.0))
            inc += float(s.get("monthly", 0)) * 12 * (1 + g) ** n
        rows.append({"year": y0 + n, "age": a, "phase": "Retired" if retired else "Working",
                     "expenses": round(exp), "purchases": round(buy), "income": round(inc),
                     "net_outflow": round(exp + buy - inc)})
    return rows


def plan(inp: dict) -> dict:
    """The Summary: corpus needed, corpus projected, shortfall/surplus, required extra SIP."""
    age0 = int(inp["age"]); R = int(inp["retire_age"])
    r_pre = float(inp.get("return_pre", 0.11)); r_post = float(inp.get("return_post", 0.07))
    W = max(0, R - age0)                       # working years left
    rows = project(inp)

    # 1) corpus needed AT retirement = PV (at R) of every net outflow during retirement
    corpus_needed = 0.0
    for row in rows:
        if row["age"] >= R:
            t = row["age"] - R
            corpus_needed += row["net_outflow"] / ((1 + r_post) ** t)

    # 2) corpus PROJECTED at retirement from current assets + their monthly contributions
    corpus_proj = 0.0
    for asset in inp.get("assets", []):
        if not asset.get("counts", True):
            continue
        r = float(asset.get("return", r_pre))
        corpus_proj += float(asset.get("value", 0)) * (1 + r) ** W
        corpus_proj += _fv_annuity(float(asset.get("monthly", 0)) * 12, W, r)

    gap = corpus_needed - corpus_proj          # >0 = shortfall
    # 3) extra monthly SIP (at r_pre over W years) that closes the gap
    denom = _fv_annuity(12, W, r_pre)          # FV of ₹1/month annuitised
    req_sip = max(0.0, gap) / denom if denom else 0.0

    status = "SHORTFALL" if gap > corpus_needed * 0.02 else ("ON TRACK" if gap > -corpus_needed * 0.05 else "SURPLUS")
    return {
        "status": status,
        "working_years_left": W,
        "corpus_needed_at_retirement": round(corpus_needed),
        "corpus_projected_at_retirement": round(corpus_proj),
        "gap": round(gap),                     # +shortfall / -surplus
        "extra_monthly_sip_to_close": round(req_sip),
        "retirement_years": sum(1 for x in rows if x["age"] >= R),
        "note": "All figures nominal ₹ at retirement. Stress-test by lowering return_pre ~2% and "
                "raising inflation ~1%. This is a projection, not a guarantee — verify with a "
                "SEBI-registered adviser before acting.",
    }


def upgrade_cost(monthly: float, start_age: int, retire_age: int, plan_until: int,
                 inflation: float = 0.06, return_post: float = 0.07, return_pre: float = 0.11) -> dict:
    """True lifetime cost of a recurring lifestyle 'upgrade' (e.g. a bigger subscription/EMI).
    A small monthly add-on is paid for decades AND steals the corpus it could have become."""
    years_working = max(0, retire_age - start_age)
    annual = monthly * 12
    paid_while_working = _fv_annuity(annual, years_working, 0.0)              # simple cash paid
    # the corpus that same SIP would have built by retirement (opportunity cost)
    foregone_corpus = _fv_annuity(annual, years_working, return_pre)
    # lump needed at retirement to keep funding it through retirement (inflated)
    fund_retirement = 0.0
    for a in range(retire_age, plan_until + 1):
        t = a - retire_age
        infl_amt = annual * (1 + inflation) ** (a - start_age)
        fund_retirement += infl_amt / ((1 + return_post) ** t)
    return {
        "monthly_addon": round(monthly),
        "cash_paid_until_retirement": round(paid_while_working),
        "foregone_corpus_at_retirement": round(foregone_corpus),
        "extra_lump_needed_to_fund_in_retirement": round(fund_retirement),
        "verdict": "A ₹" + f"{round(monthly):,}" + "/month 'small' upgrade really costs ~₹"
                   + f"{round(foregone_corpus + fund_retirement):,}" + " of future wealth. Decide on that number.",
    }


def load_inputs(path: str) -> dict:
    p = pathlib.Path(path)
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    raise ValueError("Pass a .json inputs file (see finance/examples/sample-plan.json). "
                     "For your own .xlsx, export the sheets to this JSON shape — keep the .xlsx local, out of git.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Future Financial Planner — sovereign retirement-corpus engine.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("plan"); pl.add_argument("--inputs", required=True)
    pr = sub.add_parser("project"); pr.add_argument("--inputs", required=True)
    up = sub.add_parser("upgrade"); up.add_argument("monthly", type=float)
    up.add_argument("--start", type=int, default=35); up.add_argument("--retire", type=int, default=55)
    up.add_argument("--until", type=int, default=90)
    a = ap.parse_args()
    if a.cmd == "plan":
        print(json.dumps(plan(load_inputs(a.inputs)), indent=2))
    elif a.cmd == "project":
        print(json.dumps(project(load_inputs(a.inputs)), indent=2))
    else:
        print(json.dumps(upgrade_cost(a.monthly, a.start, a.retire, a.until), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
