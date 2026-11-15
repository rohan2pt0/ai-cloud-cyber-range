# Spec: venture-per-product

Queue item `venture-per-product` in `governance/queue.json` · due 2026-11-30 · added 2026-10-22.

**The ask, as the queue holds it:** Per-product revenue and time in ./securax venture, with a check that no product is more than half of revenue (doc 107, Haier row)

## Outcome for the person

The owner sees whether one product carries too much of the revenue, before it becomes a risk.

## Data

Revenue and time entries tagged by product in the venture log.

## Screen (one action)

`./securax venture`: one line per product and one warning if any is above half.

## Test that proves it

A unit test of the share guard with fixed entries, including zero revenue.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Tagged entries and a guard.
- **Enterprise, when conditions call for it:** Product lines with margins and a board view.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
