# Spec: own-origin-hosting

Queue item `own-origin-hosting` in `governance/queue.json` · due 2026-11-20 · added 2026-11-08.

**The ask, as the queue holds it:** Host the apps on an origin of their own, on a host that applies the header rules, so a person's data does not share a browser origin with other sites

## Outcome for the person

A person's data in the hosted apps does not share a browser origin with unrelated sites, and the security headers apply.

## Data

A static project on the owner's subdomain with the header rules; a data carry-over path.

## Screen (one action)

The old address shows one card, `Move to the new address`, with one button.

## Test that proves it

A real-browser check of headers and the service worker on the new origin; data arrives through backup or sync.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One new origin.
- **Enterprise, when conditions call for it:** An origin per tenant with its own policy.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
