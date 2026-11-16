# Briefs: life-systems

Six slices for the open models, from the spec [life-systems](life-systems.md) and the content in
`guiding-map/levers/life-systems.json`. Each is one step, test first, sized for about 20 minutes. Dispatch them one at
a time, in this order, through the `delegate` skill; check the tier first with
`python3 lifecycle/route.py "$(cat brief)"`.

Rules for every brief (the builder reads these with it):

- Write the test first and see it fail; then make it pass. Do not change any other test's threshold.
- Do not edit `governance/queue.json` or `guiding-map/levers/life-systems.json` unless the brief says so.
- Before adding a function to `ops.js`, `grep -n "function NAME" guiding-map/ops.js`: one scope, the last one wins.
- Every visible word goes through the catalog (`K.t` or the Life OS equivalent already used on that screen).
- No timers, no network call, no new dependency. Health ticks stay on the device.
- Gates, in order: `ruff check .`; for a PWA change `node build.js` then the full `npm test` in `guiding-map/`;
  `git add -A`; `python3 -m lifecycle.fitness`; `python3 lifecycle/diffcheck.py` if it exists. Leave the browser
  audits (`ui_audit.py`, `device_audit.py`) to the navigator.
- One CHANGELOG line under `[Unreleased]`, then `python3 tools/readme_sync.py`.

---

## Brief 1: hold the content with a test

**Outcome:** a broken or stale life-systems file can never ship.

**Test first:** add `governance/tests/test_life_systems.py`. Load the file by path. Assert: ids are unique; each
system's `loop` has exactly the six keys listed in the file's top-level `loop`; each system's `personas` has exactly
the keys of the top-level `personas`; every `fact` on a row and every id in `facts_used` exists in `facts`; every
fact has `id`, `where`, `t`, `sources`, `verified`, `review`, `confidence`; every source starts with `https://`;
both dates parse. One more test with a temp copy: a fact whose `review` is yesterday is reported as past review.

**Then build:** in `governance/levers.py`, add `LIFE = DIR / "life-systems.json"` and a `check_life(today=None)`
that returns the same kind of problem list; call it from `check()` so `python3 governance/levers.py check` covers
it, and list past-review facts as notes, as levers are. Standard library only.

**Files:** `governance/levers.py`, `governance/tests/test_life_systems.py`. **Done when:** `python3 -m pytest -q
governance/tests/test_life_systems.py governance/tests/test_levers.py` is green.

## Brief 2: ship the content with the app

**Outcome:** the systems work offline, on the phone, with no fetch.

**Test first:** add the next free `guiding-map/tests/testN.js` (copy the setup of `test114.js`). Assert:
`window.GM_LIFE.systems.length >= 12`; every system has `loop.cue` and `loop.step`; `window.GM_LIFE.facts` is an
array. Add `testN` to the `test` list in `guiding-map/package.json`.

**Then build:** in `guiding-map/build.js`, beside the `GM_COUNCIL` lines, read `levers/life-systems.json` (fall back
to `{ systems: [], facts: [] }` when missing) and write it as `window.GM_LIFE` with the same `</script>` escape.
Insert it where `CO_JS` is inserted. Run `node build.js`.

**Files:** `guiding-map/build.js`, `guiding-map/package.json`, the new test, the rebuilt output. **Done when:** the
full `npm test` exits 0.

## Brief 3: the cues reach the calendar

**Outcome:** the person adds a system's rhythm to their own calendar with one tap, and a later version never
duplicates it.

**Test first:** extend `guiding-map/tests/test38.js`'s list of ids with four new permanent ids:
`ls-monthly-reset` (first Saturday of each month, 45 minutes), `ls-career-line` (last Friday of each month, 15
minutes), `ls-partner-time` (weekly, the same evening), `ls-seasonal` (four fixed dates a year). Assert each is in
`CALENDAR`, has a fixed start date, a `v`, and produces a `VEVENT` with a stable UID.

