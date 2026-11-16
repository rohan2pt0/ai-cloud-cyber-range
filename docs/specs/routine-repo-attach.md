# Spec: routine-repo-attach

Queue item `routine-repo-attach` in `governance/queue.json` · due 2026-11-10 · added 2026-11-08.

**The ask, as the queue holds it:** The daily build routine runs with no repository or GitHub tools attached, so a fresh session may start empty

## Outcome for the person

The daily build routine always starts with the repository in hand.

## Data

The routine's prompt and its first step.

## Screen (one action)

The routine's report: one line, attached or not.

## Test that proves it

One run confirms; then the fallback step is removed.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A self-attach step.
- **Enterprise, when conditions call for it:** Routines defined in the repository and checked.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
