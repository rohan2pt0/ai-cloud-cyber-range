# Spec: ai-gap-g13

Queue item `ai-gap-g13` in `governance/queue.json` · due 2026-12-10 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G13 (doc 105): Token-exact context management with the model's tokenizer

## Outcome for the person

Long conversations are cut exactly where the model's limit is, so answers neither fail nor lose what matters.

## Data

Token counts from the model's own tokenizer.

## Screen (one action)

Nothing new; a long chat keeps working.

## Test that proves it

Tests with known strings per tokenizer: counts match, a context at the limit is trimmed without an error.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Exact counts for the local models.
- **Enterprise, when conditions call for it:** Per-model budgets with summarisation policy.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
