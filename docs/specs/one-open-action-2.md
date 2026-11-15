# Spec: one-open-action-2

Queue item `one-open-action-2` in `governance/queue.json` · due 2026-11-24 · added 2026-11-10.

**The ask, as the queue holds it:** Finish the one-open-action principle on the screens slice 1 left: the generated cockpit page (one Do next, the rest under Later; doc 37 and test_cockpit_priority.py still say three), the Life OS Goals and OKR tabs (one key result in focus), and the kit Goals module

## Outcome for the person

On the cockpit, Goals and OKRs the person is never asked to choose what to do next: one item is in focus.

## Data

The cockpit's ranked actions; for OKRs, each key result's pace (from, to, current, dates).

## Screen (one action)

Cockpit: one `Do next` and a folded `Later (n)`. OKRs: the key result furthest behind its pace, with one button, `Update it`.

## Test that proves it

`test_cockpit_priority.py` changed from three to one primary; a jsdom test that exactly one primary control is visible on Goals and OKRs.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A ranking rule in the generator and the Life OS.
- **Enterprise, when conditions call for it:** The same rule as a shared kit primitive, with a team view that shows each member's one action.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
