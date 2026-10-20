#!/usr/bin/env python3
"""A second pair of eyes on a change, from the strongest open models, before you merge it (doc 83).

    ./securax review                    review everything that differs from main (committed or not)
    ./securax review --base REF         review against another branch or commit
    ./securax review --model ALIAS      another model alias (default: strong; ./securax providers list)
    ./securax review --dry-run          show what would be sent, and its size; send nothing

The change goes through the SecuRAX gateway like every other AI call (guardrails, audit, data residency). The reviewer is told the
repository's hard rules (BUILD-CONTRACT.md, AGENTS.md section 4) and asked for real defects only: a bug, a security weakness, a broken
rule, a missing test, each with the file, what goes wrong and the fix. It refuses a change that touches vault/ or an .env file, so
private data is never sent. The answer is advice to weigh, not an order: CI and the tests still decide. Standard library only.
Exit codes: 0 reviewed (or nothing to review), 1 the gateway could not answer, 2 refused or bad usage.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_CHARS = 60000
PRIVATE = re.compile(r"(^|/)(vault/|\.env($|\.)|[^/]*\.(key|pem)$)")
ASK = """You are reviewing one change to SecuRAX, a security estate for Indian BFSI. Report only REAL defects, most severe first, at most 10:
a correctness bug, a security weakness, a broken repository rule, or new behaviour with no test. For each one give: the file and line,
what goes wrong (a concrete input or situation), and the fix. No style comments, no praise, no summary of the change. If you find
nothing that matters, answer exactly: No blocking findings.

The repository's hard rules, in short:
{rules}"""


def git(*args: str, root: pathlib.Path | None = None) -> str:
    return subprocess.run(["git", "-C", str(root or ROOT), *args], capture_output=True, text=True).stdout


def default_base(root: pathlib.Path | None = None) -> str:
    for ref in ("origin/main", "main"):
        mb = git("merge-base", "HEAD", ref, root=root).strip()
        if mb:
            return mb
    return "HEAD"


def change(base: str, root: pathlib.Path | None = None) -> tuple[str, list[str]]:
    """(the unified diff against base, including new untracked files; the paths it touches)."""
    root = root or ROOT
    diff = git("diff", base, root=root)
    new = [f for f in git("ls-files", "--others", "--exclude-standard", root=root).splitlines() if f]
    for f in new:
        try:
            body = (root / f).read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        diff += f"\n--- /dev/null\n+++ b/{f}\n" + "".join("+" + line + "\n" for line in body.splitlines())
    paths = sorted(set(re.findall(r"^\+\+\+ b/(.+)$", diff, re.M)) | set(re.findall(r"^--- a/(.+)$", diff, re.M)))
    return diff, paths


def rules(root: pathlib.Path | None = None) -> str:
    """The hard rules: BUILD-CONTRACT.md's rule lines and AGENTS.md section 4, kept short."""
    root = root or ROOT
    out = []
    contract = (root / "BUILD-CONTRACT.md")
    if contract.exists():
        out += [ln for ln in contract.read_text("utf-8").splitlines() if re.match(r"^\s*(\d+\.|-)\s+\*\*", ln)][:25]
    agents = (root / "AGENTS.md").read_text("utf-8") if (root / "AGENTS.md").exists() else ""
    m = re.search(r"## 4\..*?(?=\n## )", agents, re.S)
    if m:
        out.append(m.group(0))
    return "\n".join(out)[:6000]


def messages(diff: str, root: pathlib.Path | None = None) -> list[dict]:
    if len(diff) > MAX_CHARS:
        diff = diff[:MAX_CHARS] + f"\n\n[the change is longer: only the first {MAX_CHARS} characters are shown]"
    return [{"role": "system", "content": ASK.format(rules=rules(root))}, {"role": "user", "content": "The change (unified diff):\n\n" + diff}]


def post(url: str, key: str, body: dict, timeout: int = 480) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}", "User-Agent": "securax-review"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main(argv: list[str] | None = None, send=post) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="")
    ap.add_argument("--model", default="strong")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    base = a.base or default_base()
    diff, paths = change(base)
    if not diff.strip():
        print(f"Nothing to review: no difference from {base[:12]}.")
        return 0
    private = [p for p in paths if PRIVATE.search(p)]
    if private:
        print("Refused: the change touches private files, which are never sent to a model: " + ", ".join(private[:5]))
        return 2
    msgs = messages(diff)
    size = sum(len(m["content"]) for m in msgs)
    print(f"Reviewing {len(paths)} file(s) against {base[:12]} with '{a.model}' through the SecuRAX gateway ({size:,} characters)…")
    if a.dry_run:
        print("(dry run: nothing sent)  files: " + ", ".join(paths[:20]) + (" …" if len(paths) > 20 else ""))
        return 0
    api = os.environ.get("REVIEW_API_BASE", "http://localhost:8080/v1").rstrip("/")
    try:
        r = send(api + "/chat/completions", os.environ.get("REVIEW_API_KEY", "sk-range-dev"),
                 {"model": a.model, "messages": msgs, "temperature": 0.1})
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"The gateway could not answer ({e}). Is the estate up?  ./securax up   Which models work:  ./securax models")
        return 1
    text = ((r.get("choices") or [{}])[0].get("message") or {}).get("content") or "(empty answer)"
    print(f"\n{text.strip()}\n\n(answered by {r.get('model', a.model)}; advice to weigh, not an order: CI and the tests decide)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
