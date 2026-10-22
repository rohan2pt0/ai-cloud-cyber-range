"""Are the digest pins still current? (doc 87) For every service in local/compose/digest-pins.json, ask the registry
what digest its pinned TAG points at today. A tag that moved (a maintainer rebuilt it, usually for security fixes)
means the pin is stale: run with --write to take the new digest, then review the change like any other.

    python3 tools/digest_check.py            report: current, moved, or could not check (exit 1 if any moved)
    python3 tools/digest_check.py --write    also rewrite the moved pins in the compose files (text edit, nothing else)

It does not depend on Dependabot reading every compose file name. The weekly supply-chain-watch job runs it.
Standard library only; the network is used only to ask the registries, never to pull an image.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "local" / "compose"
PINNED = re.compile(r"^(?P<ref>[^@\s]+):(?P<tag>[^@\s:/]+)@(?P<digest>sha256:[0-9a-f]{64})$")
ACCEPT = ", ".join(["application/vnd.oci.image.index.v1+json", "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.oci.image.manifest.v1+json", "application/vnd.docker.distribution.manifest.v2+json"])


def split_ref(ref: str) -> tuple[str, str]:
    """'nginx' -> registry-1.docker.io, library/nginx; 'ghcr.io/o/r' -> ghcr.io, o/r."""
    first = ref.split("/", 1)[0]
    if "/" in ref and ("." in first or ":" in first or first == "localhost"):
        host, repo = ref.split("/", 1)
    else:
        host, repo = "registry-1.docker.io", ref if "/" in ref else f"library/{ref}"
    return host, repo


def _bearer(challenge: str, repo: str, opener) -> str:
    """Anonymous token from the registry's own WWW-Authenticate challenge (Docker Hub, ghcr.io and others)."""
    params = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
    realm = params.pop("realm", "")
    if not realm.startswith("https://"):
        return ""
    params.setdefault("scope", f"repository:{repo}:pull")
    with opener(urllib.request.Request(realm + "?" + urllib.parse.urlencode(params)), timeout=20) as r:
        body = json.loads(r.read())
    return body.get("token") or body.get("access_token") or ""


def current_digest(ref: str, tag: str, opener=urllib.request.urlopen, sleep=time.sleep) -> str:
    host, repo = split_ref(ref)
    url = f"https://{host}/v2/{repo}/manifests/{tag}"
    headers = {"Accept": ACCEPT}
    for attempt in range(4):
        try:
            with opener(urllib.request.Request(url, method="HEAD", headers=headers), timeout=20) as r:
                return r.headers.get("Docker-Content-Digest", "")
        except urllib.error.HTTPError as e:
            if e.code == 401 and "Authorization" not in headers:
                headers["Authorization"] = "Bearer " + _bearer(e.headers.get("WWW-Authenticate", ""), repo, opener)
                continue
            if e.code == 429 and attempt < 3:              # Docker Hub's anonymous rate limit: wait as asked, at most 10 s
                sleep(min(10.0, float(e.headers.get("Retry-After") or 3)))
                continue
            raise
    return ""


def pins() -> list[dict]:
    """Every pinned service: file, service, image line, ref, tag, digest."""
    spec = json.loads((COMPOSE / "digest-pins.json").read_text("utf-8"))
    out = []
    for fname, services in spec["files"].items():
        text = (COMPOSE / fname).read_text("utf-8")
        for svc in services:
            m = re.search(rf"(?m)^  {re.escape(svc)}:\n(?:(?!^  \S).*\n)*?\s+image:\s*(\S+)", text)
            pm = PINNED.match(m.group(1)) if m else None
            out.append({"file": fname, "service": svc, "image": m.group(1) if m else "", **(pm.groupdict() if pm else {})})
    return out


def check(opener=urllib.request.urlopen) -> list[dict]:
    rows = []
    for p in pins():
        if "digest" not in p:
            rows.append({**p, "state": "not pinned"})
            continue
        try:
            now = current_digest(p["ref"], p["tag"], opener)
        except (OSError, ValueError) as e:
            rows.append({**p, "state": "could not check", "why": str(e)[:120]})
            continue
        rows.append({**p, "now": now, "state": "current" if now == p["digest"] else ("moved" if now else "could not check")})
    return rows


def write(rows: list[dict]) -> int:
    n = 0
    for r in rows:
        if r["state"] == "moved":
            f = COMPOSE / r["file"]
            text = f.read_text("utf-8")
            new = f"{r['ref']}:{r['tag']}@{r['now']}"
            if text.count(r["image"]) == 1:
                f.write_text(text.replace(r["image"], new), "utf-8")
                n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    rows = check()
    for r in rows:
        print(f"  {r['state']:<15} {r['file']}:{r['service']:<14} {r['image']}" + (f"\n                  now {r['now']}" if r["state"] == "moved" else "")
              + (f"   ({r['why']})" if r.get("why") else ""))
    moved = [r for r in rows if r["state"] in ("moved", "not pinned")]
    if a.write and moved:
        print(f"rewrote {write(rows)} pin(s); review the diff, run the tests, then open a pull request")
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
