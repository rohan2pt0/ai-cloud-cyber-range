#!/usr/bin/env python3
"""INSIGHT — one durable idea a week, aimed at a goal you actually set (doc 115).

The opposite of a feed. Not news, not a scraper, no network: a bounded, curated, on-device library of high-leverage
ideas (decision-making & leadership, security & AI-risk craft, mental models, money & financial independence). Each
week it serves exactly ONE idea, paraphrased in plain words with its source named and a single concrete action — and
it never repeats one until its theme is exhausted.

It aims the idea by YOUR state, in this order:
  1. Your active OKRs — the lowest-progress goal whose text matches a theme (the idea serves what you're trying to move).
  2. Else your weakest Wheel-of-Life area, when that area maps to a theme (career, growth, money).
  3. Else it rotates across all themes week to week, so there is always a useful signal.

    ./securax insight            print this week's one idea
    ./securax insight --send     the same, short, to your phone (the weekly `insight` routine) — and mark it seen
    ./securax insight --json     for the cockpit / other tools

It reads only what you already have on THIS machine (the `sovS` Life OS blob); nothing leaves your box. The "seen"
ledger lives under ~/.securax/insight/ so an idea isn't repeated; if that can't be written it falls back to a weekly
rotation (so it still varies, just without the never-repeat guarantee). Standard library only. Exit code 0 always.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "governance" / "insight.json"
WEEK = 7 * 86400


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def seen_path() -> pathlib.Path:
    return home() / "insight" / "seen.json"


def corpus() -> dict:
    with open(CORPUS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ── reading your state ───────────────────────────────────────────────────────────────────────────────

def _sov(state: dict | None) -> dict:
    """The decoded Life OS state blob (`sovS`): {} when it cannot be read."""
    try:
        payload = (state or {}).get("payload") or {}
        sov = payload.get("sovS")
        return json.loads(sov) if isinstance(sov, str) else (sov or {})
    except (ValueError, AttributeError, TypeError):
        return {}


def okrs(state: dict | None) -> list:
    """Active OKRs as [{o, krs:[{t, v}]}]; [] when none. Matches the Life OS `S.okrs` shape."""
    sov = _sov(state)
    out = []
    for o in sov.get("okrs") or []:
        if isinstance(o, dict) and o.get("o"):
            out.append(o)
    return out


def okr_progress(o: dict) -> float:
    """Mean key-result progress (0..1), mirroring the Life OS okrAvg(); 0.0 when no key results."""
    krs = [kr for kr in (o.get("krs") or []) if isinstance(kr, dict)]
    vals = [float(kr.get("v") or 0) for kr in krs]
    return sum(vals) / len(vals) if vals else 0.0


def wheel_scores(state: dict | None) -> dict:
    """{area_key: 1-10} from the synced wheel; {} when nothing is scored."""
    wheel = _sov(state).get("wheel") or {}
    return {k: v for k, v in wheel.items() if isinstance(v, (int, float)) and v > 0}


# ── aiming ───────────────────────────────────────────────────────────────────────────────────────────

def match_domain(text: str, domains: dict) -> str | None:
    """The theme whose keywords best match free text (an OKR objective + its key results); None if none match."""
    low = (text or "").lower()
    best, best_hits = None, 0
    for dom, meta in domains.items():
        hits = sum(1 for kw in meta.get("keywords", []) if kw in low)
        if hits > best_hits:
            best, best_hits = dom, hits
    return best


def wheel_domain(key: str, domains: dict) -> str | None:
    """The theme a wheel area maps to (career→leadership, growth→thinking, money→money); None for areas with no theme."""
    for dom, meta in domains.items():
        if key in meta.get("wheel", []):
            return dom
    return None


def aim(state: dict | None, now: float, domains: dict) -> dict:
    """Decide which theme this week's idea comes from, and why. Never raises."""
    week = int(now // WEEK)
    # 1. OKRs: the lowest-progress goal whose text matches a theme.
    cand = []
    for o in okrs(state):
        text = o.get("o", "") + " " + " ".join(kr.get("t", "") for kr in (o.get("krs") or []) if isinstance(kr, dict))
        dom = match_domain(text, domains)
        if dom:
            cand.append((okr_progress(o), o.get("o", ""), dom))
    if cand:
        cand.sort(key=lambda t: t[0])
        _, goal, dom = cand[0]
        return {"basis": "okr", "domain": dom, "goal": goal}
    # 2. Weakest wheel area that maps to a theme.
    scores = wheel_scores(state)
    themed = {k: v for k, v in scores.items() if wheel_domain(k, domains)}
    if themed:
        order = list(domains)
        k = min(themed, key=lambda kk: (themed[kk], order.index(wheel_domain(kk, domains))))
        return {"basis": "wheel", "domain": wheel_domain(k, domains), "area": k, "score": themed[k]}
    # 3. Rotate across all themes, week by week, so there is always a signal.
    doms = list(domains)
    return {"basis": "rotate", "domain": doms[week % len(doms)]}


# ── picking the idea (non-repeating) ──────────────────────────────────────────────────────────────────

def pick(domain: str, ideas: list, now: float, seen: list | None) -> dict:
    """This week's idea for the theme. seen=list → first unseen (never repeat; cycle restarts when exhausted);
    seen=None → weekly rotation (used when the ledger can't be read). Never raises on a known theme."""
    pool = [i for i in ideas if i.get("domain") == domain]
    if not pool:
        pool = ideas  # a theme with no ideas should never happen (a test guards it); degrade, don't crash.
    if seen is None:
        return dict(pool[int(now // WEEK) % len(pool)], cycled=False)
    unseen = [i for i in pool if i["id"] not in set(seen)]
    if unseen:
        return dict(unseen[0], cycled=False)
    return dict(pool[0], cycled=True)  # theme exhausted: start its cycle again.


def read_seen() -> list | None:
    """The served-idea ledger as a list; None when it can't be read (so pick() falls back to rotation)."""
    try:
        with open(seen_path(), encoding="utf-8") as f:
            data = json.load(f)
        return [str(x) for x in data] if isinstance(data, list) else []
    except FileNotFoundError:
        return []  # writable location, just nothing served yet.
    except (OSError, ValueError):
        return None


def mark_seen(idea_id: str, ideas: list) -> None:
    """Record that an idea was sent. When a theme is fully served, drop that theme's ids so its cycle can restart."""
    try:
        p = seen_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        seen = read_seen() or []
        if idea_id not in seen:
            seen.append(idea_id)
        by_dom: dict[str, list] = {}
        for i in ideas:
            by_dom.setdefault(i["domain"], []).append(i["id"])
        dom = next((i["domain"] for i in ideas if i["id"] == idea_id), None)
        if dom and set(by_dom[dom]).issubset(set(seen)):
            seen = [s for s in seen if s not in set(by_dom[dom])]
            if idea_id not in seen:
                seen.append(idea_id)  # keep the one just sent, so it isn't re-shown immediately.
        with open(p, "w", encoding="utf-8") as f:
            json.dump(seen, f)
    except OSError:
        pass  # a read-only box still gets a (rotating) idea; the never-repeat guarantee just lapses.


# ── assembling the week ───────────────────────────────────────────────────────────────────────────────

def build(now: float | None = None, state: dict | None = None, seen: list | None = (), _corpus: dict | None = None) -> dict:
    """This week's idea with its aim. seen=() means 'load the ledger'; pass a list (or None) in tests. Never raises."""
    now = now or time.time()
    c = _corpus if _corpus is not None else corpus()
    domains, ideas = c["domains"], c["ideas"]
    if state is None:
        pr = _load("securax_progress_insight", "governance/progress.py")
        state = pr.life_state()
    s = read_seen() if seen == () else seen
    a = aim(state, now, domains)
    idea = pick(a["domain"], ideas, now, s)
    return {"aim": a, "idea": idea, "theme": domains[a["domain"]]["label"], "at": int(now)}


def _why(a: dict, theme: str) -> str:
    if a["basis"] == "okr":
        return f"aimed at your goal — “{a['goal']}” ({theme})"
    if a["basis"] == "wheel":
        return f"aimed at your lowest Wheel area that this covers — {a['area']} ({a['score']}/10, {theme})"
    return f"a broad lever this week — {theme}"


def short(p: dict) -> str:
    """The phone message: one idea, its action, one line of why. Never a wall of text."""
    i, a = p["idea"], p["aim"]
    base = a["basis"]
    lead = {"okr": "This week's idea, aimed at a goal you set", "wheel": "This week's idea, for your weakest area",
            "rotate": "This week's idea"}[base]
    return (f"{lead}:\n"
            f"“{i['title']}” — {i['idea']}\n"
            f"Do this week: {i['action']}\n"
            f"({i['source']})")


def report(p: dict, say=print) -> None:
    i, a, theme = p["idea"], p["aim"], p["theme"]
    say("INSIGHT · one durable idea this week, aimed at what you're trying to move.\n")
    say(f"{_why(a, theme)}.\n")
    say(f"“{i['title']}”")
    say(f"   {i['idea']}")
    say(f"   Source: {i['source']}")
    say(f"\n→ Do this week: {i['action']}")
    if i.get("cycled"):
        say("\n(You've now seen every idea in this theme at least once — starting the set again.)")
    say("\nOne idea, one action. Next week aims at whatever you're trying to move then.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="insight", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    c = corpus()
    p = build(_corpus=c)
    if args.json:
        print(json.dumps(p, ensure_ascii=False, indent=1))
    elif args.send:
        msg = short(p)
        subprocess.run([sys.executable, str(ROOT / "governance" / "notify.py"), "send", msg, "--title", "This week: one idea"],
                       capture_output=True, timeout=60)
        mark_seen(p["idea"]["id"], c["ideas"])
        print(msg)
    else:
        report(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
