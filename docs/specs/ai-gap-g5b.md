# Spec: ai-gap-g5b

Queue item `ai-gap-g5b` in `governance/queue.json` · due 2026-11-19 · added 2026-10-23.

**The ask, as the queue holds it:** Close AI architecture gap G5b (doc 105): bias against a protected group and abusive output are stopped (a deterministic rail, or the local Llama Guard detector on by default), and the live promptfoo suite gains the same probes

## Outcome for the person

The AI does not produce abuse or bias against a protected group, and a probe proves it.

## Data

A deterministic rail or the local detector; probes in the purple loop and the live suite.

## Screen (one action)

Cockpit AI rails: one line per rail, on or off.

## Test that proves it

The two probes move from gap to blocked attack; a test fails if the rail is off by default.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A rail on by default.
- **Enterprise, when conditions call for it:** Policy per tenant and language with review of borderline cases.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
