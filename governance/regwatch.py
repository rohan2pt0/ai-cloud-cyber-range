#!/usr/bin/env python3
"""Regulator watch: new RBI and SEBI circulars, directions and press releases, fetched from the regulators' own RSS feeds.

    ./securax regwatch fetch [--notify] [--quiet]   fetch every feed, keep NEW items in vault/regwatch.json;
                                                    --notify pushes the new titles to your phone (ntfy / webhook)
    ./securax regwatch list [--days 30] [--regulator RBI]
    ./securax regwatch digest [--month 2026-10] [--out FILE] [--send]
                                                    the monthly digest as Markdown (stdout, a file, or your phone)
    ./securax regwatch sources                      the feeds and the regulators to check by hand

Sources and filters are data: governance/regwatch-feeds.json. The first fetch of a feed records what is already there
without alerting, so you are told only about items published after you started watching.

Honesty rules: titles, dates and links only, exactly as the regulator published them. Nothing is summarised or
interpreted, because a wrong summary of a circular is worse than none: read the source before acting. A link that does
not point to the regulator's own site is dropped.
Standard library only. Exit codes: 0 ok, 1 a feed failed (the others are still kept), 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
FEEDS = ROOT / "governance" / "regwatch-feeds.json"
STATE = ROOT / "vault" / "regwatch.json"
MAX_BYTES = 4_000_000
UA = "Mozilla/5.0 (SecuRAX regwatch; +https://cyberbaba.org)"
_CTRL = re.compile(r"[\x00-\x1f\x7f​-‏‪-‮⁠-⁤﻿]")


def load_sources(path: pathlib.Path = FEEDS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_state(path: pathlib.Path = STATE) -> dict:
    try:
        s = json.loads(path.read_text(encoding="utf-8"))
        return s if isinstance(s, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(state: dict, path: pathlib.Path = STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def clean(text: str, limit: int = 300) -> str:
    """Plain, single-line text: no control or invisible characters (they hide instructions), no HTML tags."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = _CTRL.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def parse_date(raw: str) -> str:
    """RBI sends RFC-822 ('Mon, 12 Oct 2026 23:55:00'), SEBI '16 Oct, 2026 +0530'. Returns YYYY-MM-DD or ''."""
    raw = (raw or "").strip()
    try:
        return email.utils.parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*,?\s+(\d{4})", raw)
    if m:
        try:
            return dt.datetime.strptime(" ".join(m.groups()), "%d %b %Y").date().isoformat()
        except ValueError:
            return ""
    return ""


def safe_link(link: str, hosts: list[str]) -> str:
    u = urllib.parse.urlparse((link or "").strip())
    host = (u.hostname or "").lower()
    if u.scheme in ("http", "https") and any(host == h or host.endswith("." + h) for h in hosts):
        return u._replace(scheme="https").geturl()
    return ""


def parse_feed(data: bytes, feed: dict) -> list[dict]:
    """RSS 2.0 items after the feed's filters. Refuses DTDs and entity declarations (entity-expansion attacks)."""
    if len(data) > MAX_BYTES:
        raise ValueError("feed too large")
    if re.search(rb"<!(DOCTYPE|ENTITY)", data[:4096] + data[-4096:], re.I) or b"<!ENTITY" in data:
        raise ValueError("feed declares a DTD or entities: refused")
    root = ET.fromstring(data.lstrip(b"\xef\xbb\xbf \r\n\t"))
    inc = re.compile(feed["include_link"], re.I) if feed.get("include_link") else None
    exc = re.compile(feed["exclude_title"], re.I) if feed.get("exclude_title") else None
    items = []
    for it in root.iter("item"):
        title = clean(it.findtext("title") or "")
        link = safe_link(it.findtext("link") or "", feed.get("link_hosts") or [])
        if not title or (inc and not inc.search(link)) or (exc and exc.search(title)):
            continue
        items.append({"title": title, "link": link, "published": parse_date(it.findtext("pubDate") or "")})
    return items


def key(feed_id: str, item: dict) -> str:
    return hashlib.sha256(f"{feed_id}|{item['link'] or item['title']}".encode()).hexdigest()[:16]


def merge(state: dict, feed: dict, items: list[dict], today: str) -> list[dict]:
    """Add unseen items; return the NEW ones. A feed's first fetch is a silent baseline (nothing is 'new')."""
    store = state.setdefault("items", {})
    seen_feeds = state.setdefault("feeds_seen", [])
    first = feed["id"] not in seen_feeds
    new = []
    for item in items:
        k = key(feed["id"], item)
        if k in store:
            continue
        rec = {**item, "regulator": feed["regulator"], "feed": feed["id"], "first_seen": today, "baseline": first}
        store[k] = rec
        if not first:
            new.append(rec)
    if first:
        seen_feeds.append(feed["id"])
    return new


def fetch_url(url: str, timeout: int = 30) -> bytes:
    if not url.startswith("https://"):
        raise ValueError("feeds must be https")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:            # noqa: S310 (https only, checked above)
        return r.read(MAX_BYTES + 1)


