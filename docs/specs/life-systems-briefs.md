# Briefs: life-systems

Six test-first briefs for the open models, from [life-systems.md](life-systems.md). Each is one slice an open model
can finish in about 20 minutes. Dispatch them in order, one at a time (`bash lifecycle/delegate_here.sh`), and check
the tier first with `python3 lifecycle/route.py "$(cat brief)"`.

Rules that hold for every brief (do not repeat them in the dispatch; paste them once at the top):

- Do not edit `governance/queue.json` or `guiding-map/levers/life-systems.json` (the content is reviewed; report a
  content problem, do not fix it).
- Write the test first, see it fail, then make it pass.
- In `guiding-map/ops.js`, grep for a name before you add a function: the file is one scope and the last one wins.
- Every visible word goes through `K.t`. Numbers and dates go through `Intl`.
- A line of content with `confirm` is shown with the label "check before you act".
- Gates to run before you stop, each gated on its exit code: `ruff check .`, the one test named in the brief,
  `python3 lifecycle/diffcheck.py`, then `git add -A && python3 -m lifecycle.fitness`.
- Do **not** run the browser audits (`ui_audit.py`, `device_audit.py`, `persona_audit.py`): the reviewer runs them on
  the green branch.
- Test fixtures use plainly fake people and no e-mail address or long digit run.

Test numbers below are the next free ones on main on 2026-11-16 (`test119.js` is the last). If a number is taken when
you start, use the next free one and add it to `npm test` in `guiding-map/package.json`.

## Brief 1: the content check (Python only)

**Outcome:** a broken or stale life-systems file fails a check, so wrong content cannot reach a person.

1. Test first: `governance/tests/test_life_systems.py`, loading `governance/levers.py` by path as
   `test_levers.py` does. It asserts, on the real file: at least 12 systems; each has `id`, `area`, `title`,
   `outcome`; `loop` has exactly `cue`, `smallestStep`, `reward`, `environment`, `review`, `constraint`, all
   non-empty; `cases` has exactly `distracted`, `adhd`, `novice`, `expert`; ids are unique. On a temp copy: a system
   with a missing loop part is reported by name; an item that has `sources` but an empty list is reported; a `where`
   that is not a list drawn from `IN` and `GLOBAL` is reported; a `review` date in the past is reported as past
   review. Match each error's own message (`pytest.raises(..., match=...)` or a substring of the problem line).
2. In `governance/levers.py`: add `LIFE = DIR / "life-systems.json"` and extend `check()` to return these problems,
   beside the landlord ones. Standard library only. Update the module docstring's `check` line.
3. Run: `python3 -m pytest -q governance/tests/test_life_systems.py governance/tests/test_levers.py`.

**Done when:** the new test is green and `python3 governance/levers.py check` prints no life-systems problem.

## Brief 2: the content travels with the app

**Outcome:** the loops work offline, like the savings levers.

1. Test first: `guiding-map/tests/test120.js` (copy the boot pattern of `test117.js`). It asserts
   `window.GM_LIFESYS.systems.length >= 12`, that every system has the six loop parts, and that a new helper
   `gmLifeSystems(region)` returns, for `"GLOBAL"`, no fact, milestone, schedule line, cost or season whose `where`
   lacks `"GLOBAL"`, and for `"IN"` none whose `where` lacks `"IN"`; a line with no `where` shows in both.
2. In `guiding-map/build.js`: embed `levers/life-systems.json` as `window.GM_LIFESYS`, exactly as `GM_COUNCIL` is
   embedded (same escaping, same empty default `{ systems: [] }`).
3. In `guiding-map/ops.js`: add `gmLifeSystems(region)`, a pure function that returns the systems with their
   country-bound lists filtered. It must not throw when `GM_LIFESYS` is missing or damaged (return `[]`).
4. Run: `cd guiding-map && node build.js && node tests/test120.js`.

**Done when:** test120 is green and the full `npm test` still exits 0.

## Brief 3: the loops in the calendar

**Outcome:** a person adds a loop's cue to their calendar in one tap, and a later version never clashes.

1. Test first: add the new ids to the permanent list in `guiding-map/tests/test38.js`, and a new
   `guiding-map/tests/test121.js` that asserts each fixed-rhythm id below exists in `CALENDAR` with `v: 1`, a fixed
   start date, and the rule given.
2. In `CALENDAR` (`guiding-map/ops.js`), add group `"systems"`:
   - `ls-family-health`: quarterly, first Sunday of January, April, July, October, 20 minutes.
   - `ls-ladder`: quarterly, last Friday of March, June, September, December, 15 minutes.
   - `ls-home-month`: monthly, first Saturday, 30 minutes.
   - `ls-partner`: weekly, Friday 20:30, 30 minutes (the person may move it in their calendar).
   - `ls-parents`: weekly, Sunday 11:00, 20 minutes.
   - `ls-learn`: weekly on Monday, Wednesday and Friday 07:30, 25 minutes.
   Names and descriptions in plain words, each description naming the smallest step from the content file. Never
   reuse or rename an id.
