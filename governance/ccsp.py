#!/usr/bin/env python3
"""CCSP-aligned coverage — what this estate demonstrates in practice against ISC2's CCSP domains, with every claim verifiable.

governance/ccsp-map.json lists the 38 sub-topics of ISC2's published outline (titles and weights are ISC2's; the status and evidence are
OUR assessment). This tool makes the assessment hard to fudge:

  * every evidence reference must EXIST (a file, a `./securax` command, a sandbox journey, a test) or the map is stale and the check fails;
  * "covered" requires at least one journey or test as proof: documentation alone can only ever earn "partial";
  * coverage is weighted by the exam's domain weights, so the biggest domain counts most.

It feeds `./securax evidence` (a CCSP section in the pack) and `./securax ccsp`. It is a practice map, NOT exam content, NOT study
material and NOT a prediction: passing the CCSP tests knowledge and needs the required experience; this shows where your lab is thin.

    ./securax ccsp [--domain N] [--json] [--verify]
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCORE = {"covered": 1.0, "partial": 0.5, "gap": 0.0}
ICON = {"covered": "✅", "partial": "🟡", "gap": "⬜"}
PROOF_KINDS = {"journey", "test"}
EXPECTED_TOPICS = 38
EXPECTED_WEIGHTS = {1: 17, 2: 20, 3: 17, 4: 16, 5: 17, 6: 13}


def load(path: pathlib.Path | None = None) -> dict:
    return json.loads((path or HERE / "ccsp-map.json").read_text("utf-8"))


def securax_commands(root: pathlib.Path = ROOT) -> set[str]:
    src = (root / "securax").read_text("utf-8")
    out: set[str] = set()
    for m in re.finditer(r"^  ([a-z][a-z0-9|\-]*)\)\s*$", src, re.M):
        out.update(c for c in m.group(1).split("|") if c and c != "*")
    return out


def journeys(root: pathlib.Path = ROOT) -> set[str]:
    return set(re.findall(r'@journey\(\s*"([a-z0-9_]+)"', (root / "sandbox" / "run.py").read_text("utf-8")))


def ref_ok(ref: str, cmds: set[str], jrn: set[str], root: pathlib.Path) -> bool:
    kind, _, val = ref.partition(":")
    if kind == "cmd":
        return val in cmds
    if kind == "journey":
        return val in jrn
    if kind in ("file", "test"):
        return (root / val).exists()
    return False


def problems(m: dict, root: pathlib.Path = ROOT) -> list[str]:
    """Everything wrong with the map: stale references, overclaims, a shape that no longer matches ISC2's outline."""
    cmds, jrn = securax_commands(root), journeys(root)
    out: list[str] = []
    weights = {d["id"]: d["weight"] for d in m["domains"]}
    if weights != EXPECTED_WEIGHTS or sum(weights.values()) != 100:
        out.append(f"domain weights {weights} do not match the outline ({EXPECTED_WEIGHTS})")
    topics = [t for d in m["domains"] for t in d["topics"]]
    if len(topics) != EXPECTED_TOPICS or len({t["id"] for t in topics}) != len(topics):
        out.append(f"expected {EXPECTED_TOPICS} distinct sub-topics, found {len(topics)}")
    for t in topics:
        if t["status"] not in SCORE:
            out.append(f"{t['id']}: unknown status '{t['status']}'")
        for ref in t["evidence"]:
            if not ref_ok(ref, cmds, jrn, root):
                out.append(f"{t['id']}: evidence '{ref}' does not exist (the claim is stale)")
        kinds = {r.split(":")[0] for r in t["evidence"]}
        if t["status"] == "covered" and not (kinds & PROOF_KINDS):
            out.append(f"{t['id']}: 'covered' needs a journey or test as proof, not documentation alone")
        if t["status"] == "gap" and t["evidence"]:
            out.append(f"{t['id']}: a 'gap' must not cite evidence (use partial)")
        if t["status"] != "gap" and not t["evidence"]:
            out.append(f"{t['id']}: '{t['status']}' without any evidence")
    return out


def coverage(m: dict) -> dict:
    doms = []
    for d in m["domains"]:
        n = len(d["topics"])
        counts = {s: sum(t["status"] == s for t in d["topics"]) for s in SCORE}
        pct = sum(SCORE[t["status"]] for t in d["topics"]) / n * 100
        doms.append({"id": d["id"], "name": d["name"], "weight": d["weight"], "topics": n, "counts": counts, "coverage_pct": round(pct, 1)})
    overall = sum(x["coverage_pct"] * x["weight"] for x in doms) / sum(x["weight"] for x in doms)
    gaps = [{"id": t["id"], "title": t["title"], "status": t["status"], "weight": d["weight"], "note": t["note"]}
            for d in m["domains"] for t in d["topics"] if t["status"] != "covered"]
    gaps.sort(key=lambda g: (g["status"] != "gap", -g["weight"], g["id"]))
    return {"domains": doms, "overall_weighted_pct": round(overall, 1), "backlog": gaps}


