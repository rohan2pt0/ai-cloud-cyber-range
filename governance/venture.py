#!/usr/bin/env python3
"""Venture: is the estate paying its way, and when will it? Break-even, payback and unit economics for the business built on
SecuRAX (doc 96), counting your TIME as a real cost, not only your money. Your numbers stay in vault/ (private).

    ./securax venture                         invested so far, break-even, payback month, unit economics, what must be true
    ./securax venture log time HOURS "what"   log hours you put in (valued at your hour_value)
    ./securax venture log money RS "what"     log money you spent (machines, domains, models, tools)
    ./securax venture log revenue RS "what"   log money that came in
    ./securax venture plan KEY=VALUE ...      set your assumptions, for example
                                              hour_value=2000 hours_month=40 growth=300 tiers.pro.price=1499 tiers.pro.conv_pct=1.5
    ./securax venture ask                     a structured prompt that makes an AI stress-test the plan (a pre-mortem)
    ./securax venture json                    the same numbers for a dashboard

The model is deliberately simple and explainable. Each month: free users grow by `growth`; each paid tier converts conv_pct% of the
new free users at `cac` each; paid users churn churn_pct% a month; each paid user earns price less var (its contribution margin).
Cash profit = margins - fixed_month - acquisition. Economic profit also takes off your hours_month at hour_value.
Break-even: the month cash profit turns positive. Payback: the month the running total, starting from everything you have
invested so far (money + time), turns positive. Standard library only. Exit codes: 0 ok, 2 bad usage.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULTS = ROOT / "governance" / "venture.json"


def vault() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_VAULT_DIR") or ROOT / "vault")


def _mine() -> dict:
    p = vault() / "venture.json"
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save(d: dict) -> None:
    p = vault() / "venture.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1), "utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(p)


def plan() -> dict:
    """Public example defaults, overlaid by your own plan (deep merge)."""
    base = json.loads(DEFAULTS.read_text("utf-8"))["plan"]

    def merge(a, b):
        for k, v in b.items():
            a[k] = merge(a.get(k, {}), v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
        return a
    return merge(copy.deepcopy(base), _mine().get("plan", {}))


def ledger() -> dict:
    log = _mine().get("log", [])
    p = plan()
    hours = sum(e["amount"] for e in log if e["kind"] == "time")
    money = sum(e["amount"] for e in log if e["kind"] == "money")
    revenue = sum(e["amount"] for e in log if e["kind"] == "revenue")
    return {"hours": hours, "time_value": hours * p["hour_value"], "money": money, "revenue": revenue,
            "invested": hours * p["hour_value"] + money - revenue, "entries": len(log)}


def units(p: dict) -> dict:
    out = {}
    churn = max(p["churn_pct"], 0.01) / 100
    for tid, t in p["tiers"].items():
        cm = t["price"] - t["var"]
        out[tid] = {"name": t["name"], "cm": cm, "ltv": round(cm / churn) if cm > 0 else 0,
                    "ltv_cac": round(cm / churn / t["cac"], 1) if t["cac"] and cm > 0 else None,
                    "payback_months": round(t["cac"] / cm, 1) if cm > 0 and t["cac"] else (0 if cm > 0 else None)}
    return out


def project(p: dict, start: float = 0.0) -> list[dict]:
    """Month by month. `start` is what is already invested (a negative running total to earn back)."""
    churn = p["churn_pct"] / 100
    paid = {t: 0.0 for t in p["tiers"] if p["tiers"][t]["price"] > 0}
    free, run_cash, run_econ, rows = 0.0, 0.0, -start, []
    for m in range(1, int(p["months"]) + 1):
        free += p["growth"]
        new = {t: p["growth"] * p["tiers"][t]["conv_pct"] / 100 for t in paid}
        for t in paid:
            paid[t] = paid[t] * (1 - churn) + new[t]
        margin = sum(paid[t] * (p["tiers"][t]["price"] - p["tiers"][t]["var"]) for t in paid)
        acq = sum(new[t] * p["tiers"][t]["cac"] for t in paid)
        cash = margin - p["fixed_month"] - acq
        econ = cash - p["hours_month"] * p["hour_value"]
        run_cash += cash
        run_econ += econ
        rows.append({"m": m, "free": round(free), "paid": {t: round(v, 1) for t, v in paid.items()}, "revenue": round(sum(paid[t] * p["tiers"][t]["price"] for t in paid)),
                     "cash": round(cash), "econ": round(econ), "run_econ": round(run_econ), "run_cash": round(run_cash)})
    return rows


def breakeven_users(p: dict) -> dict:
    """Paid users needed each month to cover fixed costs (and also your time), at the plan's tier mix."""
    tiers = {t: v for t, v in p["tiers"].items() if v["price"] > 0}
    w = sum(v["conv_pct"] for v in tiers.values()) or 1
    cm = sum(v["conv_pct"] / w * (v["price"] - v["var"]) for v in tiers.values())
    if cm <= 0:
        return {"cm_mix": cm, "cash": None, "with_time": None, "free_needed": None}
    cash = p["fixed_month"] / cm
    with_time = (p["fixed_month"] + p["hours_month"] * p["hour_value"]) / cm
    # paid users settle where new conversions equal churn: paid = new_free_a_month x conversion / churn
    conv, churn = w / 100, max(p["churn_pct"], 0.01) / 100
    return {"cm_mix": round(cm), "cash": round(cash, 1), "with_time": round(with_time, 1),
            "free_needed": round(with_time * churn / conv) if conv else None}


