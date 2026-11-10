#!/usr/bin/env python3
"""The open-model agent for .github/workflows/autobuild.yml: build SecuRAX from a phone, without Claude (doc 83, section 7).

    python3 lifecycle/autobuild_ci.py config         the OpenCode config for the runner (OpenCode Go only, one key, no web fetch)
    python3 lifecycle/autobuild_ci.py agent          one attempt: the model the route calls for, the brief, the last failure;
                                                     the next model in the chain if one is out of allowance
    python3 lifecycle/autobuild_ci.py slug           a branch-safe name for $TASK
    python3 lifecycle/autobuild_ci.py summary RC     the run's summary for the GitHub page

The models come from plugins/catalog.json (the same chains the estate uses), limited to OpenCode Go, so one repository secret
(OPENCODE_GO_API_KEY) serves both. `./securax autobuild` calls `agent` once per attempt and applies the gates itself: this
file only writes code, it never decides that code is good. Standard library only.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "plugins" / "catalog.json"
GO_BASE = "https://opencode.ai/inference/go/v1"
PROVIDER = "gocode"
INSTRUCTIONS = ["AGENTS.md", "BUILD-CONTRACT.md", "LESSONS.md"]


def chain(name: str, catalog: pathlib.Path = CATALOG) -> list[str]:
    """The model names of one coding chain ('builder' or 'strong'), in order, OpenCode Go only."""
    d = json.loads(catalog.read_text("utf-8"))
    by = {p["id"]: p for p in d["providers"]}
    out = []
    for pid in d["chains"][name]:
        p = by.get(pid, {})
        if p.get("api_base") == GO_BASE and p.get("model"):
            m = p["model"].split("/", 1)[1] if p["model"].startswith("openai/") else p["model"]
            out.append(m) if m not in out else None
    return out


def config(catalog: pathlib.Path = CATALOG) -> dict:
    models = {m: {"name": m, "limit": {"context": 128000, "output": 16384}} for m in chain("strong", catalog) + chain("builder", catalog)}
    first = chain("builder", catalog)[0]
    return {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "share": "disabled",
        "enabled_providers": [PROVIDER],
        "model": f"{PROVIDER}/{first}",
        "small_model": f"{PROVIDER}/{first}",
        # the runner is thrown away after the job and holds no write token, so the agent may edit and run commands without asking;
        # it may not fetch web pages, so nothing it reads from the internet can steer it
        "permission": {"edit": "allow", "bash": "allow", "webfetch": "deny"},
        "instructions": [str(ROOT / n) for n in INSTRUCTIONS],
        "provider": {PROVIDER: {"npm": "@ai-sdk/openai-compatible", "name": "OpenCode Go",
                                "options": {"baseURL": GO_BASE, "apiKey": "{env:OPENCODE_GO_API_KEY}"}, "models": models}},
    }


def tier(task: str) -> str:
    r = subprocess.run([sys.executable, str(ROOT / "lifecycle" / "route.py"), task, "--json"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("tier", "local")
    except (json.JSONDecodeError, AttributeError):
        return "strong"                      # unsure: the stronger models, never the weaker


def prompt(env: dict, strong: bool = True) -> str:
    brief = pathlib.Path(env.get("AUTOBUILD_BRIEF", ""))
    text = brief.read_text("utf-8") if brief.is_file() else env.get("AUTOBUILD_TASK", "")
    fb = pathlib.Path(env.get("AUTOBUILD_FEEDBACK", ""))
    if fb.is_file() and fb.stat().st_size:
        why = subprocess.run([sys.executable, str(ROOT / "lifecycle" / "forge.py"), "brief", str(fb)], capture_output=True, text=True).stdout
        text += "\n\nThe previous attempt FAILED the gates. Fix exactly this, and change nothing else:\n" + (why or fb.read_text("utf-8")[-4000:])
    how = ("Use the @planner subagent first, the @test-writer for the failing test, then @code-reviewer (and @security-reviewer for "
           "sensitive code) before you stop, and @docs-keeper for the paperwork." if strong else
           "Work directly: no subagents (each one is a whole extra model session, and this task is small). Read only what you need.")
    # The gates that decide, named, so the model runs them itself before it stops. Not naming diffcheck cost a whole failed
    # attempt per task (2026-11-10: the model reported "all green" from pytest and fitness, then diffcheck blocked it).
    gates = (" Before you stop, run the same gates that will judge you, and fix everything they report: ./securax verify ;"
             " python3 lifecycle/diffcheck.py ; python3 lifecycle/forge.py gate --base HEAD .")
    return text + ("\n\nWork in this checkout. Follow AGENTS.md and BUILD-CONTRACT.md. " + how + gates +
                   " Do not commit, push, skip a test or weaken a rail: the gates run after you.")


PROBE_CACHE = pathlib.Path.home() / ".cache" / "securax" / "go-models.json"
PROBE_TTL_S = 6 * 3600


def usable(models: list[str], run=subprocess.run, cache: pathlib.Path = PROBE_CACHE, now: float | None = None) -> list[str]:
    """The models that answer a one-line prompt within a minute, remembered for six hours. A model the account cannot use
    (a region or plan limit) or one that hangs is dropped before the real work, instead of costing an attempt. Never empty:
    if none answers, the whole chain is tried as before."""
    now = time.time() if now is None else now
    try:
        seen = json.loads(cache.read_text("utf-8"))
    except (OSError, ValueError):
        seen = {}
    keep = []
    for m in models:
        hit = seen.get(m)
        if not hit or now - hit.get("at", 0) > PROBE_TTL_S:
            try:
                ok = run(["opencode", "run", "--model", f"{PROVIDER}/{m}", "Reply with the single word OK."], cwd=str(ROOT),
                         timeout=60, capture_output=True).returncode == 0
            except subprocess.TimeoutExpired:
                ok = False
            hit = seen[m] = {"ok": ok, "at": now}
        if hit["ok"]:
            keep.append(m)
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(seen), "utf-8")
    except OSError:
        pass
    return keep or models


def agent(env: dict | None = None, run=subprocess.run) -> int:
    env = dict(os.environ if env is None else env)
    strong = tier(env.get("AUTOBUILD_TASK", "")) == "strong"
    models = chain("strong" if strong else "builder")
    if env.get("AUTOBUILD_PROBE", "1") != "0":
        models = usable(models, run)
    text = prompt(env, strong)
    budget = int(env.get("AUTOBUILD_MODEL_MINUTES", "25")) * 60     # a hung model call must not hold the whole run
    rc = 1
    for m in models:
        try:
            rc = run(["opencode", "run", "--model", f"{PROVIDER}/{m}", text], cwd=str(ROOT), timeout=budget).returncode
        except subprocess.TimeoutExpired:
            rc = 124
        if rc == 0:
            break
        print(f"autobuild_ci: {m} did not finish (exit {rc}); trying the next model in the chain", file=sys.stderr)
        if rc == 124 and "ran out of time" not in text:
            # Hand over, do not restart: the timed-out model's edits are still in this checkout. Without this note the next
            # model began blind, judged the task done and stopped, and the run went "green" with no change (2026-11-10).
            text += ("\n\nA previous model ran out of time on this task. Its unfinished changes are in this checkout: run "
                     "git status and git diff FIRST, keep what is right, and finish the task from there. Do not start over.")
    run(["git", "add", "-A"], cwd=str(ROOT))      # new files must be staged, or the impact-map check cannot see them
    return 0                                     # the gates decide, not the agent's exit code


def slug(task: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", task.lower()).strip("-")[:40].strip("-")
    return s or "task"


def summary(rc: int) -> str:
    if rc == 0:
        return "### autobuild: green\nThe open models built it and every gate passed. The next job opens the PR."
    return ("### autobuild: not green\nThe gates did not pass, so nothing was kept. The brief for a stronger model is in the "
            "run's artifacts (escalation-brief). Try a smaller task, or run it on the strong chain from a laptop: "
            "`./securax opencode --strong`.")


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "config":
        print(json.dumps(config(), indent=1))
        return 0
    if cmd == "agent":
        return agent()
    if cmd == "slug":
        print(slug(os.environ.get("TASK", "")))
        return 0
    if cmd == "summary":
        print(summary(int(argv[1]) if len(argv) > 1 else 1))
        return 0
    print(__doc__)
    return 0 if cmd in ("-h", "--help") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
