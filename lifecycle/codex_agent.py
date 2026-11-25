"""Builder rung: OpenAI's Codex CLI on the owner's laptop, through the owner's existing ChatGPT plan.

It costs nothing extra and shares no account with the other builder rungs. Codex is on every ChatGPT plan, with
lower usage limits on the smaller ones.

  ./securax autobuild "the task" --codex      # sets AUTOBUILD_AGENT to this file
  python3 lifecycle/codex_agent.py            # as AUTOBUILD_AGENT: reads AUTOBUILD_TASK, AUTOBUILD_BRIEF, AUTOBUILD_FEEDBACK

One-time set-up, on the laptop only: install Codex (npm install -g @openai/codex, checked with 0.171.0), then sign in
once with your ChatGPT account: codex login. This file only checks that the sign-in file exists. It never opens it.
Exit codes: 0 Codex ran, 2 not available (the reason is printed), 3 the plan's usage limit is reached (the next rung takes over).
Standard library only.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOT_READY = "install Codex and sign in once with your ChatGPT account: codex login"
LIMIT_REASON = "Codex usage limit reached on your ChatGPT plan; the next rung takes over"
LIMIT_WORDS = ("usage limit", "rate limit", "hit your limit", "quota")
EXIT_NOT_AVAILABLE, EXIT_LIMIT = 2, 3
GATES = ("\n\nWork in this checkout. Follow AGENTS.md and BUILD-CONTRACT.md. Before you stop, run the gates and fix what they report:\n"
         "   ruff check .\n"
         "   python3 -m pytest -q\n"
         "Do not commit, push, skip a test or weaken a rail: the gates run after you. Do not install anything.")


def _auth_file(home) -> pathlib.Path:
    base = os.environ.get("CODEX_HOME")
    return (pathlib.Path(base) if base else pathlib.Path(home) / ".codex") / "auth.json"


def available(which=shutil.which, home=None) -> tuple[bool, str]:
    """(True, "") when a codex binary is on PATH and the sign-in file exists (existence only, never opened)."""
    home = pathlib.Path.home() if home is None else home
    if not which("codex") or not _auth_file(home).exists():
        return False, NOT_READY
    return True, ""


def prompt(task: str, feedback_file=None) -> str:
    text = task
    fb = pathlib.Path(feedback_file) if feedback_file else None
    if fb and fb.is_file() and fb.stat().st_size:
        text += "\n\nThe previous attempt FAILED the gates. Fix exactly this, and change nothing else:\n" + fb.read_text("utf-8")[-4000:]
    return text + GATES


def command(task: str, feedback_file=None) -> list[str]:
    # workspace-write: it may edit this checkout only (the default is read-only). approval_policy never: it never stops to ask.
    return ["codex", "exec", "--sandbox", "workspace-write", "-c", 'approval_policy="never"', prompt(task, feedback_file)]


def _run(argv):
    p = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main(env=None, run=None, which=shutil.which, home=None) -> int:
    env = os.environ if env is None else env
    ok, why = available(which=which, home=home)
    if not ok:
        print("codex: " + why, file=sys.stderr)
        return EXIT_NOT_AVAILABLE
    brief = pathlib.Path(env.get("AUTOBUILD_BRIEF", ""))
    task = brief.read_text("utf-8") if brief.is_file() else env.get("AUTOBUILD_TASK", "")
    rc, out = (run or _run)(command(task, env.get("AUTOBUILD_FEEDBACK")))
    print(out[-4000:])
    if rc != 0 and any(w in out.lower() for w in LIMIT_WORDS):
        print("codex: " + LIMIT_REASON, file=sys.stderr)
        return EXIT_LIMIT
    return rc


if __name__ == "__main__":
    sys.exit(main())
