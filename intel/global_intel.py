#!/usr/bin/env python3
"""Global Intelligence — make the best collective decision, before it becomes a commodity.

The method the user already runs by hand — open r/CCSP, filter **Top / All time**, read the
highest-ranked posts, spot the pattern everyone agrees on (e.g. "Pete Zerger + LEARNZAPP"),
then act — turned into a repeatable engine for *every* sphere of life. It is the same logic
behind McKinsey/BCG ("the pattern across hundreds of engagements"), Amazon best-seller +
BIFL filters, and buying the Honda Activa (most-sold + best resale = refined over many cycles).

THE ONE OPERATOR INSIGHT THIS ENCODES — two opposite regimes:

  * REPLICATE: proven playbooks (pass an exam, buy a product, a known career path). Community
    "Top / All-time" consensus is GOLD here. The LINDY effect applies — the longer something
    has stayed top-ranked, the more battle-tested it is. Low variance, high success odds.
    -> COPY the consensus.

  * EDGE: getting in "before it becomes a commodity" (a YouTube channel, selling a course like
    Warikoo / Luke Ahmad, a rising trend). Here "Top / All-time" is a LAGGING indicator — by
    the time it is all-time-top, you are late. You need RISING / early signals plus your own
    unfair advantage. -> BEAT the consensus, do not copy it.

So the two modes weight evidence in opposite directions (old+proven vs new+rising), and every
opportunity is scored against YOUR real capabilities (so it is realistically implementable),
placed on the diffusion-of-innovation curve (are you early or late?), and wrapped in a
worst-case pre-mortem (Taleb barbell + Klein pre-mortem) so you are always prepared.

ANTI-HALLUCINATION BY DESIGN: this engine never invents rankings or trends. It analyses only
the signals YOU collect (paste, CSV, or an official API) and labels every estimate as such.
Pure standard library; fully offline; vendor/source-agnostic (no single point of failure).
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re

# A small, extensible stop-list so auto-extracted "candidates" are real names, not filler.
_STOP = {
    "the", "and", "for", "you", "your", "with", "this", "that", "have", "from", "are", "was",
    "all", "any", "can", "will", "just", "like", "get", "got", "use", "used", "using", "best",
    "good", "great", "really", "very", "much", "more", "most", "some", "they", "them", "what",
    "when", "how", "why", "who", "but", "not", "than", "then", "also", "about", "would", "could",
    "should", "did", "does", "exam", "test", "study", "studying", "passed", "pass", "cleared",
    "it", "is", "to", "of", "in", "on", "a", "an", "i", "my", "me", "we", "course", "courses",
}


# --------------------------------------------------------------------------- #
# 1. Weight each signal — the crux of the two regimes.
# --------------------------------------------------------------------------- #
def signal_weight(score: float = 0.0, rank: int = 1, age_days: float = 0.0,
                  mode: str = "replicate") -> float:
    """How much one ranked item counts.

    score    = upvotes / ratings / likes (strength of collective endorsement)
    rank     = position in the Top list (1 = best); lower is better
    age_days = how old the item is
    mode     = 'replicate' (reward age = Lindy/time-tested) or 'edge' (reward recency = catch
               the trend before it commoditises).
    """
    popularity = math.log10(max(score, 0) + 10)            # diminishing returns on raw votes
    rank_w = 1.0 / (1 + 0.15 * max(rank - 1, 0))           # rank 1 full; decays down the list
    if mode == "edge":
        freshness = math.exp(-max(age_days, 0) / 180.0)    # ~6-month decay: stale trend = late
        return popularity * rank_w * (0.3 + 0.7 * freshness)
    # replicate: the longer it has stayed top, the more proven (Lindy), capped at +50%.
    lindy = 1 + min(max(age_days, 0) / 365.0, 5) * 0.10
    return popularity * rank_w * lindy


# --------------------------------------------------------------------------- #
# 2. Extract the consensus — "what do the top results agree on?"
# --------------------------------------------------------------------------- #
def _candidates_from_text(text: str) -> set[str]:
    """Heuristic named-entity guess: capitalised words/phrases and brand-like tokens.

    Used only when you do NOT supply a vocabulary. Supplying a vocabulary (the names you saw
    recurring) is more accurate and is the recommended path."""
    out: set[str] = set()
    # Capitalised runs of up to 3 words (e.g. "Pete Zerger", "Mike Chapple").
    for m in re.finditer(r"\b([A-Z][a-zA-Z0-9+.&]+(?:\s+[A-Z][a-zA-Z0-9+.&]+){0,2})\b", text or ""):
        phrase = m.group(1).strip()
        if phrase.lower() not in _STOP and len(phrase) > 2:
            out.add(phrase)
    # ALL-CAPS / brandy tokens (e.g. "LEARNZAPP", "OSCP", "AWS").
    for m in re.finditer(r"\b([A-Z]{3,}[A-Z0-9]*)\b", text or ""):
        out.add(m.group(1))
    return out


def extract_consensus(items: list[dict], vocabulary: list[str] | None = None,
                      mode: str = "replicate", min_sources: int = 2) -> list[dict]:
    """Rank the recommendations the community agrees on, weighted by rank/score/age.

    items: list of {"source","rank","score","age_days","title","text"} you collected from
           Top/All-time (Reddit), best-seller/BIFL (Amazon), top videos (YouTube), etc.
    vocabulary: optional explicit list of names to count precisely (best accuracy, no guessing).
    Returns [{name, weight, mentions, distinct_sources, consensus}], highest first.
    A result backed by < min_sources distinct sources is flagged low-confidence, not dropped.
    """
    tally: dict[str, dict] = {}
    for it in items:
        text = f"{it.get('title', '')} {it.get('text', '')}"
        w = signal_weight(it.get("score") or 0, int(it.get("rank") or 1),
                          it.get("age_days") or 0, mode)   # `or 0/1` tolerates JSON nulls
        src = it.get("source", "?")
        names = (set(vocabulary) if vocabulary else _candidates_from_text(text))
        for name in names:
            if vocabulary:  # precise, case-insensitive, whitespace-flexible match
                pat = re.compile(re.escape(name).replace(r"\ ", r"\s+"), re.I)
                if not pat.search(text):
                    continue
            rec = tally.setdefault(name, {"name": name, "weight": 0.0, "mentions": 0, "sources": set()})
            rec["weight"] += w
            rec["mentions"] += 1
            rec["sources"].add(src)
    total_w = sum(r["weight"] for r in tally.values()) or 1.0
    ranked = []
    for r in sorted(tally.values(), key=lambda x: x["weight"], reverse=True):
        ranked.append({
            "name": r["name"],
            "weight": round(r["weight"], 2),
            "mentions": r["mentions"],
            "distinct_sources": len(r["sources"]),
            "consensus": round(r["weight"] / total_w, 3),         # share of total evidence
            "confidence": "high" if len(r["sources"]) >= min_sources and r["mentions"] >= 3
                          else ("medium" if len(r["sources"]) >= min_sources else "low"),
        })
    return ranked


def consensus_strength(ranked: list[dict], n_items: int) -> dict:
    """How much to trust the consensus overall: enough data + clear agreement (concentration)."""
    if not ranked:
        return {"verdict": "no signal", "advice": "Collect more top-ranked posts/reviews first."}
    top = ranked[0]
    concentration = sum(r["consensus"] ** 2 for r in ranked[:5])   # Herfindahl-style (0..1)
    enough = n_items >= 8
    clear = concentration >= 0.25 and top["distinct_sources"] >= 2
    verdict = ("strong" if enough and clear else
               "emerging" if clear else
               "thin — gather more data")
    return {"verdict": verdict, "leader": top["name"], "leader_consensus": top["consensus"],
            "agreement_concentration": round(concentration, 3), "signals_analysed": n_items,
            "advice": ("Act on the leader." if verdict == "strong" else
                       "Promising, but widen your sample (more Top/All-time items) before betting big."
                       if verdict == "emerging" else
                       "Not enough agreement yet — collect more highly-ranked items.")}


# --------------------------------------------------------------------------- #
# 3. Capability fit — "does this match what *I* can realistically do?"
# --------------------------------------------------------------------------- #
def capability_fit(opportunity: dict, profile: dict) -> dict:
    """Score 0..1 how implementable an opportunity is for YOU, and name the gaps.

    profile: {"skills":[...], "assets":[...], "edge":[...],
              "constraints":{"time_hrs_week":N, "capital_inr":N, "risk":"low|med|high"}}
    opportunity: {"name","requires_skills":[...], "requires_time_hrs_week":N,
                  "requires_capital_inr":N, "risk":"low|med|high"}
    'edge' = your rare / credentialed advantages (e.g. CISSP, CISM, BFSI) — overlap here is the
    'unfair advantage' that makes success realistic and defensible.
    """
    have = {s.lower() for s in profile.get("skills", []) + profile.get("assets", []) + profile.get("edge", [])}
    need = [s for s in opportunity.get("requires_skills", [])]
    matched = [s for s in need if s.lower() in have]
    gaps = [s for s in need if s.lower() not in have]
    skill_fit = len(matched) / len(need) if need else 1.0

    # Unfair advantage = how many of the needed skills are among your RARE/credentialed edges.
    # More overlap = a deeper moat; scales (not a flat bonus) so a stronger moat ranks higher.
    edge = {e.lower() for e in profile.get("edge", [])}
    unfair = [s for s in need if s.lower() in edge]
    edge_component = 0.25 * min(len(unfair) / 3.0, 1.0)

    # Constraint comfort = how much headroom you have within your limits. Rewards the lighter,
    # cheaper, safer option among otherwise-equal choices (do the easiest winnable thing first).
    con = profile.get("constraints", {})
    need_time = opportunity.get("requires_time_hrs_week", 0)
    need_cap = opportunity.get("requires_capital_inr", 0)
    cap_time = con.get("time_hrs_week", 1e9)
    cap_cap = con.get("capital_inr", 1e18)
    time_ok, cap_ok = need_time <= cap_time, need_cap <= cap_cap
    risk_order = {"low": 0, "med": 1, "medium": 1, "high": 2}
    risk_ok = risk_order.get(opportunity.get("risk", "low"), 0) <= risk_order.get(con.get("risk", "high"), 2)
    time_slack = max(0.0, (cap_time - need_time) / cap_time) if cap_time else 1.0
    cap_slack = max(0.0, (cap_cap - need_cap) / cap_cap) if cap_cap else 1.0
    comfort = 0.25 * ((time_slack + cap_slack + (1.0 if risk_ok else 0.0)) / 3.0)

    # A violated hard constraint dominates — it should sink the score, not just dent it.
    penalty = (0 if time_ok else 0.3) + (0 if cap_ok else 0.3) + (0 if risk_ok else 0.3)
    fit = max(0.0, min(1.0, 0.5 * skill_fit + edge_component + comfort - penalty))

    blockers = []
    if not time_ok: blockers.append("needs more weekly time than you have")
    if not cap_ok: blockers.append("needs more capital than your cap")
    if not risk_ok: blockers.append("riskier than your tolerance")
    return {
        "name": opportunity.get("name", "?"),
        "fit": round(fit, 3),
        "verdict": "strong fit" if fit >= 0.7 else "possible (close gaps)" if fit >= 0.45 else "weak fit",
        "unfair_advantage": unfair,
        "skill_gaps": gaps,
        "blockers": blockers,
    }


# --------------------------------------------------------------------------- #
# 4. Timing — where is this on the adoption curve? (only matters in EDGE mode)
# --------------------------------------------------------------------------- #
def commoditization_stage(volume_series: list[float]) -> dict:
    """Estimate the diffusion-of-innovation stage from a time-ordered volume series
    (e.g. monthly post counts / search interest / new creators). ESTIMATE — label it so.

    Entry sweet-spot for EDGE is 'early adopters' -> 'early majority' (rising, not saturated).
    'late majority'/'laggard' = already a commodity; you must differentiate or pass.
    """
    s = [max(0.0, float(v)) for v in volume_series if v is not None]
    if len(s) < 3:
        return {"stage": "unknown", "note": "need >= 3 periods of volume data", "estimate": True}
    peak = max(s) or 1.0
    recent = sum(s[-3:]) / 3.0
    earlier = sum(s[:3]) / 3.0
    growth = (recent - earlier) / (earlier + 1e-9)
    saturation = recent / peak
    if saturation < 0.25 and growth > 0.3:
        stage, entry = "innovators", "very early — high risk, high edge; only with an unfair advantage"
    elif growth > 0.5:
        stage, entry = "early adopters", "SWEET SPOT — rising fast, not yet crowded. Enter now."
    elif growth > 0.1:
        stage, entry = "early majority", "good entry if you differentiate; window is closing"
    elif saturation > 0.8 and abs(growth) <= 0.1:
        stage, entry = "late majority", "commoditised — only enter with a sharp niche/unfair edge"
    else:
        stage, entry = "laggard / declining", "likely too late; pass or find the next wave"
    return {"stage": stage, "entry_advice": entry, "growth_rate": round(growth, 2),
            "saturation": round(saturation, 2), "estimate": True}


# --------------------------------------------------------------------------- #
# 5. Worst-case readiness — pre-mortem + barbell (always be prepared).
# --------------------------------------------------------------------------- #
def premortem(decision: str, known_risks: list[str] | None = None,
              reversible: bool = True, safe_core_pct: int = 90) -> dict:
    """Klein pre-mortem + Taleb barbell: assume it failed, list why, protect the downside."""
    generic = [
        "The consensus was popular but wrong for my specific context.",
        "I underestimated the time/effort and quit before it compounded.",
        "A hidden prerequisite skill/asset I don't have blocked me.",
        "The trend commoditised before I shipped (I was late).",
        "A single dependency failed and I had no fallback.",
    ]
    return {
        "decision": decision,
        "imagine_it_failed_why": (known_risks or []) + generic,
        "barbell": f"Protect {safe_core_pct}% (time/capital) in the safe, proven core; risk only "
                   f"{100 - safe_core_pct}% on the speculative upside — never bet the base.",
        "reversible": reversible,
        "kill_criteria": "Pre-commit the metric + date at which you stop (e.g. 'no traction in "
                         "90 days / after 10 attempts -> stop and reassess').",
        "worst_case_reserve": "Keep an emergency fund + a Plan B that needs none of this to work.",
    }


# --------------------------------------------------------------------------- #
# 6. Orchestrator — one call: consensus -> timing -> fit -> worst-case plan.
# --------------------------------------------------------------------------- #
def decide(goal: str, items: list[dict], mode: str = "replicate",
           vocabulary: list[str] | None = None, profile: dict | None = None,
           opportunities: list[dict] | None = None,
           volume_series: list[float] | None = None) -> dict:
    ranked = extract_consensus(items, vocabulary, mode)
    out: dict = {
        "goal": goal,
        "mode": mode,
        "mode_meaning": ("REPLICATE a proven playbook — copy the time-tested consensus."
                         if mode == "replicate" else
                         "Find an EDGE before it commoditises — favour rising signals + your unfair advantage."),
        "consensus": ranked[:10],
        "consensus_strength": consensus_strength(ranked, len(items)),
        "grounding": f"Based ONLY on the {len(items)} signal(s) you provided — rankings are from "
                     "your data, not invented. Collect more Top/All-time items for higher confidence.",
    }
    if mode == "edge" and volume_series:
        out["timing"] = commoditization_stage(volume_series)
    if opportunities and profile:
        fits = sorted((capability_fit(o, profile) for o in opportunities),
                      key=lambda x: x["fit"], reverse=True)
        out["capability_fit"] = fits
        out["recommended"] = next((f["name"] for f in fits if f["fit"] >= 0.45), None)
    out["worst_case"] = premortem(goal)
    out["next_action"] = ("Act on the top-consensus item above." if ranked and
                          out["consensus_strength"]["verdict"] == "strong"
                          else "Gather more highly-ranked data before committing significant resources.")
    return out


# --------------------------------------------------------------------------- #
# Loaders + CLI
# --------------------------------------------------------------------------- #
def load_items(path: str) -> list[dict]:
    """Load collected signals from a .json (list of dicts) or .csv file. Source-agnostic:
    you bring the data (pasted from Reddit Top/All-time, Amazon, YouTube, or an official API)."""
    p = pathlib.Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        data = json.loads(raw)
        return data if isinstance(data, list) else data.get("items", [])
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(raw)))
    for r in rows:  # cast the numeric columns if present
        for k in ("rank", "score", "age_days"):
            if r.get(k) not in (None, ""):
                r[k] = float(r[k])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Global Intelligence — community-signal decision engine.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decide", help="full decision from a file of collected signals")
    d.add_argument("goal")
    d.add_argument("--items", required=True, help="path to .json/.csv of ranked signals")
    d.add_argument("--mode", choices=["replicate", "edge"], default="replicate")
    d.add_argument("--vocab", default="", help="comma-separated names to count precisely")
    d.add_argument("--profile", default="", help="path to a profile .json (skills/assets/edge/constraints)")
    d.add_argument("--opportunities", default="", help="path to an opportunities .json (edge mode)")
    d.add_argument("--volume", default="", help="comma-separated volume series (edge-mode timing)")

    c = sub.add_parser("consensus", help="just the ranked consensus from a file")
    c.add_argument("--items", required=True)
    c.add_argument("--mode", choices=["replicate", "edge"], default="replicate")
    c.add_argument("--vocab", default="")

    args = ap.parse_args()
    vocab = [v.strip() for v in args.vocab.split(",") if v.strip()] or None
    if args.cmd == "consensus":
        items = load_items(args.items)
        print(json.dumps(extract_consensus(items, vocab, args.mode), indent=2))
        return 0
    items = load_items(args.items)
    profile = json.loads(pathlib.Path(args.profile).read_text()) if args.profile else None
    opps = json.loads(pathlib.Path(args.opportunities).read_text()) if args.opportunities else None
    vol = [float(x) for x in args.volume.split(",") if x.strip()] if args.volume else None
    print(json.dumps(decide(args.goal, items, args.mode, vocab, profile, opps, vol), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
