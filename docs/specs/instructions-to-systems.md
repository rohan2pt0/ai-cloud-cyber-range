# Spec: instructions-to-systems

Queue item `instructions-to-systems` in `governance/queue.json` · due 2026-11-28 · added 2026-11-12.

**The ask, as the queue holds it:** Owner, 2026-11-12: lists of instructions (the Growth daily routine was the example) only tell a person what to do; turn every such list in the Life OS and the kit apps into a system that helps them actually do it

## Outcome for the person

A list that used to be read once becomes something the person actually does each day.

## Data

Per list: its items as loop steps (cue, two-minute floor), a streak, and the last done date. Bounded to one record per item.

## Screen (one action)

One open item with one button, `Done`; the streak and a small win at the end. A missed day shows once, kindly.

## Test that proves it

`test62.js` for the Growth routine, repeated for each converted list: one item in view, the floor counts, never-miss-twice wording appears once.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Each list converted by hand into the loop pattern.
- **Enterprise, when conditions call for it:** A loop builder in the kit: any edition turns a checklist into a system from data.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
