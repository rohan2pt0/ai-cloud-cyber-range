# Spec: github-api-backoff

Queue item `github-api-backoff` in `governance/queue.json` · due 2026-11-30 · added 2026-11-08.

**The ask, as the queue holds it:** gh api searches hit GitHub's secondary rate limit during a busy round

## Outcome for the person

A busy round does not stall on GitHub's rate limit.

## Data

The rule: tools first, one search per question, one retry after a wait.

## Screen (one action)

Nothing new.

## Test that proves it

A note in the delegate skill and a small test of the retry helper.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A rule and a helper.
- **Enterprise, when conditions call for it:** A shared client with budgets.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
