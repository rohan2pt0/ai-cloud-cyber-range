#!/usr/bin/env python3
"""Names that must never appear in this public repository: organisations, exercises, people (doc 65).

    ./securax privacy check            scan every tracked file; exit 1 and name the file and line if a listed name appears
    ./securax privacy add "Some Name"  add a name to the list (only its fingerprint is stored, never the name)

How it works: the list in governance/private-names.json holds SHA-256 fingerprints of lower-cased names (one to six words),
not the names themselves, so the guard does not reveal what it guards. Every word, and every run of two to six words, in
every tracked text file is fingerprinted and compared. A second, private list can sit in vault/private-names.txt (plain names,
one per line, never committed). A fingerprint hides a name from a casual reader; it does not stop someone confirming a guess.
Runs in CI as the fitness check `private-names`. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIST = ROOT / "governance" / "private-names.json"
PRIVATE = ROOT / "vault" / "private-names.txt"
WORD = re.compile(r"[a-z0-9]+")
SKIP = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".pdf", ".xlsx", ".docx", ".zip", ".gz", ".woff", ".woff2", ".ttf")


def fingerprint(name: str) -> str:
    return hashlib.sha256(" ".join(WORD.findall(name.lower())).encode()).hexdigest()


def load(path: pathlib.Path = LIST, private: pathlib.Path = PRIVATE) -> set[str]:
    fps = set(json.loads(path.read_text("utf-8")).get("fingerprints", [])) if path.exists() else set()
    if private.exists():
        fps |= {fingerprint(n) for n in private.read_text("utf-8").splitlines() if n.strip() and not n.startswith("#")}
    return fps


def hits(text: str, fps: set[str]) -> list[tuple[int, str]]:
    """(line number, matched words) for every listed name in the text."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        words = WORD.findall(line.lower())
        for size in range(1, 7):
            for i in range(len(words) - size + 1):
                phrase = " ".join(words[i:i + size])
                if hashlib.sha256(phrase.encode()).hexdigest() in fps:
                    out.append((n, phrase))
    return out


def tracked(root: pathlib.Path = ROOT) -> list[str]:
    r = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True)
    return [f for f in r.stdout.splitlines() if not f.lower().endswith(SKIP)]


def problems(root: pathlib.Path = ROOT, fps: set[str] | None = None) -> list[str]:
    fps = load() if fps is None else fps
    found = []
    for f in tracked(root):
        if fingerprint(pathlib.Path(f).stem.replace("-", " ").replace("_", " ")) in fps:
            found.append(f"{f}: the file name")
        try:
            text = (root / f).read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found += [f"{f}:{n}" for n, _ in hits(text, fps)]
    return found


def add(name: str, path: pathlib.Path = LIST) -> bool:
    data = json.loads(path.read_text("utf-8")) if path.exists() else {"about": "", "fingerprints": []}
    fp = fingerprint(name)
    if fp in data["fingerprints"]:
        return False
    data["fingerprints"] = sorted(set(data["fingerprints"]) | {fp})
    path.write_text(json.dumps(data, indent=1) + "\n", "utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check")
    a_add = sub.add_parser("add")
    a_add.add_argument("name")
    a = ap.parse_args(argv)
    if a.cmd == "add":
        print("✔ added (only its fingerprint is stored)" if add(a.name) else "already on the list")
        return 0
    found = problems()
    if not found:
        print("✔ no private name appears in any tracked file")
        return 0
    print("✗ a private name appears here (reword it, or rename the file):")
    for p in found[:50]:
        print("  " + p)
    if len(found) > 50:
        print(f"  … and {len(found) - 50} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
