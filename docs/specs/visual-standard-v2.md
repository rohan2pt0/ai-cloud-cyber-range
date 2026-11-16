# Spec: visual-standard-v2

Queue item `visual-standard-v2` in `governance/queue.json` · due 2026-11-30 · added 2026-11-12.

**The ask, as the queue holds it:** Owner, 2026-11-12: the UI, UX and graphics do not look appealing or intuitive; the owner is visually driven; make the look and feel the best in every tab, from every angle of the person's experience

## Outcome for the person

Every tab is pleasant and obvious at a glance, with a rich but restrained palette where each colour has one job.

## Data

The palette decision (navy to midnight teal foundation, teal for progress, gold for achievement) as tokens in `governance/design.json`.

## Screen (one action)

No new screen; each tab gets one hero and one primary.

## Test that proves it

`test72.js`, the contrast and UI rules in `ui_audit.py` (both themes), and a screenshot review per tab.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Tokens applied tab by tab.
- **Enterprise, when conditions call for it:** Theme packs per edition from the same tokens, with automated visual regression.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
