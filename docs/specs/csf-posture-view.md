# Spec: csf-posture-view

Queue item `csf-posture-view` in `governance/queue.json` · due 2026-12-09 · added 2026-11-11.

**The ask, as the queue holds it:** Owner, 2026-11-11: a cue from an analyst firm's one-page cyber maturity posture (cited by reference, not copied): per NIST CSF 2.0 function, current maturity next to its importance (target), and under each function a few operational measures shown as actual against target

## Outcome for the person

A security lead shows the board one page: where each function stands against where it needs to be, with a few measures behind it.

## Data

Per NIST CSF 2.0 function: current maturity, target, and a few operational measures (actual and target) from existing comply and readiness data.

## Screen (one action)

One page in the cockpit; the function with the largest gap is highlighted, one button, `See what closes it`.

## Test that proves it

A generator test with fixed inputs: six functions, gap sorted, no figure without a source in the data; the page passes the design standard.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A static page from the estate's own data.
- **Enterprise, when conditions call for it:** Trend over quarters, peer-free benchmarks from the organisation's own targets, export for the board pack.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
