#!/usr/bin/env python3
"""MUTATE: prove the tests would catch a weakened safety rail (practical mutation testing, Petrović & Ivanković, ICSE-SEIP 2018).

A green test run says the code works. It does not say the tests would notice if a rail were quietly loosened. So this tool makes
one small change at a time ("a mutant") to the rail code, runs the tests that guard it, and records the result:

  KILLED     the tests failed: they would catch this weakening        TIMEOUT   the tests hung: counted as killed
  SURVIVED   the tests still passed: a missing test, or a change that cannot alter behaviour (an "equivalent mutant")

Like Google, it mutates only meaningful code and skips "arid" code: docstrings, logging and print calls, f-strings (message
text), __repr__/__str__, type annotations and the `if __name__ == "__main__"` block. The operators:

  compare      < <=, > >=, == !=, is / is not, in / not in        negate      `not (...)` around an if/while condition
  and-or       swap `and` and `or`                                 return-bool `return True` <-> `return False`
  number       a numeric constant +1 and -1 (0/1 inside range() are skipped)                 raise-pass  a `raise` becomes `pass`

The targets (tools/mutate.json) are the rail files, most important first, each with the tests that guard it. Every mutant runs
from a fresh bytecode cache with a timeout. The original file is restored after every mutant (in a finally block, mtime included),
checked by hash at the end, and a journal outside the repository restores it on the next run even if this one is killed.

A RATCHET, like fitness: tools/mutate-baseline.json lists the known survivors with a reason. `--check` fails only on a NEW survivor.

    python3 tools/mutate.py --all [--max N] [--check] [--json] [--out report.json]   # every target (the weekly run)
    python3 tools/mutate.py --diff origin/main --check                              # only lines changed since BASE (for a PR)
    python3 tools/mutate.py --file apps/estate-sync/syncsvc/guard.py                # one target
    python3 tools/mutate.py --all --update-baseline                                 # a deliberate, reviewed act

--max N caps the mutants per file (an even spread over the file, so the cap never covers only its top). Standard library only.
"""
from __future__ import annotations

import argparse
import ast
import base64
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "tools" / "mutate.json"
BASELINE = ROOT / "tools" / "mutate-baseline.json"
UNREVIEWED = "unreviewed: add a test that kills it, or say why it is equivalent"
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
ARID_FUNCS = {"__repr__", "__str__", "__format__"}
FLIP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
        ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}
OPSTR = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=", ast.Is: "is", ast.IsNot: "is not",
         ast.In: "in", ast.NotIn: "not in"}


@dataclasses.dataclass
class Mutant:
    file: str
    line: int
    span: tuple[int, int, int, int]             # lineno, col (UTF-8 bytes), end_lineno, end_col: the source replaced
    operator: str
    replacement: str
    scope: str = "<module>"
    original: str = ""
    mutated: str = ""
    key: str = ""

    def public(self) -> dict:
        return {"file": self.file, "line": self.line, "operator": self.operator, "scope": self.scope,
                "original": self.original, "mutated": self.mutated, "key": self.key}


