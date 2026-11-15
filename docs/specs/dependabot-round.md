# Spec: dependabot-round

Queue item `dependabot-round` in `governance/queue.json` · due 2026-10-26 · added 2026-10-22.

**The ask, as the queue holds it:** Handle the open Dependabot pull requests (some waiting since 2026-10-11) instead of letting them age

## Outcome for the person

The estate does not run old, vulnerable software because updates sat unread.

## Data

Open update pull requests and their age.

## Screen (one action)

`./securax progress`: one line, oldest waiting update in days.

## Test that proves it

Each update merges only when CI is green; a routine reports any older than 14 days.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A weekly round by hand.
- **Enterprise, when conditions call for it:** Auto-merge for low-risk updates by risk tier (`review-risk-tiers`).

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
