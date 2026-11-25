#!/usr/bin/env python3
"""CHANGELOG FRAGMENTS: parallel pull requests never clash on CHANGELOG.md; each change adds its own file and a fold
brings them together (queue changelog-fragments).

    python3 tools/changelog_fold.py [ROOT]

Each change writes changes/<branch>.md: name the file after your branch, one line, no bullet. The fold moves every
fragment to the top of [Unreleased] in file-name order (each as a bullet) and removes the files. Running it with no
fragments changes nothing. A fragment that is empty or longer than one line is refused and nothing is written.
Standard library only.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD = re.compile(r"^## \[Unreleased\][ \t]*$", re.M)


def fold(root: pathlib.Path = ROOT) -> int:
    """Fold changes/*.md into the top of [Unreleased] and return how many were folded."""
    root = pathlib.Path(root)
    folder = root / "changes"
    files = sorted(folder.glob("*.md"), key=lambda p: p.name) if folder.is_dir() else []
    if not files:
        return 0
    lines = []
    for p in files:
        text = p.read_text("utf-8").strip()
        if not text:
            raise ValueError(f"{p.relative_to(root)}: the changelog fragment is empty; "
                             "name the file after your branch, write one line, no bullet.")
        if len(text.splitlines()) > 1:
            raise ValueError(f"{p.relative_to(root)}: a changelog fragment must be one line; "
                             "name the file after your branch, write one line, no bullet.")
        lines.append(text)
    cl = root / "CHANGELOG.md"
    changelog = cl.read_text("utf-8")
    m = HEAD.search(changelog)
    if not m:
        raise ValueError("CHANGELOG.md has no [Unreleased] section")
    add = "\n" + "\n".join(f"- {line}" for line in lines)
    cl.write_text(changelog[:m.end()] + add + changelog[m.end():], "utf-8")
    for p in files:
        p.unlink()
    return len(files)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="changelog_fold", description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", default=str(ROOT), help="repository root (default: this checkout)")
    a = ap.parse_args(argv)
    try:
        count = fold(a.root)
    except ValueError as exc:
        print(f"changelog_fold: {exc}", file=sys.stderr)
        return 1
    print(f"changelog_fold: {count} fragment(s) folded into CHANGELOG.md" if count else "changelog_fold: no fragments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
