# Spec: door-access-bypass

Queue item `door-access-bypass` in `governance/queue.json` · due 2026-12-05 · added 2026-11-08.

**The ask, as the queue holds it:** Let the one path /_door.json through Cloudflare Access, so a machine behind the sign-in page shows as up on the door

## Outcome for the person

A machine behind the sign-in page still shows as up on the door.

## Data

One bypass rule for the single path that says only ok.

## Screen (one action)

The door shows the machine's true state.

## Test that proves it

Proven against the stand-in the tests already use; only that path is open.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One rule.
- **Enterprise, when conditions call for it:** Signed health answers per node.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
