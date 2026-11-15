# Spec: delivery-four-keys

Queue item `delivery-four-keys` in `governance/queue.json` · due 2026-11-26 · added 2026-11-08.

**The ask, as the queue holds it:** Measure delivery by outcomes: how often we ship, how long a change takes, how often a change fails, how fast we restore

## Outcome for the person

The owner sees whether delivery is getting faster and safer, from facts.

## Data

Git history and a cached snapshot of CI runs.

## Screen (one action)

`./securax progress`: four numbers with their trend.

## Test that proves it

Unit tests on a temporary repository with known history; offline-first.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Two keys from git.
- **Enterprise, when conditions call for it:** All four with targets per team.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
