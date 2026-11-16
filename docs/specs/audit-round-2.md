# Spec: audit-round-2

Queue item `audit-round-2` in `governance/queue.json` · due 2026-11-20 · added 2026-11-11.

**The ask, as the queue holds it:** Audit round 2, correctness: income, expenses, net worth, cover, renewals and tax checked against the real papers; every calendar date right (doc 134)

## Outcome for the person

Every number on Today matches the owner's real papers, so decisions made from it are sound.

## Data

The owner's papers (kept in `vault/`, never committed) against income, expenses, net worth, cover, renewals, tax and each calendar date.

## Screen (one action)

A private check list: one line per number, `Matches` or `Fix`; one button, `Next number`.

## Test that proves it

A session log of each mismatch found and the test added for its cause; the round closes when a second pass finds none.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One sitting with the papers, by hand.
- **Enterprise, when conditions call for it:** A reconciliation routine: statements shared in are compared with stored values each month, differences shown as one question.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
