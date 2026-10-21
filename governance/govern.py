#!/usr/bin/env python3
"""Govern: how the organisation is doing on governance, people, process and technology, what the minimum basic and the
highest possible look like, and what to do next with who, when and how much (doc 94). Built for decision makers.

    ./securax govern                       where we stand, per area; what closing the gaps costs; the top recommendations
    ./securax govern profile --users N --endpoints N --apps N --sites N [--coverage 24x7|business] [--org "Name"]
                                           your organisation's size (sizes the team and the budget; private, in vault/)
    ./securax govern mark ID done|partial|none [--note "what we did"]
                                           record where a capability stands (./securax govern list shows the IDs)
    ./securax govern list [--tier basic|standard|advanced]   every capability, its tier and its state
    ./securax govern team [--tier basic|standard|advanced]   the people you need: roles, how many, skills, certifications, cost
    ./securax govern board [--out FILE]    the one-page Board / executive report (Markdown), with the 5W1H for each gap
    ./securax govern templates [DIR] [--org "Name"]
                                           the template pack: policies, SOPs, registers, vision, executive deck, Board table

Tiers: basic = the minimum basic every organisation needs; standard = good practice for a regulated or mid-size one;
advanced = the highest level worth reaching. Each recommendation answers the 5W1H: What, Why, Who, When, Where, How,
and How much. Budgets are indicative bands for India (doc 94 has the sources); confirm every one with three quotes.
Your answers stay in vault/ (private, never committed). Standard library only. Exit codes: 0 ok, 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "governance" / "govern.json"
TEMPLATES = ROOT / "templates" / "govern"
TIERS = ("basic", "standard", "advanced")
TIER_W = {"basic": 3, "standard": 2, "advanced": 1}
STATE_W = {"done": 1.0, "partial": 0.5, "none": 0.0}
DOMAINS = ("governance", "people", "process", "technology")


def vault() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_VAULT_DIR") or ROOT / "vault")


def catalog() -> dict:
    return json.loads(CATALOG.read_text("utf-8"))


def _load(name: str, default):
    try:
        return json.loads((vault() / name).read_text("utf-8"))
    except (OSError, ValueError):
        return default


def _save(name: str, data) -> None:
    vault().mkdir(parents=True, exist_ok=True)
    p = vault() / name
    p.write_text(json.dumps(data, indent=1, ensure_ascii=False), "utf-8")
    try:
        p.chmod(0o600)
    except OSError:
        pass


def marks() -> dict:
    return _load("govern.json", {})


def profile() -> dict:
    return {**catalog()["reference_org"], **_load("govern-profile.json", {})}


def state(cid: str, m: dict | None = None) -> str:
    return ((m if m is not None else marks()).get(cid) or {}).get("state", "none")


# ------------------------------------------------------------------------------------------------------------ money
def cost(c: dict, prof: dict) -> tuple[float, float]:
    """Indicative Rs lakh per year for one capability at this organisation's size."""
    k = c.get("cost", {})
    lo, hi = k.get("fixed", [0, 0])
    for unit, n in (("per_endpoint", prof["endpoints"]), ("per_user", prof["users"])):
        if unit in k:
            lo += k[unit][0] * n / 1e5
            hi += k[unit][1] * n / 1e5
    return round(lo, 1), round(hi, 1)


def money(lo: float, hi: float) -> str:
    def one(x: float) -> str:
        return f"{x / 100:.1f} Cr" if x >= 100 else f"{x:.0f} L"
    return "Rs 0" if hi <= 0 else f"Rs {one(lo)} - {one(hi)}"


# ------------------------------------------------------------------------------------------------------------ people
def team(tier: str, prof: dict) -> list[dict]:
    """How many people of each role, for this size and tier. The rules are plain ratios, shown in doc 94."""
    users, eps, apps = prof["users"], prof["endpoints"], prof["apps"]
    lvl = TIERS.index(tier)
    seats = max(1, math.ceil(eps / 5000))
    in_house_24x7 = prof.get("coverage", "24x7") == "24x7" and lvl == 2
    n = {
        "ciso": 1,
        "grc_lead": 1,
        "grc_analyst": max(1, math.ceil(users / (2500, 2000, 1500)[lvl])),
        "architect": (0, 1, max(1, math.ceil(apps / 40)))[lvl],
        "test_lead": (0, 1, 1)[lvl],
        "tester": max(1, math.ceil(apps / (40, 20, 12)[lvl])),
        "tool_lead": (0, 1, 1)[lvl],
        "engineer": max(1, math.ceil(eps / (3000, 2000, 1500)[lvl])),
        "soc_manager": (0, 1, 1)[lvl],
        "soc_l2": (1, max(2, 2 * seats), 2 * seats + 1)[lvl],
        "soc_l1": 5 * seats if in_house_24x7 else 0,
        "ir_lead": (0, 1, 1)[lvl],
        "dfir": (0, 0, max(1, math.ceil(eps / 5000)))[lvl],
        "resilience_lead": (0, 1, 1)[lvl],
    }
    n["pmo"] = 1 if lvl >= 1 and sum(n.values()) >= 8 else 0
    roles = {r["id"]: r for r in catalog()["roles"]}
    out = []
    for rid, count in n.items():
        if count:
            r = roles[rid]
            out.append({**r, "count": count, "cost": (round(count * r["lpa"][0], 1), round(count * r["lpa"][1], 1))})
    return out


