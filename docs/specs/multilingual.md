# Spec: multilingual

Queue item `multilingual` in `governance/queue.json` · due 2026-12-15 · added 2026-11-10.

**The ask, as the queue holds it:** Owner, 2026-11-10: make the apps multilingual. English, Hindi and Marathi first (more by adding one catalog file); the device's language by default, a one-tap switch, English fallback for anything untranslated, Indian number grouping, offline

## Outcome for the person

A person reads the apps in Hindi or Marathi from the first screen, with numbers the Indian way, offline.

## Data

Catalog files per language (`guiding-map/i18n/lifeos.<lang>.json`, kit catalogs); coverage counts per screen.

## Screen (one action)

Settings: one switch, `Language`, defaulting to the device's. No other step.

## Test that proves it

`test50.js` and the kit language checks: no missing key on the key screens, English fallback elsewhere, and a coverage number that only goes up.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Catalogs inlined at build, exact-match swap.
- **Enterprise, when conditions call for it:** Whole-sentence templates with plurals, professional review, and per-tenant glossaries.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
