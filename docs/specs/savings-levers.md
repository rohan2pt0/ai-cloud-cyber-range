# Spec: savings-levers

Queue item `savings-levers` in `governance/queue.json` · due 2026-12-13 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: help cut the cost of living and tax legitimately and keep it sustainable (rooftop solar with the subsidy, state bus concessions for women and parents, Ayushman for parents over 70, the cheaper tax regime, presumptive tax for consultants, an HUF only where it fits, and every such scheme), as working …

## Outcome for the person

The household legitimately pays less tax and less for living, through a lever it actually completes, and sees the rupees saved each year.

## Data

`guiding-map/levers/levers.json` (11 levers: who it fits, what it saves, steps, a template, the official portal, sources, review date). Matching uses facts already in the profile; ticks per step on the device.

## Screen (one action)

The Savings levers card on Money: the one lever with the largest saving that fits, with one button, `Start: step 1`. Others fold under `Later (n)`.

## Test that proves it

`test114.js` plus persona runs: a lever shows only when its facts fit; a lever past its review date is labelled; the saved total equals the sum of completed levers.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Static levers matched on the device.
- **Enterprise, when conditions call for it:** Levers per country and per employer, kept current by `scheme-watch`, with an advisor view by consent.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
