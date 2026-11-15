# Spec: review-risk-tiers

Queue item `review-risk-tiers` in `governance/queue.json` · due 2026-11-21 · added 2026-11-07.

**The ask, as the queue holds it:** Risk-tiered human approval for merges: none for low-risk changes, one for medium, two for high (the way the Claude Code team does it)

## Outcome for the person

Low-risk changes merge without waiting; risky ones always get the right number of human looks.

## Data

A map from route tier to approvals needed (0, 1, 2) in governance data.

## Screen (one action)

`./securax ship check`: one line, approvals needed and given.

## Test that proves it

Tests: a strong-tier change cannot merge with fewer than two approvals; a local one needs none.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A rule in the ship command.
- **Enterprise, when conditions call for it:** Branch protection and named reviewers by area.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
