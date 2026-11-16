# Spec: spend-guard

Queue item `spend-guard` in `governance/queue.json` · due 2026-11-12 · added 2026-10-22.

**The ask, as the queue holds it:** Rupee caps, not only token caps: cost per request in rupees (doc 105 G16), a monthly rupee limit per provider in the gateway, and a check that warns when a paid key has no provider-side limit

## Outcome for the person

A runaway AI bill cannot happen: spending stops at a rupee cap the owner set.

## Data

Cost per call in rupees, a monthly total per provider, the caps; bounded to one counter per provider per month.

## Screen (one action)

Cockpit: one line, spent of cap this month; at 80% one alert with one action, `Raise or keep the cap`.

## Test that proves it

Gateway tests: at the cap the local model answers, an unknown price counts high, a paid key with no provider-side limit warns.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Per-provider caps on one gateway.
- **Enterprise, when conditions call for it:** Budgets per team and project on a shared store (`ai-gap-g8`), with chargeback export.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
