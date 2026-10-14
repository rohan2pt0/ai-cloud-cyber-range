#!/usr/bin/env python3
"""FORGE — the admission gate that decides whether a (model-made) change is really done.

`verify` answers "do the existing checks pass?". A weak model, or a strong one in a hurry, can pass that while fixing nothing: tests that
never touch the change, a branch nobody exercises, a 40-branch function. FORGE asks the harder questions, mechanically and offline
(standard library only, no tokens):

  fail-to-pass  the tests the change ADDED must fail on the code before it       (a test that cannot fail proves nothing)
  mutation      deliberately break the changed lines; the tests must notice       (a surviving mutant = an untested line)
  budget        complexity / length of the functions the change touched, vs before (no new 40-branch function; legacy is not punished)
  brief         turn a red `verify` log into a short, typed, current-state brief    (the next attempt sees evidence, not a 60-line dump)
  classify      is this red an INFRA problem (daemon died, network) or a CODE problem? (infra is retried, code is repaired — never mixed up)

Why: published work on agentic repair finds that looping on a weak verifier overfits to it, and that stale traces make later revisions
worse. So each attempt gets a fresh, typed, evidence-bound brief, and "green" has to survive a verifier that fights back.
Surviving mutants include equivalent ones, so the gate scores (killed / total) against a threshold; it is a strong signal, not a proof.

    python3 lifecycle/forge.py gate  --base REF [--tests "CMD"] [--max-mutants 24] [--min-score 0.6] [--strict] [--json]
    python3 lifecycle/forge.py brief FILE [--max-lines 12]
    python3 lifecycle/forge.py classify FILE [--json]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]*\.py$")
MAX_COMPLEXITY, MAX_FUNC_LINES = 15, 80
PYTEST = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider"]


def sh(args: list[str], cwd: pathlib.Path = ROOT, timeout: int = 600) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(args, 124, e.stdout or "", "timeout")


# ───────────────────────────────────────── what changed ─────────────────────────────────────────
def changed_lines(base: str, root: pathlib.Path = ROOT) -> dict[str, set[int]]:
    """{path: set of added/modified line numbers (new side)} for tracked changes vs base, plus untracked files (every line)."""
    out: dict[str, set[int]] = {}
    cur = None
    for line in sh(["git", "diff", "--no-color", "-U0", base], root).stdout.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
            out.setdefault(cur, set())
        elif line.startswith("+++ "):
            cur = None
        elif line.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                start, n = int(m.group(1)), int(m.group(2) or 1)
                out[cur].update(range(start, start + n))
    for f in sh(["git", "ls-files", "-o", "--exclude-standard"], root).stdout.split("\n"):
        p = root / f
        if f and p.is_file():
            try:
                out[f] = set(range(1, len(p.read_text("utf-8").splitlines()) + 1))
            except (UnicodeDecodeError, OSError):
                pass
    return out


def py_files(ch: dict[str, set[int]], tests: bool) -> list[str]:
    return sorted(p for p in ch if p.endswith(".py") and bool(TEST_PATH.search(p)) == tests and ch[p])


# ───────────────────────────────────────── budget (complexity) ─────────────────────────────────────────
def complexity(fn: ast.AST) -> int:
    """McCabe-style: 1 + decision points. Nested functions count toward their parent (they are part of its reading cost)."""
    n = 1
    for node in ast.walk(fn):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler, ast.Assert, ast.comprehension)):
            n += 1
            if isinstance(node, ast.comprehension):
                n += len(node.ifs)
        elif isinstance(node, ast.BoolOp):
            n += len(node.values) - 1
        elif isinstance(node, ast.match_case):
            n += 1
    return n


def functions(src: str) -> dict[str, tuple[int, int, int]]:
    """{qualname: (complexity, first_line, last_line)}; empty if the file does not parse."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    res: dict[str, tuple[int, int, int]] = {}

    def walk(node: ast.AST, prefix: str) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{prefix}{ch.name}"
                res[q] = (complexity(ch), ch.lineno, ch.end_lineno or ch.lineno)
                walk(ch, q + ".")
            elif isinstance(ch, ast.ClassDef):
                walk(ch, f"{prefix}{ch.name}.")
    walk(tree, "")
    return res


