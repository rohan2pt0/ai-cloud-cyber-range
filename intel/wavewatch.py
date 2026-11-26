#!/usr/bin/env python3
"""Wave watch: a weekly read of reputable-forum news titles and links, so each horizon wave gets a "heat".

    ./securax intel waves               the six waves, ranked by how often they were in the forums' news this month
    ./securax intel waves fetch         read every forum search now and keep new titles in vault/wavewatch.json
    ./securax intel waves sources       the six waves and the forums they are read from

How it works (OSINT, standard library only, reuses intel/threatwatch.py):
  1. Waves and forums are data (intel/wave-patterns.json): six horizon waves (slowdown, prices and rates, trade
     shocks, health and weather, scams, AI and work), each searched once across the reputable forums (WEF, IMF,
     RBI, World Bank, OECD, CERT-In). Only titles, dates and links are kept, exactly as published.
  2. Each title is matched to a wave by its regex: the search is wide, the regex is the gate.
  3. A wave's heat is how often it was in the forums' news in the last 30 days. The report ranks the waves by heat.

Safety by design: news only ranks a wave and links evidence; it can never write or change a step, so a poisoned
feed cannot change what a person does. XML with a DTD or entities is refused; links off the source's own hosts are
dropped; text is cleaned and capped. Nothing personal is read or sent: the requests carry no profile.
Exit codes: 0 ok, 1 a source failed (the others are still used), 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WAVE_PATTERNS = ROOT / "intel" / "wave-patterns.json"
STATE = ROOT / "vault" / "wavewatch.json"
HEAT_DAYS = 30
MAX_TITLES_PER_WAVE = 5


def _threatwatch():
    """The hardened reader and the shared functions (load, sources, match, fetch, merge) live in the threat engine."""
    spec = importlib.util.spec_from_file_location("securax_threatwatch", ROOT / "intel" / "threatwatch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TW = _threatwatch()
load = TW.load
sources = TW.sources
match = TW.match
fetch = TW.fetch
merge = TW.merge
compile_patterns = TW.compile_patterns


def pack(lib: dict, state: dict, today: str) -> dict:
    """The public pack: every wave with its heat and up to five recent titles, in plain words (titles only)."""
    since = (dt.date.fromisoformat(today) - dt.timedelta(days=HEAT_DAYS)).isoformat()
    by = {}
    for i in state.get("items", []):
        by.setdefault(i["pattern"], []).append(i)
    waves = []
    for p in lib["patterns"]:
        items = sorted(by.get(p["id"], []), key=lambda i: i.get("date") or i.get("seen", ""), reverse=True)
        recent = [i for i in items if since <= (i.get("date") or i.get("seen", "")) <= today]
        seen_t, titles = set(), []
        for i in recent:
            if i["title"] not in seen_t and len(titles) < MAX_TITLES_PER_WAVE:
                seen_t.add(i["title"])
                titles.append(i["title"])
        waves.append({"id": p["id"], "heat": len({i["title"].lower() for i in recent}), "items": titles})
    waves.sort(key=lambda w: (-w["heat"], w["id"]))
    return {"waves": waves}


def _state(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"items": []}


def report(pk: dict, lib: dict) -> str:
    names = {p["id"]: p["name"] for p in lib["patterns"]}
    lines = [f"Horizon waves in the forums' news (last {HEAT_DAYS} days), ranked by how often:"]
    for w in pk["waves"]:
        lines.append(f"\n  {names.get(w['id'], w['id'])}  [in the news: {w['heat']}]")
        for t in w["items"][:3]:
            lines.append(f"    - {t}")
        if not w["items"]:
            lines.append("    - nothing this month")
    lines.append("\nNews ranks a wave; it never writes a step.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax intel waves", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="list", choices=["list", "fetch", "sources"])
    a = ap.parse_args(argv)
    lib, today = load(WAVE_PATTERNS), dt.date.today().isoformat()
    if a.cmd == "sources":
        for s in sources(lib, lib):
            print(f"{s.get('pattern', '') or s['id']:<14} {s['title']}")
        print(f"\n{len(lib['patterns'])} waves in intel/wave-patterns.json")
        return 0
    rc = 0
    state = _state(STATE)
    if a.cmd == "fetch" or (a.cmd == "list" and not state.get("items")):
        found, failed = fetch(lib, lib)
        new = merge(state, found, today)
        for f in failed:
            print(f"  ! source failed (the others were used): {f}", file=sys.stderr)
        rc = 1 if failed else 0
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(STATE)
        if a.cmd == "fetch":
            print(f"{new} new title(s) matched; {len(state['items'])} kept; {len(failed)} source(s) failed.")
            return rc
    print(report(pack(lib, state, today), lib))
    return rc


if __name__ == "__main__":
    sys.exit(main())
