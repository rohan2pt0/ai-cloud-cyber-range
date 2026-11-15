# Spec: ai-gap-g7

Queue item `ai-gap-g7` in `governance/queue.json` · due 2026-11-12 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G7 (doc 105): Thumbs up/down in chat flows into the answer-quality set

## Outcome for the person

A thumbs-down in chat becomes a test, so the same poor answer is caught next time.

## Data

The rated exchange, kept locally with consent; sensitive text never leaves local models.

## Screen (one action)

In chat: thumbs up or down; nothing else.

## Test that proves it

A rated item appears in the quality set after review; a PII check runs before it is stored.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Feedback on one node.
- **Enterprise, when conditions call for it:** A review queue with roles before an item joins a shared set.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
