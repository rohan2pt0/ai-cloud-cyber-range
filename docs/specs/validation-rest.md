# Spec: validation-rest

Queue item `validation-rest` in `governance/queue.json` · due 2026-11-25 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: input validation everywhere (age 200, minus salary impossible)

## Outcome for the person

An impossible value (age 200, a minus salary, a deadline in 1970) can never be saved anywhere, so no screen ever shows nonsense.

## Data

One rule per field (type, range, relation to another field), held beside the field's definition; the remaining fields are the money cards, Kids, Commit, OKR key results, Inbox amounts and the Life Map flow.

## Screen (one action)

No new screen. On a bad value the field itself says what is allowed and offers the nearest valid value as one tap, `Use 60`.

## Test that proves it

`robustness_audit.py` extended to type out-of-range and wrong-typed values into every typed field in a real browser; zero bad values stored, zero page errors.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Each field routed through `gmFieldGuard` with its rule.
- **Enterprise, when conditions call for it:** Rules published as a schema shared by the kit, imports, sync and any API, so a value refused on screen is refused at every door.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
