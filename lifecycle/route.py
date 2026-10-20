#!/usr/bin/env python3
"""Which builder a task goes to: the local/cheap tier, OpenCode, or the strong open models, and why (docs 23 and 83).

    ./securax route "add a /metrics endpoint with a test"           before the work: from the words and any paths named
    ./securax route "…" --files a.py b.py                           with the files you expect to touch
    ./securax route "…" --base main                                 after the work: from what the diff actually touched
    ./securax route "…" --json

The rules are data (lifecycle/route.json): the STRONG tier for security, crypto, identity, sync and merge logic, regulator mapping, a
listed sensitive path, or a change across many areas (components from lifecycle/impact.json); OpenCode for a few areas or a
wiring job; local for the rest. autobuild asks this first and builds a strong-tier task with the strong chain (the strongest open
models, through the same gates) instead of spending three cheap attempts on it. The strong tier was "claude" before doc 83; old
rule files (claude_paths / claude_words) still load. Exit codes: 0 always for a decision, 2 bad usage.
"""
from __future__ import annotations

import fnmatch
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = pathlib.Path(__file__).resolve().parent / "route.json"
IMPACT = pathlib.Path(__file__).resolve().parent / "impact.json"


def _load(p: pathlib.Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _match(path: str, pats: list[str]) -> str | None:
    return next((p for p in pats if fnmatch.fnmatch(path, p) or (p.endswith("/**") and path.startswith(p[:-3] + "/"))), None)


def areas(files: list[str], impact: dict | None = None) -> list[str]:
    comps = (impact if impact is not None else _load(IMPACT)).get("components", {})
    out = []
    for f in files:
        for name, c in comps.items():
            if _match(f, c.get("paths", [])) and name not in out:
                out.append(name)
                break
    return out


def named_paths(task: str) -> list[str]:
    """Paths written in the task itself ("fix governance/finish.py"), so a pre-work decision can use them."""
    return [m.strip(".,;:'\"`()") for m in re.findall(r"[\w.-]+(?:/[\w.*-]+)+", task)]


def decide(task: str, files: list[str] | None = None, rules: dict | None = None, impact: dict | None = None) -> dict:
    r = rules if rules is not None else _load(RULES)
    files = list(dict.fromkeys((files or []) + named_paths(task)))
    low = " " + task.lower() + " "
    why = []
    hot = [(f, p) for f in files if (p := _match(f, r.get("strong_paths", r.get("claude_paths", []))))]
    why += [f"touches {f} (sensitive: {p})" for f, p in hot[:3]]
    words = [w for w in r.get("strong_words", r.get("claude_words", [])) if re.search(r"(?<![a-z])" + re.escape(w), low)]
    if words:
        why.append("about " + ", ".join(words[:4]))
    ar = areas(files, impact)
    if len(ar) > r.get("max_opencode_areas", 3):
        why.append(f"spans {len(ar)} areas ({', '.join(ar)})")
    if why:
        return {"tier": "strong", "why": why, "areas": ar}
    ow = [w for w in r.get("opencode_words", []) if w in low]
    if len(ar) > r.get("max_local_areas", 1) or ow:
        return {"tier": "opencode", "why": ([f"spans {len(ar)} areas ({', '.join(ar)})"] if len(ar) > 1 else []) + (["a wiring or refactor job"] if ow else []),
                "areas": ar}
    return {"tier": "local", "why": ["one area, no sensitive path or topic"], "areas": ar}


NEXT = {"local": './securax autobuild "{t}"', "opencode": "./securax opencode",
        "strong": './securax autobuild "{t}"   (it uses the strong open models), or work on it yourself in  ./securax opencode --strong'}


def changed(base: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", base], capture_output=True, text=True).stdout
    new = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True).stdout
    return [x for x in (out + new).splitlines() if x]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    words, files, base, as_json, mode, it = [], [], "", False, "words", iter(argv)
    for a in it:
        if a == "--files":
            mode = "files"
        elif a == "--base":
            base, mode = next(it, ""), "words"
        elif a == "--json":
            as_json = True
        elif mode == "files" and not a.startswith("--"):
            files.append(a)
        else:
            words.append(a)
    task = " ".join(words).strip()
    if not task:
        print(__doc__)
        return 2
    if base:
        files = files + changed(base)
    d = decide(task, files)
    if as_json:
        print(json.dumps(d))
        return 0
    print(f"tier: {d['tier']}  ({'; '.join(d['why'])})")
    print("next: " + NEXT[d["tier"]].format(t=task.replace('"', "'")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