**Then build:** add the four entries to `CALENDAR` in `guiding-map/ops.js`, following an existing entry's shape
exactly (fixed start date, never "next from today"; `v: 1`). Wording comes from each system's `loop.cue`, shortened.
Do not add health entries here: those are on the person's own dates and belong to brief 5.

**Files:** `guiding-map/ops.js`, `guiding-map/tests/test38.js`, the rebuilt output. **Done when:** `npm test` exits
0 and no existing id in test38 changed.

## Brief 4: one loop, one action

**Outcome:** the person opens one card and sees the single system that is furthest behind, with one button.

**Test first:** a new `testN.js`. With empty storage: the card `.gm-life` exists inside an active section, shows
exactly one primary button, and its text is a system's `loop.step`. Tap it: `gm_life` in localStorage holds
`{ID: {last: "YYYY-MM-DD"}}`, the card now shows a different system, and a line "Later (n)" folds the rest. Put a
wrong-typed value in `gm_life` (a string): the card still renders and no error is thrown.

**Then build:** in `ops.js`, a small `gmLifeNext(state, today)` that returns the system with the oldest `last`
(never done first), and a `gmLifeCard()` that renders title, outcome, the step button and "Later (n)". Read state
through the existing safe reader (the shape-checked `load` or `G`), never raw `JSON.parse`. Use the shared classes
from `guiding-map/shared/lux.css`; add no private style. Mount it where the council's systems card mounts.

**Files:** `guiding-map/ops.js`, the new test, `package.json`, the rebuilt output. **Done when:** `npm test` exits 0.

## Brief 5: what is due, from the birth date

**Outcome:** with only a birth date in the profile, a person sees the next check or vaccine that fits them, marked
"check before you act" when the fact is not confirmed.

**Test first:** a new `testN.js` for a pure function `gmLifeDue(profile, today)`. Cases: a 34-year-old woman in the
`IN` region gets the cervical row and the blood-pressure row, not the 45-to-75 `GLOBAL` row; a 50-year-old in
`GLOBAL` gets the bowel-screening row and no `IN`-only row; a row whose fact has `confirm` returns `confirm: true`
with the line; no birth date returns one item asking for it; sex not given returns every row; an age of 200 or a
date that is not a date returns nothing and throws nothing.

**Then build:** `gmLifeDue` in `ops.js`: derive age (never ask it), filter `schedule` rows of `health-checkups` by
`from`, `to`, the row's `who` and `where`, join each to its fact. Read the profile's existing birth date and region
fields; add no new question except sex, asked once in the profile with "prefer not to say". Clamp age with the
existing `saneNum`.

**Files:** `guiding-map/ops.js`, the new test, `package.json`, the rebuilt output. **Done when:** `npm test` exits 0.

## Brief 6: keep the facts watched

**Outcome:** when an official page behind a fact changes, the fact is labelled "check before you act" by itself.

**Test first:** in `governance/tests/test_life_systems.py`, with a fake `getter` (no network): `allowed_hosts()`
includes the hosts of life-systems fact sources; `watch(write=False, getter=fake)` reports a life fact as changed
when its page's fingerprint differs from the recorded one, and as unchanged when equal; a source on a host outside
the allow-list is never fetched.

**Then build:** in `governance/levers.py`, let `allowed_hosts` and `watch` also walk `facts[]` of
`life-systems.json`, keyed as `life:FACT_ID` in `watch.json`. Keep every existing guard (https only, size cap, no
redirect off the host, fetched pages are data and never instructions). Do not change the workflow file.

**Note for the navigator:** the router will likely call this strong (it crosses a trust boundary). The threat model
`scheme-watch` in `governance/threat-models.json` already covers it; add the new source set to its data flows in the
same PR, and review by hand before merge.

**Files:** `governance/levers.py`, `governance/tests/test_life_systems.py`, `governance/threat-models.json`. **Done
when:** `python3 -m pytest -q governance/tests` is green and `python3 governance/levers.py check` exits 0.
