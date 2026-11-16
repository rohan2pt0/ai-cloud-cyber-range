# Spec: essentials-first

Queue item `essentials-first` in `governance/queue.json` · due 2026-11-29 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: how many values must I enter for the app to be fully useful; are any asked twice; ask only the 80/20 values first, automate the rest from one source of truth, and build the systems so the numbers stay true with least friction

## Outcome for the person

A newcomer gets a useful Today after about ten answers, not sixty, and never types the same fact twice.

## Data

A field register: each fact, its one home, how often it changes (fixed, changes, derived), and which screens read it. The measured baseline is about 60 values and 24 ticks.

## Screen (one action)

First run asks the vital few with example values already filled; one button, `Looks right`. Every later fact is asked where it is first needed, once.

## Test that proves it

`test42.js` (ask-by-frequency) extended: no fact has two inputs; a count of required inputs for the persona stays under the budget; the count only goes down.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One profile as the single source, other screens read it.
- **Enterprise, when conditions call for it:** The same register as a data contract for imports, sync and connectors, so a fact arriving from a bank feed fills every screen.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
