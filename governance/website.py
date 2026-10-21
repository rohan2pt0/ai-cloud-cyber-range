#!/usr/bin/env python3
"""The public site's address, and putting it on your own domain without breaking a link (doc 99).

    ./securax site                 where the site answers now, and whether your domain is ready
    ./securax site domain NAME     use NAME (for example example.org): prints the DNS records and the one GitHub setting
    ./securax site live            checks NAME answers over HTTPS with this site, then switches every link to it
    ./securax site off             go back to the GitHub Pages address (links stop pointing at the domain)
    ./securax site check           build-free check of the README's links (the site build checks every page)

Until a domain is live, every page, the README and the docs point at the GitHub Pages address, which always works.
`site live` refuses until the domain resolves to GitHub Pages AND serves this site over HTTPS, so no link is ever
switched to an address that is not there yet. Standard library only.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "governance"))
import config  # noqa: E402

PAGES_A = ("185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153")   # GitHub Pages docs, Oct 2026
PAGES_AAAA = ("2606:50c0:8000::153", "2606:50c0:8001::153", "2606:50c0:8002::153", "2606:50c0:8003::153")
DOMAIN = re.compile(r"(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")


def set_brand(key: str, value: str, path: pathlib.Path | None = None) -> None:
    """Change one KEY=value line in brand.env, keeping every comment and the order (never a rewrite of the file)."""
    path = path or config.BRAND_FILE
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    for i, ln in enumerate(lines):
        if re.match(rf"^\s*{key}\s*=", ln):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", "utf-8")


def pages_host(vals: dict[str, str]) -> str:
    owner = vals.get("REPO_SLUG", "").split("/")[0].lower()
    return f"{owner}.github.io" if owner else "OWNER.github.io"


def resolves(name: str) -> set[str]:
    try:
        return {ai[4][0] for ai in socket.getaddrinfo(name, 443, proto=socket.IPPROTO_TCP)}
    except OSError:
        return set()


def answers(url: str, timeout: float = 15) -> tuple[bool, str]:
    """(serves this site, what happened). This site = the page carries the product name."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "securax-site-check"}), timeout=timeout) as r:
            body = r.read(200_000).decode("utf-8", "ignore")
            ok = r.status == 200 and config.values().get("PRODUCT_NAME", "SecuRAX") in body
            return ok, f"HTTP {r.status}" + ("" if ok else ", but it is not this site")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - any failure is the answer
        return False, type(e).__name__ + (f": {e.reason}" if getattr(e, "reason", None) else "")


def records(dom: str, vals: dict[str, str]) -> list[str]:
    host = pages_host(vals)
    apex = dom.count(".") == 1
    if apex:
        return [f"A     {dom}   {ip}" for ip in PAGES_A] + [f"AAAA  {dom}   {ip}" for ip in PAGES_AAAA] + [f"CNAME www.{dom}   {host}."]
    return [f"CNAME {dom}   {host}."]


def status(vals: dict[str, str], say=print) -> int:
    url, dom = vals["SITE_URL"], vals.get("SITE_DOMAIN", "")
    live = url.startswith(f"https://{dom}/") if dom else False
    say(f"The site answers at: {url or '(no address: set REPO_SLUG in brand.env)'}")
    if not dom:
        say("No domain set. To use your own:  ./securax site domain example.org")
        return 0
    if live:
        ok, why = answers(url)
        say(f"Your domain {dom} is live: {'✔ ' + why if ok else '✗ ' + why + ' — check DNS, or go back with  ./securax site off'}")
        return 0 if ok else 1
    ips = resolves(dom)
    say(f"Your domain {dom} is set but not live yet, so no link points at it.")
    if not ips:
        say("  DNS: it does not resolve yet. Add these records at your DNS provider:")
        for r in records(dom, vals):
            say("    " + r)
    else:
        on_pages = bool(ips & set(PAGES_A + PAGES_AAAA))
        say(f"  DNS: resolves to {', '.join(sorted(ips))}" + ("" if on_pages else
            " (not GitHub Pages: if it is behind Cloudflare's proxy that is fine; otherwise check the records)"))
    say(f"  GitHub: Settings → Pages → Custom domain → {dom} → Save, then tick Enforce HTTPS once it is offered.")
    say("  Then:  ./securax site live")
    return 0


def go_live(vals: dict[str, str], say=print, brand: pathlib.Path | None = None) -> int:
    dom = vals.get("SITE_DOMAIN", "")
    if not dom:
        say("✗ No domain set. First:  ./securax site domain example.org")
        return 2
    if not resolves(dom):
        say(f"✗ {dom} does not resolve yet. Nothing changed; every link keeps the working address. See:  ./securax site")
        return 1
    ok, why = answers(f"https://{dom}/")
    if not ok:
        say(f"✗ https://{dom}/ does not serve this site yet ({why}). Nothing changed. See:  ./securax site")
        return 1
    set_brand("SITE_LIVE", "yes", brand)
    say(f"✔ {dom} serves this site over HTTPS. Every link now points at https://{dom}/.")
    say("  Next: commit brand.env and README.md (python3 tools/readme_sync.py refreshes the README), and push.")
    say("  If you build in CI from repository variables, also set the variable SITE_LIVE=yes.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("domain")
    d.add_argument("name")
    sub.add_parser("live")
    sub.add_parser("off")
    sub.add_parser("check")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    vals = config.values()
    if a.cmd == "domain":
        dom = a.name.lower().removeprefix("https://").removeprefix("http://").strip("/")
        if not DOMAIN.fullmatch(dom):
            print(f"✗ {a.name!r} is not a domain name (like example.org, no path)")
            return 2
        set_brand("SITE_DOMAIN", dom)
        set_brand("SITE_LIVE", "no")
        print(f"✔ domain set to {dom}. Links keep the working address until it is live.\n")
        return status(config.values())
    if a.cmd == "live":
        return go_live(vals)
    if a.cmd == "off":
        set_brand("SITE_LIVE", "no")
        print(f"✔ links point at {config.values()['SITE_URL']} again (the domain stays set for later)")
        return 0
    if a.cmd == "check":
        return subprocess.call([sys.executable, str(ROOT / "tools" / "linkcheck.py"), "--readme"])
    return status(vals)


if __name__ == "__main__":
    sys.exit(main())
