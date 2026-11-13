#!/usr/bin/env python3
"""Threat watch: red-team your life from what is happening in the world, not only from what you type in.

    ./securax intel threats              the threats in the news this month, ranked, each with the drill to rehearse
    ./securax intel threats fetch        read every open source now and keep new matches in vault/threatwatch.json
    ./securax intel threats pack [--fetch] [--out FILE]
                                         write the public drill pack the Life OS reads (default website/app/intel.json)
    ./securax intel threats sources      the sources and the patterns

How it works (OSINT, standard library only):
  1. Sources are data (intel/threat-feeds.json): security newsrooms read in full, and one news search per threat
     pattern and region. Only titles, dates and links are kept, exactly as published; nothing is summarised.
  2. Each title is matched to the curated library (intel/threat-patterns.json): honeytrap, digital arrest, a cloned
     voice, SIM swap and more, each with drills (test cases to rehearse) and the signs to watch for.
  3. A pattern's heat is how often it was in the news in the last 30 days. The pack ranks the patterns by heat x
     severity, so this month's live threats come first.

Safety by design: news only ranks a pattern and links evidence; it can never write or change a drill, so a poisoned
feed cannot change what a person rehearses. XML with a DTD or entities is refused; links off a source's own hosts are
dropped; text is cleaned of control characters and capped; the state keeps at most MAX_ITEMS items for KEEP_DAYS days.
Nothing personal is read or sent: the requests carry no profile, and the pack is the same for everyone.
Exit codes: 0 ok, 1 a source failed (the others are still used), 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "intel" / "threat-patterns.json"
FEEDS = ROOT / "intel" / "threat-feeds.json"
STATE = ROOT / "vault" / "threatwatch.json"
PACK = ROOT / "website" / "app" / "intel.json"   # next to the hosted Life OS, which reads it same-origin
MAX_ITEMS = 2000          # the state's bound (doc 80): oldest first out
KEEP_DAYS = 120
HEAT_DAYS = 30
NEWS_PER_PATTERN = 3


def _regwatch():
    """The hardened RSS reader (DTD refusal, size cap, link host check) is shared with the regulator watch."""
    spec = importlib.util.spec_from_file_location("securax_regwatch", ROOT / "governance" / "regwatch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RW = _regwatch()


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compile_patterns(lib: dict) -> list[tuple[dict, re.Pattern]]:
    return [(p, re.compile(p["match"], re.I)) for p in lib["patterns"]]


def sources(feeds: dict, lib: dict) -> list[dict]:
    """Every request to make: each newsroom, then one search per pattern and edition (a country pattern only in its region)."""
    out = [dict(f, region="global") for f in feeds.get("feeds", [])]
    s = feeds.get("search")
    if s:
        for p in lib["patterns"]:
            for e in s["editions"]:
                if p.get("where", "global") not in ("global", e["region"]):
                    continue
                url = s["url"].format(q=urllib.parse.quote_plus(p["query"]), hl=e["hl"], gl=e["gl"], lang=e["lang"])
                out.append({"id": f"search-{p['id']}-{e['region']}", "title": s["title"], "url": url,
                            "link_hosts": s["link_hosts"], "region": e["region"], "pattern": p["id"]})
    return out


def _source_name(title: str) -> tuple[str, str]:
    """News search titles end ' - Outlet'; split it off so the outlet shows on its own."""
    m = re.match(r"^(.*\S)\s+-\s+([^-]{2,60})$", title)
    return (m.group(1), m.group(2).strip()) if m else (title, "")


def match(items: list[dict], src: dict, compiled) -> list[dict]:
    """Items whose title matches a pattern. A search result is checked too: the search is wide, the regex is the gate."""
    out = []
    for it in items:
        head, outlet = _source_name(it["title"])
        for p, rx in compiled:
            if rx.search(head):
                out.append({"pattern": p["id"], "title": head, "outlet": outlet or src.get("title", ""), "link": it["link"],
                            "date": it.get("published", ""), "region": src.get("region", "global")})
    return out


def fetch(feeds: dict, lib: dict, getter=None) -> tuple[list[dict], list[str]]:
    getter = getter or RW.fetch_url
    compiled, found, failed = compile_patterns(lib), [], []
    for src in sources(feeds, lib):
        try:
            found += match(RW.parse_feed(getter(src["url"]), src), src, compiled)
        except Exception as exc:  # one dead source never stops the rest
            failed.append(f"{src['id']}: {str(exc)[:120]}")
    return found, failed


def merge(state: dict, found: list[dict], today: str) -> int:
    """Keep each (pattern, link or title) once, dated when first seen; drop old items and cap the size."""
    have = {(i["pattern"], i["link"] or i["title"]) for i in state.setdefault("items", [])}
    new = 0
    for f in found:
        k = (f["pattern"], f["link"] or f["title"])
        if k in have:
            continue
        have.add(k)
        state["items"].append(dict(f, seen=today))
        new += 1
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=KEEP_DAYS)).isoformat()
    state["items"] = [i for i in state["items"] if (i.get("date") or i["seen"]) >= cutoff][-MAX_ITEMS:]
    state["updated"] = today
    return new


def pack(lib: dict, state: dict, today: str) -> dict:
    """The public pack: every pattern with its drills, ranked by heat x severity, with up to three recent headlines."""
    since = (dt.date.fromisoformat(today) - dt.timedelta(days=HEAT_DAYS)).isoformat()
    by = {}
    for i in state.get("items", []):
        by.setdefault(i["pattern"], []).append(i)
    pats = []
    for p in lib["patterns"]:
        items = sorted(by.get(p["id"], []), key=lambda i: i.get("date") or i["seen"], reverse=True)
        recent = [i for i in items if (i.get("date") or i["seen"]) >= since]
        seen_t, news = set(), []
        for i in recent:
            t = i["title"].lower()
            if t not in seen_t and len(news) < NEWS_PER_PATTERN:
                seen_t.add(t)
                news.append({k: i[k] for k in ("title", "outlet", "link", "date", "region")})
        entry = {k: p[k] for k in ("id", "name", "where", "severity", "story", "signs", "drills")}
        entry.update(heat=len({i["title"].lower() for i in recent}), news=news)
        pats.append(entry)
    pats.sort(key=lambda e: (-(e["heat"] * e["severity"]), -e["severity"], e["id"]))
    return {"version": lib.get("version", 1), "generated": today, "heat_days": HEAT_DAYS,
            "sources": len(sources(load(FEEDS), lib)) if FEEDS.exists() else 0, "patterns": pats}


def _state(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"items": []}


def _save(state: dict, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def report(pk: dict, top: int = 5) -> str:
    lines = [f"Threats in the news (last {pk['heat_days']} days), ranked by how often x how much harm:"]
    for p in pk["patterns"][:top]:
        lines.append(f"\n  {p['name']}  [in the news: {p['heat']}, harm {p['severity']}/3]")
        for n in p["news"][:2]:
            lines.append(f"    - {n['date']} {n['title']} ({n['outlet']})")
        lines.append(f"    Drill: {p['drills'][0]['try']}")
        lines.append(f"    Passes if: {p['drills'][0]['pass']}")
    lines.append("\nRehearse them in the Life OS: Risk tab, 'Threats in the news'.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax intel threats", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="list", choices=["list", "fetch", "pack", "sources"])
    ap.add_argument("--fetch", action="store_true", help="pack: read the sources first (for the daily site build)")
    ap.add_argument("--out", default=str(PACK))
    ap.add_argument("--state", default=str(STATE))
    a = ap.parse_args(argv)
    lib, feeds, today = load(PATTERNS), load(FEEDS), dt.date.today().isoformat()
    state_path = pathlib.Path(a.state)
    if a.cmd == "sources":
        for s in sources(feeds, lib):
            print(f"{s['id']:<34} {s['region']:<7} {s['title']}")
        print(f"\n{len(lib['patterns'])} patterns in intel/threat-patterns.json")
        return 0
    rc = 0
    state = _state(state_path)
    if a.cmd == "fetch" or (a.cmd == "pack" and a.fetch) or (a.cmd == "list" and not state.get("items")):
        found, failed = fetch(feeds, lib)
        new = merge(state, found, today)
        for f in failed:
            print(f"  ! source failed (the others were used): {f}", file=sys.stderr)
        rc = 1 if failed else 0
        if a.cmd != "pack" or state_path.parent.exists():
            _save(state, state_path)
        if a.cmd == "fetch":
            print(f"{new} new headline(s) matched; {len(state['items'])} kept; {len(failed)} source(s) failed.")
            return rc
    pk = pack(lib, state, today)
    if a.cmd == "pack":
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(pk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"pack: {len(pk['patterns'])} patterns, {sum(p['heat'] for p in pk['patterns'])} headlines in {pk['heat_days']} days -> {out}")
        return 0  # a failed source never fails the site build: the pack still carries every drill
    print(report(pk))
    return rc


if __name__ == "__main__":
    sys.exit(main())