# ───────────────────────────────────────────── finding mutants ─────────────────────────────────────────────
class _Finder(ast.NodeVisitor):
    """Walks one module and records every mutant site outside arid code. It never changes the tree: each mutant is a text splice."""

    def __init__(self, src: bytes, rel: str) -> None:
        self.src, self.rel, self.out, self.scope = src, rel, [], []

    def seg(self, node: ast.AST) -> str:
        return _segment(self.src, node)

    def add(self, node: ast.AST, op: str, repl: str) -> None:
        self.out.append(Mutant(self.rel, node.lineno, (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset), op, repl,
                               ".".join(self.scope) or "<module>"))

    # arid code: never descend
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in ARID_FUNCS:
            return
        for d in node.decorator_list:
            self.visit(d)
        for default in [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]:
            self.visit(default)                 # defaults are behaviour; annotations (args/returns) are skipped
        self.scope.append(node.name)
        for stmt in node.body:
            self.visit(stmt)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        for stmt in node.body:
            self.visit(stmt)
        self.scope.pop()

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        return

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Name) and f.id == "print":
            return
        if isinstance(f, ast.Attribute) and (f.attr in LOG_METHODS and "log" in self.seg(f.value).lower()
                                             or self.seg(f).startswith("warnings.warn")):
            return
        if isinstance(f, ast.Name) and f.id == "range":
            for a in node.args:
                if not (isinstance(a, ast.Constant) and a.value in (0, 1) and not isinstance(a.value, bool)):
                    self.visit(a)
            return
        self.generic_visit(node)

    # operators
    def visit_If(self, node: ast.If) -> None:
        if self.seg(node.test).replace("'", '"') == '__name__ == "__main__"':
            return
        self.add(node.test, "negate", f"(not ({self.seg(node.test)}))")
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.add(node.test, "negate", f"(not ({self.seg(node.test)}))")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        parts = [self.seg(c) for c in [node.left, *node.comparators]]
        for i, op in enumerate(node.ops):
            if type(op) not in FLIP:
                continue
            ops = [OPSTR[type(o)] for o in node.ops]
            ops[i] = OPSTR[FLIP[type(op)]]
            text = parts[0] + "".join(f" {o} {p}" for o, p in zip(ops, parts[1:]))
            self.add(node, "compare", f"({text})")
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        other = " or " if isinstance(node.op, ast.And) else " and "
        self.add(node, "and-or", "(" + other.join(f"({self.seg(v)})" for v in node.values) + ")")
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, bool):
            self.add(v, "return-bool", str(not v.value))
            return
        self.generic_visit(node)

    def visit_List(self, node: ast.List | ast.Tuple | ast.Set) -> None:
        if len(node.elts) >= 5 and all(_is_number(e) for e in node.elts):
            return                              # a lookup table (check-digit tables and the like): data, not logic
        self.generic_visit(node)

    visit_Tuple = visit_Set = visit_List

    def visit_Constant(self, node: ast.Constant) -> None:
        if not _is_number(node):
            return
        hexa = self.seg(node).lower().startswith("0x")
        for d in (1, -1):
            n = node.value + d
            self.add(node, "number", hex(n) if hexa and n >= 0 else repr(n))

    def visit_Raise(self, node: ast.Raise) -> None:
        self.add(node, "raise-pass", "pass")


