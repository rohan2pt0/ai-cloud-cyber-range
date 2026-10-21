#!/usr/bin/env python3
"""Suite: every component built ready to be sold to everyone, from one person to a group of companies (doc 97).
One shared platform (identity, roles, audit, tenancy, policy, metering, export, residency, continuity) is built once;
every component declares the edition it starts in and the platform services it uses. The open core stays open.

    ./securax suite                        the editions, how ready each is to sell, the platform, and the gaps that block the most
    ./securax suite components             every component: its edition, the services it uses, its enterprise readiness
    ./securax suite sheet EDITION [--out F] a one-page datasheet for an edition: what is included today, what is on the way
    ./securax suite check                  every feature is declared and every claim has evidence (fitness runs this)
    ./securax suite json                   the same for a dashboard

A service counts as built only when the files that prove it exist. A datasheet lists as included only what is built:
partial and planned items appear under "on the way" with their date, so nothing is sold before it exists.
Standard library only. Exit codes: 0 ok, 1 check failed, 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUITE = ROOT / "governance" / "suite.json"
FEATURES = ROOT / "features.json"
STATUS = {"built": 1.0, "partial": 0.5, "planned": 0.0}


def load() -> dict:
    return json.loads(SUITE.read_text("utf-8"))


def features() -> dict:
    return {f["id"]: f for f in json.loads(FEATURES.read_text("utf-8"))["features"]}


def check(s: dict | None = None, feats: dict | None = None) -> list[str]:
    """Everything that would make the suite a claim on paper rather than a fact. Empty means sound."""
    s = s or load()
    feats = feats if feats is not None else features()
    svc, eds, comps, err = s["services"], {e["id"]: e for e in s["editions"]}, s["components"], []
    for fid in sorted(set(feats) - set(comps)):
        err.append(f"feature {fid} is not declared in governance/suite.json (its edition and the platform services it uses)")
    for cid in sorted(set(comps) - set(feats)):
        err.append(f"suite component {cid} is not a feature in features.json")
    for cid, c in comps.items():
        if c.get("from") not in eds:
            err.append(f"{cid}: edition {c.get('from')!r} is unknown")
        for u in c.get("uses", []):
            if u not in svc:
                err.append(f"{cid}: uses an unknown service {u!r}")
        if len(str(c.get("enterprise", ""))) < 15:
            err.append(f"{cid}: say in a sentence what the enterprise version adds")
    for sid, v in svc.items():
        if v.get("status") not in STATUS:
            err.append(f"service {sid}: status must be built, partial or planned")
        if v.get("open"):
            if v.get("status") in ("built", "partial") and not v.get("evidence"):
                err.append(f"service {sid}: a built or partial open service names the files that prove it")
            for f in v.get("evidence", []):
                if not (ROOT / f).exists():
                    err.append(f"service {sid}: evidence {f} does not exist")
        elif v.get("evidence"):
            err.append(f"service {sid}: commercial code lives in the private repository; it has no evidence in this public one")
        if v.get("status") != "built" and not (v.get("gap") and v.get("target")):
            err.append(f"service {sid}: name the gap and a target date")
    order = [e["id"] for e in s["editions"]]
    for a, b in zip(order, order[1:]):
        if not set(eds[a]["requires"]) <= set(eds[b]["requires"]):
            err.append(f"edition {b} must include everything {a} has")
    for r in eds[order[0]]["requires"]:   # what the free edition stands on must itself be open
        if r in svc and not svc[r]["open"]:
            err.append(f"the first edition needs {r}, which is closed: everything a person needs to be safe stays open")
    for must in ("identity", "export"):   # the open-core promise: no SSO tax, and your data always leaves with you
        if must not in eds[order[0]]["requires"] or not svc[must]["open"]:
            err.append(f"{must} must be open and in the first edition")
    for e in s["editions"]:
        for r in e["requires"]:
            if r not in svc:
                err.append(f"edition {e['id']}: requires an unknown service {r!r}")
    return err


def readiness(s: dict, uses: list[str]) -> float:
    return round(100 * sum(STATUS[s["services"][u]["status"]] for u in uses) / len(uses)) if uses else 100


def analyse(s: dict | None = None) -> dict:
    s = s or load()
    today = dt.date.today().isoformat()
    eds = []
    for e in s["editions"]:
        missing = [r for r in e["requires"] if s["services"][r]["status"] != "built"]
        eds.append({**e, "ready": readiness(s, e["requires"]), "sellable": not missing, "blocked_by": missing})
    blocks: dict[str, int] = {}
    for c in s["components"].values():
        for u in c["uses"]:
            if s["services"][u]["status"] != "built":
                blocks[u] = blocks.get(u, 0) + 1
    for e in eds:
        for u in e["blocked_by"]:
            blocks[u] = blocks.get(u, 0) + 5   # an edition it blocks weighs more than a component
    gaps = sorted(({"id": k, "weight": v, **s["services"][k], "overdue": s["services"][k].get("target", "9") < today} for k, v in blocks.items()),
                  key=lambda g: (-g["weight"], g.get("target", "9")))
    comps = {cid: {**c, "ready": readiness(s, c["uses"])} for cid, c in s["components"].items()}
    avg = round(sum(c["ready"] for c in comps.values()) / max(1, len(comps)))
    return {"editions": eds, "gaps": gaps, "components": comps, "average_ready": avg,
            "open": sum(1 for v in s["services"].values() if v["open"]), "services": len(s["services"])}


def rs(x) -> str:
    return "free" if not x else f"Rs {x:,} a user a month"


def report(a: dict, s: dict, say=print) -> None:
    say("THE SUITE: one platform, every component ready for one person or a group of companies (doc 97)\n")
    say("Editions, and how ready each is to sell")
    for e in a["editions"]:
        state = "ready" if e["sellable"] else "waits on " + ", ".join(e["blocked_by"])
        say(f"  {e['name']:<11} {rs(e['price']):<24} {e['ready']:>3}%  {state}")
        say(f"  {'':<11} for {e['who']}")
    say(f"\nThe shared platform ({a['open']} of {a['services']} services open source)")
    for sid, v in s["services"].items():
        mark = {"built": "✔", "partial": "◐", "planned": "·"}[v["status"]]
        say(f"  {mark} {sid:<13} {'open  ' if v['open'] else 'closed'} {v['name']}" + (f"  (by {v['target']})" if v["status"] != "built" else ""))
    say(f"\nComponents: {len(a['components'])}, on average {a['average_ready']}% enterprise-ready (share of the services each uses that are built)")
    say("\nThe gaps that unlock the most, first")
    for g in a["gaps"][:6]:
        say(f"  {g['id']:<13} by {g['target']}{'  OVERDUE' if g['overdue'] else ''}: {g['gap']}")
    say("\nNext: ./securax suite sheet business (a datasheet) · suite components · doc 97 for the open-core rules")


def sheet(a: dict, s: dict, ed_id: str) -> str:
    e = next(x for x in a["editions"] if x["id"] == ed_id)
    inc = [r for r in e["requires"] if s["services"][r]["status"] == "built"]
    way = [r for r in e["requires"] if s["services"][r]["status"] != "built"]
    lines = [f"# {e['name']} edition", "", f"**For:** {e['who']} ({e['seats']} seats). **Price:** {rs(e['price'])}, excluding GST (a price to test, not a quote).", "",
             "## Included today", ""]
    lines += [f"- {s['services'][r]['name']}" for r in inc] or ["- (nothing yet: see below)"]
    lines += ["", "## On the way", ""]
    lines += [f"- {s['services'][r]['name']}: by {s['services'][r]['target']}" for r in way] or ["- nothing: every part of this edition is built"]
    lines += ["", "## Every component, and what this edition adds", "", "| Component | Today | In larger editions |", "|---|---|---|"]
    feats = features()
    for cid, c in a["components"].items():
        lines.append(f"| {feats.get(cid, {}).get('name', cid)} | {c['ready']}% of its platform built | {c['enterprise']} |")
    lines += ["", "## The open-core promise", ""] + [f"- {p}" for p in s["open_core"]]
    lines += ["", f"_Generated by ./securax suite sheet {ed_id} on {dt.date.today().isoformat()} from governance/suite.json._", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax suite", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "components", "sheet", "check", "json"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    s = load()
    if a.cmd == "check":
        err = check(s)
        for e in err:
            print("✘ " + e)
        if not err:
            print(f"✔ {len(s['components'])} components declared; every built service is proven by its files; the open core holds")
        return 1 if err else 0
    res = analyse(s)
    if a.cmd == "json":
        print(json.dumps(res, indent=1))
        return 0
    if a.cmd == "components":
        feats = features()
        for cid, c in sorted(res["components"].items(), key=lambda kv: kv[1]["ready"]):
            print(f"  {c['ready']:>3}%  {feats.get(cid, {}).get('name', cid):<44} uses {', '.join(c['uses']) or '-'}")
        return 0
    if a.cmd == "sheet":
        ids = [e["id"] for e in s["editions"]]
        if not a.args or a.args[0] not in ids:
            print(f"usage: ./securax suite sheet {'|'.join(ids)} [--out FILE]", file=sys.stderr)
            return 2
        text = sheet(res, s, a.args[0])
        if a.out:
            pathlib.Path(a.out).write_text(text, "utf-8")
            print(f"✔ written: {a.out}")
        else:
            print(text)
        return 0
    report(res, s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
