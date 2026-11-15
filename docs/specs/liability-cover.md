# Spec: liability-cover

Queue item `liability-cover` in `governance/queue.json` · due 2026-11-30 · added 2026-10-22.

**The ask, as the queue holds it:** Professional indemnity and cyber cover, and contract terms capping liability at twelve months' fees, before the first paid contract

## Outcome for the person

A mistake in a paid engagement cannot ruin the owner: cover is in place and liability is capped in the contract.

## Data

Policy dates and the contract clause (private); the guard `insurance` holds yes or no and the renewal date.

## Screen (one action)

One line in the venture view: covered until a date, with `Add to calendar` for renewal.

## Test that proves it

The guard fails a paid contract while cover is missing or expired.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One policy and one clause.
- **Enterprise, when conditions call for it:** Cover scaled with revenue and per-market terms.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