def fetch_all(sources: dict, state: dict, getter=fetch_url, today: str | None = None) -> tuple[list[dict], list[str]]:
    today = today or dt.date.today().isoformat()
    new, errors = [], []
    for feed in sources.get("feeds", []):
        try:
            new += merge(state, feed, parse_feed(getter(feed["url"]), feed), today)
            state.setdefault("last_ok", {})[feed["id"]] = today
        except Exception as e:                                          # one broken feed must not hide the others
            errors.append(f"{feed['id']}: {type(e).__name__}: {clean(str(e), 120)}")
    state["last_fetch"] = today
    return new, errors


def items_between(state: dict, start: str, end: str, regulator: str | None = None) -> list[dict]:
    """Items whose date (published, else first seen) falls in [start, end], newest first. Baseline items are included:
    they were genuinely published in that window, we just did not alert on them."""
    out = []
    for it in state.get("items", {}).values():
        d = it.get("published") or it.get("first_seen", "")
        if start <= d <= end and (not regulator or it.get("regulator", "").lower() == regulator.lower()):
            out.append(it)
    return sorted(out, key=lambda i: (i.get("published") or i.get("first_seen", ""), i["title"]), reverse=True)


def month_range(month: str) -> tuple[str, str]:
    y, m = (int(x) for x in month.split("-"))
    start = dt.date(y, m, 1)
    end = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
    return start.isoformat(), end.isoformat()


def digest(state: dict, sources: dict, month: str) -> str:
    start, end = month_range(month)
    label = dt.date.fromisoformat(start).strftime("%B %Y")
    lines = [f"# Regulator watch: {label}", "",
             "Titles, dates and links exactly as the regulators published them. Nothing here is a summary or advice:",
             "read the source before acting.", ""]
    regs = [f["regulator"] for f in sources.get("feeds", [])]
    for reg in dict.fromkeys(regs):
        its = items_between(state, start, end, reg)
        lines += [f"## {reg} ({len(its)})", ""]
        lines += [f"- {i.get('published') or i['first_seen']} · [{i['title']}]({i['link']})" if i["link"]
                  else f"- {i.get('published') or i['first_seen']} · {i['title']}" for i in its] or ["- nothing new"]
        lines.append("")
    if sources.get("manual"):
        lines += ["## Check by hand (no feed published)", ""]
        lines += [f"- [{m['title']}]({m['url']})" for m in sources["manual"]]
        lines.append("")
    if state.get("last_fetch"):
        lines.append(f"_Last fetched {state['last_fetch']}. Sources and filters: governance/regwatch-feeds.json._")
    return "\n".join(lines).rstrip() + "\n"


def alert_text(new: list[dict]) -> str:
    head = f"{len(new)} new regulator item(s):"
    body = [f"• {i['regulator']}: {i['title']}" + (f" {i['link']}" if i["link"] else "") for i in new[:10]]
    if len(new) > 10:
        body.append(f"…and {len(new) - 10} more: ./securax regwatch list")
    return "\n".join([head, *body])


def _deliver(text: str, title: str) -> int:
    sys.path.insert(0, str(ROOT / "governance"))
    import notify  # noqa: PLC0415 (optional channel, loaded on use)
    return notify.deliver(text, title=title)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax regwatch", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("fetch")
    f.add_argument("--notify", action="store_true")
    f.add_argument("--quiet", action="store_true")
    ls = sub.add_parser("list")
    ls.add_argument("--days", type=int, default=30)
    ls.add_argument("--regulator")
    d = sub.add_parser("digest")
    d.add_argument("--month", default=dt.date.today().strftime("%Y-%m"), help="YYYY-MM, or 'last' for last month")
    d.add_argument("--out")
    d.add_argument("--send", action="store_true")
    sub.add_parser("sources")
    a = ap.parse_args(argv)
    sources, state = load_sources(), load_state()

    if a.cmd == "fetch":
        new, errors = fetch_all(sources, state)
        save_state(state)
        for e in errors:
            print(f"feed failed: {e}", file=sys.stderr)
        if new and not a.quiet:
            print(alert_text(new))
        elif not a.quiet:
            print(f"nothing new ({len(state.get('items', {}))} items tracked)")
        if new and a.notify:
            _deliver(alert_text(new), "Regulator watch")
        return 1 if errors else 0
    if a.cmd == "list":
        end = dt.date.today()
        its = items_between(state, (end - dt.timedelta(days=a.days)).isoformat(), end.isoformat(), a.regulator)
        for i in its:
            print(f"{i.get('published') or i['first_seen']}  {i['regulator']:<5} {i['title']}\n{'':17}{i['link']}")
        if not its:
            print("nothing in that window (run: ./securax regwatch fetch)")
        return 0
    if a.cmd == "digest":
        if a.month == "last":
            a.month = (dt.date.today().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", a.month):
            print("--month must look like 2026-10", file=sys.stderr)
            return 2
        md = digest(state, sources, a.month)
        if a.out:
            pathlib.Path(a.out).write_text(md, encoding="utf-8")
            print(f"wrote {a.out}")
        elif not a.send:
            print(md, end="")
        if a.send:
            return _deliver(md, f"Regulator digest {a.month}")
        return 0
    if a.cmd == "sources":
        for fd in sources.get("feeds", []):
            print(f"{fd['regulator']:<8} {fd['title']}\n{'':9}{fd['url']}  (last ok: {state.get('last_ok', {}).get(fd['id'], 'never')})")
        for m in sources.get("manual", []):
            print(f"{m['regulator']:<8} {m['title']}\n{'':9}{m['url']}  (check by hand)")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
