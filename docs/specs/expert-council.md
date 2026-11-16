# Spec: expert-council

Queue item `expert-council` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15 (clarified): improve the app as if the world's best professionals (pilots, surgeons, doctors, risk officers, intelligence, military, investors, CFOs, lawyers, architects, behavioural scientists, coaches, professors, sales leaders, marketers, economists and more) poured their expertise into systems …

## Outcome for the person

A household gets the habits of the best professionals as small systems it can run: fewer nasty surprises, calmer money, better decisions, stronger ties. The person sees one closed gap or one finished ritual each week.

## Data

Content as data in `guiding-map/levers/council*.json` (item 1 in `council.json`; items 4 to 8 in `council-4-pace.json` to `council-8-learning.json`). The person's ticks, plans and journal entries stay on the device, bounded (one record per plan, close, decision, person, card).

## Screen (one action)

One Council card: the single most severe open item for this household, with one button, `Do this now`. Closed items fold under `Done (n)`; the rest wait under `Later (n)`.

## Test that proves it

One jsdom test per item (as `test117.js` does for item 1): the right item is on top for a persona, one tap closes it, the reward shows, and nothing else competes. A persona run (salaried with children, retired, founder) proves each sees only what applies.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One person, offline, content inlined at build time; ticks in device storage.
- **Enterprise, when conditions call for it:** Content packs signed and versioned (`signed-official-content`), reviewed per country by a professional, with a household or team roll-up through the shared roles and audit services.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
