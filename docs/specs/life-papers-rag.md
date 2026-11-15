# Spec: life-papers-rag

Queue item `life-papers-rag` in `governance/queue.json` · due 2026-11-08 · added 2026-10-22.

**The ask, as the queue holds it:** Answer questions about my own policies and statements from my papers, privately (personal RAG)

## Outcome for the person

The person asks a question about their own policy or statement and gets the answer with its page, privately.

## Data

Document text in the private workspace, answered by a local model only.

## Screen (one action)

One box, `Ask your papers`.

## Test that proves it

A test that the route uses a local model only and the answer cites its document; no text leaves the machine.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One workspace on one machine.
- **Enterprise, when conditions call for it:** Per-member access and retrieval checks (`ai-gap-g15`).

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
