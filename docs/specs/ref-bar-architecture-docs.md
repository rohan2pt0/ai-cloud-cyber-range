# Spec: ref-bar-architecture-docs

Queue item `ref-bar-architecture-docs` in `governance/queue.json` · due 2026-12-19 · added 2026-11-08.

**The ask, as the queue holds it:** C4 context and container diagrams plus short decision records, so a fresh engineer sees the system and why it is so

## Outcome for the person

A fresh engineer sees the system and why it is so, in ten minutes.

## Data

C4 context and container diagrams as text; five decision records.

## Screen (one action)

One docs page, `Architecture at a glance`.

## Test that proves it

`mkdocs build --strict`; each decision record links to the code it describes.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Two diagrams and five records.
- **Enterprise, when conditions call for it:** Records for every strong-tier change.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
