#!/usr/bin/env python3
"""Regulatory gap assessment — RBI NBFC Directions 2026 and SEBI CSCRF against what this estate DEMONSTRATES.

    ./securax comply                 both, summary
    ./securax comply rbi|cscrf       one regulation, per-requirement table (--md for markdown, --json for machines)
    ./securax comply cscrf --category qre    only what applies to that SEBI category (mii|qre|mid|small|self)
    ./securax comply --verify        consistency only (also part of ./securax verify, ./securax fitness and the evidence pack)

Read this before quoting a number
---------------------------------
* A software estate cannot be "100% compliant". Compliance belongs to the REGULATED ENTITY: its Board, committees, CISO reporting line,
  people, contracts, premises and DR site. Those obligations are listed as `entity` and are NEVER counted as covered by software.
* For the requirements software CAN address, each row is `supported` (a mechanism exists AND a journey/test proves it), `partial`
  (something exists; the shortfall is named in `note`), or `gap` (nothing yet; `next` says what would close it). `na` = not applicable
  to this estate's nature (mobile apps, algo-trading...).
* The map is hard to fudge: every evidence reference must exist, `supported` needs a journey or test as proof, and a `gap` cites no
  evidence. Titles/paragraph numbers/applicability come from the regulator's text (read 2026-10-14); status and notes are OUR
  assessment and can be wrong: challenge them. Not legal advice and not an audit opinion.

Standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("securax_ccsp", HERE / "ccsp.py")
_ccsp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ccsp)

MAPS = {"rbi": "regmap-rbi-nbfc.json", "cscrf": "regmap-sebi-cscrf.json", "mit-ai-risk": "regmap-mit-ai-risk.json", "nist-ai-600-1": "regmap-nist-ai-600-1.json", "pqc": "regmap-pqc.json"}
STATUSES = ("supported", "partial", "gap", "entity", "na")
SCORE = {"supported": 1.0, "partial": 0.5, "gap": 0.0}          # only these are "software scope"
ICON = {"supported": "✅", "partial": "🟡", "gap": "⬜", "entity": "🏛", "na": "➖"}
PROOF = {"journey", "test"}
PRIORITIES = ("high", "medium", "low")


def load(key: str, root: pathlib.Path = ROOT) -> dict:
    return json.loads((root / "governance" / MAPS[key]).read_text("utf-8"))


def problems(m: dict, root: pathlib.Path = ROOT) -> list[str]:
    cmds, jrn = _ccsp.securax_commands(root), _ccsp.journeys(root)
    out: list[str] = []
    ids = [i["id"] for i in m["items"]]
    if len(ids) != len(set(ids)):
        out.append("duplicate item ids")
    cats = set(m.get("categories", {}))
    for i in m["items"]:
        n = i["id"]
        if i["status"] not in STATUSES:
            out.append(f"{n}: unknown status '{i['status']}'")
        for ref in i["evidence"]:
            if not _ccsp.ref_ok(ref, cmds, jrn, root):
                out.append(f"{n}: evidence '{ref}' does not exist (the claim is stale)")
        kinds = {r.split(":")[0] for r in i["evidence"]}
        if i["status"] == "supported" and not (kinds & PROOF):
            out.append(f"{n}: 'supported' needs a journey or test as proof, not documentation alone")
        if i["status"] == "gap" and i["evidence"]:
            out.append(f"{n}: a 'gap' must not cite evidence (use partial)")
        if i["status"] == "partial" and not i["evidence"]:
            out.append(f"{n}: 'partial' without any evidence")
        if i["status"] in ("partial", "gap") and not i.get("next"):
            out.append(f"{n}: '{i['status']}' must say what would close it (`next`)")
        if i["status"] in ("partial", "gap") and i.get("priority") not in PRIORITIES:
            out.append(f"{n}: '{i['status']}' needs a priority {PRIORITIES}")
        if cats and i["applies"] != "all" and not set(i["applies"]) <= cats:
            out.append(f"{n}: applies-to {i['applies']} is not within the declared categories {sorted(cats)}")
    return out


def in_scope(i: dict, category: str | None) -> bool:
    return not category or i["applies"] == "all" or category in i["applies"]


def coverage(m: dict, category: str | None = None) -> dict:
    items = [i for i in m["items"] if in_scope(i, category)]
    cnt = {s: sum(i["status"] == s for i in items) for s in STATUSES}
    tech = cnt["supported"] + cnt["partial"] + cnt["gap"]
    pct = round(sum(SCORE[i["status"]] for i in items if i["status"] in SCORE) / tech * 100, 1) if tech else 0.0
    order = {"high": 0, "medium": 1, "low": 2}
    backlog = sorted((i for i in items if i["status"] in ("gap", "partial")),
                     key=lambda i: (order[i["priority"]], i["status"] != "gap", i["id"]))
    return {"category": category, "counts": cnt, "software_scope_items": tech, "software_scope_coverage_pct": pct,
            "entity_items": cnt["entity"], "total_items": len(items), "backlog": backlog}


def render_md(key: str, m: dict, category: str | None = None, probs: list[str] | None = None) -> str:
    cov = coverage(m, category)
    c = cov["counts"]
    o = [f"# Gap assessment — {m['source']['title']}", "",
         f"> {m['about']}", "",
         f"Source: [{m['source']['title']}]({m['source']['url']}) — {m['source']['issued']}; read {m['source']['read_on']}. {m['source']['caveat']}", "",
         ("Applicability scope: " + (f"**{m['categories'][category]}**" if category else "all layers / categories (use `--category` to narrow).")), "",
         f"**Software-scope coverage: {cov['software_scope_coverage_pct']}%** of {cov['software_scope_items']} requirements software can address "
         f"(✅ {c['supported']} supported · 🟡 {c['partial']} partial · ⬜ {c['gap']} gap), "
         f"plus **{c['entity']} obligations that belong to the regulated entity** (🏛, never counted as covered by software) and {c['na']} not applicable (➖).", "",
         "> This is **not** a compliance certification and a tool cannot make an entity \"100% compliant\"; "
         "it shows what the estate demonstrably does, what it does not, and what only the entity can do.", ""]
    o += ["## Backlog — what to build or fix, highest priority first", ""]
    for i in cov["backlog"][:25]:
        o.append(f"- {ICON[i['status']]} **{i['id']}** ({i['priority']}) {i['title']} — {i['note']} **Next:** {i['next']}")
    o += ["", "## Every requirement", "", "| | Ref | Requirement | Applies | Evidence / note |", "|---|---|---|---|---|"]
    for i in m["items"]:
        if not in_scope(i, category):
            continue
        ap = "all" if i["applies"] == "all" else ", ".join(i["applies"])
        ev = ", ".join("`" + e + "`" for e in i["evidence"])
        o.append(f"| {ICON[i['status']]} | {i['id']} | {i['title']} | {ap} | {(ev + ' — ') if ev else ''}{i['note']} |")
    o += ["", "## Integrity", ("- ✅ every evidence reference resolves and every 'supported' item is proven by a journey or test." if not probs
                              else "- ❌ " + "\n- ❌ ".join(probs)),
          "", "_Status is our own assessment of a lab estate, against the regulator's text as read on the date above. Challenge it._"]
    return "\n".join(o) + "\n"


def evidence_artifacts(root: pathlib.Path = ROOT) -> dict[str, bytes] | None:
    """{filename: bytes} for the evidence pack, or None if the maps are absent."""
    files: dict[str, bytes] = {}
    summary = {}
    try:
        for key in MAPS:
            m = load(key, root)
            probs = problems(m, root)
            files[f"compliance-{key}.md"] = render_md(key, m, None, probs).encode()
            cov = coverage(m)
            summary[key] = {"software_scope_coverage_pct": cov["software_scope_coverage_pct"], "counts": cov["counts"],
                            "integrity_problems": probs}
    except (OSError, ValueError, KeyError):
        return None
    files["compliance-summary.json"] = json.dumps(summary, indent=2).encode()
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("which", nargs="?", choices=[*MAPS, "all"], default="all")
    ap.add_argument("--category", default="", help="CSCRF: mii|qre|mid|small|self")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    keys = list(MAPS) if a.which == "all" else [a.which]
    rc = 0
    for key in keys:
        m = load(key)
        probs = problems(m)
        rc |= 1 if probs else 0
        cat = a.category or None
        if cat and cat not in m.get("categories", {}):
            if a.which != "all":
                print(f"{key}: no category '{cat}' (choices: {', '.join(m.get('categories', {})) or 'none — this regulation is layered by chapter'})")
                return 2
            cat = None
        if a.verify:
            print(f"{key}: " + ("\n".join(probs) if probs else "consistent (every reference resolves, every 'supported' is proven)"))
            continue
        if a.json:
            print(json.dumps({key: {"coverage": coverage(m, cat), "integrity_problems": probs}}, indent=2))
            continue
        if a.md:
            print(render_md(key, m, cat, probs))
            continue
        cov = coverage(m, cat)
        c = cov["counts"]
        print(f"{m['source']['title']}" + (f"  [{m['categories'][cat]}]" if cat else ""))
        print(f"  software-scope coverage {cov['software_scope_coverage_pct']}%  (✅{c['supported']} supported  🟡{c['partial']} partial  ⬜{c['gap']} gap)"
              f"   🏛 {c['entity']} entity obligations   ➖ {c['na']} n/a")
        print("  top of the backlog:")
        for i in cov["backlog"][:5]:
            print(f"    {ICON[i['status']]} {i['id']:<12} ({i['priority']}) {i['title']}")
        if probs:
            print("  ⚠ INCONSISTENT:\n    " + "\n    ".join(probs))
    if not a.verify and not a.json and not a.md:
        print("\nA tool cannot make an entity 100% compliant: 🏛 items are the entity's. Detail: ./securax comply rbi|cscrf --md")
    return rc


if __name__ == "__main__":
    sys.exit(main())
