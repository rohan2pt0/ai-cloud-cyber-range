# Spec: private-review-briefing

Queue item `private-review-briefing` in `governance/queue.json` · due 2026-12-16 · added 2026-11-11.

**The ask, as the queue holds it:** A private security and continuity review at onboarding and a one-page monthly briefing, both generated on the family's own device: what was checked, what changed, the one decision needed

## Outcome for the person

The family reads one page a month: what was checked, what changed, and the one decision needed.

## Data

Existing sources only (cockpit vital signs, the Stack, renewals, readiness); generated and kept on the family's device.

## Screen (one action)

The briefing page: one decision at the top with one button, `Decide`; the rest is a calm summary. `Save as PDF` is folded.

## Test that proves it

A generator test with fixed inputs: exactly one decision, nothing sent off the device, the page passes the design standard and prints on one page.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A page generated on the device.
- **Enterprise, when conditions call for it:** A briefing per household member or entity, co-signed by an advisor by consent.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
