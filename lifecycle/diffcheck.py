#!/usr/bin/env python3
"""DIFFCHECK — the build contract's hard rules, enforced on the diff instead of trusted.

An agent (small local model or large) that is told "never skip a test" will, under pressure to get green, still sometimes skip a
test. So the rules that CAN be checked mechanically are checked here, on the actual diff, before `autobuild` may commit:

  BLOCK  test weakening   a skip/xfail added, or test functions / assertions removed
  BLOCK  rails weakening  a guardrail pattern deleted, a fail-closed default loosened
  BLOCK  fake green       `continue-on-error`, `|| true`, `--no-verify`, `noqa`/`type: ignore` piles added to pass checks
  BLOCK  secrets          a credential-shaped string or a real .env added
  WARN   scope creep      many files / many lines, whitespace-only churn, comments deleted, new dependencies

WARN becomes BLOCK with --strict. Surgical changes (Karpathy's rule 3) cannot be fully proven by a script; these are the proxies that
catch the usual offenders. Standard library only (secret patterns come from the gateway's own guardrails).

    python3 lifecycle/diffcheck.py [--base REF] [--strict] [--json]      # default: uncommitted changes vs HEAD
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "llm-gateway"))
from app import guardrails  # noqa: E402

MAX_FILES, MAX_LINES = 12, 400
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]*\.py$|[._-]test\.[jt]sx?$|\.spec\.[jt]sx?$")
SKIP_ADDED = re.compile(r"@pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|@unittest\.skip|\b(it|test|describe)\.skip\(|\bxit\(|\bxdescribe\(|t\.Skip\(")
TEST_DEF = re.compile(r"^\s*(async\s+)?def\s+test_\w+|^\s*(it|test)\(\s*['\"]")
ASSERT = re.compile(r"\bassert\b|\bexpect\(|\bassert\w*\(|\.should\.|self\.assert")
RAIL_ENTRY = re.compile(r"^\s*\(\s*[\"'](PI|SECRET|LEAK|OUT|PII|DOS)-[\w-]+[\"']")
LOOSEN = [
    (re.compile(r"FAIL_MODE\s*[=:]\s*[\"']?open"), "FAIL_MODE set to open (the gateway must fail closed)"),
    (re.compile(r"GUARDRAIL_MODE\s*[=:]\s*[\"']?monitor"), "GUARDRAIL_MODE set to monitor (rails would stop blocking)"),
    (re.compile(r"RATE_LIMIT_PER_MIN\s*[=:]\s*[\"']?(0|9{4,})"), "rate limit effectively disabled"),
]
FAKE_GREEN = [
    (re.compile(r"continue-on-error:\s*true"), "CI step made non-fatal (continue-on-error)", "workflow"),
    (re.compile(r"\|\|\s*true\b"), "failure swallowed with '|| true'", "workflow"),
    (re.compile(r"\bgit\s+(commit|push|merge|rebase)\b[^\n]*--no-(verify|gpg-sign)"), "git hooks/signing bypassed", "any"),
    (re.compile(r"#\s*type:\s*ignore|#\s*ruff:\s*noqa|/\*\s*eslint-disable|//\s*@ts-ignore|#\s*pylint:\s*disable"), "linter/type-check silenced inline", "any"),
]
DEP_FILES = {"requirements.txt", "requirements-dev.txt", "package.json", "pyproject.toml", "Pipfile", "go.mod"}


def sh(args: list[str], cwd: pathlib.Path = ROOT) -> str:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout


class Change:
    def __init__(self, path: str) -> None:
        self.path, self.added, self.removed = path, [], []

    @property
    def is_test(self) -> bool:
        return bool(TEST_PATH.search(self.path))


def parse(diff: str) -> dict[str, Change]:
    out: dict[str, Change] = {}
    cur: Change | None = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            cur = out.setdefault(line[6:], Change(line[6:]))
        elif line.startswith("--- a/") and not out:
            continue
        elif cur and line.startswith("+") and not line.startswith("+++"):
            cur.added.append(line[1:])
        elif cur and line.startswith("-") and not line.startswith("---"):
            cur.removed.append(line[1:])
    return out


def collect(base: str, root: pathlib.Path = ROOT) -> tuple[dict[str, Change], int]:
    """Changes vs `base`, including untracked files (counted as fully added). Also returns the count of whitespace-only churn lines."""
    changes = parse(sh(["git", "diff", "--no-color", "-U0", base], root))
    for f in sh(["git", "ls-files", "-o", "--exclude-standard"], root).split("\n"):
        p = root / f
        if f and p.is_file() and p.stat().st_size < 400_000:
            try:
                changes.setdefault(f, Change(f)).added = p.read_text("utf-8").splitlines()
            except UnicodeDecodeError:
                pass
    nows_by = parse(sh(["git", "diff", "--no-color", "-U0", "-w", base], root))
    churn = 0
    for path, c in changes.items():
        if c.removed:                                           # only files that EXISTED: a new file has no "old formatting" to disturb
            w = nows_by.get(path)                               # absent from the -w diff = every change in it was whitespace-only
            churn += max(0, len(c.added) + len(c.removed) - (len(w.added) + len(w.removed) if w else 0))
    return changes, churn


def evaluate(changes: dict[str, Change], ws_churn: int = 0) -> list[dict]:
    res: list[dict] = []

    def add(level: str, rule: str, path: str, why: str, fix: str) -> None:
        res.append({"level": level, "rule": rule, "file": path, "why": why, "fix": fix})

    total = sum(len(c.added) + len(c.removed) for c in changes.values())
    for path, c in changes.items():
        name = path.rsplit("/", 1)[-1]
        if c.is_test:
            for ln in c.added:
                if SKIP_ADDED.search(ln):
                    add("BLOCK", "test-skipped", path, f"a test is skipped/xfailed: {ln.strip()[:80]!r}", "make the test pass by fixing the code; never skip it")
                    break
            gone = sum(1 for ln in c.removed if TEST_DEF.match(ln)) - sum(1 for ln in c.added if TEST_DEF.match(ln))
            if gone > 0:
                add("BLOCK", "test-removed", path, f"{gone} test function(s) removed without replacement", "restore them; a failing test is a finding, not clutter")
            lost = sum(1 for ln in c.removed if ASSERT.search(ln)) - sum(1 for ln in c.added if ASSERT.search(ln))
            if lost >= 2:
                add("BLOCK", "assertions-weakened", path, f"{lost} more assertions removed than added", "keep the assertions; fix the code under test")
        if "guardrails" in path or "providers" in path:
            gone = sum(1 for ln in c.removed if RAIL_ENTRY.match(ln)) - sum(1 for ln in c.added if RAIL_ENTRY.match(ln))
            if gone > 0:
                add("BLOCK", "rail-removed", path, f"{gone} guardrail rule(s) deleted", "rails are never weakened to pass a task")
        for rx, why in LOOSEN:
            if any(rx.search(ln) for ln in c.added):
                add("BLOCK", "rails-loosened", path, why, "keep the secure default; use a per-run override if you need otherwise")
        for rx, why, scope in FAKE_GREEN:
            if scope == "workflow" and ".github/workflows" not in path:
                continue
            if any(rx.search(ln) for ln in c.added) and not c.is_test:
                add("BLOCK", "fake-green", path, why, "fix the cause instead of hiding the failure")
        if name == ".env" or (name.startswith(".env.") and name not in (".env.example", ".env.sample")):
            add("BLOCK", "env-file-added", path, "an environment file (real keys live only in git-ignored .env)", "remove it; document the variable in .env.example")
        text = "\n".join(c.added)
        secret_rules = {f.rule for f in guardrails.check_output(text[:200000], set(), set())[1] if f.rule.startswith("SECRET-")}
        if secret_rules:
            add("BLOCK", "secret-added", path, f"credential-shaped string(s): {', '.join(sorted(secret_rules))}", "remove it and rotate the key if it was ever real")
        if c.removed and not c.is_test:
            cm = sum(1 for ln in c.removed if ln.strip().startswith(("#", "//")) and len(ln.strip()) > 12) - sum(1 for ln in c.added if ln.strip().startswith(("#", "//")))
            if cm >= 5:
                add("WARN", "comments-deleted", path, f"{cm} comment lines deleted", "keep comments unless your change made them wrong")
        if name in DEP_FILES and any(ln.strip() for ln in c.added):
            add("WARN", "dependency-change", path, "dependency manifest changed", "justify every new dependency in the commit message")
    if len(changes) > MAX_FILES:
        add("WARN", "scope-files", "(diff)", f"{len(changes)} files changed (budget {MAX_FILES})", "split the task: one validated change beats three")
    if total > MAX_LINES:
        add("WARN", "scope-lines", "(diff)", f"{total} lines changed (budget {MAX_LINES})", "could it be smaller? every line must trace to the task")
    if ws_churn >= 10:
        add("WARN", "whitespace-churn", "(diff)", f"{ws_churn} lines changed only in whitespace/formatting", "do not reformat code you were not asked to touch")
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="HEAD", help="compare the working tree with this ref (default HEAD = uncommitted changes)")
    ap.add_argument("--strict", action="store_true", help="WARN also fails")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    changes, ws = collect(a.base)
    res = evaluate(changes, ws)
    blocks = [r for r in res if r["level"] == "BLOCK" or (a.strict and r["level"] == "WARN")]
    if a.json:
        print(json.dumps({"files": len(changes), "findings": res, "ok": not blocks}, indent=2))
    else:
        print(f"diffcheck: {len(changes)} file(s) changed vs {a.base}: {'FAILED' if blocks else 'ok'}"
              f" ({sum(r['level'] == 'BLOCK' for r in res)} blocking, {sum(r['level'] == 'WARN' for r in res)} warning)")
        for r in res:
            print(f"  {r['level']:<5} {r['rule']:<20} {r['file']}: {r['why']}\n        → {r['fix']}")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
