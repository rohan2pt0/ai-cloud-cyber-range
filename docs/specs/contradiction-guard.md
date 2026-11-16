# Spec: contradiction-guard

Queue item `contradiction-guard` in `governance/queue.json` · due 2026-11-27 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: reject contradictory answers automatically everywhere (not only gentle hints)

## Outcome for the person

The person can trust every number, because the app never keeps two answers that cannot both be true.

## Data

One rule table (pairs of facts and the condition that makes them conflict), checked on every save. No new stored data beyond the answer the person picks.

## Screen (one action)

When a save conflicts, one small sheet: `Which is true?` with two buttons, each naming one answer in plain words. The other fact is corrected by the app.

## Test that proves it

A table-driven jsdom test: every rule is triggered once, the sheet shows two choices, either choice leaves a consistent profile, and no rule can be bypassed through another screen or an import.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A static rule table in the Life OS, run on the device.
- **Enterprise, when conditions call for it:** The same engine as a platform policy service: an organisation adds its own rules, and conflicts in shared records are logged to audit.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
