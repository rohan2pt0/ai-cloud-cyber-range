# Spec: fits-the-person

Queue item `fits-the-person` in `governance/queue.json` · due 2026-11-29 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: anyone can use the open-source Life OS (student, salaried, business owner, retired, UHNWI, a mix of these), so a first-run questionnaire shows only what applies and can be changed; contradictory answers are caught; impossible numbers can never be saved anywhere (age 200, minus salary); prove with …

## Outcome for the person

A student, a salaried person, a business owner or a retired person each sees only what applies to them, and can change that at any time.

## Data

Roles chosen in `Make it yours` (several at once), the profile rulebook `guardP`, and a map of which tab and card each role shows.

## Screen (one action)

`Make it yours`: tap the roles that are you; one button, `Show my app`. Changing later is one line in the Menu.

## Test that proves it

Automated persona runs (each role and common mixes) in a real browser: no irrelevant card, no empty screen, no impossible value accepted; `test106.js` holds the questionnaire.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Roles stored on the device, screens filtered at render.
- **Enterprise, when conditions call for it:** Role packs per segment and organisation, assigned through the roles service, with a default per edition.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
