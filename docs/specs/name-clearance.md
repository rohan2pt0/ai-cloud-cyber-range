# Spec: name-clearance

Queue item `name-clearance` in `governance/queue.json` · due 2026-11-30 · added 2026-10-22.

**The ask, as the queue holds it:** An IP attorney's clearance search for the product and brand names (India first, spellings and domains included), then a filing in the company's name, before the first invoice or any public rename

## Outcome for the person

The names can be used and defended, so nothing has to be renamed after customers arrive.

## Data

The attorney's search results (private); the guard `brand-cleared` holds only yes or no and a date.

## Screen (one action)

`./securax config check`: one line, cleared or not.

## Test that proves it

The guard fails a public rename or first invoice while not cleared.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One search in India.
- **Enterprise, when conditions call for it:** Clearance per market before each launch.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