# ------------------------------------------------------------------------------------------------------------ analysis
def analyse(m: dict | None = None, prof: dict | None = None) -> dict:
    m = marks() if m is None else m
    prof = profile() if prof is None else prof
    caps = catalog()["capabilities"]
    cov = {d: {t: [0.0, 0] for t in TIERS} for d in DOMAINS}
    for c in caps:
        cov[c["domain"]][c["tier"]][0] += STATE_W[state(c["id"], m)]
        cov[c["domain"]][c["tier"]][1] += 1
    pct = {d: {t: (round(100 * v[0] / v[1]) if v[1] else 100) for t, v in tiers.items()} for d, tiers in cov.items()}
    overall = {t: round(100 * sum(STATE_W[state(c["id"], m)] for c in caps if c["tier"] == t) /
                        max(1, sum(1 for c in caps if c["tier"] == t))) for t in TIERS}
    gaps = []
    for c in caps:
        s = state(c["id"], m)
        if s == "done":
            continue
        gap = 1 - STATE_W[s]
        lo, hi = cost(c, prof)
        gaps.append({**c, "state": s, "priority": round(c["impact"] * TIER_W[c["tier"]] * gap, 2),
                     "when": catalog()["phases"][c["tier"]], "cost_lh": (round(lo * gap, 1), round(hi * gap, 1))})
    gaps.sort(key=lambda g: (-g["priority"], TIERS.index(g["tier"]), g["id"]))
    budget = {}
    for t in TIERS:
        upto = TIERS[: TIERS.index(t) + 1]
        lo = sum(g["cost_lh"][0] for g in gaps if g["tier"] in upto)
        hi = sum(g["cost_lh"][1] for g in gaps if g["tier"] in upto)
        people = (0.0, 0.0) if state("ppl-team", m) == "done" else tuple(sum(r["cost"][i] for r in team(t, prof)) for i in (0, 1))
        budget[t] = {"tools_process": (round(lo, 1), round(hi, 1)), "people": (round(people[0], 1), round(people[1], 1)),
                     "total": (round(lo + people[0], 1), round(hi + people[1], 1))}
    return {"coverage": pct, "overall": overall, "maturity": maturity(overall), "gaps": gaps, "budget": budget, "profile": prof,
            "marked": sum(1 for c in caps if c["id"] in m), "total": len(caps)}


def maturity(o: dict) -> tuple[int, str]:
    if o["basic"] < 60:
        return 1, "Initial: the minimum basics are not yet in place"
    if o["basic"] < 100:
        return 2, "Developing: most basics are in place; finish them first"
    if o["standard"] < 60:
        return 3, "Defined: all basics done; good practice under way"
    if o["advanced"] < 40:
        return 4, "Managed: good practice in place; leading practice next"
    return 5, "Optimised: leading practice in place; keep it tested"


def w5h(g: dict) -> dict:
    return {"What": g["name"], "Why": g["why"], "Who": g["owner"], "When": f"{g['when']} ({g['tier']})", "Where": g["area"],
            "How": g["how"] + (f" (template: {g['template']})" if g.get("template") else ""), "How much": money(*g["cost_lh"]) + " a year"}


# ------------------------------------------------------------------------------------------------------------ outputs
def report(a: dict, say=print, top: int = 7) -> None:
    lvl, words = a["maturity"]
    p = a["profile"]
    say(f"GOVERN · {p.get('org', 'your organisation')}: {p['users']} users, {p['endpoints']} endpoints, {p['apps']} applications\n")
    say(f"Maturity: level {lvl} of 5. {words}.")
    if a["marked"] == 0:
        say("  (Nothing is marked yet, so everything reads as missing. Mark what you have:  ./securax govern list  then  govern mark ID done)")
    say(f"  Minimum basic: {a['overall']['basic']}% in place · standard: {a['overall']['standard']}% · highest possible: {a['overall']['advanced']}%\n")
    say(f"  {'area':<12} {'basic':>6} {'standard':>9} {'advanced':>9}")
    for d in DOMAINS:
        c = a["coverage"][d]
        say(f"  {d:<12} {c['basic']:>5}% {c['standard']:>8}% {c['advanced']:>8}%")
    say("\nWhat it costs to close the gaps (a year, indicative, India; confirm with 3 quotes)")
    for t, label in (("basic", "Minimum basic"), ("standard", "Standard"), ("advanced", "Highest possible")):
        b = a["budget"][t]
        say(f"  {label:<17} {money(*b['total']):>22}  (tools and process {money(*b['tools_process'])}; people {money(*b['people'])})")
    say(f"\nThe top {top} recommendations (5W1H), most risk removed first")
    for i, g in enumerate(a["gaps"][:top], 1):
        w = w5h(g)
        say(f"  {i}. {w['What']}  [{g['tier']}, {g['state']}]")
        for k in ("Why", "Who", "When", "How", "How much"):
            say(f"       {k}: {w[k]}")
    say("\nNext: ./securax govern team (who you need) · govern board (the one-page report) · govern templates (policies, SOPs, deck)")