def budget(base: str, ch: dict[str, set[int]], root: pathlib.Path = ROOT) -> list[dict]:
    res = []
    for path in py_files(ch, tests=False):
        new = functions((root / path).read_text("utf-8"))
        old_src = sh(["git", "show", f"{base}:{path}"], root).stdout
        old = functions(old_src) if old_src else {}
        for q, (cx, a, b) in new.items():
            if not (ch[path] & set(range(a, b + 1))):
                continue                                                      # untouched function: not this change's debt
            before = old.get(q, (0, 0, 0))[0]
            if cx > MAX_COMPLEXITY and cx > before:
                res.append(dict(level="BLOCK", rule="complexity", file=path, why=f"{q}: complexity {cx} (was {before or 'new'}, budget {MAX_COMPLEXITY})",
                                fix="split it into smaller functions; every branch is a place for a bug"))
            if b - a + 1 > MAX_FUNC_LINES and q not in old:
                res.append(dict(level="WARN", rule="function-length", file=path, why=f"{q}: {b - a + 1} lines (budget {MAX_FUNC_LINES})", fix="split it"))
    return res


# ───────────────────────────────────────── mutation ─────────────────────────────────────────
FLIP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt,
        ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}


class Mutator(ast.NodeTransformer):
    """Applies exactly one mutation: the `target`-th mutable node (in walk order) that sits on a changed line."""

    def __init__(self, lines: set[int], target: int | None) -> None:
        self.lines, self.target, self.i, self.what = lines, target, -1, ""

    def hit(self, node: ast.AST, what: str) -> bool:
        if getattr(node, "lineno", None) not in self.lines:
            return False
        self.i += 1
        if self.i == self.target:
            self.what = f"line {node.lineno}: {what}"
            return True
        return False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if type(node.ops[0]) in FLIP and self.hit(node, f"{type(node.ops[0]).__name__} flipped"):
            node.ops[0] = FLIP[type(node.ops[0])]()
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        if self.hit(node, "and/or swapped"):
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self.hit(node, "`not` removed"):
            return node.operand
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool):
            if self.hit(node, f"{node.value} -> {not node.value}"):
                return ast.copy_location(ast.Constant(not node.value), node)
        elif isinstance(node.value, int) and self.hit(node, f"{node.value} -> {node.value + 1}"):
            return ast.copy_location(ast.Constant(node.value + 1), node)
        return node

    def visit_Return(self, node: ast.Return) -> ast.AST:
        self.generic_visit(node)
        if node.value is not None and not (isinstance(node.value, ast.Constant) and node.value.value is None) and self.hit(node, "return value dropped (None)"):
            node.value = ast.Constant(None)
        return node


def mutate_file(src: str, lines: set[int], target: int) -> tuple[str, str] | None:
    tree = ast.parse(src)
    m = Mutator(lines, target)
    out = m.visit(tree)
    if not m.what:
        return None
    return ast.unparse(ast.fix_missing_locations(out)), m.what


def mutation_gate(files: dict[str, set[int]], test_cmd: list[str] | None, max_mutants: int, min_score: float, root: pathlib.Path = ROOT,
                  timeout: int = 300) -> tuple[list[dict], dict]:
    res: list[dict] = []
    stats = {"mutants": 0, "killed": 0, "survived": []}
    budget_left = max_mutants
    for path in sorted(files):
        if budget_left <= 0:
            break
        src_path = root / path
        original = src_path.read_text("utf-8")
        try:
            tree = ast.parse(original)
        except SyntaxError:
            continue
        probe = Mutator(files[path], None)
        probe.visit(tree)                                                    # counts mutable nodes on changed lines (no target: no mutation)
        total = probe.i + 1
        if total <= 0:
            continue
        # deterministic sample: stable order from a hash of the file, so a re-run explains the same survivors
        order = sorted(range(total), key=lambda k: hashlib.sha1(f"{path}:{k}".encode()).hexdigest())[:budget_left]
        cmd = test_cmd or relevant_tests(path, root)
        if sh(cmd, root, timeout).returncode != 0:                           # a red/broken test command "kills" every mutant: measure nothing rather than lie
            res.append(dict(level="BLOCK", rule="mutation-baseline", file=path, why="the tests are not green on the unmodified change, so mutation results would be meaningless",
                            fix="make the relevant tests pass first (command: " + " ".join(cmd[:8]) + ")"))
            continue
        for k in order:
            made = mutate_file(original, files[path], k)
            if not made:
                continue
            mutated, what = made
            budget_left -= 1
            stats["mutants"] += 1
            try:
                src_path.write_text(mutated, "utf-8")
                rc = sh(cmd, root, timeout).returncode
            finally:
                src_path.write_text(original, "utf-8")                       # ALWAYS restore: the gate never leaves a mutant behind
            if rc != 0:
                stats["killed"] += 1
            else:
                stats["survived"].append(f"{path}  {what}")
    n = stats["mutants"]
    if n:
        score = stats["killed"] / n
        stats["score"] = round(score, 2)
        if n >= 3 and score < min_score:
            res.append(dict(level="BLOCK", rule="mutation-score", file="(diff)",
                            why=f"tests caught {stats['killed']}/{n} deliberate breakages ({score:.0%}, need {min_score:.0%}); survivors: " + "; ".join(stats["survived"][:4]),
                            fix="add assertions that fail when those lines are wrong"))
        elif stats["survived"]:
            res.append(dict(level="WARN", rule="mutation-survivors", file="(diff)", why="; ".join(stats["survived"][:4]),
                            fix="each survivor is a changed line no test depends on (or an equivalent mutant)"))
    return res, stats