def analyse() -> dict:
    p, led = plan(), ledger()
    rows = project(p, led["invested"])
    be = next((r["m"] for r in rows if r["cash"] >= 0), None)
    be_time = next((r["m"] for r in rows if r["econ"] >= 0), None)
    pay = next((r["m"] for r in rows if r["run_econ"] >= 0), None)
    return {"plan": p, "ledger": led, "units": units(p), "users": breakeven_users(p), "breakeven_month": be,
            "breakeven_with_time_month": be_time, "payback_month": pay, "rows": rows, "examples": not _mine().get("plan")}


def rs(x: float) -> str:
    x = float(x)
    if abs(x) >= 1e7:
        return f"Rs {x / 1e7:.2f} Cr"
    if abs(x) >= 1e5:
        return f"Rs {x / 1e5:.1f} L"
    return f"Rs {x:,.0f}"


def leverage() -> dict | None:
    """How far one kit stretches: modules, apps built from it, and module uses across them (the 'same system, many apps' number)."""
    try:
        sys.path.insert(0, str(ROOT / "governance"))
        import oskit
        apps = [e for e in oskit.editions().values() if not e.get("template")]
        return {"modules": len(oskit.MODULES), "apps": len(apps) + 1,   # + the Life OS, the first app of the family
                "uses": sum(len(e.get("modules") or {}) for e in apps)}
    except Exception:  # noqa: BLE001 - a convenience line must never fail the report
        return None


def must_be_true(a: dict) -> list[str]:
    p, out = a["plan"], []
    for tid, u in a["units"].items():
        t = p["tiers"][tid]
        if t["price"] <= 0:
            continue
        if u["cm"] <= 0:
            out.append(f"{t['name']}: the price does not cover its own running cost. Raise the price or cut what each user costs.")
        elif u["ltv_cac"] is not None and u["ltv_cac"] < 3:
            out.append(f"{t['name']}: a customer is worth {u['ltv_cac']}x what it costs to win one; aim for 3x or more (lower churn, cheaper acquisition, or a higher price).")
    if a["breakeven_month"] is None:
        out.append(f"No cash break-even within {p['months']} months at these numbers. The quickest lever is usually the paid tier's price or conversion, not more free users.")
    if a["breakeven_month"] is not None and a["breakeven_with_time_month"] is None:
        u = a["users"]
        if p["growth"] < u["free_needed"]:
            out.append(f"It covers its costs but never your time at {p['growth']:g} new free users a month: it needs about {u['free_needed']:,}. "
                       "Grow faster (a partner channel), convert better, or put fewer hours in each month.")
        else:
            out.append(f"It covers its costs, and would cover your time once about {u['with_time']:g} people pay, but churn of {p['churn_pct']:g}% a month "
                       f"keeps the paid base from getting there within {p['months']} months. Cutting churn or raising conversion gets there fastest.")
    if a["ledger"]["entries"] == 0:
        out.append("Nothing logged yet: log your hours and spend (venture log time 2 \"...\") so payback counts what you really put in.")
    return out


