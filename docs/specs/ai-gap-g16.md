# Spec: ai-gap-g16

Queue item `ai-gap-g16` in `governance/queue.json` · due 2026-12-10 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G16 (doc 105): Cost per request in rupees in the allowance and the cockpit

## Outcome for the person

The owner sees what each AI request cost in rupees, where the allowance is shown.

## Data

Cost per request from `app/spend.py`.

## Screen (one action)

Cockpit allowance row: tokens and rupees side by side.

## Test that proves it

A gateway test with a fixed price table.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A figure in the cockpit.
- **Enterprise, when conditions call for it:** Cost by team, project and model with export.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
