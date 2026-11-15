# Spec: estate-gap-gates

Queue item `estate-gap-gates` in `governance/queue.json` · due 2026-11-15 · added 2026-10-28.

**The ask, as the queue holds it:** Close the remaining gap classes the production-readiness assessment found: our gates prove code consistency in a clean container but not real-machine runtime or first-run UX, which is how a broken Studio recipe and an unwritable data dir reached a real machine green. Gates 1+2 (doc-recipe validator, Studio real-start …

## Outcome for the person

What works in CI also works on a real machine and on first run, so the owner stops finding breakage by hand.

## Data

Gap classes from the assessment, each mapped to a gate (selftest probes, a first-run journey, others).

## Screen (one action)

`./securax selftest`: one green or red line, and for red the one command to see why.

## Test that proves it

Each gate is proven by re-introducing the original fault and seeing it fail; new owner findings map to a class and a gate.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Probes and one journey in the sandbox.
- **Enterprise, when conditions call for it:** A matrix of real machines (Windows, WSL, a small PC) run on a schedule.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
