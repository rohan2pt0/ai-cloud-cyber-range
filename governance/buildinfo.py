#!/usr/bin/env python3
"""Which build is this? The release number (VERSION) changes only when a release is cut; the BUILD changes with every commit.

    python3 governance/buildinfo.py            the label, e.g.  v0.1.0+74 · 21006c7  (74 changes since release 0.1.0)
    python3 governance/buildinfo.py json       everything, as JSON
    python3 governance/buildinfo.py write      guiding-map/build.json, which the Life OS badge and its offline cache read

`./securax up` runs `write` on every start, so the app shows the code that is actually running without anyone bumping a
number by hand. Standard library only; without git it falls back to the release number alone.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "guiding-map" / "build.json"


def _git(root: pathlib.Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def parse_describe(desc: str) -> tuple[int | None, str]:
    """`v0.1.0-74-g21006c7` -> (74, "21006c7"); anything else -> (None, "")."""
    m = re.fullmatch(r"v?.+-(\d+)-g([0-9a-f]+)", desc)
    return (int(m.group(1)), m.group(2)) if m else (None, "")


def label(version: str, changes: int | None, commit: str) -> str:
    if not commit:
        return f"v{version}"
    if changes == 0:
        return f"v{version} · {commit}"                     # exactly the release
    return f"v{version}+{changes} · {commit}" if changes else f"v{version} · {commit}"


def info(root: pathlib.Path = ROOT) -> dict:
    try:
        version = (root / "VERSION").read_text("utf-8").strip() or "0.0.0-dev"
    except OSError:
        version = "0.0.0-dev"
    # changes are counted from THIS release's tag; before it is tagged there is no count (never "0.2.0+74" from 0.1.0's tag)
    changes, commit = parse_describe(_git(root, "describe", "--tags", "--long", "--match", f"v{version}"))
    commit = commit or _git(root, "rev-parse", "--short", "HEAD")
    return {"version": version, "changes": changes, "commit": commit, "date": _git(root, "log", "-1", "--format=%cs"),
            "label": label(version, changes, commit)}


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "label"
    i = info()
    if cmd == "json":
        print(json.dumps(i))
    elif cmd == "write":
        OUT.write_text(json.dumps(i) + "\n", "utf-8")
        print(i["label"])
    elif cmd == "label":
        print(i["label"])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