def relevant_tests(path: str, root: pathlib.Path = ROOT) -> list[str]:
    """Tests that mention the module by name; if none, the whole suite (slow but never wrongly green)."""
    stem = pathlib.Path(path).stem
    pat = re.compile(rf"\b{re.escape(stem)}\b")
    hits = []
    for t in root.rglob("test_*.py"):
        if any(part in (".git", "node_modules", "__pycache__") for part in t.parts):
            continue
        try:
            if pat.search(t.read_text("utf-8", "ignore")):
                hits.append(str(t.relative_to(root)))
        except OSError:
            pass
    return PYTEST + sorted(hits)[:6] if hits else PYTEST


# ───────────────────────────────────────── fail-to-pass ─────────────────────────────────────────
def fail_to_pass(base: str, ch: dict[str, set[int]], root: pathlib.Path = ROOT, timeout: int = 300) -> list[dict]:
    tests = py_files(ch, tests=True)
    srcs = py_files(ch, tests=False)
    if not tests or not srcs:
        return []                                                            # tests-only or code-only changes have nothing to compare
    wt = pathlib.Path(tempfile.mkdtemp(prefix="forge-f2p-"))
    try:
        if sh(["git", "worktree", "add", "--detach", str(wt / "w"), base], root).returncode != 0:
            return [dict(level="WARN", rule="fail-to-pass", file="(diff)", why="could not check out the base to run the new tests against it", fix="run on a git checkout")]
        w = wt / "w"
        for t in tests:                                                     # the NEW tests, on the OLD code
            (w / t).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / t, w / t)
        rc = sh(PYTEST + tests, w, timeout).returncode
        if rc == 0:
            return [dict(level="WARN", rule="fail-to-pass", file=", ".join(tests[:3]),
                         why="the new/changed tests also PASS on the code from before the change, so they do not prove the change works",
                         fix="assert the new behaviour (they must fail without your change)")]
        return []
    finally:
        sh(["git", "worktree", "remove", "--force", str(wt / "w")], root)
        shutil.rmtree(wt, ignore_errors=True)


# ───────────────────────────────────────── failure typing ─────────────────────────────────────────
INFRA = [
    r"Cannot connect to the Docker daemon", r"error during connect", r"docker daemon", r"Temporary failure in name resolution",
    r"Could not resolve host", r"Connection (reset|refused|timed out)", r"TLS handshake timeout", r"no space left on device",
    r"toomanyrequests", r"rate limit", r"\b50[234]\b (Bad Gateway|Service Unavailable|Gateway Time-out)", r"context deadline exceeded",
    r"pull access denied", r"net/http: request canceled", r"Read timed out", r"i/o timeout",
]
KINDS = [
    ("diffcheck", re.compile(r"^\s*BLOCK\s+\S+", re.M)),
    ("lint", re.compile(r"^\S+\.py:\d+:\d+: [A-Z]+\d+|^[A-Z]+\d{3} ", re.M)),
    ("test", re.compile(r"^FAILED |^E {2,}|AssertionError|^_{3,} .* _{3,}$", re.M)),
    ("config", re.compile(r"baseline|compose|yaml|schema|vet pin|regmap|fitness", re.I)),
]


