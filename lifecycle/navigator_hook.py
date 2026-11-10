"""Navigator mode: Claude routes and reviews, the open models build (owner, 2026-11-10).

A Claude Code hook (.claude/settings.json runs it at session start and on every message). It puts one short rule in
front of the model, with this month's Claude share, so delegation never depends on the model remembering a skill:

  build, fix, add or change work in this repository  ->  the `delegate` skill first (route.py, then the open models);
  Claude edits by hand only for strong-tier work, review fixes, merge conflicts and paperwork.

Why: on 2026-11-08/09 sessions delegated through lifecycle/delegate_here.sh and the open models wrote the work; on
2026-11-10 a fresh session skipped the skill and Claude wrote every commit. A rule that lives only in a skill's
description is optional; a hook is not.

    python3 lifecycle/navigator_hook.py            print the reminder (what the hook injects)
It never fails a prompt: any error prints the rule alone and exits 0.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_WORDS = ("build", "fix", "add", "change", "implement", "make", "create", "update", "refactor", "queue", "slice", "next")

RULE = ("NAVIGATOR MODE (owner rule, AGENTS.md section 1): for any build, fix, add or change work in this repository, "
        "invoke the `delegate` skill FIRST: route with lifecycle/route.py, then hand local/opencode-tier work to the open "
        "models (path B: bash lifecycle/delegate_here.sh in the background; the opencode.ai key is injected by the proxy). "
        "Claude writes code by hand only for strong-tier work, review fixes, merge conflicts and paperwork, and says in one "
        "line why when it does.")


def share_line() -> str:
    spec = importlib.util.spec_from_file_location("securax_share", ROOT / "lifecycle" / "share.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    month = dt.date.today().replace(day=1).isoformat()
    rep = mod.report(mod.commits(month))
    if not rep:
        return ""
    r = rep[0]
    return (f"This month: Claude {r['claude']} commits, open models {r['cheap']}, owner {r['you']} "
            f"(Claude {round(r['claude_share'] * 100)}%; goal 20% or less).")


def message(prompt: str = "") -> str:
    try:
        extra = share_line()
    except Exception:          # git missing, shallow clone, anything: the rule still goes out
        extra = ""
    text = RULE + (" " + extra if extra else "")
    if prompt and not any(w in prompt.lower() for w in BUILD_WORDS):
        text = "Navigator mode is on (delegate build work; see AGENTS.md section 1). " + extra
    return text.strip()


def main() -> int:
    raw = "" if sys.stdin.isatty() else sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {}
    event = data.get("hook_event_name", "")
    text = message(str(data.get("prompt", "")))
    if event in ("UserPromptSubmit", "SessionStart"):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
