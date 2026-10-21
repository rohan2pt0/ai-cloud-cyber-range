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
    ./securax govern org [--tier T] [--out F.svg]   the organogram: the CISO, a lead per function, how many under each
    ./securax govern map [--out F.svg]   every capability, layer by layer, coloured by where you stand
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
import re
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


def summary(a: dict, top: int = 5) -> dict:
    """The few numbers an executive app shows (Vantage reads this as portal/govern-state.json): no notes, no marks detail."""
    b = a["budget"]["basic"]["total"]
    return {"maturity": a["maturity"][0], "words": a["maturity"][1], "coverage": a["overall"], "at": dt.date.today().isoformat(),
            "budget": f"{money(*b)} a year for the minimum basic", "marked": a["marked"], "total": a["total"],
            "top": [{"what": g["name"], "who": g["owner"], "when": g["when"], "how_much": money(*g["cost_lh"]), "tier": g["tier"]} for g in a["gaps"][:top]]}


def write_state(a: dict | None = None) -> pathlib.Path | None:
    """Write portal/govern-state.json for the apps on this address. Never fails the caller."""
    out = pathlib.Path(os.environ.get("GOVERN_STATE_OUT") or ROOT / "portal" / "govern-state.json")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(summary(a or analyse()), indent=1), "utf-8")
        tmp.replace(out)
        return out
    except OSError:
        return None


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


# ------------------------------------------------------------------------------------------------------------ pictures
# The cockpit shows these as pictures, so a decision maker sees the shape at a glance and needs no command (doc 94, section 5).
SHORT = {"gov-policy": "Policy and standards", "gov-structure": "CISO, committee, RACI", "gov-risk": "Risk register", "gov-metrics": "KPIs and Board report", "gov-privacy": "DPDP programme", "gov-tprm": "Vendor risk", "gov-iso27001": "ISO 27001",
         "gov-iso22301": "ISO 22301", "gov-grc": "GRC platform", "gov-insurance": "Cyber insurance", "gov-ai": "AI governance",
         "ppl-team": "Core security team", "ppl-awareness": "Awareness, phishing tests", "ppl-training": "Training, certifications",
         "ppl-kt": "Knowledge transfer", "ppl-range": "Range exercises", "prc-inventory": "Asset inventory", "prc-classify": "Classification",
         "prc-vuln": "Vuln. SLAs", "prc-patch": "Patching", "prc-change": "Change, exceptions", "prc-access": "Access reviews",
         "prc-ir": "IR and crisis plan", "prc-backup": "Tested offline backups", "prc-sdlc": "Secure SDLC, API", "prc-vendor-sla": "Vendor scorecards",
         "prc-drills": "BCP / DR drills", "prc-ctem": "CTEM",
         "tec-ngfw": "Firewalls", "tec-email": "Email security", "tec-edr": "EDR", "tec-mfa": "MFA", "tec-vulnscan": "Vuln. scanning",
         "tec-logging": "Central logging", "tec-encryption": "Encryption", "tec-waf": "WAF", "tec-ddos": "Anti-DDoS", "tec-dns": "DNS security",
         "tec-nac": "NAC", "tec-mdm": "MDM", "tec-pam": "PAM", "tec-iam": "IAM / IGA", "tec-ad": "AD hardening", "tec-siem": "SIEM",
         "tec-soc": "24x7 SOC", "tec-sast": "SAST / DAST", "tec-asm": "Attack surface", "tec-ti": "Threat intel", "tec-dlp": "DLP",
         "tec-classify": "Data discovery", "tec-ztna": "ZTNA", "tec-ndr": "NDR", "tec-soar": "SOAR", "tec-ueba": "UEBA / XDR",
         "tec-bas": "Attack simulation", "tec-deception": "Deception", "tec-api": "API security", "tec-bot": "Bots / RASP", "tec-dam": "DAM / masking",
         "tec-drm": "DRM", "tec-forensics": "Forensics", "tec-pqc": "Quantum-safe"}