def board(a: dict, top: int = 10) -> str:
    p, (lvl, words) = a["profile"], a["maturity"]
    today = dt.date.today().isoformat()
    L = [f"# Information security: where we stand and what we need ({p.get('org', 'our organisation')}, {today})", "",
         "## 1. In one line",
         f"Maturity level **{lvl} of 5**: {words}. The minimum basics are **{a['overall']['basic']}%** in place; good practice "
         f"**{a['overall']['standard']}%**; leading practice **{a['overall']['advanced']}%**.", "",
         "## 2. Where we stand", "", "| Area | Minimum basic | Standard | Highest possible |", "|---|---|---|---|"]
    L += [f"| {d.title()} | {a['coverage'][d]['basic']}% | {a['coverage'][d]['standard']}% | {a['coverage'][d]['advanced']}% |" for d in DOMAINS]
    L += ["", "## 3. What it takes (a year, indicative, to be confirmed by quotes)", "",
          "| Target | Tools and process | People | Total |", "|---|---|---|---|"]
    for t, label in (("basic", "Minimum basic"), ("standard", "Standard"), ("advanced", "Highest possible")):
        b = a["budget"][t]
        L.append(f"| {label} | {money(*b['tools_process'])} | {money(*b['people'])} | **{money(*b['total'])}** |")
    L += ["", f"## 4. The top {top} actions (5W1H)", "", "| # | What | Why | Who | When | Where | How | How much |", "|---|---|---|---|---|---|---|---|"]
    for i, g in enumerate(a["gaps"][:top], 1):
        w = w5h(g)
        L.append(f"| {i} | {w['What']} | {w['Why']} | {w['Who']} | {w['When']} | {w['Where']} | {w['How']} | {w['How much']} |")
    t = team("standard", p)
    L += ["", "## 5. The team good practice needs", "", "| Role | How many | Key skills | Certifications |", "|---|---|---|---|"]
    L += [f"| {r['name']} | {r['count']} | {r['skills']} | {r['certs']} |" for r in t]
    L += [f"| **Total** | **{sum(r['count'] for r in t)}** | | |", "",
          "## 6. What we ask of management", "",
          "- Approve the minimum-basic budget and the team plan.", "- Name business owners for the top risks and their dates.",
          "- Back the policies and the exception rule: every exception has an owner and an end date.",
          "- Join one tabletop exercise a year.", "",
          "_Prepared with SecuRAX Govern. Figures are indicative bands for India; each needs three quotes before approval._", ""]
    return "\n".join(L)


def html_card(a: dict | None = None) -> str:
    """The Govern card for the Command Center cockpit: no script, no external address."""
    a = analyse() if a is None else a
    E = html.escape
    lvl, words = a["maturity"]
    bars = "".join(
        f"<tr><td>{E(d.title())}</td>" + "".join(f"<td><div class='bar{' low' if a['coverage'][d][t] < 60 else ''}' style='width:{max(a['coverage'][d][t], 2)}%'></div>"
                                                 f"<span class='muted'>{a['coverage'][d][t]}%</span></td>" for t in TIERS) + "</tr>"
        for d in DOMAINS)
    rows = "".join(f"<tr><td><b>{E(g['name'])}</b><br><span class='muted'>{E(g['why'])}</span></td><td>{E(g['owner'])}</td>"
                   f"<td>{E(g['when'])}</td><td>{E(money(*g['cost_lh']))}</td></tr>" for g in a["gaps"][:5])
    b = a["budget"]
    return ("<div class='card' id='govern'><h2>Govern <span class='muted'>· for decision makers: where we stand, the minimum "
            "basic and the highest possible, and what it takes</span></h2>"
            f"<p class='big'>Maturity level {lvl} of 5</p><p class='muted'>{E(words)}.</p>"
            "<table><tr><th>Area</th><th>Minimum basic</th><th>Standard</th><th>Highest possible</th></tr>" + bars + "</table>"
            f"<p>To reach the <b>minimum basic</b>: {E(money(*b['basic']['total']))} a year. To reach the <b>highest possible</b>: "
            f"{E(money(*b['advanced']['total']))} a year <span class='muted'>(indicative, India, people included; confirm with "
            "three quotes)</span>.</p>"
            "<h3>Next five, most risk removed first</h3><table><tr><th>What and why</th><th>Who</th><th>When</th><th>How much a year</th></tr>"
            + rows + "</table><p class='muted'>The full 5W1H, the team plan and the one-page Board report: "
            "<code>./securax govern</code>, <code>govern team</code>, <code>govern board</code>. Policies, SOPs, registers and the "
            "executive deck: <code>./securax govern templates</code>.</p></div>")


