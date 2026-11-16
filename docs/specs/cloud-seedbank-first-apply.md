# Spec: cloud-seedbank-first-apply

Queue item `cloud-seedbank-first-apply` in `governance/queue.json` · due 2026-11-30 · added 2026-11-07.

**The ask, as the queue holds it:** Apply the dormant cloud seed bank once on one real account, with its budget alarm, and prove it

## Outcome for the person

The dormant cloud copy is proven to come alive on a real account, with a budget alarm.

## Data

The seed bank's infrastructure code; one account; the alarm threshold.

## Screen (one action)

`./securax grow`: asks for approval once, then one line of what was created.

## Test that proves it

The alarm fires in a test, data is kept, and the teardown leaves nothing billed.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One cloud, once.
- **Enterprise, when conditions call for it:** Three clouds with scheduled drills.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
