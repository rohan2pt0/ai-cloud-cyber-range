# Spec: threat-models-by-risk

Queue item `threat-models-by-risk` in `governance/queue.json` · due 2026-12-05 · added 2026-11-08.

**The ask, as the queue holds it:** Threat-model the rest by risk, highest first: the AI gateway, sync, the hunt fleet, crisis, the identity registry (doc 133)

## Outcome for the person

The riskiest components have been thought through as an attacker would, with every threat answered.

## Data

One model per component in `governance/threat-models.json` (parts, flows, boundaries, six STRIDE ways).

## Screen (one action)

`./securax threats`: the one unanswered threat.

## Test that proves it

Fitness `threat-modelled`; the baseline in `lifecycle/fitness.json` goes up; evidence paths exist.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Models as data, reviewed by the owner.
- **Enterprise, when conditions call for it:** Models tied to tests and re-reviewed on change.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