STACK = [("Governance", lambda c: c["domain"] == "governance"), ("People", lambda c: c["domain"] == "people"),
         ("Process", lambda c: c["domain"] == "process"),
         *[(label, (lambda a: lambda c: c["domain"] == "technology" and c["area"] == a)(area)) for area, label in (
             ("perimeter", "Perimeter"), ("network", "Network"), ("endpoint", "Endpoint"), ("identity", "Identity"),
             ("application", "Application"), ("data", "Data"), ("secops", "Security operations"), ("resilience", "Resilience"))]]
VERT = {"Governance, risk and compliance": "GRC", "Technical assurance": "Testing and assurance", "Security operations": "SOC", "Incident response": "Incident response"}
SVG_STYLE = ("<style>.t{font:12px system-ui,sans-serif;fill:var(--ink,#14202b)}.m{font:11px system-ui,sans-serif;fill:var(--mut,#5a6876)}"
             ".h{font:600 12px system-ui,sans-serif;fill:var(--ink,#14202b)}.box{fill:var(--card,#fff);stroke:var(--line,#c9d1da);stroke-width:1.2}"
             ".lead{stroke:var(--acc,#2554c7);stroke-width:2}.wire{stroke:var(--mut,#5a6876);stroke-width:1;fill:none}"
             ".done{fill:rgba(27,138,75,.16);stroke:var(--g,#1b8a4b)}.part{fill:rgba(183,121,31,.16);stroke:var(--a,#b7791f)}"
             ".miss{fill:var(--card,#fff);stroke:var(--r,#c0392b);stroke-dasharray:4 3}.later{fill:var(--card,#fff);stroke:var(--line,#c9d1da)}"
             ".band{fill:var(--bg,#f6f7f9)}</style>")


def short(c: dict) -> str:
    return SHORT.get(c["id"]) or re.split(r" \(|: | and | with ", c["name"])[0][:24]


def plan_tier(a: dict) -> str:
    """The tier being worked to: the first one not yet complete."""
    return next((t for t in TIERS if a["overall"][t] < 100), TIERS[-1])


def _lines(text: str, width: int) -> list[str]:
    words, out, cur = text.replace(" / ", "/ ").split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return (out + [cur])[:3]


