# Spec: readiness-import

Queue item `readiness-import` in `governance/queue.json` · due 2026-11-19 · added 2026-10-22.

**The ask, as the queue holds it:** Import a consultant's gap-assessment workbook into a readiness assessment

## Outcome for the person

A consultant's gap workbook becomes a live assessment in one step, with nothing retyped.

## Data

The workbook's rows mapped to requirements; secret-looking columns are dropped and reported.

## Screen (one action)

`Import a workbook`: one button; the result shows mapped, unmapped and dropped.

## Test that proves it

Tests with a synthetic workbook: mapping is right, unknown rows are listed, no sensitive column is kept.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One known layout.
- **Enterprise, when conditions call for it:** Layout detection and a partner template.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