def report(a: dict, say=print) -> None:
    p, led, u = a["plan"], a["ledger"], a["users"]
    say("VENTURE: is the estate paying its way? (doc 96)" + ("   [example numbers: set yours with ./securax venture plan KEY=VALUE]" if a["examples"] else ""))
    say(f"\nPut in so far: {led['hours']:g} hours (worth {rs(led['time_value'])} at {rs(p['hour_value'])}/hour) + {rs(led['money'])} spent"
        f" - {rs(led['revenue'])} earned = {rs(led['invested'])} to earn back")
    say("\nUnit economics (a month, per paid user; prices exclude GST)")
    for tid, x in a["units"].items():
        t = p["tiers"][tid]
        if t["price"] <= 0:
            say(f"  {t['name']}: free; costs you {rs(t['var'])} a user")
            continue
        say(f"  {t['name']}\n     price {rs(t['price'])}, margin {rs(x['cm'])}, worth {rs(x['ltv'])} over a lifetime, "
            f"LTV:CAC {x['ltv_cac'] if x['ltv_cac'] is not None else '-'}, acquisition paid back in {x['payback_months']} month(s)")
    if u["cash"] is not None:
        say(f"\nBreak-even: {u['cash']:g} paying users cover the running costs ({rs(p['fixed_month'])}/month); "
            f"{u['with_time']:g} also pay for your {p['hours_month']:g} hours a month. At your conversion and churn that needs about {u['free_needed']:,} new free users a month, kept up.")
    def when(m):
        return f"in month {m}" if m else f"not within {p['months']} months"
    say(f"  Projected: cash break-even {when(a['breakeven_month'])}; paying for your time too {when(a['breakeven_with_time_month'])}; "
        f"everything you put in is back {when(a['payback_month'])}.")
    last = a["rows"][-1]
    say(f"  After {p['months']} months: {last['free']:,} free users, " + ", ".join(f"{round(v)} {k}" for k, v in last["paid"].items()) + f", {rs(last['revenue'])} a month in revenue.")
    mt = must_be_true(a)
    if mt:
        say("\nWhat must be true (fix these first)")
        for m in mt:
            say("  - " + m)
    lev = leverage()
    if lev:
        say(f"\nPlatform leverage: {lev['modules']} kit modules power {lev['apps']} app(s) ({lev['uses']} module uses); a new app is one JSON file (./securax os new).")
    say("Dual use: every part of the estate earns twice; see doc 96 or ./securax venture json")
    say("\nNext: log as you go (venture log time|money|revenue) · stress-test it with an AI: ./securax venture ask")


ASK = """ROLE: You are a sceptical venture investor and an Indian chartered accountant reviewing a bootstrapped software business.
CONTEXT (all figures in Indian rupees, a month unless stated; prices exclude 18% GST):
{context}
THE MODEL: free users grow by a fixed number a month; each paid tier converts a share of new free users at a cost (CAC);
paid users churn a fixed share a month; profit = margins - fixed costs - acquisition; the founder's time is valued at the hour rate.
TASK:
1. Pre-mortem: it is three years from now and this failed. Give the five most likely reasons, most likely first.
2. For each assumption (price, conversion, churn, CAC, growth, costs), say if it is optimistic, fair or conservative for India, and why.
3. Name the three cheapest experiments (under Rs 10,000 and four weeks each) that would prove or kill the riskiest assumptions.
4. What would make it break even sooner without more money: pricing, packaging, a partner channel or a different first customer?
CONSTRAINTS: say "unknown" rather than invent a fact or a figure; mark any benchmark you use with where it comes from; no generic advice.
OUTPUT: four numbered sections; tables where they help; at most 400 words."""


