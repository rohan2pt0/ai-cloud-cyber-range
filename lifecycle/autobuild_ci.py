#!/usr/bin/env python3
"""The open-model agent for .github/workflows/autobuild.yml: build SecuRAX from a phone, without Claude (doc 83, section 7).

    python3 lifecycle/autobuild_ci.py config         the OpenCode config for the runner (OpenCode Go only, one key, no web fetch)
    python3 lifecycle/autobuild_ci.py agent          one attempt: the model the route calls for, the brief, the last failure;
                                                     the next model in the chain if one is out of allowance
    python3 lifecycle/autobuild_ci.py slug           a branch-safe name for $TASK
    python3 lifecycle/autobuild_ci.py check          is $TASK a brief one model can finish alone? (small, test-first, no slow audit)
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
    # The order matters as much as the names. `./securax verify` is the slow one (the full pytest and the whole Life OS suite,
    # about 10 minutes, silent), so the model is told to run it ONCE, last, into a file: run early or twice it used up the
    # model's time, and on 2026-11-15 its silence was read as a hung model (see `watched`). Each command is on its own line,
    # with no sentence full stop after it: the model once ran the full stop as an argument.
    gates = ("\n\nTest first, then the gates, in this order:\n"
             "1. Write the one test the brief names and see it fail. Change the code until that ONE test passes. While you work, "
             "run only that test (seconds), never a whole suite.\n"
             "2. Then the fast gates, and fix what they report:\n"
             "   ruff check .\n"
             "   git add -A\n"
             "   python3 lifecycle/diffcheck.py\n"
             "   python3 lifecycle/forge.py gate --base HEAD\n"
             "3. Last, ONCE, the slow gate. It is silent for about 10 minutes and already holds the full pytest and the full Life OS "
             "npm test, so do not run those separately:\n"
             "   ./securax verify > /tmp/verify.log 2>&1; echo rc=$?; tail -n 40 /tmp/verify.log\n"
             "Do not run a browser audit (ui_audit, device_audit, kit_audit, persona_audit, robustness_audit) or the sandbox, and "
             "do not install anything: the reviewer runs those after you.")
    return text + ("\n\nWork in this checkout. Follow AGENTS.md and BUILD-CONTRACT.md. " + how + gates +
                   "\nDo not commit, push, skip a test or weaken a rail: the gates run after you.")


PROBE_CACHE = pathlib.Path.home() / ".cache" / "securax" / "go-models.json"
PROBE_TTL_S = 6 * 3600
HUNG_TTL_S = 30 * 60     # a model marked hung on a real task is looked at again after this (an outage clears, a bad model stays out)


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
        ttl = HUNG_TTL_S if hit and hit.get("why") else PROBE_TTL_S      # a hang may have been the provider: look again soon
        if not hit or now - hit.get("at", 0) > ttl:
            try:
                r = run(["opencode", "run", "--model", f"{PROVIDER}/{m}", "Reply with the single word OK."], cwd=str(ROOT),
                        timeout=60, capture_output=True, text=True)
                said = (getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or "")
                # opencode exits 0 even on a provider error ("Error: UnknownError ... Unexpected server error", 2026-11-10),
                # so a model is usable only if it really answered OK and printed no error
                ok = r.returncode == 0 and bool(re.search(r"\bOK\b", said)) and not re.search(r"\bError\b|UnknownError", said)
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
    if not keep:
        print("autobuild_ci: no OpenCode Go model answers right now (the provider is failing or out of allowance); "
              "trying the chain anyway, and the watchdog will stop a silent one", file=sys.stderr)
    return keep or models


STALL_S = 6 * 60      # no output for this long = the model hangs (it printed nothing in 25 min twice on 2026-11-10)
TOOL_S = 20 * 60      # one command of the model's own may stay silent this long (the Life OS suite alone takes 7 minutes, verify 10)
OUT_OF_TIME = 123     # the model was working but used its time; 124 means it hung (silent, and running nothing)


def _busy(pid: int, run=subprocess.run) -> bool:
    """Is the model running a command of its own right now? OpenCode prints a command only when it ENDS, so a model
    waiting for `npm test` or `./securax verify` is silent for minutes while it works. Its commands are child processes
    of the agent; a model waiting for the provider has none. Unsure (no `ps`) means no: the old, stricter rule."""
    try:
        out = run(["ps", "-eo", "pid=,ppid="], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return any(line.split()[1:2] == [str(pid)] for line in out.splitlines())


def watched(cmd: list[str], budget: int, stall: int = STALL_S, cwd: str = str(ROOT), tool: int = TOOL_S) -> int:
    """Run a model, passing its output through, and stop it early when it goes SILENT: a working model prints its
    reads, edits and commands as it goes; one that prints nothing for `stall` seconds is hung, and waiting the whole
    budget for it cost 25 minutes per task. Silence while the model runs a command of its own is work, not a hang
    (on 2026-11-15 the Life OS suite passed 6 minutes and every delegated task was stopped mid-test): that is allowed
    `tool` seconds. Returns the exit code, 124 when it hung, 123 (OUT_OF_TIME) when it was working but used its time."""
    import selectors
    import signal
    # its own process group, so that stopping the model also stops the command it started (an orphaned test run would
    # keep writing into the checkout while the next model works in it)
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)
    start = last = time.time()
    try:
        while True:
            if sel.select(timeout=5):
                chunk = os.read(p.stdout.fileno(), 65536)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.flush()
                last = time.time()
            now = time.time()
            quiet = now - last
            working = quiet > stall and _busy(p.pid)          # asked only once the quiet limit has passed
            if now - start > budget:
                why, rc = "used its %d min" % (budget // 60), OUT_OF_TIME
            elif working and quiet > tool:
                why, rc = "ran one command for %d min with no output" % (tool // 60), OUT_OF_TIME
            elif quiet > stall and not working:
                why, rc = "went silent for %d min and was running no command" % (stall // 60), 124
            else:
                continue
            print(f"autobuild_ci: stopping the model: it {why}", file=sys.stderr)
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                p.kill()
            p.wait(timeout=30)
            return rc
        return p.wait(timeout=60)
    finally:
        sel.close()


def _mark_hung(model: str, cache: pathlib.Path = PROBE_CACHE) -> None:
    """A model that hung on real work is skipped for the probe's six hours, even though it answers a one-line prompt."""
    try:
        seen = json.loads(cache.read_text("utf-8"))
    except (OSError, ValueError):
        seen = {}
    seen[model] = {"ok": False, "at": time.time(), "why": "hung on a real task"}
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(seen), "utf-8")
    except OSError:
        pass