def render_md(m: dict, cov: dict, probs: list[str] | None = None) -> str:
    o = [f"# CCSP-aligned coverage — {m['source']['read_on']}", "",
         f"> {m['about']}", "",
         f"Source of titles and weights: [{m['source']['outline']}]({m['source']['url']}) (page header date {m['source']['page_header_date']}). {m['source']['caveat']}", "",
         f"**Weighted practice coverage: {cov['overall_weighted_pct']}%** (covered = 1, partial = 0.5, gap = 0; weighted by the exam's domain weights).", "",
         "| Domain | Weight | ✅ | 🟡 | ⬜ | Coverage |", "|---|---|---|---|---|---|"]
    for d in cov["domains"]:
        c = d["counts"]
        o.append(f"| {d['id']} · {d['name']} | {d['weight']}% | {c['covered']} | {c['partial']} | {c['gap']} | {d['coverage_pct']}% |")
    o += ["", "## Sub-topics"]
    for d in m["domains"]:
        o += ["", f"### Domain {d['id']} · {d['name']} ({d['weight']}%)", "", "| | Sub-topic | Evidence | Note |", "|---|---|---|---|"]
        for t in d["topics"]:
            o.append(f"| {ICON[t['status']]} | {t['id']} {t['title']} | {', '.join('`' + e + '`' for e in t['evidence']) or '—'} | {t['note']} |")
    o += ["", "## Backlog (gaps first, then the heaviest-weighted partials)"]
    for g in cov["backlog"][:12]:
        o.append(f"- {ICON[g['status']]} **{g['id']}** {g['title']} (domain weight {g['weight']}%): {g['note']}")
    o += ["", "## Integrity", ("- ✅ every evidence reference resolves and every 'covered' item is backed by a journey or test." if not probs else "- ❌ " + "\n- ❌ ".join(probs)),
          "", "_A practice map for a lab, not exam content and not a prediction of an exam result. Status is our own assessment: challenge it._"]
    return "\n".join(o) + "\n"


def evidence_artifacts(root: pathlib.Path = ROOT) -> tuple[bytes, str] | None:
    """(json bytes, markdown) for the evidence pack, or None if the map is absent."""
    try:
        m = load(root / "governance" / "ccsp-map.json")
    except (OSError, ValueError):
        return None
    probs, cov = problems(m, root), None
    cov = coverage(m)
    return json.dumps({"coverage": cov, "integrity_problems": probs}, indent=2).encode(), render_md(m, cov, probs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--domain", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true", help="only check that the map is consistent (exit 1 if not)")
    a = ap.parse_args(argv)
    m = load()
    probs = problems(m)
    if a.verify:
        print("\n".join(probs) if probs else "ccsp map: consistent (every reference resolves, every 'covered' is proven)")
        return 1 if probs else 0
    cov = coverage(m)
    if a.json:
        print(json.dumps({"coverage": cov, "integrity_problems": probs}, indent=2))
        return 1 if probs else 0
    if a.domain:
        d = next((x for x in m["domains"] if x["id"] == a.domain), None)
        if not d:
            print("domain must be 1-6")
            return 2
        print(f"Domain {d['id']} · {d['name']} ({d['weight']}%)")
        for t in d["topics"]:
            print(f"  {ICON[t['status']]} {t['id']} {t['title']}\n      {t['note']}\n      evidence: {', '.join(t['evidence']) or '—'}")
        return 0
    print(f"CCSP-aligned practice coverage (weighted): {cov['overall_weighted_pct']}%   — a map of this lab, not exam content")
    for d in cov["domains"]:
        c = d["counts"]
        print(f"  Domain {d['id']} {d['name']:<44} {d['weight']:>2}%   ✅{c['covered']} 🟡{c['partial']} ⬜{c['gap']}   {d['coverage_pct']:>5}%")
    print("\nBiggest gaps (build it, or study it, or both):")
    for g in cov["backlog"][:6]:
        print(f"  {ICON[g['status']]} {g['id']} {g['title']}  (domain weight {g['weight']}%)")
    print("\n  ./securax ccsp --domain 5     detail for one domain      ./securax evidence     includes this map in the audit pack")
    if probs:
        print("\n⚠ the map is INCONSISTENT:\n  " + "\n  ".join(probs))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
