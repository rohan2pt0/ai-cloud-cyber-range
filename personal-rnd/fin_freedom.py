"""FIRE / financial-freedom calculator — Indian context, offline, read-only.

Does arithmetic on numbers YOU type. No account data, no network. For live holdings use
the INDMoney connector in the Claude app; keep identifiers out of this file.
"""
from __future__ import annotations

import argparse
import json


def fi_plan(monthly_expense: float, annual_return: float = 0.10, inflation: float = 0.06,
            swr: float = 0.035, current_corpus: float = 0.0, monthly_invest: float = 0.0) -> dict:
    """Years-to-FI using real (inflation-adjusted) returns and a safe-withdrawal rule."""
    annual_expense = monthly_expense * 12
    target_corpus = annual_expense / swr                      # e.g. 3.5% SWR => 28.6x
    real_return = (1 + annual_return) / (1 + inflation) - 1   # real monthly growth below
    r = (1 + real_return) ** (1 / 12) - 1

    corpus, months = current_corpus, 0
    while corpus < target_corpus and months < 1200:
        corpus = corpus * (1 + r) + monthly_invest
        months += 1
    savings_rate = monthly_invest / (monthly_invest + monthly_expense) if (monthly_invest + monthly_expense) else 0
    return {
        "target_corpus": round(target_corpus),
        "multiple_of_annual_expense": round(target_corpus / annual_expense, 1),
        "real_return_pct": round(real_return * 100, 2),
        "savings_rate_pct": round(savings_rate * 100, 1),
        "years_to_FI": round(months / 12, 1) if months < 1200 else ">100 (increase savings)",
        "emergency_fund_target": round(monthly_expense * 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expense", type=float, required=True, help="Monthly expense (INR)")
    ap.add_argument("--corpus", type=float, default=0.0, help="Current invested corpus (INR)")
    ap.add_argument("--invest", type=float, default=0.0, help="Monthly investment (INR)")
    ap.add_argument("--return", dest="ret", type=float, default=0.10, help="Nominal annual return (0.10=10%)")
    ap.add_argument("--inflation", type=float, default=0.06)
    ap.add_argument("--swr", type=float, default=0.035, help="Safe withdrawal rate (0.035=3.5%)")
    a = ap.parse_args()
    plan = fi_plan(a.expense, a.ret, a.inflation, a.swr, a.corpus, a.invest)
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
