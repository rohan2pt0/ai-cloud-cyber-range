# 103 · Nothing asked is lost

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: ./securax backlog lists every unfinished item from six places (deferred asks, dated promises, open pull requests, branches with no PR, unpushed work, agents' scratch copies); a daily workflow keeps it in one GitHub issue with no session needed; the Command Center shows the count; every agent must write down what it did not finish. The Dependabot backlog is queued for 2026-10-26. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** sessions get cut off (a usage limit, a restart), and pull requests get superseded. Make sure no request and no
started piece of work quietly goes to waste: go back over what happened, find what was left, and fix it for good.

## 1. What going back over it found

| Where work can be left | What was there on 2026-10-22 |
|---|---|
| Feature pull requests (#38 to #125) | **All on main.** Some were merged as merge commits rather than squashes, so they do not carry "(#N)" in their title, but every one landed |
| The one closed, unmerged pull request (#90, image refresh) | Its changes reached main through a later pull request |
| Dependabot pull requests | **20 open, the oldest 11 days old**, never handled: GitHub Actions, FastAPI, Python 3.14, Postgres 18, Terraform providers. One (#103, nginx) is superseded by the nginx 1.30 fix |
| Dated promises in the docs | **None late** (the roadmap sweep, PR #125, closed the late ones); 18 fall due in the next five months |
| Agents stopped by a usage limit | Four, this morning. Their partial work survived only because it was copied back by hand; nothing guaranteed it |
| Asks made in this session | Checked one by one against the repository (section 4) |

## 2. The fix: one queue, kept outside any session

`./securax backlog` lists everything started or promised and not finished, most urgent first, from six places:

| Source | What counts |
|---|---|
| `governance/queue.json` | an ask that was deferred, in our own words, with a due date and the next step |
| dated rows in these docs | a "Next, with dates" row due within 14 days or past its date (a struck or "done" row is finished) |
| pull requests | any still open; a Dependabot bump nobody handled counts too |
| branches | commits main does not have, with no pull request |
| this machine | commits not pushed, edits not committed |
| agents' scratch copies | changes in `.claude/worktrees/` never brought back |

- **The `backlog` workflow** rebuilds one GitHub issue, "Backlog: what is not finished", every morning at 09:13 IST, and
  whenever the queue changes on main. It runs on GitHub's machines, so it needs no Claude session and no laptop; you can
  read it in the GitHub app.
- **The Command Center** shows the count in its Mission line, from what the laptop knows (it asks no network).
- **Every agent's rule** (`AGENTS.md` 5b): push each round before a long wait, write down every unfinished ask in the queue
  in the same commit, and bring back agents' work before stopping.

## 3. What the queue holds now

See `governance/queue.json` and the Backlog issue. The largest item is the Dependabot round: merge the safe minor bumps
together, decide each major on its own (a Postgres major moves your data; FastAPI moves the test client), and close what is
superseded, by 2026-10-26.

## 4. The asks, checked one by one

Every message typed into this session since 2026-10-10 was read back: 270 messages, which split into 146 distinct asks.
Each was checked against main (a commit, a changelog line, a doc). The full table stays private, in the session's scratch
space, because it quotes the owner's own words.

| Outcome | Asks |
|---|---|
| Done on main | 113 |
| Partly done | 22 (five of them only wait for PR #126 to merge) |
| Dated for later in a doc | 6 |
| Not done | 1 (this queue, built the same day) |
| Declined, with the reason recorded | 1 |
| Help on the owner's own machine, given in chat | 3 |

**What the partly-done ones have in common:** the code is built and tested, but the last step needs something the
sandbox cannot give: a real phone, a real always-on server, an account (the Play Store, Cloudflare, GitLab), or a choice
the owner keeps (spending money). These are now in the queue as **waiting for the owner**, with the exact step, so they are
seen every day instead of forgotten. The rest of the partly-done asks have a due date and a next step in the queue.

**The ask raised most often is the one least done:** building SecuRAX without paid Claude. The tools exist (route, brief,
autobuild, ship, ai share), but Claude still made most of the commits. It is in the queue for 2026-11-05.
