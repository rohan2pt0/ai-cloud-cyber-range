#!/usr/bin/env python3
"""Self-correcting model names: ask each provider which models your key can use TODAY.

WHY: provider model lineups churn (models are retired every few months). A hard-coded default that was fine at
release can start returning 404 and silently knock out the first rung of the fail-over ladder. So at key-setup
time and (at most once a day) at start-up, this asks each provider's own model list and, if the configured model
is gone, switches `<ID>_MODEL` in .env to the best live match from `plugins/catalog.json` -> `discover.prefer`.

  python3 model_discovery.py --env-file .env            # report only
  python3 model_discovery.py --env-file .env --write    # also update .env (then regenerate the router config)

Standard library only. Keys are sent only to their own provider (as `./securax` already does) and never printed.
A network error or an unreachable provider changes NOTHING (offline = keep what you have).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "..", "plugins", "catalog.json")
TIMEOUT = 8


def natural_key(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def parse_env_file(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def set_env_value(path: str, key: str, value: str) -> None:
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    for i, ln in enumerate(lines):
        if ln.startswith(key + "="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def fetch_models(d: dict, key: str, opener=urllib.request.urlopen) -> list[str]:
    """Return live model ids. Raises PermissionError on 401/403, OSError on other network trouble."""
    url, kind = d["url"], d["kind"]
    headers = {"User-Agent": "securax-model-discovery"}
    if kind == "gemini":
        url += ("&" if "?" in url else "?") + "key=" + key
    elif kind == "anthropic":
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = "Bearer " + key
    rewrite = os.environ.get("SECURAX_DISCOVERY_REWRITE", "")      # test hook: send provider calls to a local stand-in
    if rewrite:
        parts = urllib.parse.urlsplit(url)
        headers["Host"] = parts.netloc
        url = rewrite.rstrip("/") + parts.path + ("?" + parts.query if parts.query else "")
    try:
        with opener(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise PermissionError(str(e.code)) from None
        raise OSError(f"http {e.code}") from None
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise OSError(str(e)) from None
    if kind == "gemini":
        return [m["name"].split("/", 1)[-1] for m in data.get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", ["generateContent"])]
    return [m["id"] for m in data.get("data", []) if isinstance(m, dict) and "id" in m]


def pick(models: list[str], prefer: list[str], exclude: str) -> str | None:
    ex = re.compile(exclude, re.I) if exclude else None
    usable = [m for m in models if not (ex and ex.search(m))]
    for pat in prefer:
        rx = re.compile(pat)
        hits = sorted((m for m in usable if rx.search(m)), key=natural_key, reverse=True)
        if hits:
            return hits[0]
    return None


def check(catalog: dict, env: dict[str, str], opener=urllib.request.urlopen) -> list[dict]:
    """One result per provider that has a key AND a discovery recipe."""
    results = []
    exclude = catalog.get("_discover_exclude", "")
    for p in catalog.get("providers", []):
        d = p.get("discover")
        if not d:
            continue
        keys = p.get("env", [])
        key = env.get(keys[0], "") if keys else ""
        if not key:
            continue
        pid, prefix = p["id"], d["prefix"]
        current = env.get(pid.upper() + "_MODEL", "") or p.get("model", "")
        cur_id = current[len(prefix):] if current.startswith(prefix) else current
        r = {"id": pid, "current": current, "status": "", "new": ""}
        try:
            live = fetch_models(d, key, opener)
        except PermissionError:
            r["status"] = "key-rejected"
            results.append(r)
            continue
        except OSError:
            r["status"] = "unreachable"
            results.append(r)
            continue
        if cur_id in live:
            r["status"] = "ok"
        else:
            best = pick(live, d["prefer"], exclude)
            if best:
                r.update(status="replaced", new=prefix + best)
            else:
                r["status"] = "no-match"
        results.append(r)
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"))
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    catalog = json.load(open(a.catalog, encoding="utf-8"))
    env = {**parse_env_file(a.env_file), **{k: v for k, v in os.environ.items() if k.endswith("_API_KEY") or k.endswith("_MODEL")}}
    res = check(catalog, env)
    if not res:
        print("  (no provider keys with a model list to check)")
    changed = 0
    for r in res:
        sym = {"ok": "✔", "replaced": "↻", "key-rejected": "✘", "unreachable": "·", "no-match": "?"}[r["status"]]
        msg = {"ok": f"{r['current']} is live",
               "replaced": f"{r['current']} is gone → using {r['new']}",
               "key-rejected": "the provider REJECTED this key (revoked, mistyped or wrong provider)",
               "unreachable": "could not reach the provider (offline? keeping current)",
               "no-match": f"{r['current']} not found and no known replacement — see the provider's model list"}[r["status"]]
        print(f"  {sym} {r['id']:<11} {msg}")
        if r["status"] == "replaced" and a.write:
            set_env_value(a.env_file, r["id"].upper() + "_MODEL", r["new"])
            changed += 1
    if changed:
        print(f"  updated {changed} model name(s) in {a.env_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
