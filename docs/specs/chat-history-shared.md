# Spec: chat-history-shared

Queue item `chat-history-shared` in `governance/queue.json` · due 2026-12-19 · added 2026-11-08.

**The ask, as the queue holds it:** Chat history on every node, so a conversation survives the machine it started on (the one single point left in the services)

## Outcome for the person

A conversation survives the machine it started on.

## Data

A shared database with a standby (doc 86).

## Screen (one action)

Chat simply shows the history on any node.

## Test that proves it

A failover drill: the primary is lost and history is still there; the resilience register is updated.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** History per node, stated honestly.
- **Enterprise, when conditions call for it:** Replicated storage with tested RPO.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
