#!/usr/bin/env python3
"""The monthly failure guards (doc 108): the patterns that broke RIM, Nokia, Kodak, Byju's, GoMechanic, Builder.ai and others,
turned into numbers with a line each that SecuRAX checks for you. Run it on the first of every month.

    ./securax venture guards            every guard: PASS, WATCH, FAIL or NOT YET (not enough data to judge, never a pass)
    ./securax venture guards --json     the same, for a dashboard

What it reads, all private, all yours: vault/venture.json (the time, money and revenue you log with ./securax venture log, and
plan settings such as cash and last_independent_review), governance/shifts.json (the platform shifts you review), products.json
(each product's dated stop test) and the public website (the words it uses). The guards and their lines are in
governance/guards.json, so a line can be tightened without touching code. Standard library only; no network.
Exit codes: 0 nothing failed, 1 a guard failed.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUARDS = ROOT / "governance" / "guards.json"
SHIFTS = ROOT / "governance" / "shifts.json"
PRODUCTS = ROOT / "products.json"
SITE = ROOT / "website"
ICON = {"pass": "✔ PASS", "watch": "~ WATCH", "fail": "✗ FAIL", "notyet": "· NOT YET"}


def today() -> dt.date:
    return dt.date.fromisoformat(os.environ["SECURAX_TODAY"]) if os.environ.get("SECURAX_TODAY") else dt.date.today()


def _venture():
    spec = importlib.util.spec_from_file_location("securax_venture_g", ROOT / "governance" / "venture.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _log(v) -> list[dict]:
    return [e for e in v._mine().get("log", []) if isinstance(e, dict)]


def _window(log: list[dict], kind: str, days: int, now: dt.date) -> float:
    start = now - dt.timedelta(days=days)
    return sum(e["amount"] for e in log if e.get("kind") == kind and dt.date.fromisoformat(e["d"]) > start)


def _share(log: list[dict], key: str) -> tuple[str, float, float]:
    """(the largest holder, its share %, the revenue that carries the tag at all)."""
    by: dict[str, float] = {}
    for e in log:
        if e.get("kind") == "revenue" and e.get(key):
            by[e[key]] = by.get(e[key], 0) + e["amount"]
    total = sum(by.values())
    if not total:
        return "", 0.0, 0.0
    top = max(by, key=by.get)
    return top, round(100 * by[top] / total, 1), total


def _r(gid: str, state: str, value: str, why: str) -> dict:
    return {"id": gid, "state": state, "value": value, "why": why}


def check(now: dt.date | None = None, root: pathlib.Path = ROOT) -> list[dict]:
    now = now or today()
    g = {x["id"]: x for x in json.loads(GUARDS.read_text("utf-8"))["guards"]}
    v = _venture()
    log, p = _log(v), v.plan()
    out = []

    # 1. runway: cash on hand against the net monthly burn of the last 90 days
    burn = (_window(log, "money", 90, now) - _window(log, "revenue", 90, now)) / 3
    cash = float(p.get("cash") or 0)
    line = g["runway"]["line"]
    if burn <= 0:
        out.append(_r("runway", "pass" if log else "notyet", "no net burn" if log else "nothing logged",
                      "revenue covers spending" if log else "log money and revenue: ./securax venture log money|revenue RS \"what\""))
    elif not cash:
        out.append(_r("runway", "notyet", f"burn {v.rs(burn)}/month", "set your cash: ./securax venture plan cash=RS"))
    else:
        months = cash / burn
        out.append(_r("runway", "pass" if months >= line else "watch" if months >= line / 2 else "fail", f"{months:.1f} months",
                      f"at least {line} months of net burn in cash"))

    # 2. burn multiple: net burn over net new revenue, last 90 days (growth bought with cash, not earned)
    rev_now, rev_before = _window(log, "revenue", 90, now), _window(log, "revenue", 180, now) - _window(log, "revenue", 90, now)
    growth = rev_now - rev_before
    if not rev_now:
        out.append(_r("burn-multiple", "notyet", "no revenue yet", "judged once revenue comes in"))
    elif growth <= 0:
        out.append(_r("burn-multiple", "watch" if burn > 0 else "pass", "revenue not growing", "spending is not buying growth"))
    else:
        bm = max(burn * 3, 0) / growth
        line = g["burn-multiple"]["line"]
        out.append(_r("burn-multiple", "pass" if bm <= line else "watch" if bm <= 2 * line else "fail", f"{bm:.1f}", f"at most {line}"))

    # 3 and 4. concentration: no product, and no customer, carries the business
    for gid, key in (("product-share", "product"), ("customer-share", "customer")):
        top, share, tagged = _share(log, key)
        line = g[gid]["line"]
        if not tagged:
            out.append(_r(gid, "notyet", "no tagged revenue", f"log revenue with --{key} to judge"))
        else:
            out.append(_r(gid, "pass" if share <= line else "fail", f"{top} {share}%", f"at most {line}% from one {key}"))

    # 5. revenue recognition: revenue counts only when money arrived, with its reference
    rev = [e for e in log if e.get("kind") == "revenue"]
    bad = [e for e in rev if not e.get("ref")]
    out.append(_r("revenue-proof", "notyet" if not rev else "pass" if not bad else "fail",
                  f"{len(bad)} of {len(rev)} without a reference" if rev else "no revenue yet",
                  "every revenue line carries --ref (invoice and UTR): money received, not promised"))

    # 6. an independent review once revenue is material
    total_rev = sum(e["amount"] for e in rev)
    last = p.get("last_independent_review") or ""
    if total_rev < g["independent-review"]["line"]:
        out.append(_r("independent-review", "notyet", f"revenue {v.rs(total_rev)}", f"needed from {v.rs(g['independent-review']['line'])} of revenue"))
    else:
        fresh = bool(last) and (now - dt.date.fromisoformat(last)).days <= 365
        out.append(_r("independent-review", "pass" if fresh else "fail", last or "never",
                      "a chartered accountant reviews the books every year: ./securax venture plan last_independent_review=YYYY-MM-DD"))

    # 7. claims: no marketing word the code cannot prove
    words = g["claims"]["words"]
    hits = []
    for f in sorted(SITE.glob("**/*.html")) + [PRODUCTS]:
        if "docs" in f.relative_to(root).parts[:2]:
            continue
        text = re.sub(r"<[^>]+>", " ", f.read_text("utf-8", "ignore")).lower()
        hits += [f"{f.relative_to(root)}: \"{w}\"" for w in words if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", text)]
    out.append(_r("claims", "fail" if hits else "pass", f"{len(hits)} unprovable word(s)" if hits else "none",
                  "; ".join(hits[:4]) if hits else "the site says only what the tests prove"))

    # 8. stop tests: a product past its kill_if date needs a decision
    due = []
    for pr in json.loads(PRODUCTS.read_text("utf-8"))["products"] if PRODUCTS.exists() else []:
        m = re.search(r"\d{4}-\d{2}-\d{2}", pr.get("kill_if", ""))
        if m and dt.date.fromisoformat(m.group(0)) < now:
            due.append(pr["id"])
    out.append(_r("stop-tests", "fail" if due else "pass", ", ".join(due) or "none due",
                  "decide each: stop, fold into another product, or show the evidence that it passed" if due else "every stop test is in the future"))

    # 9. platform shifts: reviewed every quarter (Nokia, RIM and Kodak saw the shift and defended the old margin)
    sh = json.loads(SHIFTS.read_text("utf-8"))
    stale = [s["id"] for s in sh["shifts"] if (now - dt.date.fromisoformat(s["reviewed"])).days > g["shift-watch"]["line"]]
    out.append(_r("shift-watch", "fail" if stale else "pass", f"{len(sh['shifts'])} shifts, {len(stale)} stale",
                  ("review: " + ", ".join(stale)) if stale else "each shift reviewed within the quarter"))
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    res = check()
    titles = {x["id"]: x["title"] for x in json.loads(GUARDS.read_text("utf-8"))["guards"]}
    if "--json" in argv:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        print("The monthly failure guards (doc 108): what broke others, checked against your numbers")
        for r in res:
            print(f"  {ICON[r['state']]:<10} {titles[r['id']]:<44} {r['value']}")
            if r["state"] != "pass":
                print(f"             {r['why']}")
    return 1 if any(r["state"] == "fail" for r in res) else 0


if __name__ == "__main__":
    sys.exit(main())
