# Spec: ui-rules-lint

Queue item `ui-rules-lint` in `governance/queue.json` · due 2026-11-28 · added 2026-11-09.

**The ask, as the queue holds it:** Hold the owner's UI rules in the real-browser audits: tap targets, 16 px inputs, inputmode, line length and height, no pure black, underlined links, no hover-only controls, right-aligned numeric cells; fail on a new violation

## Outcome for the person

A new screen cannot break the owner's UI rules without the build saying so.

## Data

The rules as checks in the three real-browser audits.

## Screen (one action)

The audit report: one line per break.

## Test that proves it

A planted violation of each rule fails its audit.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Eight rules in the audits.
- **Enterprise, when conditions call for it:** The rules as a shared linter for partner editions.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