def agent(env: dict | None = None, run=subprocess.run) -> int:
    env = dict(os.environ if env is None else env)
    strong = tier(env.get("AUTOBUILD_TASK", "")) == "strong"
    models = chain("strong" if strong else "builder")
    if env.get("AUTOBUILD_PROBE", "1") != "0":
        models = usable(models, run)
    text = prompt(env, strong)
    # a model call must not hold the whole run; 40 min leaves room for the one slow gate (about 10) after the work itself
    budget = int(env.get("AUTOBUILD_MODEL_MINUTES", "40")) * 60
    rc = 1
    for m in models:
        cmd = ["opencode", "run", "--model", f"{PROVIDER}/{m}", text]
        if run is subprocess.run:                              # the real thing: watch for a silent (hung) model
            rc = watched(cmd, budget, int(env.get("AUTOBUILD_STALL_MINUTES", "6")) * 60,
                         tool=int(env.get("AUTOBUILD_TOOL_MINUTES", "20")) * 60)
            if rc == 124:                                      # only a real hang: a model that used its time is not a bad model
                _mark_hung(m)
        else:                                                  # tests inject their own runner
            try:
                rc = run(cmd, cwd=str(ROOT), timeout=budget).returncode
            except subprocess.TimeoutExpired:
                rc = 124
        if rc == 0:
            break
        print(f"autobuild_ci: {m} did not finish (exit {rc}); trying the next model in the chain", file=sys.stderr)
        if rc in (124, OUT_OF_TIME) and "ran out of time" not in text:
            # Hand over, do not restart: the timed-out model's edits are still in this checkout. Without this note the next
            # model began blind, judged the task done and stopped, and the run went "green" with no change (2026-11-10).
            text += ("\n\nA previous model ran out of time on this task. Its unfinished changes are in this checkout: run "
                     "git status and git diff FIRST, keep what is right, and finish the task from there. Do not start over.")
    run(["git", "add", "-A"], cwd=str(ROOT))      # new files must be staged, or the impact-map check cannot see them
    return 0                                     # the gates decide, not the agent's exit code


BRIEF_MAX = 1500      # characters: "3 to 8 lines". Longer briefs kept the model reading and planning past its time
BRIEF_FILES = 4       # more files than this is more than one step: send it as slices
SLOW = ("ui_audit", "device_audit", "kit_audit", "persona_audit", "robustness_audit", "sandbox/run.py", "verify --full")
_PATH = re.compile(r"(?<![\w./-])(?:[\w.-]+/)+[\w.-]+\.[a-z]{1,5}\b|(?<![\w./-])(?:securax|[\w-]+\.(?:py|js|json|sh|css|html|md|yml))\b")
PAPERWORK = ("CHANGELOG.md", "README.md", "LESSONS.md", "tools/readme_sync.py", "tools/features_sync.py", "docs/sync_status.py",
             "governance/queue.json", "guiding-map/build.js", "build.js", "guiding-map/package.json", "package.json")


def brief_problems(task: str) -> list[str]:
    """Why one model could not finish this brief alone, in plain words; empty when it can. A brief is one step: short,
    with the ONE test that proves it named first, at most four files, and no check that takes minutes in a browser.
    The template is .claude/skills/delegate/GOLDEN-BRIEF.md."""
    out = []
    if len(task) > BRIEF_MAX:
        out.append(f"it is {len(task)} characters (the limit is {BRIEF_MAX}): cut it into slices of one step each")
    if not re.search(r"\btest\w*\.(?:py|js)\b", task):
        out.append("it names no test file: say which new or existing test must fail before and pass after (Test: path/test_x.py)")
    slow = [w for w in SLOW if w in task]
    if slow:
        out.append("it asks for a slow check (" + ", ".join(slow) + "): the reviewer runs those; put their findings in the brief instead")
    files = {m.group(0) for m in _PATH.finditer(task)}
    files = {f for f in files if f not in PAPERWORK and not re.search(r"(^|/)test\w*\.(?:py|js)$", f)}
    if len(files) > BRIEF_FILES:
        out.append(f"it names {len(files)} files to change (the limit is {BRIEF_FILES}): one slice per step, in order")
    return out


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
    if cmd == "check":
        bad = brief_problems(os.environ.get("TASK", ""))
        for b in bad:
            print("- " + b)
        return 1 if bad else 0
    if cmd == "summary":
        print(summary(int(argv[1]) if len(argv) > 1 else 1))
        return 0
    print(__doc__)
    return 0 if cmd in ("-h", "--help") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