def ask_prompt(a: dict) -> str:
    p, u = a["plan"], a["users"]
    lines = [f"- invested so far: {rs(a['ledger']['invested'])} (time valued at {rs(p['hour_value'])}/hour)",
             f"- fixed costs {rs(p['fixed_month'])}; founder time {p['hours_month']:g} hours; free users added {p['growth']:g}; churn {p['churn_pct']:g}%"]
    for t in p["tiers"].values():
        if t["price"] <= 0:
            lines.append(f"- free tier '{t['name']}': costs {rs(t['var'])} a user to serve")
            continue
        lines.append(f"- tier '{t['name']}': price {rs(t['price'])}, cost per user {rs(t['var'])}, conversion {t['conv_pct']:g}% of new free users, CAC {rs(t['cac'])}")
    lines.append(f"- result: break-even at {u['cash']} paying users; cash break-even month {a['breakeven_month']}; payback month {a['payback_month']}")
    return ASK.format(context="\n".join(lines))


def _coerce(v: str):
    try:
        return float(v) if "." in v else int(v)
    except ValueError:
        return v


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax venture", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "log", "plan", "ask", "json"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "log":
        if len(a.args) < 2 or a.args[0] not in ("time", "money", "revenue"):
            print('usage: ./securax venture log time|money|revenue AMOUNT "what"', file=sys.stderr)
            return 2
        try:
            amt = float(a.args[1])
        except ValueError:
            print("the amount must be a number (hours for time, rupees for money and revenue)", file=sys.stderr)
            return 2
        if amt < 0:
            print("the amount must not be negative", file=sys.stderr)
            return 2
        d = _mine()
        d.setdefault("log", []).append({"d": dt.date.today().isoformat(), "kind": a.args[0], "amount": amt, "what": " ".join(a.args[2:])[:200]})
        d["log"] = d["log"][-5000:]   # bounded: years of daily entries
        _save(d)
        print(f"✔ logged {a.args[0]} {amt:g} (private, vault/venture.json)")
        return 0
    if a.cmd == "plan":
        if not a.args:
            print(json.dumps(plan(), indent=1))
            return 0
        d = _mine()
        known, tier_keys = plan(), {"name", "price", "var", "conv_pct", "cac"}
        for kv in a.args:
            k, eq, v = kv.partition("=")
            path = k.split(".")
            if not eq:
                print(f"{kv!r}: use KEY=VALUE, for example tiers.pro.price=1499", file=sys.stderr)
                return 2
            # a top-level number, or tiers.<any tier name>.<one of the tier's settings>
            fine = (len(path) == 1 and path[0] in known and path[0] != "tiers") or (len(path) == 3 and path[0] == "tiers" and path[1] and path[2] in tier_keys)
            if not fine:
                print(f"unknown setting {k!r}. See ./securax venture plan", file=sys.stderr)
                return 2
            node = d.setdefault("plan", {})
            for part in path[:-1]:
                node = node.setdefault(part, {})
            node[path[-1]] = v if path[-1] == "name" else _coerce(v)
            if path[0] == "tiers" and path[1] not in known["tiers"]:
                node.setdefault("name", path[1].capitalize())
                for tk in ("price", "var", "conv_pct", "cac"):
                    node.setdefault(tk, 0)
        _save(d)
        print("✔ plan saved (private, vault/venture.json)")
        return 0
    res = analyse()
    if a.cmd == "json":
        out = {k: v for k, v in res.items() if k != "rows"} | {"rows": res["rows"][:: max(1, len(res["rows"]) // 12)]}
        out["dual_use"] = json.loads(DEFAULTS.read_text("utf-8"))["dual_use"]
        out["leverage"] = leverage()
        print(json.dumps(out, indent=1))
        return 0
    if a.cmd == "ask":
        print(ask_prompt(res))
        print("\n(Paste it into the estate's chat, or any AI. The prompt asks for facts it cannot check to be marked unknown.)", file=sys.stderr)
        return 0
    report(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
