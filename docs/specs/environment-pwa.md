# Spec: environment-pwa

Queue item `environment-pwa` in `governance/queue.json` · due 2026-11-30 · added 2026-10-23.

**The ask, as the queue holds it:** A one-tap Life OS screen for ./securax environment (doc 112): the person picks the struggles that are theirs and each set-and-forget change becomes a card with its one-time steps and a 'done' tick — so a non-technical person gets the whole benefit without a terminal. Then add more reversals (a work-hours focus mode, …

## Outcome for the person

A non-technical person makes the set-and-forget changes that remove a daily struggle, without a terminal.

## Data

The catalogue from `governance/environment.py` (struggles, reversals, one-time steps); ticks on the device.

## Screen (one action)

The person taps their struggle; one change is shown with one button, `Done`.

## Test that proves it

A jsdom test: one change in view, steps as printed, a tick moves to the next, a weak Wheel spoke leads to its fixes.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A screen over the existing catalogue.
- **Enterprise, when conditions call for it:** Changes applied by the estate itself where safe, and team environments by policy.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
