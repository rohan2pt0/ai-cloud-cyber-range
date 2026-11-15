# Spec: auto-numbers

Queue item `auto-numbers` in `governance/queue.json` · due 2026-12-05 · added 2026-11-14.

**The ask, as the queue holds it:** Numbers arrive by themselves (bank SMS, fund and demat statements, holdings for the birthday-month rebalance), even at some cost; copy-paste is only the fallback

## Outcome for the person

Balances and holdings update by themselves; copying is only the fallback.

## Data

Bank alerts read on the device with a permission asked at use; web push from the estate.

## Screen (one action)

Money: `Updated today` and one switch per source.

## Test that proves it

`test99.js`; tests that the permission is the narrowest and removable; a threat model per source.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** E-mail alerts read on the device.
- **Enterprise, when conditions call for it:** Account-aggregator and statement feeds by consent, per country.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
