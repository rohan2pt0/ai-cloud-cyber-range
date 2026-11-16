# Briefs: life-systems

Six briefs for the open models, in order. Each is one step, test first, sized to finish in 20 minutes. Send them one
at a time through the `delegate` skill; check the tier with `python3 lifecycle/route.py "$(cat brief)"` first.
The content is in `guiding-map/levers/life-systems.json`; the plan is in [life-systems.md](life-systems.md).

**Rules for every brief** (paste them with the brief):

- Write the test first, see it fail, then make it pass. Use the next free test number in `guiding-map/tests/` and add
  it to the `test` line in `guiding-map/package.json`.
- Before adding a function to `ops.js`, `grep -n` for its name: one scope, the last declaration wins.
- A helper used by two closures lives where both can reach it; never swallow a ReferenceError in a `try`.
- Arm no timer in jsdom. Every visible word goes through the catalog. No new dependency, no network call.
- Edit `ops.js` (or the app code above the ops marker), then `node build.js`. Never hand-edit built output.
- Gates to run, in this order: `node build.js`, `npm test` in `guiding-map/` (the whole suite, exit code 0),
  `ruff check .`, `git add -A`, `python3 -m lifecycle.fitness`, `python3 lifecycle/diffcheck.py`.
- Do not run the browser audits (`ui_audit.py`, `device_audit.py`, `robustness_audit.py`): the navigator runs them on
  the green branch.
- Do not edit `governance/queue.json` or `guiding-map/levers/life-systems.json`.

---

## Brief 1: load the content, safely

**Outcome:** the Life OS has the twelve loops in hand, and a missing or damaged file never breaks a page.

1. Test: after the build, `window.GM_SYSTEMS.systems.length` is 12 and each has the six `loop` parts. With
   `window.GM_SYSTEMS` set to `null`, to `{}` and to `{"systems": "x"}`, `gmSystems()` returns `[]` and nothing throws.
2. In `build.js`, inline `guiding-map/levers/life-systems.json` as `window.GM_SYSTEMS`, the same way `GM_LEVERS` is
   inlined.
3. In `ops.js`, add `gmSystems()`: returns the array of systems whose `where` fits the person's region (Local India
   shows `IN`; Global shows `GLOBAL`), or `[]` on any bad shape.

**Done when:** the new test passes and the full `npm test` is green. Touch no screen.

## Brief 2: the Systems card, one open action

**Outcome:** the person sees the one loop that is furthest behind and one button for its smallest step.

1. Test: with example data, Today shows one card titled "Systems" with exactly one primary button; the other loops
   are inside a folded "Later (n)" line; with `gmSystems()` empty there is no card and no error.
2. Add `gmSystemsCard()` to `ops.js`. Pick the loop by this order: a health loop never done, then the loop with the
   oldest tick, then file order. Show its `title`, its `loop.smallestStep` as the button, and its `outcome` as one
   line. Use the shared look (`lux.css` classes already in use on the Savings levers card); add no new CSS.
3. A guest sees it with example data they can correct.

**Done when:** the new test and `test39.js` (one open action) pass.

## Brief 3: a tick that counts, a miss recalled once

**Outcome:** one tap records the step; the count only goes up; a miss is mentioned once, kindly.

1. Test: tapping the button stores a tick with today's date under one storage key (`gm_systems`), raises "times
   done" by one and moves the card to the next loop. A stored value of the wrong type (a string, an array, `null`)
   reads as "no ticks" and does not throw. After 37 ticks on one loop, 36 are kept. A loop missed for one cycle
   shows the recall line once; on the next render it is gone.
2. Add `gmSystemTick(id)` and the reader, with the shape checked against the default as `load` does with `SHAPES`.
3. No streak counter anywhere: only "times done" and "last done".

**Done when:** the new test passes and the full `npm test` is green.

## Brief 4: the cues in the calendar

**Outcome:** every repeating cue has "Add to calendar" beside it, from the one registry.

1. Test: `CALENDAR` holds these eleven new ids, each with a fixed start date, a `rule` and `v: 1`:
   `health-checkup-yearly`, `health-flu-yearly`, `health-family-month`, `family-child-year`, `family-parents-call`,
   `family-parents-year`, `family-partner-week`, `career-quarter`, `learning-block`, `home-reset-month`,
   `home-season` (one item, four dates a year). Add the ids to the list in `test38.js`.
2. Add the eleven entries to `CALENDAR` in `ops.js`, in the same shape as the existing entries. Wording comes from
   each loop's `loop.cue`, shortened to one line.
3. The Systems card shows "Add to calendar" for the loop in view.

**Done when:** the new test and `test38.js` pass. An id, once merged, is never deleted or renamed.

## Brief 5: facts shown honestly

**Outcome:** the person can open a loop and see what it rests on, with unsure facts marked.

1. Test: opening a loop lists its `facts`; a fact with a `confirm` line shows the label "Check before you act" and
   the confirm text; a fact with `sources` shows "Source" links with `rel="noopener noreferrer"` and
   `target="_blank"`; text from the file is set with `textContent`, never `innerHTML`; when today is after the
   file's `review` date every fact shows the label.
2. Add `gmSystemDetail(id)` to `ops.js`: the outcome, the six loop parts in plain rows, then the facts, then the
   `schedule`, `milestones`, `seasons`, `checklist` or `template` when the loop has one. A `template` gets one
   "Copy" button.
3. Health loops end with the line "A doctor decides what you need."

**Done when:** the new test passes and the full `npm test` is green.

## Brief 6: the content check

**Outcome:** a broken or stale content file fails a check before a person sees it.

1. Test (`governance/tests/`, pytest): a good file passes; a system missing a loop part, a persona case, or a fact
   with neither `sources` nor `confirm` fails with a message that names the system's `id`; a file past its `review`
   date is listed, not failed; a source that is not `https://` fails.
2. In `governance/levers.py`, extend `check` to validate `life-systems.json` with those rules (standard library
   only). Match errors by their own message in the tests (`pytest.raises(..., match=...)`).
3. Add nothing to `watch`: the source watch for this file is a later slice.

**Done when:** `python3 governance/levers.py check` passes on the real file, and `python3 -m pytest -q` is green.
