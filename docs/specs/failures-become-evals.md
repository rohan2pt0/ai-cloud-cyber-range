# Spec: failures-become-evals

Queue item `failures-become-evals` in `governance/queue.json` · due 2026-11-28 · added 2026-11-07.

**The ask, as the queue holds it:** Every real failure becomes a daily test of the AI reviewer: the lessons and the adversary findings, replayed against it

## Outcome for the person

The AI reviewer keeps catching every mistake that has already happened once.

## Data

A dataset built from `LESSONS.md` and adversary findings.

## Screen (one action)

`./securax progress`: one line, reviewer catches n of n known failures.

## Test that proves it

`review --eval` scores it; the daily routine fails on a drop.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A local dataset.
- **Enterprise, when conditions call for it:** Shared eval sets across teams with privacy review.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
