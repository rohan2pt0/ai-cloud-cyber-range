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


def prompt(env: dict) -> str:
    brief = pathlib.Path(env.get("AUTOBUILD_BRIEF", ""))
    text = brief.read_text("utf-8") if brief.is_file() else env.get("AUTOBUILD_TASK", "")
    fb = pathlib.Path(env.get("AUTOBUILD_FEEDBACK", ""))
    if fb.is_file() and fb.stat().st_size:
        why = subprocess.run([sys.executable, str(ROOT / "lifecycle" / "forge.py"), "brief", str(fb)], capture_output=True, text=True).stdout
        text += "\n\nThe previous attempt FAILED the gates. Fix exactly this, and change nothing else:\n" + (why or fb.read_text("utf-8")[-4000:])
    return text + ("\n\nWork in this checkout. Follow AGENTS.md and BUILD-CONTRACT.md. Use the @planner subagent first, the "
                   "@test-writer for the failing test, then @code-reviewer (and @security-reviewer for sensitive code) before you stop, "
                   "and @docs-keeper for the paperwork. Do not commit, push, skip a test or weaken a rail: the gates run after you.")


def agent(env: dict | None = None, run=subprocess.run) -> int:
    env = dict(os.environ if env is None else env)
    models = chain("strong" if tier(env.get("AUTOBUILD_TASK", "")) == "strong" else "builder")
    text = prompt(env)
    rc = 1
    for m in models:
        rc = run(["opencode", "run", "--model", f"{PROVIDER}/{m}", text], cwd=str(ROOT)).returncode
        if rc == 0:
            break
        print(f"autobuild_ci: {m} did not finish (exit {rc}); trying the next model in the chain", file=sys.stderr)
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