def classify(text: str) -> dict:
    infra = [p for p in INFRA if re.search(p, text, re.I)]
    kinds = [k for k, rx in KINDS if rx.search(text)]
    if infra and not kinds:
        verdict = "infra"                                                    # nothing in it points at the code
    elif infra:
        verdict = "mixed"
    else:
        verdict = "code" if kinds else "unknown"
    return {"verdict": verdict, "kinds": kinds, "infra_signals": infra[:3]}


def brief(text: str, max_lines: int = 12) -> str:
    """A short, typed, current-state brief. The newest evidence only; never the whole log."""
    c = classify(text)
    if c["verdict"] == "infra":
        return ("The failure is INFRASTRUCTURE, not your code (" + "; ".join(c["infra_signals"]) + "). Change nothing; the gate will be re-run.\n")
    lines = text.splitlines()
    out = [f"Failure type: {', '.join(c['kinds']) or 'unknown'}. Fix ONLY these, from the current code (earlier attempts are discarded):"]
    picks: list[str] = []
    for kind, rx in KINDS:
        if kind not in c["kinds"]:
            continue
        for i, ln in enumerate(lines):
            if rx.search(ln):
                picks.append(ln.rstrip()[:220])
                if kind == "diffcheck" and i + 1 < len(lines) and "→" in lines[i + 1]:
                    picks.append(lines[i + 1].strip()[:220])
        picks.append("")
    picks = [p for p in dict.fromkeys(picks) if p]                           # de-duplicate, keep order
    out += picks[:max_lines] or [ln for ln in lines if ln.strip()][-max_lines:]
    out.append("Do not skip, delete or weaken a test to get green: fix the code.")
    return "\n".join(out) + "\n"


# ───────────────────────────────────────── CLI ─────────────────────────────────────────
def gate(base: str, tests: str | None, max_mutants: int, min_score: float, strict: bool, root: pathlib.Path = ROOT) -> tuple[list[dict], dict]:
    ch = changed_lines(base, root)
    res: list[dict] = []
    res += budget(base, ch, root)
    res += fail_to_pass(base, ch, root)
    mres, stats = mutation_gate({p: ch[p] for p in py_files(ch, tests=False)}, shlex.split(tests) if tests else None, max_mutants, min_score, root)
    res += mres
    if strict:
        for r in res:
            r["level"] = "BLOCK"
    return res, {"files": len(ch), **stats}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--base", default="HEAD")
    g.add_argument("--tests", default=None, help="command that exits 0 when the relevant tests pass (default: tests that mention each changed module)")
    g.add_argument("--max-mutants", type=int, default=24)
    g.add_argument("--min-score", type=float, default=0.6)
    g.add_argument("--strict", action="store_true", help="WARN also fails")
    g.add_argument("--json", action="store_true")
    g.add_argument("--root", default=".", help="the git checkout to gate (default: the current directory)")
    b = sub.add_parser("brief")
    b.add_argument("file")
    b.add_argument("--max-lines", type=int, default=12)
    c = sub.add_parser("classify")
    c.add_argument("file")
    c.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "brief":
        sys.stdout.write(brief(pathlib.Path(a.file).read_text("utf-8", "ignore"), a.max_lines))
        return 0
    if a.cmd == "classify":
        r = classify(pathlib.Path(a.file).read_text("utf-8", "ignore"))
        print(json.dumps(r) if a.json else f"{r['verdict']} {' '.join(r['kinds'])}")
        return 0 if r["verdict"] == "infra" else 1                           # exit 0 = "retry, do not repair"
    res, stats = gate(a.base, a.tests, a.max_mutants, a.min_score, a.strict, pathlib.Path(a.root).resolve())
    blocks = [r for r in res if r["level"] == "BLOCK"]
    if a.json:
        print(json.dumps({"stats": stats, "findings": res, "ok": not blocks}, indent=2))
    else:
        m = f", mutation {stats.get('killed', 0)}/{stats.get('mutants', 0)} caught" if stats.get("mutants") else ""
        print(f"forge: {stats['files']} file(s) vs {a.base}: {'FAILED' if blocks else 'ok'}{m}")
        for r in res:
            print(f"  {r['level']:<5} {r['rule']:<18} {r['file']}: {r['why']}\n        → {r['fix']}")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