3. Do not add the dated ones (`ls-checkup`, `ls-flu`, `ls-child`, `ls-renewal`, `ls-season`): they are brief 5.
4. Run: `cd guiding-map && node build.js && node tests/test38.js && node tests/test121.js`.

**Done when:** both tests are green and the exported `.ics` for one of them has a stable UID across two builds.

## Brief 4: the Systems card, one open action

**Outcome:** the person sees the one loop that most needs them, and one button.

1. Test first: `guiding-map/tests/test122.js`. With an empty store, the card shows exactly one primary button and
   the rest under "Later (n)". After `gmLifeTick("home-monthly")`, that loop shows "running" and is no longer the
   open one. A loop marked "I already do this" is never the open one. A rested loop is not shown as open. The card
   renders with `GM_LIFESYS` missing (a calm empty state, no error).
2. In `guiding-map/ops.js`: `gmLifeState()` reads and writes one key, `gm_lifesys`, shaped
   `{ [id]: { state: "on" | "rest" | "mine", last: ISO date, n: count } }`; register its shape so the loader's shape
   check and quarantine cover it. `gmLifeTick(id)` stamps `last` and raises `n`. `gmLifeOpen()` picks the open loop:
   first a loop with a dated item due within 30 days, else the one never ticked, else the one whose `last` is oldest
   against its own rhythm.
3. Render one card (reuse the council card's classes from `shared/lux.css`; no new CSS): the loop's title, its
   `smallestStep`, one primary button "Done", and a quiet "I already do this". The card goes on the Today tab's
   "Later" fold, not above the daily three.
4. Run: `cd guiding-map && node build.js && node tests/test122.js && node tests/test39.js`.

**Done when:** test122 and the one-open-action test (test39) are green.

## Brief 5: dated items from the person's own dates

**Outcome:** check-ups, children's milestones, renewals and seasons arrive in the calendar by themselves, from facts
the profile already holds.

1. Test first: `guiding-map/tests/test123.js`. With a fake profile (an adult born 1986, a child born 2021, a parent
   born 1955, region India): `gmLifeDated()` returns a yearly check-up item per person in their birth month; an item
   for the child's fifth birthday (the identity update) 60 days ahead; no item for an age already passed; nothing
   for the parent's health card if the parent is under 70 and one if 70 or more. In Global mode, no India milestone.
   Each item's id is `ls-<kind>-<stable person key>-<age or year>` and is the same across two calls. A damaged birth
   date yields no item and no loop (cap every date loop).
2. In `guiding-map/ops.js`: `gmLifeDated()` builds the items from the profile and `gmLifeSystems(region)`, and hands
   them to `gmCalendarDated` under its existing contract (UID from the permanent id, the ledger raises SEQUENCE, a
   done item goes out once as CANCELLED). Ask for nothing new: if a birth date is missing, the item is simply absent.
3. An item made from a line with `confirm` carries "check before you act" at the end of its description.
4. Run: `cd guiding-map && node build.js && node tests/test123.js && node tests/test40.js`.

**Done when:** test123 and the dated-calendar test (test40) are green.

## Brief 6: a miss is recalled once, and progress counts loops

**Outcome:** a slipped loop is brought back kindly, once, and the week's review shows loops that ran.

1. Test first: `guiding-map/tests/test124.js`. A loop whose cue passed two days ago with no tick shows one calm
   line on Today ("Your monthly home reset is waiting. Two minutes?") with one button; after it is seen once
   (`gmLifeRecalled(id)`), it does not show again until the loop's next cue. The line never contains "overdue",
   "missed", "failed" or a count of days. With three loops ticked this week, `gmLifeWeek()` returns `{ ran: 3 }` and
   the Sunday summary shows "3 systems ran this week". No streak is stored or shown anywhere.
2. In `guiding-map/ops.js`: `gmLifeRecall()` returns at most one loop to recall (the most consequential: a dated item
   first), `gmLifeRecalled(id)` records that it was shown, `gmLifeWeek()` counts loops with `last` in the current
   week. Add the count to the existing Sunday summary; no new screen.
3. Python side, test first in `governance/tests/` beside the existing progress tests: `./securax progress` prints a
   line "Life systems: N ran this week" when the exported count file is present, and stays silent when it is not.
4. Run: `cd guiding-map && node build.js && node tests/test124.js`, then the named Python test.

**Done when:** both tests are green and the full `npm test` exits 0.

## After the six

The reviewer (not the builder) runs `ui_audit.py`, `device_audit.py` and `persona_audit.py` on the green branch, adds
the four persona cases of the spec to the persona audit, declares the feature in `features.json` and
`governance/suite.json`, and adds a `life-systems` entry to `governance/evolution.json`. The facts join the scheme
watch only after its threat model is extended to the new sources.