def templates(dest: pathlib.Path, org: str) -> list[pathlib.Path]:
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    for f in sorted(TEMPLATES.iterdir()):
        if f.is_file():
            target = dest / f.name
            if target.exists():                        # never overwrite a copy someone has already edited
                continue
            text = f.read_text("utf-8").replace("{{ORG}}", org).replace("{{DATE}}", dt.date.today().isoformat())
            target.write_text(text, "utf-8")
            out.append(target)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="govern", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "profile", "mark", "list", "team", "board", "templates", "json"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--users", type=int)
    ap.add_argument("--endpoints", type=int)
    ap.add_argument("--apps", type=int)
    ap.add_argument("--sites", type=int)
    ap.add_argument("--coverage", choices=["24x7", "business"])
    ap.add_argument("--org")
    ap.add_argument("--tier", choices=TIERS, default=None)
    ap.add_argument("--note", default="")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    caps = {c["id"]: c for c in catalog()["capabilities"]}
    if a.cmd == "profile":
        p = _load("govern-profile.json", {})
        for k in ("users", "endpoints", "apps", "sites", "coverage", "org"):
            if getattr(a, k) is not None:
                p[k] = getattr(a, k)
        _save("govern-profile.json", p)
        print("✔ saved (private, vault/govern-profile.json): " + ", ".join(f"{k}={v}" for k, v in {**catalog()['reference_org'], **p}.items()))
        return 0
    if a.cmd == "mark":
        if len(a.args) != 2 or a.args[0] not in caps or a.args[1] not in STATE_W:
            print("usage: ./securax govern mark ID done|partial|none [--note \"...\"]   (IDs: ./securax govern list)")
            return 2
        m = marks()
        m[a.args[0]] = {"state": a.args[1], "note": a.note, "at": dt.date.today().isoformat()}
        _save("govern.json", m)
        print(f"✔ {caps[a.args[0]]['name']}: {a.args[1]}")
        return 0
    if a.cmd == "list":
        m = marks()
        for c in catalog()["capabilities"]:
            if a.tier and c["tier"] != a.tier:
                continue
            s = state(c["id"], m)
            print(f"  {'✔' if s == 'done' else ('◐' if s == 'partial' else '·')} {c['id']:<15} {c['tier']:<9} {c['domain']:<11} {c['name']}")
        return 0
    if a.cmd == "team":
        tier = a.tier or "standard"
        t = team(tier, profile())
        print(f"THE TEAM for the {tier} tier ({profile()['users']} users, {profile()['endpoints']} endpoints, {profile()['apps']} apps)\n")
        for r in t:
            print(f"  {r['count']:>2} x {r['name']:<40} Rs {r['lpa'][0]}-{r['lpa'][1]} LPA each")
            print(f"       skills: {r['skills']}\n       certifications: {r['certs']}")
        lo, hi = sum(r["cost"][0] for r in t), sum(r["cost"][1] for r in t)
        print(f"\n  {sum(r['count'] for r in t)} people, {money(lo, hi)} a year (salary bands from 2026 Indian surveys; doc 94)")
        print("  Consultants can fill any role in year 1, with a knowledge-transfer plan so the internal team leads by year 2.")
        return 0
    res = analyse()
    if a.cmd == "json":
        print(json.dumps(res, indent=1, default=list))
        return 0
    if a.cmd == "board":
        text = board(res)
        if a.out:
            pathlib.Path(a.out).write_text(text, "utf-8")
            print(f"✔ written: {a.out}")
        else:
            print(text)
        return 0
    if a.cmd == "templates":
        dest = pathlib.Path(a.args[0]) if a.args else vault() / "govern-templates"
        made = templates(dest, a.org or profile().get("org") or "[Organisation name]")
        print(f"✔ {len(made)} template(s) in {dest}" + ("" if made else " (all were already there; edited copies are never overwritten)"))
        for f in made:
            print("    " + f.name)
        return 0
    report(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
