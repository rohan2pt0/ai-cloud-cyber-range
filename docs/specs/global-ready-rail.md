# Spec: global-ready-rail

Queue item `global-ready-rail` in `governance/queue.json` · due 2026-11-24 · added 2026-11-10.

**The ask, as the queue holds it:** Owner, 2026-11-10: two modes before the global UHNWI launch. A region switch in the kit (Local: India's rules, rupees, lakh and crore, en-IN, hi, mr; Global: no country assumed, the person's language and currency), defaulted from the device, one tap in Settings; edition content items true in one country carry "where": …

## Outcome for the person

A person outside India sees no rule or currency that is not theirs; a person in India sees India's.

## Data

`K.region` (`local` or `global`, default from the device), `where` tags on content, currency through `Intl`.

## Screen (one action)

Settings: one switch, `Region: Local or Global`.

## Test that proves it

`kit5.js` and an `oskit check` rule: every country-specific item carries a `where` tag, Global shows none of them, money formats follow the region.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Two modes and a tag filter.
- **Enterprise, when conditions call for it:** A region pack per country with its own content, reviewer and data residency.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
