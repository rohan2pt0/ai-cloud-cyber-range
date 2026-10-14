#!/usr/bin/env python3
"""How big can this estate grow, what switches on at each size, and what is honestly NOT built yet.

    ./securax capacity                    the whole ladder, 1 person to 100,000
    ./securax capacity --people 60        the tier for 60 people: what to switch on, who you need, what is missing
    ./securax capacity --people 60 --json
    ./securax capacity --bench            measure the guardrail engine on THIS machine (requests/second/core)

Data lives in governance/scale-tiers.json. 'have' and 'dormant' items must point at a file that exists (the test
enforces it), so the ladder cannot promise what the repository does not contain. Guidance, not a guarantee.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "scale-tiers.json"
MARK = {"have": "[have]   ", "dormant": "[dormant]", "gap": "[GAP]    "}


def load() -> list[dict]:
    return json.loads(DATA.read_text("utf-8"))["tiers"]


def tier_for(people: int, tiers: list[dict] | None = None) -> dict:
    ts = tiers or load()
    for t in ts:
        if t["people"][0] <= people <= t["people"][1]:
            return t
    return ts[-1]


def problems(tiers: list[dict] | None = None) -> list[str]:
    out, ts = [], tiers or load()
    for i, t in enumerate(ts):
        lo, hi = t["people"]
        if i == 0 and lo != 1:
            out.append("ladder must start at 1 person")
        if i and ts[i - 1]["people"][1] + 1 != lo:
            out.append(f"{t['id']}: gap or overlap with the tier before")
        for c in t["capabilities"]:
            if c["state"] in ("have", "dormant") and not (ROOT / c.get("evidence", "")).exists():
                out.append(f"{t['id']}/{c['name']}: evidence '{c.get('evidence')}' does not exist")
            if c["state"] == "gap" and not c.get("next"):
                out.append(f"{t['id']}/{c['name']}: a gap needs a 'next' step")
    return out


def bench() -> dict:
    sys.path.insert(0, str(ROOT / "apps" / "llm-gateway"))
    try:
        from app import guardrails as g
    except Exception as e:                                       # gateway deps not installed here
        return {"error": f"cannot import the guardrails ({type(e).__name__})"}
    sample = ("Summarise the attached quarterly risk report for the audit committee and list three actions. " * 8)[:800]
    n, t0 = 2000, time.perf_counter()
    for _ in range(n):
        g.inspect_input(sample, 8000)
    dt = time.perf_counter() - t0
    return {"rails_checks_per_second_per_core": round(n / dt), "sample_bytes": len(sample),
            "note": "Rails only. Real chat throughput is limited by the model (tokens/second), not by these checks: "
                    "size the model tier with your own load test before promising anything."}


def render(t: dict) -> str:
    lo, hi = t["people"]
    out = [f"{t['id'].upper()}  ({lo:,}-{hi:,} people)  {t['shape']}",
           f"  humans needed: {t['humans']}", f"  toil: {t['toil']}"]
    for c in t["capabilities"]:
        extra = c.get("switch") or c.get("next") or ""
        out.append(f"  {MARK[c['state']]} {c['name']}" + (f"\n             -> {extra}" if extra else ""))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--people", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--bench", action="store_true")
    a = ap.parse_args(argv)
    if a.bench:
        b = bench()
        print(json.dumps(b, indent=2) if a.json else "\n".join(f"{k}: {v}" for k, v in b.items()))
        return 1 if "error" in b else 0
    ts = load()
    if a.people is not None:
        if a.people < 1:
            print("--people must be at least 1")
            return 2
        t = tier_for(a.people, ts)
        gaps = [c["name"] for c in t["capabilities"] if c["state"] == "gap"]
        if a.json:
            print(json.dumps({"people": a.people, "tier": t, "gaps": gaps}, indent=2))
        else:
            print(render(t))
            print(f"\n{len(gaps)} gap(s) at this size." if gaps else "\nNo known gaps at this size.")
        return 0
    if a.json:
        print(json.dumps(ts, indent=2))
    else:
        print("\n\n".join(render(t) for t in ts))
        print("\nPick your size:  ./securax capacity --people N")
    return 0


if __name__ == "__main__":
    sys.exit(main())