def org_svg(a: dict | None = None, tier: str | None = None, standalone: bool = False) -> str:
    """The organogram for the tier being worked to: the CISO, a lead per function, and who works under each."""
    a = analyse() if a is None else a
    tier = tier or plan_tier(a)
    t = team(tier, a["profile"])
    E = html.escape
    leads = {"grc_lead", "architect", "test_lead", "tool_lead", "soc_manager", "ir_lead", "resilience_lead"}
    cols: dict[str, list[dict]] = {}
    for r in t:
        if r["id"] not in ("ciso", "pmo"):
            cols.setdefault(r["vertical"], []).append(r)
    W, colw = 1100, max(130, (1100 - 20) // max(1, len(cols)))
    W = max(W, 20 + colw * len(cols))
    rows = max((len(v) for v in cols.values()), default=0)
    H = 150 + rows * 80
    out = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='Organogram for the {tier} tier'>", SVG_STYLE]
    cx = W // 2
    ciso = next(r for r in t if r["id"] == "ciso")
    out.append(f"<rect class='box lead' x='{cx - 120}' y='10' width='240' height='46' rx='8'/><text class='h' x='{cx}' y='30' text-anchor='middle'>{E(ciso['name'].split(' / ')[0])}</text>"
               f"<text class='m' x='{cx}' y='47' text-anchor='middle'>owns cyber risk; reports to the Board</text>")
    pmo = next((r for r in t if r["id"] == "pmo"), None)
    if pmo:
        out.append(f"<path class='wire' d='M{cx + 120} 33 H{cx + 170}' stroke-dasharray='4 3'/><rect class='box' x='{cx + 170}' y='14' width='190' height='38' rx='8'/>"
                   f"<text class='t' x='{cx + 265}' y='37' text-anchor='middle'>{pmo['count']} × programme manager</text>")
    if cols:
        x0, x1 = 10 + colw // 2, 10 + colw * (len(cols) - 1) + colw // 2
        out.append(f"<path class='wire' d='M{cx} 56 V80 M{x0} 80 H{x1}'/>")
    for i, (vert, people) in enumerate(cols.items()):
        x = 10 + i * colw
        mid = x + colw // 2
        out.append(f"<path class='wire' d='M{mid} 80 V96'/><text class='h' x='{mid}' y='112' text-anchor='middle'>{E(VERT.get(vert, vert))}</text>")
        for k, r in enumerate(sorted(people, key=lambda r: r["id"] not in leads)):
            y = 122 + k * 80
            name = _lines(r["name"], max(14, (colw - 16) // 7))
            cls = "box lead" if r["id"] in leads else "box"
            out.append(f"<path class='wire' d='M{mid} {y - 10} V{y}'/><rect class='{cls}' x='{x + 6}' y='{y}' width='{colw - 12}' height='66' rx='8'/>"
                       f"<text class='h' x='{mid}' y='{y + 18}' text-anchor='middle'>{r['count']} ×</text>"
                       + "".join(f"<text class='t' x='{mid}' y='{y + 34 + n * 14}' text-anchor='middle'>{E(line)}</text>" for n, line in enumerate(name)))
    out.append("</svg>")
    svg = "".join(out)
    return _standalone(svg) if standalone else svg


def _standalone(svg: str) -> str:
    """A file of its own (for a deck): the namespace a file needs, which a page must not carry (the cockpit names no address)."""
    m = re.search(r"viewBox='0 0 (\d+) (\d+)'", svg)
    size = f"width='{m.group(1)}' height='{m.group(2)}' " if m else ""
    return "<?xml version='1.0' encoding='UTF-8'?>\n" + svg.replace("<svg ", f"<svg xmlns='http://www.w3.org/2000/svg' {size}", 1)


def stack_svg(a: dict | None = None, m: dict | None = None, standalone: bool = False) -> str:
    """Every capability, layer by layer: green in place, amber partly, red dashed a missing basic, grey a later tier."""
    a = analyse() if a is None else a
    m = marks() if m is None else m
    E = html.escape
    W, left, rows, y = 1100, 160, [], 10
    for label, pick in STACK:
        caps = [c for c in catalog()["capabilities"] if pick(c)]
        if not caps:
            continue
        chips, x, line = [], left, 0
        for c in sorted(caps, key=lambda c: (TIERS.index(c["tier"]), c["id"])):
            text = short(c) + ("" if c["tier"] == "basic" else " ·" + c["tier"][0].upper())
            w = 20 + int(7.0 * len(text))
            if x + w > W - 10:
                x, line = left, line + 1
            st = state(c["id"], m)
            cls = {"done": "done", "partial": "part"}.get(st, "miss" if c["tier"] == "basic" else "later")
            chips.append((x, line, w, cls, text, c["name"]))
            x += w + 6
        h = 34 + line * 30
        rows.append(f"<rect class='band' x='0' y='{y}' width='{W}' height='{h}' rx='6'/><text class='h' x='10' y='{y + 21}'>{E(label)}</text>"
                    + "".join(f"<g><title>{E(full)}</title><rect class='{cls}' x='{cx}' y='{y + 6 + ln * 30}' width='{w}' height='22' rx='11'/>"
                              f"<text class='t' x='{cx + w / 2:.0f}' y='{y + 21 + ln * 30}' text-anchor='middle'>{E(tx)}</text></g>" for cx, ln, w, cls, tx, full in chips))
        y += h + 6
    legend = (f"<g transform='translate(10,{y + 6})'><rect class='done' width='16' height='12' rx='6'/><text class='m' x='22' y='10'>in place</text>"
              "<rect class='part' x='100' width='16' height='12' rx='6'/><text class='m' x='122' y='10'>partly</text>"
              "<rect class='miss' x='190' width='16' height='12' rx='6'/><text class='m' x='212' y='10'>missing basic: first</text>"
              "<rect class='later' x='350' width='16' height='12' rx='6'/><text class='m' x='372' y='10'>later tier (·S standard, ·A advanced)</text></g>")
    svg = f"<svg viewBox='0 0 {W} {y + 26}' role='img' aria-label='Capabilities layer by layer'>{SVG_STYLE}{''.join(rows)}{legend}</svg>"
    return _standalone(svg) if standalone else svg


def _w5h_html(g: dict) -> str:
    E = html.escape
    w = w5h(g)
    tpl = f" <span class='muted'>Template: {E(g['template'])}</span>" if g.get("template") else ""
    return (f"<details class='gap'><summary><b>{E(g['name'])}</b> <span class='muted'>· {E(g['tier'])} · {E(g['owner'])} · "
            f"{E(g['when'])} · {E(money(*g['cost_lh']))}</span></summary><dl class='w5h'>"
            + "".join(f"<dt>{k}</dt><dd>{E(str(w[k]))}</dd>" for k in ("What", "Why", "Who", "When", "Where", "How", "How much")) + f"</dl>{tpl}</details>")


GOV_CSS = ("<style>#govern dl.w5h{display:grid;grid-template-columns:7em 1fr;gap:2px 10px;margin:.4rem 0 .6rem}#govern dt{color:var(--mut);font-weight:600}"
           "#govern dd{margin:0}#govern details.gap{border-bottom:1px solid var(--line);padding:6px 0}#govern details.sub{margin:.6rem 0}"
           "#govern details.sub>summary{font-size:1rem}#govern table{border-collapse:collapse;width:100%;font-size:.9rem}"
           "#govern td,#govern th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left}</style>")


def html_card(a: dict | None = None) -> str:
    """The Govern panel for the cockpit: folded to one line; open it and everything is there, with no command to run.
    No script, no external address (the cockpit's rule)."""
    a = analyse() if a is None else a
    E = html.escape
    lvl, words = a["maturity"]
    b, tier = a["budget"], plan_tier(a)
    t = team(tier, a["profile"])
    people = sum(r["count"] for r in t)
    top = a["gaps"][:10]
    basics_left = sum(1 for g in a["gaps"] if g["tier"] == "basic")
    summary = (f"<b>Govern</b> <span class='muted'>· maturity {lvl}/5 · minimum basic {a['overall']['basic']}% in place · "
               f"{basics_left} basic gap(s) · {E(money(*b['basic']['total']))} a year to reach it</span>")
    budget = "".join(f"<tr><td>{lbl}</td><td>{E(money(*b[k]['tools_process']))}</td><td>{E(money(*b[k]['people']))}</td><td><b>{E(money(*b[k]['total']))}</b></td></tr>"
                     for k, lbl in (("basic", "Minimum basic"), ("standard", "Standard"), ("advanced", "Highest possible")))
    note = "" if a["marked"] else "<p class='muted'>Nothing is marked yet, so every capability reads as missing. Mark what you have with <code>./securax govern mark ID done</code>.</p>"
    return (GOV_CSS + f"<details class='card panel' id='govern'><summary>{summary}</summary>"
            f"<p class='big'>Maturity level {lvl} of 5 <span class='muted'>· {E(words)}</span></p>{note}"
            f"<details class='sub' open><summary>The capability stack, layer by layer</summary>{stack_svg(a)}</details>"
            f"<details class='sub'><summary>The team for the {E(tier)} tier: {people} people ({E(money(sum(r['cost'][0] for r in t), sum(r['cost'][1] for r in t)))} a year)</summary>"
            f"{org_svg(a, tier)}<p class='muted'>Consultants can fill any box in year 1 and train the team that leads in year 2.</p></details>"
            f"<details class='sub'><summary>The next {len(top)} to do, most risk removed first (open one for its 5W1H)</summary>{''.join(_w5h_html(g) for g in top)}"
            f"<p class='muted'>{len(a['gaps'])} open in all; the full list is in the Board report.</p></details>"
            f"<details class='sub'><summary>What it costs, a year</summary><table><tr><th>To reach</th><th>Tools and process</th><th>People</th><th>Total</th></tr>{budget}</table>"
            "<p class='muted'>Indicative bands for India, October 2026; confirm each with three quotes (doc 94).</p></details>"
            "</details>")


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
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "profile", "mark", "list", "team", "board", "templates", "json", "org", "map"])
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
    if a.cmd in ("org", "map"):
        svg = org_svg(res, a.tier, standalone=True) if a.cmd == "org" else stack_svg(res, standalone=True)
        out = pathlib.Path(a.out or f"govern-{a.cmd}.svg")
        out.write_text(svg, "utf-8")
        print(f"✔ written: {out}  (open it in a browser, or drop it into the Board deck)")
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
    if write_state(res):
        print("  (Vantage, the CISO app, shows this summary too: http://localhost:8088/vantage/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
