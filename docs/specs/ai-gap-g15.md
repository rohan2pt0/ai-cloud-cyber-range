# Spec: ai-gap-g15

Queue item `ai-gap-g15` in `governance/queue.json` · due 2026-11-19 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G15 (doc 105): Retrieval checks: per-document owner and class at retrieval; scan documents before indexing

## Outcome for the person

A person's question never retrieves a document they should not see, and a poisoned document is caught before indexing.

## Data

Owner and class on each document; a scan result before indexing.

## Screen (one action)

Nothing new for the person; a refused document shows why.

## Test that proves it

Tests: retrieval filters by owner and class, a document with injected instructions is flagged.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Labels on one workspace.
- **Enterprise, when conditions call for it:** Attribute-based access tied to the identity service.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
