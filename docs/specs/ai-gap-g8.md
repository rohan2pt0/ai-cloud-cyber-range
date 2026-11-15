# Spec: ai-gap-g8

Queue item `ai-gap-g8` in `governance/queue.json` · due 2026-12-31 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G8 (doc 105): Shared store for rate limits, allowances and the audit chain when a second gateway replica runs

## Outcome for the person

A second gateway replica does not double the allowance or fork the audit chain.

## Data

One shared store for rate limits, allowances and the chain.

## Screen (one action)

The cockpit shows one allowance, whichever replica answered.

## Test that proves it

A load test with two replicas: limits hold, the chain verifies (as `test_load_audit_chain.py` does for one).

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One gateway with a lock.
- **Enterprise, when conditions call for it:** A replicated store with a standby and tested failover.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
