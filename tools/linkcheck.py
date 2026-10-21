#!/usr/bin/env python3
"""Every link on the built site works (doc 99).

    python3 tools/linkcheck.py website              every internal link, image and anchor exists; no link to a domain
                                                   that is not live yet (offline, fast: CI runs it on every build)
    python3 tools/linkcheck.py website --external  also open every link to another site (weekly in CI; needs network)
    python3 tools/linkcheck.py --readme            the README's own links: files exist, no link to a domain not live yet

An internal link is resolved to a file in the built folder, the way a static host serves it (a folder means its
index.html). A site that blocks robots (403, 429) is reported as unknown, never as broken: only "not found", "gone"
and an address that does not resolve count. Exit 1 when anything is broken. Standard library only.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html.parser
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "governance"))
import config  # noqa: E402

SKIP = ("mailto:", "tel:", "javascript:", "data:", "blob:")
BLOCKED = {401, 403, 405, 406, 429, 451, 999}


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("id", "name"):
            if a.get(k) and (k == "id" or tag == "a"):
                self.ids.add(a[k])
        for k in ("href", "src"):
            v = (a.get(k) or "").strip()
            if v and not (tag == "link" and (a.get("rel") or "") in ("preconnect", "dns-prefetch")):
                self.links.append(v)


def parse(path: pathlib.Path) -> Page:
    p = Page()
    p.feed(path.read_text("utf-8", "ignore"))
    return p


def target(site: pathlib.Path, page: pathlib.Path, url: str, base: str = "/") -> pathlib.Path | None:
    """base: the folder the site is served from (/ on your domain, /REPO/ on GitHub Pages); a /-path starts there."""
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    if not path:
        return page
    if path.startswith("/"):
        path = path[len(base):] if path.startswith(base) else path.lstrip("/")
        t = site / path
    else:
        t = page.parent / path
    t = pathlib.Path(os.path.normpath(t))
    if t.is_dir():
        t = t / "index.html"
    return t if t.exists() else None


def not_live_domain(vals: dict[str, str]) -> str:
    """The brand domain, when links to it would not work yet (SITE_LIVE is not yes)."""
    dom = vals.get("SITE_DOMAIN", "").lower()
    return dom if dom and vals.get("SITE_URL", "").find(dom) < 0 else ""


def check_site(site: pathlib.Path, vals: dict[str, str]) -> tuple[list[str], set[str], int]:
    pages = {p: parse(p) for p in site.rglob("*.html")}
    dead_dom = not_live_domain(vals)
    base = urllib.parse.urlsplit(vals.get("SITE_URL") or "/").path or "/"
    broken, external, n = [], set(), 0
    for page, info in pages.items():
        rel = page.relative_to(site)
        for url in info.links:
            if url.startswith(SKIP):
                continue
            n += 1
            parts = urllib.parse.urlsplit(url)
            if parts.scheme in ("http", "https") or url.startswith("//"):
                host = (parts.hostname or "").lower()
                if dead_dom and (host == dead_dom or host.endswith("." + dead_dom)):
                    broken.append(f"{rel}: links to {url}, but {dead_dom} is not live yet (./securax site status)")
                else:
                    external.add(url.split("#")[0])
                continue
            t = target(site, page, url, base)
            if t is None:
                broken.append(f"{rel}: {url} does not exist")
            elif parts.fragment and t.suffix == ".html" and t in pages and parts.fragment not in pages[t].ids:
                broken.append(f"{rel}: {url} has no anchor #{parts.fragment}")
    return broken, external, n


def check_readme(vals: dict[str, str]) -> list[str]:
    text = re.sub(r"```.*?```", "", (ROOT / "README.md").read_text("utf-8"), flags=re.S)
    dead_dom, out = not_live_domain(vals), []
    for url in re.findall(r"\]\(([^)\s]+)\)", text):
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
        if dead_dom and (host == dead_dom or host.endswith("." + dead_dom)):
            out.append(f"README.md: links to {url}, but {dead_dom} is not live yet")
        elif not re.match(r"^[a-z]+:", url) and not url.startswith("#") and not (ROOT / url.split("#")[0]).exists():
            out.append(f"README.md: {url} does not exist")
    return out


def fetch(url: str) -> int | str:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0 (linkcheck; SecuRAX docs)"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code not in (400, 403, 404, 405, 501):
                return e.code
        except Exception as e:  # noqa: BLE001 - any network failure is a result to report
            if method == "GET":
                return type(e).__name__
    return "unknown"


def check_external(urls: set[str]) -> tuple[list[str], list[str]]:
    with cf.ThreadPoolExecutor(16) as ex:
        res = dict(zip(sorted(urls), ex.map(fetch, sorted(urls))))
    dead = [f"{s} {u}" for u, s in res.items() if s in (404, 410) or s == "URLError"]
    unknown = [f"{s} {u}" for u, s in res.items() if s != 200 and f"{s} {u}" not in dead and not (isinstance(s, int) and s < 400)]
    return dead, unknown


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("site", nargs="?", help="the built site folder (website/)")
    ap.add_argument("--external", action="store_true", help="also open every link to another site")
    ap.add_argument("--readme", action="store_true", help="check README.md's links")
    a = ap.parse_args(argv)
    vals = config.values()
    broken: list[str] = []
    if a.readme:
        broken += check_readme(vals)
    if a.site:
        site = pathlib.Path(a.site)
        if not site.is_dir():
            print(f"✗ no built site at {site}: run  bash website/build.sh")
            return 1
        b, external, n = check_site(site, vals)
        broken += b
        print(f"{n} links checked on {len(list(site.rglob('*.html')))} pages; {len(external)} go to other sites")
        if a.external:
            dead, unknown = check_external(external)
            broken += [f"dead link to another site: {d}" for d in dead]
            for u in unknown:
                print(f"  ? {u}   (the site refused a robot or timed out; check it by hand)")
    for b in broken:
        print(f"✗ {b}")
    print("✔ every link works" if not broken else f"{len(broken)} broken link(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
