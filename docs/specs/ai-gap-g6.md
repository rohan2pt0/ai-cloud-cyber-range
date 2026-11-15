# Spec: ai-gap-g6

Queue item `ai-gap-g6` in `governance/queue.json` · due 2026-11-12 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G6 (doc 105): Answer-quality set for the chat models, run on every model change, score in progress

## Outcome for the person

A model change cannot quietly make answers worse.

## Data

A fixed answer-quality set and its score per model.

## Screen (one action)

`./securax progress`: one line, answer quality and its change.

## Test that proves it

The set runs on every model change; a drop below the threshold fails.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A small local set.
- **Enterprise, when conditions call for it:** Per-team sets grown from real feedback (`ai-gap-g7`).

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
