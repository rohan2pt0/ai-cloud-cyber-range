"""Savings levers: keep them true by themselves (queue scheme-watch, owner 2026-11-15).

Schemes and tax rules change on known dates: the Union Budget (about 1 February), state budgets (March), the small-savings
rate notice (the last day of each quarter) and the new tax year (1 April). This module checks the levers' content and
watches their official sources, so a lever whose source changed is labelled "check before you act" until a person (or a
reviewed pull request) updates it. Fetched pages are DATA, never instructions: only hashed and compared, never executed,
never followed beyond their own host, size-capped, from allow-listed hosts only (threat model scheme-watch).

    python3 governance/levers.py check              validate levers.json and landlord.json; list levers past review
    python3 governance/levers.py calendar           the dates rules usually change, next first
    python3 governance/levers.py watch [--write]    fetch each lever's sources, compare with levers/watch.json;
                                                    --write records new hashes and the changed levers

Standard library only; runs offline for check and calendar.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIR = ROOT / "guiding-map" / "levers"
LEVERS = DIR / "levers.json"
LANDLORD = DIR / "landlord.json"
WATCH = DIR / "watch.json"
MAX_BYTES = 2_000_000
TIMEOUT = 20
NEEDED = ("id", "area", "where", "title", "when", "saves", "steps", "verified", "review", "confidence")
# when rules usually change: (month, day, what)
CALENDAR = [(2, 1, "Union Budget: tax slabs, rebates, new schemes"), (3, 15, "state budgets: state schemes and concessions"),
            (4, 1, "new tax year: regime choice, limits take effect"), (1, 1, "small-savings rates for January to March"),
            (4, 1, "small-savings rates for April to June"), (7, 1, "small-savings rates for July to September"),
            (10, 1, "small-savings rates for October to December")]


def load(path: pathlib.Path = LEVERS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(today: dt.date | None = None) -> list[str]:
    """Problems in the content (empty list = fine). Past-review levers are reported as notes, not problems."""
    today = today or dt.date.today()
    probs: list[str] = []
    data = load()
    seen = set()
    for lv in data.get("levers", []):
        lid = lv.get("id", "?")
        for k in NEEDED:
            if k not in lv:
                probs.append(f"{lid}: missing {k}")
        if lid in seen:
            probs.append(f"{lid}: duplicate id")
        seen.add(lid)
        for k in ("verified", "review"):
            try:
                dt.date.fromisoformat(lv.get(k, ""))
            except ValueError:
                probs.append(f"{lid}: {k} is not a date")
        for u in lv.get("sources", []):
            if not str(u).startswith("https://"):
                probs.append(f"{lid}: source is not https: {u}")
    ll = load(LANDLORD)
    for d in ll.get("duties", []):
        if not d.get("id") or not d.get("title") or not d.get("how"):
            probs.append(f"landlord {d.get('id', '?')}: needs id, title and how")
    return probs


def past_review(today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    return [lv["id"] for lv in load().get("levers", []) if dt.date.fromisoformat(lv["review"]) < today]


def calendar(today: dt.date | None = None) -> list[tuple[dt.date, str]]:
    today = today or dt.date.today()
    out = []
    for m, d, what in CALENDAR:
        x = dt.date(today.year, m, d)
        if x < today:
            x = dt.date(today.year + 1, m, d)
        out.append((x, what))
    return sorted(out)


def allowed_hosts(data: dict | None = None) -> set[str]:
    """Only hosts the content itself cites may be fetched (no host can be injected from outside)."""
    data = data or load()
    hosts = set()
    for lv in data.get("levers", []):
        for u in lv.get("sources", []):
            h = urllib.parse.urlparse(u).hostname
            if h:
                hosts.add(h.lower())
    return hosts


class _SameHost(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).hostname != urllib.parse.urlparse(req.full_url).hostname:
            raise ValueError("redirect leaves the host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, hosts: set[str]) -> bytes:
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or (p.hostname or "").lower() not in hosts or p.port not in (None, 443) or p.username:
        raise ValueError("not an allow-listed https source")
    opener = urllib.request.build_opener(_SameHost)
    req = urllib.request.Request(url, headers={"User-Agent": "securax-levers-watch"})
    with opener.open(req, timeout=TIMEOUT) as r:
        return r.read(MAX_BYTES + 1)[:MAX_BYTES]


def fingerprint(body: bytes) -> str:
    """The page's visible text, normalised, hashed: scripts, styles and markup never count, and nothing is executed."""
    t = body.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", t)
    t = html.unescape(re.sub(r"(?s)<[^>]+>", " ", t))
    t = re.sub(r"\d{1,2}:\d{2}(:\d{2})?", " ", t)          # clocks and visitor counters are not a rule change
    t = re.sub(r"\s+", " ", t).strip().lower()
    return hashlib.sha256(t.encode()).hexdigest()


def watch(write: bool = False, getter=fetch, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    data = load()
    hosts = allowed_hosts(data)
    state = json.loads(WATCH.read_text()) if WATCH.exists() else {"hashes": {}, "changed": {}}
    hashes, changed = state.get("hashes", {}), state.get("changed", {})
    report = {"checked": today.isoformat(), "changed": [], "failed": [], "new": []}
    urls = sorted({u for lv in data.get("levers", []) for u in lv.get("sources", [])})
    moved = set()                                           # each source is fetched once, however many levers cite it
    for u in urls:
        try:
            fp = fingerprint(getter(u, hosts))
        except Exception as e:  # noqa: BLE001 - a dead source is reported, never fatal
            report["failed"].append(f"{u}: {str(e)[:80]}")
            continue
        if u not in hashes:
            report["new"].append(u)
        elif hashes[u] != fp:
            moved.add(u)
        hashes[u] = fp
    for lv in data.get("levers", []):
        if moved.intersection(lv.get("sources", [])):
            report["changed"].append(lv["id"])
            changed[lv["id"]] = today.isoformat()
    report["changed"] = sorted(set(report["changed"]))
    if write:
        WATCH.write_text(json.dumps({"checked": today.isoformat(), "hashes": hashes, "changed": changed}, indent=1, sort_keys=True) + "\n")
    return report


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "check"
    if cmd == "check":
        probs = check()
        for p in probs:
            print("✘", p)
        due = past_review()
        print(f"{len(load()['levers'])} levers; {len(probs)} problem(s); past review: {', '.join(due) or 'none'}")
        return 1 if probs else 0
    if cmd == "calendar":
        for d, what in calendar():
            print(d.isoformat(), what)
        return 0
    if cmd == "watch":
        r = watch(write="--write" in argv)
        print(json.dumps(r, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
