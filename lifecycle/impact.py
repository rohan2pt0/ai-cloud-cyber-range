#!/usr/bin/env python3
"""IMPACT — before you change something, see what it can hurt; after, see what must be re-proven.

    ./securax impact [--base origin/main] [--json]      files changed -> components touched -> what they feed -> journeys to run

lifecycle/impact.json maps every tracked file to a component, what each component feeds (downstream) and which real-product journeys guard it.
Reading the result: "touches" are the components you edited; "also affected" are everything downstream of them; "run these journeys" are the proofs
for both. A touched component with NO guarding journey is called out as a blind spot. `fitness` fails when a tracked file belongs to no component or a
named journey does not exist, so this map cannot go stale. Standard library only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def load() -> dict:
    return json.loads((HERE / "impact.json").read_text("utf-8"))


def matches(path: str, pat: str) -> bool:
    if pat.endswith("/**"):
        return path.startswith(pat[:-2])
    if "/" not in pat:                                   # a bare pattern matches the file name anywhere or the whole path
        return fnmatch.fnmatch(path.rsplit("/", 1)[-1], pat) or fnmatch.fnmatch(path, pat)
    return fnmatch.fnmatch(path, pat)


def owners(path: str, m: dict) -> list[str]:
    return [n for n, c in m["components"].items() if any(matches(path, p) for p in c["paths"])]


def ignored(path: str, m: dict) -> bool:
    return any(matches(path, p) for p in m["ignore"])


def journeys_defined(root: pathlib.Path = ROOT) -> set[str]:
    return set(re.findall(r'@journey\(\s*"([a-z0-9_]+)"', (root / "sandbox" / "run.py").read_text("utf-8")))


def problems(m: dict, files: list[str], root: pathlib.Path = ROOT) -> list[str]:
    out = []
    jr = journeys_defined(root)
    names = set(m["components"])
    for n, c in m["components"].items():
        for j in c["guarded_by"]:
            if j not in jr:
                out.append(f"{n}: guarded by journey '{j}' which does not exist")
        for a in c["affects"]:
            if a not in names:
                out.append(f"{n}: affects unknown component '{a}'")
    for f in files:
        if not owners(f, m) and not ignored(f, m):
            out.append(f"{f}: belongs to no component (add it to lifecycle/impact.json or its ignore list)")
    return out


def downstream(start: set[str], m: dict) -> set[str]:
    seen, todo = set(), list(start)
    while todo:
        n = todo.pop()
        for a in m["components"][n]["affects"]:
            if a not in seen and a not in start:
                seen.add(a)
                todo.append(a)
    return seen


def tracked(root: pathlib.Path = ROOT) -> list[str]:
    r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
    return [x for x in r.stdout.splitlines() if x]


def changed(base: str, root: pathlib.Path = ROOT) -> list[str]:
    out: set[str] = set()
    for args in (["git", "diff", "--name-only", f"{base}...HEAD"], ["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"],
                 ["git", "ls-files", "--others", "--exclude-standard"]):
        r = subprocess.run(args, cwd=root, capture_output=True, text=True)
        if r.returncode == 0:
            out |= {x for x in r.stdout.splitlines() if x}
    return sorted(out)


def analyse(files: list[str], m: dict) -> dict:
    touched: dict[str, list[str]] = {}
    unowned = []
    for f in files:
        os_ = owners(f, m)
        if not os_:
            if not ignored(f, m):
                unowned.append(f)
            continue
        for o in os_:
            touched.setdefault(o, []).append(f)
    down = downstream(set(touched), m)
    journeys = sorted({j for n in set(touched) | down for j in m["components"][n]["guarded_by"]})
    blind = sorted(n for n in touched if not m["components"][n]["guarded_by"])
    return {"touches": {k: len(v) for k, v in sorted(touched.items())}, "also_affected": sorted(down), "run_journeys": journeys, "blind_spots": blind, "unowned_files": unowned}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    m = load()
    files = changed(a.base)
    res = analyse(files, m)
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    if not files:
        print("No changes against " + a.base + ": nothing to assess.")
        return 0
    print(f"{len(files)} file(s) changed against {a.base}")
    print("  touches:        " + (", ".join(f"{k} ({v})" for k, v in res["touches"].items()) or "nothing mapped"))
    print("  also affected:  " + (", ".join(res["also_affected"]) or "nothing downstream"))
    if res["run_journeys"]:
        print("  prove it still works:   python3 sandbox/run.py -j " + ",".join(res["run_journeys"]))
    print("  always:         ./securax verify     (unit tests, lint, budgets, maps)")
    if res["blind_spots"]:
        print("  ⚠ blind spot (no journey guards this): " + ", ".join(res["blind_spots"]))
    if res["unowned_files"]:
        print("  ⚠ not in the impact map: " + ", ".join(res["unowned_files"][:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
