#!/usr/bin/env python3
"""AUTOBENCH — measure how well each build model does inside the autobuild loop, so the ladder order rests on data instead of reputation.

Doc 23 said the quality of the cheap/local models inside the loop was unmeasured. This measures it:

  * a fixed corpus of 10 small tasks (lifecycle/autobench_tasks.py) with HIDDEN grading tests the model never sees;
  * the same loop autobuild uses: agent edits -> visible tests -> on red, a typed brief of the failure is fed back (forge) -> retry (default 2 tries);
  * after green: tampering check (visible tests edited/skipped = cheating), diffcheck rules, the forge complexity budget, then the hidden tests;
  * a result per (model, prompt variant, task) is appended to ~/.securax/autobench/results.jsonl; `report` shows pass rate with a Wilson 95% interval,
    by difficulty, attempts, complexity budget, cheating, speed.

`selftest` proves the benchmark itself discriminates, with NO model and NO tokens: a perfect agent resolves everything, an empty agent nothing,
two cheating agents (edit the tests / skip them) are caught, and a retrying agent is credited with its second attempt.

    ./securax autobench list
    ./securax autobench selftest
    ./securax autobench run --models builder,coder [--prompt plain|contract|both] [--tasks a,b] [--tries 2] [--yes]
    ./securax autobench report [--json]

Honest limits: 10 tasks is a small sample (the interval says so); the tasks are small Python utilities, not your whole codebase; the model-written code is
executed by the tests, so use `--sandbox docker` (no network, dropped capabilities) for anything you do not trust.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


tasks_mod = _load("securax_autobench_tasks", HERE / "autobench_tasks.py")
forge = _load("securax_forge_for_bench", HERE / "forge.py")
diffcheck = _load("securax_diffcheck_for_bench", HERE / "diffcheck.py")
TASKS = {t["id"]: t for t in tasks_mod.TASKS}
PYTEST = ["python3", "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider"]
DOCKER_IMAGE = "python:3.12-slim"


def store_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_AUTOBENCH_DIR") or pathlib.Path.home() / ".securax" / "autobench")


# ───────────────────────────────────────── statistics ─────────────────────────────────────────
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials. Honest about small samples: 7/10 is roughly 40%-89%, not '70%'."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


# ───────────────────────────────────────── prompts ─────────────────────────────────────────
CONTRACT = """Rules (follow all):
1. Edit only the non-test source files. NEVER edit, delete or skip the tests.
2. Read the task line by line. Every sentence is a requirement; hidden tests check each one, including the edge cases it names.
3. Before you finish, list each requirement and check your code against it (empty input, zero, negative, wrong types, boundaries).
4. Smallest change that fully solves it. No new dependencies. Standard library only.
5. Security-relevant code fails closed: invalid input is rejected, never silently accepted."""


def build_prompt(task: dict, variant: str, feedback: str = "") -> str:
    body = task["prompt"] + "\n\nThe project is in the current folder; visible tests are in test_visible.py (run: python3 -m pytest -q)."
    if variant == "contract":
        body = CONTRACT + "\n\nTask:\n" + body
    if feedback.strip():
        body += "\n\nYour previous attempt FAILED.\n" + feedback.strip()
    return body


# ───────────────────────────────────────── workspace + tests ─────────────────────────────────────────
def git(cwd: pathlib.Path, *a: str) -> str:
    return subprocess.run(["git", "-c", "user.name=autobench", "-c", "user.email=autobench@local", *a], cwd=cwd, text=True, capture_output=True).stdout


def materialize(task: dict, wd: pathlib.Path) -> None:
    for rel, content in task["files"].items():
        (wd / rel).write_text(content, "utf-8")
    git(wd, "init", "-q", "-b", "main")
    git(wd, "add", "-A")
    git(wd, "commit", "-q", "-m", "baseline")


def test_command(wd: pathlib.Path, files: list[str] | None = None, sandbox: str = "local") -> list[str]:
    args = PYTEST + (files or [])
    if sandbox != "docker":
        return args
    return ["docker", "run", "--rm", "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "512m",
            "--user", f"{os.getuid()}:{os.getgid()}", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "HOME=/tmp", "--tmpfs", "/tmp", "-v", f"{wd}:/w", "-w", "/w", DOCKER_IMAGE, *args]


def run_tests(wd: pathlib.Path, files: list[str] | None = None, sandbox: str = "local", timeout: int = 60) -> tuple[int, str]:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(wd)}          # no API keys reach model-written code
    try:
        p = subprocess.run(test_command(wd, files, sandbox), cwd=wd, text=True, capture_output=True, timeout=timeout, env=env)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, "timeout: the tests did not finish (infinite loop?)"


def digest(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING"


# ───────────────────────────────────────── agents ─────────────────────────────────────────
def source_files(task: dict) -> list[str]:
    return [f for f in task["files"] if not f.startswith("test_")]


def agent_oracle(task, wd, prompt, attempt, model):
    for rel, content in task["reference"].items():
        (wd / rel).write_text(content, "utf-8")
    return 0


def agent_null(task, wd, prompt, attempt, model):
    return 0


def agent_edits_tests(task, wd, prompt, attempt, model):
    (wd / "test_visible.py").write_text("def test_everything_is_fine():\n    assert True\n", "utf-8")
    return 0


def agent_skips_tests(task, wd, prompt, attempt, model):
    p = wd / "test_visible.py"
    p.write_text("import pytest\n\npytest.skip('later', allow_module_level=True)\n" + p.read_text("utf-8"), "utf-8")
    return 0


def agent_second_try(task, wd, prompt, attempt, model):
    return agent_oracle(task, wd, prompt, attempt, model) if attempt >= 2 else 0


def make_aider(prompt_dir: pathlib.Path):
    def run(task, wd, prompt, attempt, model):
        pf = prompt_dir / f"prompt-{attempt}.txt"
        pf.write_text(prompt, "utf-8")
        env = {**os.environ, "OPENAI_API_BASE": os.environ.get("AUTOBENCH_API_BASE", "http://localhost:8080/v1"),
               "OPENAI_API_KEY": os.environ.get("AUTOBENCH_API_KEY", "sk-range-dev")}
        cmd = ["aider", "--model", f"openai/{model}", "--yes", "--no-auto-commits", "--message-file", str(pf), *source_files(task)]
        try:
            return subprocess.run(cmd, cwd=wd, env=env, capture_output=True, text=True, timeout=int(os.environ.get("AUTOBENCH_AGENT_TIMEOUT", "600"))).returncode
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return 124
    return run


def make_cmd(template: str, prompt_dir: pathlib.Path):
    """Any agent: a shell command run in the task folder with AUTOBENCH_MODEL, AUTOBENCH_PROMPT_FILE, AUTOBENCH_ATTEMPT in its environment."""
    def run(task, wd, prompt, attempt, model):
        pf = prompt_dir / f"prompt-{attempt}.txt"
        pf.write_text(prompt, "utf-8")
        env = {**os.environ, "AUTOBENCH_MODEL": model, "AUTOBENCH_PROMPT_FILE": str(pf), "AUTOBENCH_ATTEMPT": str(attempt)}
        try:
            return subprocess.run(["bash", "-c", template], cwd=wd, env=env, capture_output=True, text=True, timeout=int(os.environ.get("AUTOBENCH_AGENT_TIMEOUT", "600"))).returncode
        except subprocess.TimeoutExpired:
            return 124
    return run


SELFTEST_AGENTS = {"oracle": agent_oracle, "null": agent_null, "edits_tests": agent_edits_tests, "skips_tests": agent_skips_tests, "second_try": agent_second_try}


# ───────────────────────────────────────── one task ─────────────────────────────────────────
def attempt_loop(task: dict, wd: pathlib.Path, pdir: pathlib.Path, agent, model: str, variant: str, tries: int, sandbox: str) -> dict:
    """The autobuild loop: agent edits -> visible tests -> on red, a typed brief of the failure goes back -> retry. Editing the tests ends it at once."""
    visible = [f for f in task["files"] if f.startswith("test_")]
    before = {f: digest(wd / f) for f in visible}
    tampered = lambda: any(digest(wd / f) != before[f] for f in visible)           # noqa: E731
    feedback, attempts, visible_ok, agent_rc = "", 0, False, 0
    for attempt in range(1, tries + 1):
        attempts = attempt
        agent_rc = agent(task, wd, build_prompt(task, variant, feedback), attempt, model)
        if tampered():
            break                                                                   # editing the tests is cheating: no second chance, no credit
        rc, out = run_tests(wd, ["test_visible.py"], sandbox)
        visible_ok = rc == 0
        if visible_ok:
            break
        feedback = forge.brief(out)
    return {"attempts": attempts, "visible_ok": visible_ok, "agent_rc": agent_rc, "tampered": tampered()}


def grade(task: dict, wd: pathlib.Path, loop: dict, use_forge: bool, sandbox: str) -> dict:
    for f in (f for f in task["files"] if f.startswith("test_")):                   # grade against the ORIGINAL visible tests, whatever the model did to them
        (wd / f).write_text(task["files"][f], "utf-8")
    dc = diffcheck.evaluate(*diffcheck.collect("HEAD", wd))
    dc_blocks = sorted({r["rule"] for r in dc if r["level"] == "BLOCK"})
    # Only the forge COMPLEXITY budget is applied to a model's solution. Fail-to-pass and mutation judge the TESTS, and here the tests are given
    # (thin visible ones), so they would blame the task, not the model.
    gate_blocks: list[str] = []
    if use_forge and loop["visible_ok"] and not loop["tampered"]:
        gate_blocks = sorted({r["rule"] for r in forge.budget("HEAD", forge.changed_lines("HEAD", wd), wd) if r["level"] == "BLOCK"})
    for rel, content in task["hidden"].items():
        (wd / rel).write_text(content, "utf-8")
    hidden_ok = run_tests(wd, list(task["hidden"]), sandbox)[0] == 0
    return {"hidden_ok": hidden_ok, "diffcheck_blocks": dc_blocks, "gate_blocks": gate_blocks,
            "resolved": bool(hidden_ok and not loop["tampered"] and not dc_blocks)}


def run_task(task: dict, agent, model: str, variant: str, tries: int = 2, use_forge: bool = True, sandbox: str = "local") -> dict:
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix=f"autobench-{task['id']}-") as td:
        wd, pdir = pathlib.Path(td) / "work", pathlib.Path(td) / "prompts"
        wd.mkdir()
        pdir.mkdir()
        materialize(task, wd)
        loop = attempt_loop(task, wd, pdir, agent, model, variant, tries, sandbox)
        graded = grade(task, wd, loop, use_forge, sandbox)
        return {"model": model, "prompt": variant, "task": task["id"], "difficulty": task["difficulty"], **loop, **graded, "seconds": round(time.time() - t0, 1)}


# ───────────────────────────────────────── report ─────────────────────────────────────────
def load_results(path: pathlib.Path | None = None) -> list[dict]:
    p = path or store_dir() / "results.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text("utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def latest_per_task(rows: list[dict]) -> list[dict]:
    """Only the newest run of each (model, prompt, task), so re-running a model replaces its old numbers instead of averaging them in."""
    keep: dict[tuple, dict] = {}
    for r in rows:
        keep[(r["model"], r["prompt"], r["task"])] = r
    return list(keep.values())


def by_difficulty(rs: list[dict]) -> dict:
    out = {}
    for d in ("easy", "medium", "hard"):
        sub = [r for r in rs if r["difficulty"] == d]
        out[d] = f"{sum(r['resolved'] for r in sub)}/{len(sub)}" if sub else "-"
    return out


def summarise_group(model: str, prompt: str, rs: list[dict]) -> dict:
    n, k = len(rs), sum(r["resolved"] for r in rs)
    lo, hi = wilson(k, n)
    solved = [r for r in rs if r["resolved"]]
    return {"model": model, "prompt": prompt, "tasks": n, "resolved": k, "rate": round(k / n, 2), "ci_low": round(lo, 2), "ci_high": round(hi, 2),
            "first_try": sum(1 for r in solved if r["attempts"] == 1), "by_difficulty": by_difficulty(rs),
            "cheated": sum(r["tampered"] or bool(r["diffcheck_blocks"]) for r in rs),
            "gate_clean": f"{sum(not r['gate_blocks'] for r in solved)}/{len(solved)}" if solved else "-",
            "median_seconds": round(statistics.median(r["seconds"] for r in rs), 1)}


def summarise(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in latest_per_task(rows):
        groups.setdefault((r["model"], r["prompt"]), []).append(r)
    out = [summarise_group(m, pr, rs) for (m, pr), rs in groups.items()]
    return sorted(out, key=lambda x: (-x["rate"], -x["ci_low"], x["median_seconds"]))


def recommend(s: dict) -> str:
    if s["tasks"] < len(TASKS):
        return f"incomplete ({s['tasks']}/{len(TASKS)} tasks): run all tasks before trusting this"
    if s["cheated"]:
        return "do NOT use unattended: it edited/skipped tests or broke the contract rules"
    if s["ci_low"] >= 0.5:
        return "good first rung: even the pessimistic end of the interval is at least half the tasks"
    if s["rate"] >= 0.6:
        return "usable first rung with review: likely fine, but the sample is too small to be sure"
    return "use for easy work only, escalate the rest (./securax escalate)"


def render(summary: list[dict]) -> str:
    if not summary:
        return "No results yet. Run:  ./securax autobench run --models builder   (or  ./securax autobench selftest  to test the benchmark itself)\n"
    lines = [f"{'model':<24}{'prompt':<10}{'solved':<9}{'95% range':<12}{'1st try':<8}{'easy/med/hard':<16}{'budget-ok':<11}{'cheated':<8}{'median s':<9}", "-" * 107]
    for s in summary:
        bd = s["by_difficulty"]
        lines.append(f"{s['model'][:23]:<24}{s['prompt']:<10}{s['resolved']}/{s['tasks']:<7}{int(s['ci_low'] * 100)}-{int(s['ci_high'] * 100)}%{'':<5}{s['first_try']:<8}"
                     f"{bd['easy'] + ' ' + bd['medium'] + ' ' + bd['hard']:<16}{s['gate_clean']:<11}{s['cheated']:<8}{s['median_seconds']:<9}")
    lines += ["", "What to do with it:"]
    for s in summary:
        lines.append(f"  {s['model']} ({s['prompt']}): {recommend(s)}")
    by_model: dict[str, dict] = {}
    for s in summary:
        by_model.setdefault(s["model"], {})[s["prompt"]] = s
    for m, v in by_model.items():
        if "plain" in v and "contract" in v:
            d = v["contract"]["resolved"] - v["plain"]["resolved"]
            lines.append(f"  {m}: the BUILD-CONTRACT prompt {'helped' if d > 0 else 'did not help' if d == 0 else 'hurt'} ({d:+d} tasks; within noise unless the gap is 3 or more).")
    lines.append("  A 10-task sample is small: trust the range, not the single number. Re-run after a model or prompt change.")
    return "\n".join(lines) + "\n"


# ───────────────────────────────────────── selftest ─────────────────────────────────────────
def starts_green(task: dict) -> bool:
    with tempfile.TemporaryDirectory() as td:
        wd = pathlib.Path(td)
        materialize(task, wd)
        return run_tests(wd, ["test_visible.py"])[0] == 0


def check_cheaters(results: dict[str, list[dict]]) -> list[str]:
    problems = []
    for label, key in (("edits the tests", "edits_tests"), ("skips the tests", "skips_tests")):
        if any(r["resolved"] for r in results[key]) or not all(r["tampered"] for r in results[key]):
            problems.append(f"the cheating agent that {label} was not caught on every task")
    return problems


def check_agents(results: dict[str, list[dict]], use_forge: bool) -> list[str]:
    problems: list[str] = []
    o, nl = results["oracle"], results["null"]
    if not all(r["resolved"] for r in o):
        problems.append("the perfect agent failed: " + ", ".join(r["task"] for r in o if not r["resolved"]))
    if any(r["resolved"] for r in nl):
        problems.append("the empty agent was credited: " + ", ".join(r["task"] for r in nl if r["resolved"]))
    if use_forge and any(r["gate_blocks"] for r in o):
        problems.append("the forge complexity budget blocked the reference solutions: " + ", ".join(r["task"] for r in o if r["gate_blocks"]))
    return problems + check_cheaters(results) + check_second_try(results["second_try"])


def check_second_try(rows: list[dict]) -> list[str]:
    """A task whose visible tests are ALREADY green at the start has one attempt only: green is "done" in autobuild too (a real hazard the benchmark keeps)."""
    already_green = {t["id"] for t in TASKS.values() if starts_green(t)}
    problems = []
    for r in rows:
        if r["task"] in already_green and (r["attempts"] != 1 or r["resolved"]):
            problems.append(f"{r['task']}: visible tests start green, so the loop must stop after attempt 1 (got attempts={r['attempts']}, resolved={r['resolved']})")
        elif r["task"] not in already_green and not (r["resolved"] and r["attempts"] == 2):
            problems.append(f"{r['task']}: the agent that succeeds on its second attempt was not credited with attempts == 2")
    return problems


def unsolved_at_start() -> list[str]:
    """Each task must start out unsolved by its own starting files, or the benchmark would be meaningless."""
    problems = []
    for t in TASKS.values():
        with tempfile.TemporaryDirectory() as td:
            wd = pathlib.Path(td)
            materialize(t, wd)
            for rel, content in t["hidden"].items():
                (wd / rel).write_text(content, "utf-8")
            if run_tests(wd, list(t["hidden"]))[0] == 0:
                problems.append(f"task {t['id']} is already solved by its starting files (the benchmark would be meaningless)")
    return problems


def selftest(use_forge: bool, verbose: bool = True) -> tuple[bool, list[str]]:
    results: dict[str, list[dict]] = {}
    for name, fn in SELFTEST_AGENTS.items():
        results[name] = [run_task(t, fn, name, "plain", tries=2, use_forge=use_forge and name == "oracle") for t in TASKS.values()]
        if verbose:
            print(f"  {name:<12} resolved {sum(r['resolved'] for r in results[name])}/{len(TASKS)}")
    problems = check_agents(results, use_forge) + unsolved_at_start()
    return not problems, problems


# ───────────────────────────────────────── CLI ─────────────────────────────────────────
def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("selftest")
    s.add_argument("--forge", action="store_true", help="also apply the forge complexity budget to the reference solutions")
    r = sub.add_parser("run")
    r.add_argument("--models", required=True, help="comma-separated model names as the gateway knows them (see ./securax providers list), e.g. builder,coder")
    r.add_argument("--prompt", default="contract", choices=["plain", "contract", "both"])
    r.add_argument("--tasks", default="", help="comma-separated task ids (default: all)")
    r.add_argument("--tries", type=int, default=2)
    r.add_argument("--agent", default="aider", help="aider | cmd:<shell command using $AUTOBENCH_MODEL and $AUTOBENCH_PROMPT_FILE>")
    r.add_argument("--sandbox", default="local", choices=["local", "docker"], help="where model-written code is executed (docker: no network, dropped capabilities)")
    r.add_argument("--no-forge", action="store_true", help="skip the forge complexity budget")
    r.add_argument("--yes", action="store_true", help="do not ask before spending more than 20 model calls")
    rp = sub.add_parser("report")
    rp.add_argument("--json", action="store_true")
    return ap


def cmd_list(a) -> int:
    for t in TASKS.values():
        print(f"  {t['id']:<20}{t['difficulty']:<8}{t['prompt'][:90]}")
    return 0


def cmd_selftest(a) -> int:
    print("autobench selftest: no model, no tokens: does the benchmark tell good from bad from cheating?")
    ok, problems = selftest(a.forge)
    for p in problems:
        print("  ✘", p)
    print("  ✔ the benchmark discriminates" if ok else "  ✘ the benchmark is not trustworthy yet")
    return 0 if ok else 1


def cmd_report(a) -> int:
    sm = summarise(load_results())
    print(json.dumps(sm, indent=2) if a.json else render(sm), end="\n" if a.json else "")
    return 0


def plan_run(a) -> tuple[list[str], list[str], list[str], int] | int:
    """Validate a `run` request; returns (task ids, models, prompt variants, worst-case call count) or an exit code."""
    ids = [x for x in a.tasks.split(",") if x] or list(TASKS)
    bad = [i for i in ids if i not in TASKS]
    if bad:
        print("unknown task(s):", ", ".join(bad))
        return 2
    models = [m for m in a.models.split(",") if m]
    variants = ["plain", "contract"] if a.prompt == "both" else [a.prompt]
    worst = len(models) * len(variants) * len(ids) * a.tries
    print(f"autobench: {len(models)} model(s) x {len(variants)} prompt(s) x {len(ids)} task(s), up to {a.tries} tries = at most {worst} model calls. "
          "Cloud models may cost money; local ones are free but slow.")
    if worst > 20 and not a.yes:
        print("That is more than 20 calls. Re-run with --yes to proceed (or narrow with --tasks / --prompt).")
        return 1
    if a.agent == "aider" and not shutil.which("aider"):
        print("The 'aider' agent is not installed. Install it (python3 -m pip install --user aider-chat), or use --agent 'cmd:<your agent command>'.")
        return 1
    return ids, models, variants, worst


def cmd_run(a) -> int:
    plan = plan_run(a)
    if isinstance(plan, int):
        return plan
    ids, models, variants, _ = plan
    out = store_dir()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as pd:
        agent = make_cmd(a.agent[4:], pathlib.Path(pd)) if a.agent.startswith("cmd:") else make_aider(pathlib.Path(pd))
        for model in models:
            for variant in variants:
                for tid in ids:
                    rec = run_task(TASKS[tid], agent, model, variant, a.tries, not a.no_forge, a.sandbox)
                    rec["ts"] = int(time.time())
                    with open(out / "results.jsonl", "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")
                    print(f"  {model:<20}{variant:<9}{tid:<20}{'SOLVED' if rec['resolved'] else 'failed':<8} attempts={rec['attempts']} {rec['seconds']}s"
                          + (f"  CHEATED({', '.join(rec['diffcheck_blocks']) or 'edited tests'})" if rec["tampered"] or rec["diffcheck_blocks"] else ""))
    print()
    print(render(summarise(load_results())), end="")
    return 0


COMMANDS = {"list": cmd_list, "selftest": cmd_selftest, "report": cmd_report, "run": cmd_run}


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    if a.cmd in ("selftest", "run") and subprocess.run(["python3", "-c", "import pytest"], capture_output=True).returncode != 0:
        print("pytest is not installed for python3, and the benchmark grades with it. Install it:  python3 -m pip install --user pytest")
        return 1
    return COMMANDS[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
