# Spec: licence-review

Queue item `licence-review` in `governance/queue.json` · due 2026-11-30 · added 2026-10-22.

**The ask, as the queue holds it:** Owner reads governance/licences.json against what is sold; settle n8n hosting (its licence) and Open WebUI branding before a hosted offer

## Outcome for the person

Nothing sold breaks a third party's licence.

## Data

`governance/licences.json` against what each edition ships and hosts.

## Screen (one action)

`./securax licences`: the one component needing a decision.

## Test that proves it

The guard `licence-terms` and the licence tests stay green; a hosted offer is blocked until the two open questions are settled.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A manual reading by the owner.
- **Enterprise, when conditions call for it:** Automated licence policy per edition in CI with an SBOM.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
