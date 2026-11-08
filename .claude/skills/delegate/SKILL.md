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

## 2. Hand it over (one tool call)

Write the task as one self-contained brief of 3 to 8 lines. The model cannot see this chat. Include:
- the outcome, in the owner's words;
- the files to touch;
- the test or check that proves it;
- the paperwork it needs (CHANGELOG line, queue item to close, `features_sync`, and so on);
- the queue id, if there is one.

Then start the workflow with the GitHub tool:
`mcp__github__actions_run_trigger` with `method: run_workflow`, `workflow_id: autobuild.yml`, `ref: main`, and
`inputs: {"task": BRIEF, "tries": "3"}`.

Tell the owner, in two lines, what went to the open models and what you will check.

## 3. Check once, then review (not a stream of polls)

- Set **one** check-in with `send_later`, about 45 minutes ahead. A run takes up to 60 minutes. Do not subscribe to pull-request events.
- At the check-in, list the latest `autobuild.yml` run.
  - **Green**: it has opened a PR titled `autobuild: ...`. Do a strong-tier review of the diff only (`pull_request_read get_diff`): rails weakened, tests skipped, secrets, public-repo privacy, wrong scope. If the PR's CI is green and the review is clean, merge it (squash). Otherwise post one review comment saying what to fix, and either re-dispatch with a sharper brief (once) or take the task yourself.
  - **Red**: read the last 40 lines of the failed job's log and decide:
    - a model or gate failure: re-dispatch once with a sharper brief, then take it yourself;
    - the secret is missing (`Add the repository secret OPENCODE_GO_API_KEY`): stop delegating and tell the owner the one-time setup below, word for word.

## 4. Several items at once

Dispatch them one per run. The workflow queues runs (`concurrency: autobuild`), so a second dispatch waits instead of
colliding. One check-in covers the batch. Close each queue item in the PR that finishes it.

## One-time setup the owner does (from a phone browser, about 5 minutes)

1. GitHub, repository **Settings > Secrets and variables > Actions > New repository secret**. Name it `OPENCODE_GO_API_KEY`; the value is the OpenCode Go key (doc 83, section 4).
2. **Settings > Actions > General > Workflow permissions**: tick "Allow GitHub Actions to create and approve pull requests".

Until both are done, every hand-off fails in seconds. Say so plainly, and do the work yourself, the expensive way.
