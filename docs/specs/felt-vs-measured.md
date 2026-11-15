# Spec: felt-vs-measured

Queue item `felt-vs-measured` in `governance/queue.json` · due 2026-11-26 · added 2026-11-12.

**The ask, as the queue holds it:** Owner, 2026-11-12 (from the Wheel fix): apply no invented scores and felt next to measured to every self-rating

## Outcome for the person

A self-rating is never an invented number: it shows a dash until the person rates it, next to what the app really measured.

## Data

Per rating: the felt value, when it was last rated, and a measured hint where data exists (sleep from the habit streak, wellness from mindfulness days).

## Screen (one action)

A one-tap row of 1 to 10 under each rating; that tap is the only action.

## Test that proves it

A jsdom test: no default score, a dash before rating, the measured hint appears only with data, and a quarterly cue is offered.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Four ratings on the Life OS.
- **Enterprise, when conditions call for it:** The rule in the kit for every edition, with measured values from connected sources.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