def _is_number(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def _lines(src: bytes) -> list[bytes]:
    return src.splitlines(keepends=True)


def _offset(src: bytes, line: int, col: int) -> int:
    return sum(len(x) for x in _lines(src)[: line - 1]) + col


def _segment(src: bytes, node: ast.AST) -> str:
    a = _offset(src, node.lineno, node.col_offset)
    return src[a: _offset(src, node.end_lineno, node.end_col_offset)].decode("utf-8")


def apply(src: bytes, m: Mutant) -> bytes:
    """The source with one mutant spliced in; everything else (comments, layout, line numbers of the code above) is untouched."""
    a, b = _offset(src, m.span[0], m.span[1]), _offset(src, m.span[2], m.span[3])
    return src[:a] + m.replacement.encode("utf-8") + src[b:]


def find_mutants(src: bytes | str, rel: str) -> list[Mutant]:
    """Every valid mutant of a module, in source order, each with a stable key for the baseline."""
    src = src.encode("utf-8") if isinstance(src, str) else src
    f = _Finder(src, rel)
    f.visit(ast.parse(src))
    out, seen = [], {}
    old_lines = src.decode("utf-8").splitlines()
    for m in f.out:
        new = apply(src, m)
        try:
            compile(new, rel, "exec")
        except SyntaxError:
            continue
        m.original = old_lines[m.line - 1].strip()
        m.mutated = new.decode("utf-8").splitlines()[m.line - 1].strip()
        base = f"{rel}::{m.scope}::{m.operator}::{m.original} => {m.mutated}"
        seen[base] = seen.get(base, 0) + 1
        m.key = base if seen[base] == 1 else f"{base} #{seen[base]}"
        out.append(m)
    return out


def changed_lines(base: str, rel: str, root: pathlib.Path = ROOT) -> set[int]:
    """Line numbers of `rel` (in the working tree) added or changed since `base`."""
    p = subprocess.run(["git", "diff", "--no-color", "-U0", base, "--", rel], cwd=root, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"mutate: git diff against {base!r} failed: {p.stderr.strip()}")
    lines: set[int] = set()
    for h in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", p.stdout, re.M):
        start, count = int(h.group(1)), int(h.group(2) if h.group(2) is not None else 1)
        lines.update(range(start, start + count))
    return lines


def spread(items: list, n: int | None) -> list:
    """At most n items, evenly spaced over the list (deterministic), so a cap still samples the whole file."""
    if not n or len(items) <= n:
        return items
    return [items[int(i * len(items) / n)] for i in range(n)]


# ───────────────────────────────────────────── running mutants ─────────────────────────────────────────────
def _journal(root: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(tempfile.gettempdir()) / f"securax-mutate-{hashlib.sha256(str(root).encode()).hexdigest()[:12]}.json"


def recover(root: pathlib.Path = ROOT) -> list[str]:
    """Restore any file an earlier, killed run left mutated (from the journal). Returns the paths restored."""
    j, done = _journal(root), []
    try:
        rec = json.loads(j.read_text("utf-8"))
    except (OSError, ValueError):
        return done
    for rel, info in rec.items():
        p, data = root / rel, base64.b64decode(info["data"])
        if not p.exists() or p.read_bytes() != data:
            p.write_bytes(data)
            done.append(rel)
        os.utime(p, ns=(info["mtime_ns"], info["mtime_ns"]))
    j.unlink(missing_ok=True)
    return done


def test_command(target: dict) -> list[str]:
    if target.get("cmd"):
        return [sys.executable if c == "{python}" else c for c in target["cmd"]]
    return [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--no-header", *target["tests"]]


def run_tests(cmd: list[str], root: pathlib.Path, timeout: float, cache: str) -> tuple[str, float]:
    """('passed'|'failed'|'timeout', seconds). A fresh, empty bytecode cache: a same-size mutant can never reuse a stale .pyc."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPYCACHEPREFIX": cache}
    t = time.monotonic()
    proc = subprocess.Popen(cmd, cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        rc = proc.wait(timeout=timeout)
    except BaseException as e:                  # a timeout, or Ctrl-C / SIGTERM: never leave the test run behind
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()
        proc.wait()
        if not isinstance(e, subprocess.TimeoutExpired):
            raise
        return "timeout", time.monotonic() - t
    return ("passed" if rc == 0 else "failed"), time.monotonic() - t


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mutate_target(target: dict, root: pathlib.Path = ROOT, *, lines: set[int] | None = None, max_n: int | None = None,
                  timeout: float | None = None, progress=None) -> dict:
    """Run every selected mutant of one target. The file is restored after each mutant and verified by hash before returning."""
    rel = target["file"]
    path = root / rel
    original = path.read_bytes()
    st = path.stat()
    digest = sha(original)
    every = find_mutants(original, rel)
    chosen = [m for m in every if lines is None or set(range(m.span[0], m.span[2] + 1)) & lines]
    chosen = spread(chosen, max_n)
    res = {"file": rel, "generated": len(every), "mutants": len(chosen), "killed": 0, "timeout": 0, "survived": 0,
           "score": None, "survivors": [], "ran": [], "all_keys": [m.key for m in every], "error": None}
    if not chosen:
        return res
    cmd = test_command(target)
    cache = tempfile.mkdtemp(prefix="mutate-pyc-")
    journal = _journal(root)
    try:
        status, took = run_tests(cmd, root, timeout or 600, cache)
        if status != "passed":
            res["error"] = f"the tests do not pass on the unmutated file ({status}): fix them first"
            return res
        limit = timeout or max(20.0, took * 4 + 10)
        journal.write_text(json.dumps({rel: {"data": base64.b64encode(original).decode(), "mtime_ns": st.st_mtime_ns}}), "utf-8")
        for i, m in enumerate(chosen, 1):
            try:
                path.write_bytes(apply(original, m))
                status, _ = run_tests(cmd, root, limit, cache)
            finally:
                path.write_bytes(original)
                os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
            res["ran"].append(m.key)
            if status == "passed":
                res["survived"] += 1
                res["survivors"].append(m.public())
            else:
                res["killed"] += 1
                res["timeout"] += status == "timeout"
            if progress:
                progress(rel, i, len(chosen), m, status)
    finally:
        if path.read_bytes() != original:
            path.write_bytes(original)
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
        journal.unlink(missing_ok=True)
        shutil.rmtree(cache, ignore_errors=True)
    if sha(path.read_bytes()) != digest:
        raise SystemExit(f"mutate: {rel} does not match its original hash after restore (this must never happen)")
    done = res["killed"] + res["survived"]
    res["score"] = round(100 * res["killed"] / done, 1) if done else None
    return res


# ───────────────────────────────────────────── the ratchet ─────────────────────────────────────────────
def load_baseline(path: pathlib.Path = BASELINE) -> dict:
    try:
        return json.loads(path.read_text("utf-8")).get("survivors", {})
    except (OSError, ValueError):
        return {}


def compare(results: list[dict], base: dict) -> tuple[list[dict], list[str]]:
    """(new survivors not in the baseline, baseline entries that ran this time and were killed)."""
    new = [s for r in results for s in r["survivors"] if s["key"] not in base]
    alive = {s["key"] for r in results for s in r["survivors"]}
    fixed = [k for r in results for k in r["ran"] if k in base and k not in alive]
    return new, fixed


def updated_baseline(results: list[dict], base: dict) -> dict:
    """The baseline after this run: survivors added (known reasons kept); entries that ran and died, or no longer exist, dropped.
    Entries for mutants this run did not execute (a --max or --diff run) are kept as they were."""
    out = dict(base)
    for r in results:
        if r["error"]:
            continue
        exists = set(r["all_keys"])
        for k in list(out):
            if k.startswith(r["file"] + "::") and (k not in exists or k in r["ran"]):
                del out[k]
        for s in r["survivors"]:
            out[s["key"]] = base.get(s["key"], UNREVIEWED)
    return dict(sorted(out.items()))


def write_baseline(survivors: dict, path: pathlib.Path = BASELINE) -> None:
    doc = {"_doc": "Known surviving mutants (tools/mutate.py). Each is a missing test or an equivalent mutant, with the reason. "
                   "`--check` fails only on a survivor not listed here. Shrink it: add the test, then `--update-baseline`.",
           "survivors": survivors}
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", "utf-8")


# ───────────────────────────────────────────── the command ─────────────────────────────────────────────
def load_targets(path: pathlib.Path = CONFIG) -> list[dict]:
    return json.loads(path.read_text("utf-8"))["targets"]


def _interrupt(signum, frame):                  # SIGTERM / SIGHUP (a CI timeout): unwind through every finally, which restores
    raise KeyboardInterrupt(f"signal {signum}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true", help="every target in tools/mutate.json")
    mode.add_argument("--diff", metavar="BASE", help="only lines changed since BASE (e.g. origin/main)")
    ap.add_argument("--file", action="append", default=[], help="only this target (repeatable)")
    ap.add_argument("--max", type=int, default=None, help="at most N mutants per file, evenly spread")
    ap.add_argument("--timeout", type=float, default=None, help="seconds per mutant (default: 4x the clean run + 10, at least 20)")
    ap.add_argument("--check", action="store_true", help="exit 1 on a survivor that is not in the baseline")
    ap.add_argument("--update-baseline", action="store_true", help="write the survivors of this run into the baseline (reviewed!)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--out", help="also write the JSON report to this file")
    ap.add_argument("--list", action="store_true", help="list the mutants that would run, and run none")
    a = ap.parse_args(argv)
    if not (a.all or a.diff or a.file):
        ap.error("choose --all, --diff BASE or --file PATH")
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _interrupt)
    for rel in recover():
        print(f"mutate: restored {rel}, left mutated by an interrupted earlier run", file=sys.stderr)

    targets = load_targets()
    if a.file:
        want = {f.replace("\\", "/").lstrip("./") for f in a.file}
        unknown = want - {t["file"] for t in targets}
        if unknown:
            ap.error(f"not a mutation target: {', '.join(sorted(unknown))} (targets live in tools/mutate.json)")
        targets = [t for t in targets if t["file"] in want]

    def progress(rel, i, n, m, status):
        if not a.json:
            print(f"  [{i}/{n}] {status:<7} {rel.rsplit('/', 1)[-1]}:{m.line} {m.operator}", file=sys.stderr, flush=True)

    if a.list:
        for t in targets:
            lines = changed_lines(a.diff, t["file"]) if a.diff else None
            ms = [m for m in find_mutants((ROOT / t["file"]).read_bytes(), t["file"])
                  if lines is None or set(range(m.span[0], m.span[2] + 1)) & lines]
            ms = spread(ms, a.max)
            print(f"{t['file']}: {len(ms)} mutant(s)  <- {' '.join(test_command(t)[1:])}")
            for m in ms:
                print(f"  {m.line:>4} {m.operator:<11} {m.mutated[:110]}")
        return 0

    results = []
    for t in targets:
        lines = changed_lines(a.diff, t["file"]) if a.diff else None
        results.append(mutate_target(t, lines=lines, max_n=a.max, timeout=a.timeout, progress=progress))

    base = load_baseline()
    new, fixed = compare(results, base)
    errors = [r for r in results if r["error"]]
    report = {"mode": "diff " + a.diff if a.diff else "all", "max_per_file": a.max,
              "files": [{k: v for k, v in r.items() if k not in ("ran", "all_keys")} for r in results],
              "total": {k: sum(r[k] for r in results) for k in ("mutants", "killed", "timeout", "survived")},
              "new_survivors": new, "fixed_in_baseline": fixed, "ok": not errors and not (a.check and new)}
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", "utf-8")
    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for r in results:
            score = "n/a" if r["score"] is None else f"{r['score']}%"
            print(f"{r['file']}: {r['mutants']} mutant(s), {r['killed']} killed ({r['timeout']} by timeout), "
                  f"{r['survived']} survived, score {score}" + (f"  ERROR {r['error']}" if r["error"] else ""))
            for s in r["survivors"]:
                tag = "known" if s["key"] in base else "NEW  "
                print(f"  SURVIVED {tag} {s['file']}:{s['line']} {s['operator']}\n      was: {s['original']}\n      now: {s['mutated']}")
        tot = report["total"]
        done = tot["killed"] + tot["survived"]
        total_score = f"{round(100 * tot['killed'] / done, 1)}%" if done else "n/a"
        print(f"mutate: {tot['mutants']} mutant(s), score {total_score}, "
              f"{len(new)} new survivor(s)" + (f"; {len(fixed)} baseline entr(ies) now killed: tighten with --update-baseline" if fixed else ""))
        if a.check and new:
            print("mutate: FAILED: a new surviving mutant means a rail could weaken unseen. Add a test that kills it "
                  "(or, reviewed, explain it in the baseline with --update-baseline).")
    if a.update_baseline:
        nb = updated_baseline(results, base)
        write_baseline(nb)
        print(f"baseline written: {len(nb)} known survivor(s) in {BASELINE.relative_to(ROOT)}", file=sys.stderr)
    if errors:
        return 2
    return 1 if a.check and new else 0


if __name__ == "__main__":
    sys.exit(main())
