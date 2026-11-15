# Spec: ai-gap-g14

Queue item `ai-gap-g14` in `governance/queue.json` · due 2026-11-26 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G14 (doc 105): Audit chain survives restarts and is anchored daily to the off-site backup

## Outcome for the person

The record of what the AI did survives a restart and cannot be rewritten without notice.

## Data

The audit chain on disk and a daily anchor in the off-site backup.

## Screen (one action)

Cockpit: one line, `Audit chain: verified to <date>`.

## Test that proves it

Tests: restart keeps the chain, a changed entry fails verification, the anchor matches.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A file chain with a daily anchor.
- **Enterprise, when conditions call for it:** Anchors to an external timestamp service and tenant-separated chains.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
