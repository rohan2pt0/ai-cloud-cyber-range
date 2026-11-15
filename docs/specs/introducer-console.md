# Spec: introducer-console

Queue item `introducer-console` in `governance/queue.json` · due 2027-01-31 · added 2026-11-11.

**The ask, as the queue holds it:** An introducer console for family offices and advisors: they see only what a family explicitly consents to share, revocable in one tap

## Outcome for the person

An advisor sees exactly what a family chose to share, and the family can take it back in one tap.

## Data

Consent records (what, to whom, until when) on the shared consent and audit rails; threat model first.

## Screen (one action)

Family side: one switch per shared item. Advisor side: the one family needing attention, one button, `Open`.

## Test that proves it

Tests: nothing is visible without consent, revocation takes effect at once, every view is in the audit log.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One advisor, read-only, by explicit share.
- **Enterprise, when conditions call for it:** A multi-family console with roles, segregation between families, and export for regulators.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
