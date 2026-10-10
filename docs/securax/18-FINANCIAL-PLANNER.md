# SecuRAX — Future Financial Planner (sovereign, offline)

A from-scratch, estate-native reimplementation of the "Future Financial Planner" spreadsheet
(`finance/planner.py`), so you keep its power **without the friction of a fragile .xlsx** and
**without your real numbers ever leaving your machine** — the repo ships only a neutral example.

## What it answers (the three questions, the same as the sheet)
1. **How big a corpus must exist at retirement** to fund the rest of your life (expenses, one-off
   purchases, minus passive income — inflated per-item, discounted at your post-retirement return)?
2. **What will your current assets + SIPs actually grow to** by then?
3. **What extra monthly SIP closes the gap** (or how big is your surplus)?

Plus the **lifestyle "upgrade" true-cost**: what a small recurring add-on really costs once you
count the corpus it could have become + the lump needed to fund it through retirement.

## Use it
```bash
./securax plan                                   # the worked example
python3 finance/planner.py plan   --inputs finance/examples/sample-plan.json
python3 finance/planner.py project --inputs finance/examples/sample-plan.json   # year-by-year
python3 finance/planner.py upgrade 5000 --start 35 --retire 55 --until 90 # lifestyle-creep cost
```
Through your AI assistant: the **`financial_plan`** MCP tool, or ask the **finance / CFO**
advisors to reason over the result.

## Your data stays yours
- Copy `finance/examples/sample-plan.json`, fill in **your** numbers, and keep that file **local**
  (outside git — it is your real finances). The engine reads any JSON of that shape.
- Keep your original `.xlsx` on your own machine; export its sheets to the JSON shape to use it
  here. Nothing is uploaded; the math is pure, offline standard-library Python.

## The inputs (shape)
`assumptions` (age, retire_age, plan_until, returns pre/post, inflation) · `expenses[]`
(monthly, own inflation, start/end age, % continuing after retirement) · `purchases[]` (one-off,
cost today, at age, % funded) · `assets[]` (value, monthly contribution, return, counts-toward-corpus)
· `income_post[]` (passive/job income in retirement). See `finance/examples/sample-plan.json`.

> Honesty note: this is a **projection, not a guarantee**. Stress-test by lowering the
> pre-retirement return ~2% and raising inflation ~1%, and confirm the plan with a
> **SEBI-registered investment adviser** before acting — the planner says so in its own output.
