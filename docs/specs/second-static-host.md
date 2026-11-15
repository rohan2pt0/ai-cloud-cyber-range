# Spec: second-static-host

Queue item `second-static-host` in `governance/queue.json` · due 2026-11-30 · added 2026-11-08.

**The ask, as the queue holds it:** A second static host for the product site, the apps and the door, so GitHub Pages is not the one place they live

## Outcome for the person

The site, the apps and the door stay reachable if the one static host is down.

## Data

The same built site deployed to a second host when its token is set.

## Screen (one action)

The door lists the mirror; the person does nothing.

## Test that proves it

A workflow test: with no token nothing happens, with one the same files are published.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A second deploy.
- **Enterprise, when conditions call for it:** Health-checked failover on the person's own domain.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
