---
name: delegate
description: Send build work to SecuRAX's open models from this chat, so paid Claude does only strong-tier work and review. Use it by default whenever the owner asks to build, fix, add or change something in this repository (including a queue item), and whenever they type /delegate. Not for questions, reviews or strong-tier work, which Claude does itself.
---

# Delegate: the open models build, Claude routes and reviews

The owner works from this chat, not a terminal. They should never have to type `./securax autobuild`. You do the routing and
the hand-off for them, in a few cheap tool calls, and spend Claude's allowance only where the router says Claude is needed.

## 1. Route it (one command)

1. Name the files the task will likely touch. Use `./securax brief "TASK"` or a quick `grep -l`; do not read whole files.
2. Run `python3 lifecycle/route.py "TASK" --files F1 F2 ... --json`.
3. Read `tier`:
   - **strong**: do it yourself, as AGENTS.md says. This covers security, crypto, auth, sync or merge logic, regulator maps, or many areas. Stop reading this skill.
   - **local** or **opencode**: go to step 2. If you doubt the router (for example the task names auth but no file matched), treat it as strong.

## 2. Hand it over: four paths, so no one of them is a single point of failure

Write the task as one self-contained brief from the template in `GOLDEN-BRIEF.md` (next to this file): six lines, at most
1,500 characters. The model cannot see this chat. Every brief has:
- the outcome, in the owner's words, and the queue id;
- **the test first:** the test file's name, why it fails now, and the two or three things it asserts;
- the files and the function to change (at most four files; `grep -n` for them yourself), and what not to touch;
- the helper or pattern to reuse;
- the paperwork (CHANGELOG line, `readme_sync`, `features_sync`, and so on);
- what is out of scope.

Check it before you send it: `TASK="$(cat brief.txt)" python3 lifecycle/autobuild_ci.py check` prints nothing when the brief is
fit. Path B runs the same check and refuses an unfit brief in a second (`CANNOT-START`), instead of failing after an hour.

**Never put a slow check in a brief.** The browser audits (`ui_audit.py`, `kit_audit.py`, `website/tests/ui_audit.py`) take 5 to 15
minutes each and the model has 40 for everything. Claude runs them on the green branch before merge, and CI runs the sandbox. When a fix
needs an audit's findings, run the audit first and put the exact list of breaks in the brief.

**One step per brief.** A model gets about 40 minutes per attempt, and the one slow gate at the end (`./securax verify`: the full
pytest and the whole Life OS suite) takes about 10 of them. A task with more than one outcome, more than four files or more than one
test goes out as slices of one step each, in order; a later slice builds on the branch of the one before it
(`DELEGATE_BASE=origin/<branch>`). For path B, start each slice with Bash `timeout: 7200000`, the maximum.

**Silence is not a hang.** OpenCode prints a command only when it ends, so a model is silent for minutes while the tests run.
The watchdog stops a model only when it is silent for 6 minutes AND running no command of its own (the log then says
`was running no command`). If the log says `used its 40 min`, the brief was too big: slice it, do not retry it.

Then take the first path that works. Each later path catches the failure of the one before it.
- **A. GitHub Actions** (survives this session ending). Use `mcp__github__actions_run_trigger` with `method: run_workflow`,
  `workflow_id: autobuild.yml`, `ref: main`, `inputs: {"task": BRIEF, "tries": "3"}`. After about 2 minutes, list the run once.
  If it failed at the install step with `Add the repository secret OPENCODE_GO_API_KEY`, go to B. Do not retry A.
- **B. This session.** Run `bash lifecycle/delegate_here.sh "BRIEF" 3` with Bash `run_in_background: true`. You are woken
  when it ends, and no Claude tokens are spent while it runs.
  - It prints `PUSHED <branch>` when green.
  - If the log shows `Invalid credential` (a 401 from the open-model host), no key is saved yet. Call `request_credential` for host `opencode.ai`
    (display name "OpenCode Go key", type bearer). The owner pastes the key once into the secure form; you never see it.
    Then run B again.
  - If the owner declines the form, go to C.
- **C. Claude does it**, the cheapest way that works. First hand the SAME golden brief to a Sonnet subagent (the Agent tool with
  `model: sonnet` and `isolation: worktree`): a brief an open model can finish alone, Sonnet can too, and it costs far less
  than this session writing the code. Review its diff as in step 3. Write the code by hand only when Sonnet also fails or the
  work is strong tier. Tell the owner in one line that this round cost Claude allowance, and why.
- **D. On the owner's laptop:** `./securax autobuild "BRIEF"` on local models, offline. Name it only when A to C are all unavailable.

Tell the owner, in two lines, what went where and what you will check.

## 3. Check once, then review (not a stream of polls)

- For A, set **one** check-in with `send_later`, about 45 minutes ahead (a run takes up to 60). For B you are woken anyway.
  Do not subscribe to pull-request events.
- **Green.** A pushes `autobuild/<slug>-<run id>` and B pushes `autobuild/<slug>-here-<time>`.
  - If no PR exists for the branch yet, open it yourself with `mcp__github__create_pull_request`, titled `autobuild: <task>`.
    A PR you open runs the full CI, so the GitHub "Actions may create PRs" setting is never needed.
  - Review only the diff (`pull_request_read get_diff`) at strong tier: rails weakened, tests skipped, secrets, public-repo privacy, wrong scope.
  - CI green and the review clean: squash-merge. Otherwise post one review comment saying what to fix, and either re-dispatch with a sharper brief (once) or take the task yourself (C).
- **Red.** Read the last 40 lines of the log or the brief. A model or gate failure gets one re-dispatch with a sharper brief, then C.

## 4. Several items at once

Dispatch them one per run. Actions queues runs (`concurrency: autobuild`); with B, run them one after another. One check-in
covers the batch. Close each queue item in the PR that finishes it.

## The key: once, in the chat, never on a settings page

The only thing the owner ever provides is the OpenCode Go key, and only once:
- In this chat, the secure form from `request_credential` saves it on the cloud environment. Path B then works in every later session.
- Optional, for path A (runs that survive a closed session): add the same key as the repository secret `OPENCODE_GO_API_KEY` at
  github.com/rohan2pt0/ai-cloud-cyber-range/settings/secrets/actions/new.

Until the key exists anywhere, every task falls to C, and the work still gets done.
