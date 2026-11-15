# Spec: rtl-ready

Queue item `rtl-ready` in `governance/queue.json` · due 2026-12-01 · added 2026-11-10.

**The ask, as the queue holds it:** Right-to-left layouts (Arabic first, Hebrew later) work in every app before the global launch

## Outcome for the person

An Arabic reader gets a layout that reads naturally right to left, with nothing clipped or mirrored wrongly.

## Data

`_meta.dir` in the catalog; CSS logical properties across `kit.css` and the Life OS styles.

## Screen (one action)

No new screen; the language switch sets the direction.

## Test that proves it

An `ar` run in `kit_audit` and the device audit: no overflow, no clipped text, mirrored navigation, numbers still left to right.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A direction attribute and a CSS sweep.
- **Enterprise, when conditions call for it:** Bidirectional content rules and review by native readers per language.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
