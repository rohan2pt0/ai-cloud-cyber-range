#!/usr/bin/env python3
"""RELEASE: cut a SecuRAX release the way well-run open projects do (small, frequent, notes from the changelog; doc 21).

    python3 tools/release.py plan [--json]     what the next release would be, and its notes (changes nothing)
    python3 tools/release.py cut [--date D]    move [Unreleased] under the new version, bump VERSION, refresh the generated parts
    python3 tools/release.py notes X.Y.Z [--check]   print one version's notes (the GitHub Release body); --check: fail if none

The next version is mechanical, from the [Unreleased] sections (Keep a Changelog, SemVer 2.0):
  only Fixed / Security                  -> PATCH  (0.3.0 -> 0.3.1)
  anything Added / Changed / Removed ... -> MINOR  (0.3.1 -> 0.4.0)
  a line marked BREAKING                 -> MAJOR from 1.0 on; while 0.x it is a MINOR (0.x promises no stability)

Publishing stays a person's decision (doc 102): `cut` only edits files. A release is published when the PR that carries
the cut is merged; the release-tag workflow then tags the merge commit and runs the release workflow. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATCH_ONLY = {"Fixed", "Security"}
HEAD = re.compile(r"^## \[(?P<v>[^\]]+)\](?: - (?P<d>\d{4}-\d{2}-\d{2}))?\s*$", re.M)


def sections(text: str) -> dict[str, str]:
    """Each '## [X]' block of the changelog by its name ('Unreleased', '0.2.0', ...), body only."""
    heads = list(HEAD.finditer(text))
    return {m["v"]: text[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)].strip("\n")
            for i, m in enumerate(heads)}


def kinds(body: str) -> dict[str, int]:
    """How many top-level entries each '### Kind' has."""
    out, cur = {}, None
    for ln in body.splitlines():
        if ln.startswith("### "):
            cur = ln[4:].strip()
            out.setdefault(cur, 0)
        elif cur and ln.startswith("- "):
            out[cur] += 1
    return {k: n for k, n in out.items() if n}


def bump(version: str, body: str) -> tuple[str, str]:
    """(next version, 'major'|'minor'|'patch') for an [Unreleased] body. Raises ValueError when there is nothing to release."""
    k = kinds(body)
    if not k:
        raise ValueError("nothing under [Unreleased]")
    major, minor, patch = (int(x) for x in version.strip().split("."))
    if "BREAKING" in body and major >= 1:
        return f"{major + 1}.0.0", "major"
    if set(k) <= PATCH_ONLY:
        return f"{major}.{minor}.{patch + 1}", "patch"
    return f"{major}.{minor + 1}.0", "minor"


def plan(root: pathlib.Path = ROOT) -> dict:
    text = (root / "CHANGELOG.md").read_text("utf-8")
    cur = (root / "VERSION").read_text("utf-8").strip()
    body = sections(text).get("Unreleased", "")
    try:
        nxt, kind = bump(cur, body)
    except ValueError:
        nxt, kind = "", ""
    return {"current": cur, "next": nxt, "kind": kind, "counts": kinds(body), "notes": body}


def cut(root: pathlib.Path = ROOT, date: str | None = None, refresh: bool = True) -> str:
    """Move [Unreleased] under the next version and bump VERSION. Returns the new version."""
    p = plan(root)
    if not p["next"]:
        raise SystemExit("release: nothing under [Unreleased], so there is nothing to release.")
    date = date or dt.date.today().isoformat()
    cl = root / "CHANGELOG.md"
    text = cl.read_text("utf-8")
    text = text.replace("## [Unreleased]\n", f"## [Unreleased]\n\n## [{p['next']}] - {date}\n", 1)   # a textual edit: the rest stays as written
    cl.write_text(text, "utf-8")
    (root / "VERSION").write_text(p["next"] + "\n", "utf-8")
    if refresh:                 # every visible version label derives from VERSION (doc 21): rebuild what shows it
        for cmd, cwd in ((["node", "build.js"], root / "guiding-map"), ([sys.executable, "tools/readme_sync.py"], root),
                         ([sys.executable, "tools/features_sync.py"], root)):
            subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
    return p["next"]


def notes(version: str, root: pathlib.Path = ROOT) -> str:
    return sections((root / "CHANGELOG.md").read_text("utf-8")).get(version, "").strip() or "See CHANGELOG.md for details."


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax release", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    pl = sub.add_parser("plan")
    pl.add_argument("--json", action="store_true")
    ct = sub.add_parser("cut")
    ct.add_argument("--date")
    nt = sub.add_parser("notes")
    nt.add_argument("version")
    nt.add_argument("--check", action="store_true", help="exit 1 when CHANGELOG.md has no section for VERSION")
    a = ap.parse_args(argv)
    if a.cmd == "cut":
        v = cut(date=a.date)
        print(f"✔ release {v} cut: CHANGELOG.md and VERSION updated. Open a PR; merging it publishes v{v}.")
        return 0
    if a.cmd == "notes":
        if a.check and a.version not in sections((ROOT / "CHANGELOG.md").read_text("utf-8")):
            print(f"release: CHANGELOG.md has no section for {a.version}", file=sys.stderr)
            return 1
        print(notes(a.version))
        return 0
    p = plan()
    if getattr(a, "json", False):
        print(json.dumps(p, indent=1))
    elif not p["next"]:
        print(f"Release {p['current']}: nothing new under [Unreleased].")
    else:
        what = ", ".join(f"{n} {k.lower()}" for k, n in p["counts"].items())
        print(f"Next release: {p['current']} -> {p['next']} ({p['kind']}: {what}).")
        print("To cut it:  ./securax release cut   (then a PR; merging it publishes the release)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
