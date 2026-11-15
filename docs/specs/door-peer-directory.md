# Spec: door-peer-directory

Queue item `door-peer-directory` in `governance/queue.json` · due 2026-12-12 · added 2026-11-08.

**The ask, as the queue holds it:** One machine address is enough: nodes tell the door about each other, so a new machine appears without typing it

## Outcome for the person

A new machine appears on the door without anyone typing its address.

## Data

An authenticated peer list from an approved node; never public.

## Screen (one action)

The door: `A new machine was found`, one button, `Add it`.

## Test that proves it

Tests: an unauthenticated request gets nothing, a peer is added only after approval; threat model first.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A list from one node.
- **Enterprise, when conditions call for it:** A signed directory with revocation.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
