# Spec: estate-map-next

Queue item `estate-map-next` in `governance/queue.json` · due 2026-11-30 · added 2026-10-23.

**The ask, as the queue holds it:** Grow the estate map (doc 113): a link from the Command Center so it is one tap from the cockpit; a resilience overlay (which single machine carries which component, from governance/resilience.json) and a compliance overlay (which control each component evidences, from the maps); and the same generator pointed at a …

## Outcome for the person

The owner sees, on one map, which machine carries what and which control each part evidences.

## Data

`features.json`, `suite.json`, `governance/resilience.json` and the comply maps.

## Screen (one action)

Command Center: one link, `Estate map`; on the map one switch between Resilience and Compliance.

## Test that proves it

A generator test: overlays read the real files, the page stays one offline file, and no raw address appears.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One generated HTML file.
- **Enterprise, when conditions call for it:** The generator pointed at a tenant's estate, with change history.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
