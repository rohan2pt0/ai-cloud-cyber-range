# Experience v3: the 20 fixes to the Life OS

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** The 20 ranked experience fixes as one-step briefs; none built yet. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Status:** ready to build, 2026-11-16. **Spec:** [experience-v3.md](experience-v3.md). **Tokens:** `governance/design-v3.json`.
**Queue:** `experience-v3` in `governance/queue.json`.

Ranked by **harm × reach ÷ effort**, each scored 1 to 5:

- **Harm:** 5 loses data or blocks the task; 4 blocks a group of people; 3 makes it hard or drives people away; 2 annoys.
- **Reach:** 5 everyone, every day; 4 most people, most days; 3 many people; 2 one group; 1 rare.
- **Effort:** 1 a few lines; 2 one function and its test; 3 touches logic in two places.

Every number under **Seen** was measured on 16 November 2026 in a real browser at 390 × 844, dark theme, or counted in
`guiding-map/ops.js`. Nothing here is a guess. Where a brief says *verify first*, the cause was not confirmed: the test decides.

## How to run one brief (the same for all 20)

One brief, one pull request, about 20 minutes.

1. **Test first.** Write `guiding-map/tests/x3_NN.js` in the style of `test110.js` (jsdom, fake data only, addresses built
   at run time). Run it: it must **fail**. If it passes before any change, commit the test alone, say so, and stop.
2. **One step.** Make the one change named. Edit `guiding-map/ops.js`, or the app code above the ops marker in
   `guiding-map/index.html`. A shared look goes in `guiding-map/shared/lux.css`, never a private copy.
3. **Before adding a function, `grep` for its name** in `ops.js` and `index.html`: one scope, the last declaration wins.
4. **Build and prove:** `cd guiding-map && node build.js && node tests/x3_NN.js && npm test`. Add `x3_NN` to the end of
   the `test` list in `guiding-map/package.json`.
5. **Gates:** `ruff check .`, `python3 -m pytest -q`, `git add -A`, then `python3 -m lifecycle.fitness`.
6. **Paperwork:** one line under `[Unreleased]` in `CHANGELOG.md`; tick the brief in the queue item's `next`.

Do **not**: run the browser audits inside the brief (the navigator runs them on the green branch); weaken or skip a test;
start a timer that keeps jsdom alive (arm repeating timers only in a real browser); touch another brief's scope.
jsdom applies no layout: assert on attributes, classes, text and stylesheet text, not on pixels.

## The ranking

| # | Fix | Harm | Reach | Effort | Score |
|---|---|---|---|---|---|
| 1 | Unsaved days, said honestly on Today | 5 | 4 | 2 | 10 |
| 2 | Escape closes the top layer | 3 | 3 | 1 | 9 |
| 3 | A tick is announced | 4 | 2 | 1 | 8 |
| 4 | The habit check is a named button | 4 | 2 | 1 | 8 |
| 5 | The stars rest | 3 | 5 | 2 | 7.5 |
| 6 | Every click target is a real button | 5 | 3 | 2 | 7.5 |
| 7 | Focus stays after a tick | 4 | 3 | 2 | 6 |
| 8 | No text under 12 px on Today | 3 | 4 | 2 | 6 |
| 9 | Late is amber, never red | 3 | 2 | 1 | 6 |
| 10 | The title names the view | 2 | 3 | 1 | 6 |
| 11 | Quiet actions get a finger-sized target | 3 | 4 | 2 | 6 |
| 12 | No loss line from example data | 4 | 3 | 2 | 6 |
| 13 | The banned words cannot come back | 2 | 5 | 2 | 5 |
| 14 | One notice above the daily three | 3 | 3 | 2 | 4.5 |
| 15 | One main landmark | 2 | 2 | 1 | 4 |
| 16 | Every field has a name | 4 | 2 | 2 | 4 |
| 17 | A rest day, in one tap | 3 | 4 | 3 | 4 |
| 18 | One heading per view | 3 | 2 | 2 | 3 |
| 19 | The More sheet is a dialog | 3 | 2 | 2 | 3 |
| 20 | Restore asks for a typed word | 5 | 1 | 2 | 2.5 |

Fix 20 scores lowest but is a **hard gate** (it can lose data): build it in the first round whatever its score.

## The briefs

### 1. Unsaved days, said honestly on Today (`x3_01`)
- **Seen:** the age of the last backup shows only inside Ops. A person whose only copy is in the browser is never told on
  the screen they open daily (friction `reinstall-data-scare`).
- **Test first:** with real (not example) data and no backup for 8 days or more, Today renders exactly one line containing
  the number of days and one button that calls the existing backup action. With a backup under 8 days old, or with
  example data, the line is absent. A dismiss hides it for 30 days.
- **The one step:** add `gmUnsavedLine()` to Today's render, reading the same backup date Ops already reads. Words:
  "N days of changes live only on this phone." Button: "Save a copy". Attention style (amber), never red.
- **Done when:** the test passes; the line never shows twice; it is the only loss-framed line on Today.

### 2. Escape closes the top layer (`x3_02`)
- **Seen:** `ops.js` and `index.html` contain no handler for the Escape key. No sheet or overlay closes from the keyboard.
- **Test first:** open the More sheet, dispatch `keydown` Escape on `document`: the sheet is closed. Repeat with
  `#gmOverlay` open: it closes. With nothing open, Escape does nothing and throws nothing. The lock screen does not close.
- **The one step:** one `keydown` listener on `document` that closes the top-most open layer (More sheet, `#gmOverlay`,
  `#gmMineSheet`) through each layer's existing close function.
- **Done when:** the test passes and no existing test changes.

### 3. A tick is announced (`x3_03`)
- **Seen:** Today has 0 live regions. Ticking "Move" tells a screen reader nothing.
- **Test first:** the page has exactly one element `#gmSay` with `aria-live="polite"` and `role="status"`, visually
  hidden. After `tgHabit(0)` its text contains the habit's name and "1 of 3". After un-ticking, it says so.
- **The one step:** add `gmSay(text)` and the hidden region (created once, outside `#sections`, so a redraw never removes
  it). Call it from the daily-three tick.
- **Done when:** the test passes; the region survives `renderAll()`.

### 4. The habit check is a named button (`x3_04`)
- **Seen:** in the full Today view each check is `<div class="hab-chk" onclick="tgHabit(i)">`: 26 × 26 px, no role, no
  name, not reachable by keyboard. Five controls on Today had no accessible name.
- **Test first:** with `gm_calm` false, every `.hab-chk` is a `<button type="button">` with `aria-pressed` true or false
  and an `aria-label` that contains the habit's name. Enter and Space toggle it.
- **The one step:** render `.hab-chk` as a button with those attributes; keep its look (reset the button's own border,
  background and font in the existing rule).
- **Done when:** the test passes; the look is unchanged in the ui audit the navigator runs.

### 5. The stars rest (`x3_05`)
- **Seen:** 30 animations (`gmtw`, the twinkle on `.gm-star`) run for ever on Today, also when the phone lies untouched.
- **Test first:** the stylesheet text contains a rule that pauses `.gm-star` under `html.gm-rest`
  (`animation-play-state:paused`). Dispatching `visibilitychange` with the document hidden adds `gm-rest` to `<html>`;
  visible again plus a `pointerdown` removes it. `window.gmRestNow()` adds it at once.
- **The one step:** add the rule and a small rest controller: `gm-rest` on hidden, and after 20 s without `pointerdown`,
  `keydown` or `scroll`. Arm the idle timer only in a real browser (skip jsdom and `navigator.webdriver`).
- **Done when:** the test passes and `npm test` still ends by itself.

### 6. Every click target is a real button (`x3_06`)
- **Seen:** elements with `onclick` that are not buttons or links and have no role: 30 on the All tab, 10 on Map, 8 on
  Stack, 8 on Risk, 6 on Today (full view), and "Back to Calm mode" (a `<span>`) on every tab. None is reachable by keyboard.
- **Test first:** after `goTab('all')`, then `map`, `stack`, `risk` and `today`, every visible `[onclick]` that is not a
  `button`, `a`, `input`, `select`, `summary` or `label` has `role="button"` and `tabindex="0"`; Enter on one runs its
  click once.
- **The one step:** add `gmA11yUpgrade(root)`, called at the end of `renderAll()`: it gives each such element the role and
  tabindex, and one delegated `keydown` listener on `#sections` clicks the focused one on Enter or Space.
- **Done when:** the test passes; an element that already had a role or a key handler is left alone.

### 7. Focus stays after a tick (`x3_07`)
- **Seen:** after ticking a daily-three tile, `document.activeElement` is the page body: the redraw replaces the tile.
  A keyboard or switch user starts again from the top after every tick.
- **Test first:** focus the first daily-three tile, call its click: afterwards `document.activeElement` is the tile with
  the same `onclick` text, and `aria-pressed` is true. Same for the second tile.
- **The one step:** in `renderAll()`, before the redraw remember the focused element's `id`, or else its `onclick`
  attribute; after the redraw focus the match with `{preventScroll:true}`. Skip when `isTyping()` is true.
- **Done when:** the test passes; no scroll jump (the call uses `preventScroll`).

### 8. No text under 12 px on Today (`x3_08`)
- **Seen:** 27 of 63 visible text nodes on Today (full view) render under 12 px. `ops.js` holds 42 inline sizes of 9 to
  11 px. The token floor is 12 px for captions and 13 px for text.
- **Test first:** on Today with `gm_calm` false and again with it true, no element inside `#sections` has an inline
  `font-size` under 12 px.
- **The one step:** in the functions that render Today only, raise every inline 9, 10 and 11 px to 12 px. Uppercase
  eyebrow labels keep their tracking. Other tabs are later slices (All: 157 of 191 nodes; Career; Property; Map).
- **Done when:** the test passes; the navigator confirms no line now wraps badly at 320 px.

### 9. Late is amber, never red (`x3_09`)
- **Seen:** a late career-plan step is written "overdue" in `var(--red)`. Red is for real danger only (`design.json`,
  alerts). For a mind that avoids what shames it, red on a late step ends the visit.
- **Test first:** with a career plan step dated last week, its row contains the word "late", does not contain "overdue",
  and its date uses `var(--amber)`, not `var(--red)`.
- **The one step:** in the career plan row, change the colour to amber and the word to "late". Nothing else.
- **Done when:** the test passes. (The landlord desk's legal due dates keep their own wording: a real deadline.)

### 10. The title names the view (`x3_10`)
- **Seen:** `document.title` is fixed at "The Guiding Map" on every tab, while the header says "My Life OS". Nothing
  sets it. The app switcher, history and a screen reader all hear the same wrong name.
- **Test first:** after `goTab('today')` the title is "Today · Life OS"; after `goTab('okr')` it starts with that tab's
  label from `TABS`.
- **The one step:** in `goTab`, set `document.title` to the tab's label, " · ", and the app's name through the catalog.
- **Done when:** the test passes in English; other languages use the translated label.

### 11. Quiet actions get a finger-sized target (`x3_11`)
- **Seen:** text actions measure under 44 px: "Back to Calm mode" 174 × 18, "Got it, hide this", "Open the profile"
  100 × 20, "Show me everything". `lux.css` already has an invisible hit area for tapped terms.
- **Test first:** `guiding-map/shared/lux.css` has a class `sx-hit` whose rule sets a pseudo-element hit area of at least
  44 px high without changing the line box; the four actions above carry that class.
- **The one step:** add `.sx-hit` to `lux.css` (reuse the technique of the gloss rule) and put the class on those four.
- **Done when:** the test and `governance/tests/test_shared_look.py` pass.

### 12. No loss line from example data (`x3_12`) (*verify first*)
- **Seen:** loss-framed advice exists ("about ₹X a month back that you are leaving on the table"). A newcomer's screen
  runs on example numbers. A loss computed from invented numbers is not an honest loss.
- **Test first:** with `P.example` true and example card data, the rendered advice contains no "leaving on the table" and
  no rupee figure framed as a loss; with real data it does.
- **The one step:** where that action list is built, skip loss-framed lines while the profile is example data, and show
  the existing "example" mark instead.
- **Done when:** the test passes. If it passed before any change, keep the test and close the brief.

### 13. The banned words cannot come back (`x3_13`)
- **Seen:** the ritual text says "Habit streaks: anything missed twice". Nothing stops shame words returning.
- **Test first:** read `behaviour.streak.words_never` from `governance/design-v3.json`; fail if any appears, as a whole
  phrase and in any letter case, in a visible string of `ops.js` or of `guiding-map/i18n/lifeos.en.json`. Comments and
  identifiers (for example `missedTwice`) do not count: scan string literals only.
- **The one step:** reword each hit with a word from `words_instead` (for example "Habits: after two quiet days, a
  recovery day, the floor only").
- **Done when:** the test passes; this is the first test that reads `design-v3.json`.

### 14. One notice above the daily three (`x3_14`)
- **Seen:** the full Today view stacks four notices ("Lost?", "Example data", the decade card, "13 fields still hold
  example numbers") before the first action, which starts 690 px down an 844 px screen. Two of them say the same thing.
- **Test first:** with `gm_calm` false and example data, at most one notice element precedes the daily three in
  `#sections`; the others sit inside one closed `<details>` whose summary reads "Later (n)"; "Example data" appears once.
- **The one step:** in Today's full render, keep the first notice by this order (danger, example data, the rest), fold
  the others under "Later (n)", and drop the second example notice.
- **Done when:** the test passes; `test39.js` (one open action) still passes.

### 15. One main landmark (`x3_15`)
- **Seen:** the page has a skip link and a nav, but no `<main>`. A screen reader cannot jump to the content.
- **Test first:** exactly one element has `role="main"` (or is `<main>`), it contains `#sections`, it has
  `tabindex="-1"`, and the skip link's `href` points at its `id`.
- **The one step:** give the wrapper of `#sections` `role="main"`, an `id` and `tabindex="-1"`; point the skip link at it.
- **Done when:** the test passes; no style changes.

### 16. Every field has a name (`x3_16`)
- **Seen:** fields with no label and no `aria-label`: Property 16 of 16, Commit 3 of 4, Ask 1 of 1, Growth 1 of 1,
  Money 1 of 2.
- **Test first:** after `goTab` to each of those five tabs, every visible `input`, `select` and `textarea` has an
  `aria-label`, an `aria-labelledby` or a `<label>`.
- **The one step:** add `gmNameFields(root)` to the end of `renderAll()`: an unnamed field takes its `aria-label` from its
  `placeholder`, else from the text of the nearest preceding label-like element in its row.
- **Done when:** the test passes; a field that already had a name is untouched.

### 17. A rest day, in one tap (`x3_17`)
- **Seen:** a person can pause all rituals, but cannot mark today as rest. The only way to not do the three is to miss.
- **Test first:** Today shows one quiet action "Rest today" under the daily three. Tapping it stores today's date in
  `gm_rest`, shows "Resting today" with an Undo, and the seven-day row draws that day with class `gm-rest-day` and the
  label "rested". At most two rest days are offered in any seven.
- **The one step:** the action, the stored date (in the `SHAPES` list, so damaged storage is caught) and the row's
  drawing. Slice 2, a separate brief: the miss logic (`missedTwice`, habit strength) treats a rest day as neutral.
- **Done when:** the test passes; the robustness audit's key list includes `gm_rest`.

### 18. One heading per view (`x3_18`)
- **Seen:** 24 of 26 tabs render no heading at all. A screen reader user cannot tell where they are or move by heading.
- **Test first:** after `goTab` to every id in `TABS`, `#sections` contains exactly one `<h1>` and its text is the tab's
  label.
- **The one step:** in `goTab` (or the section render), insert one `<h1 class="sx-vh">` with the tab's label at the top of
  the active section; `.sx-vh` (visually hidden) goes in `lux.css`. A tab that already shows a visible title turns that
  title into the `h1` instead.
- **Done when:** the test passes; nothing moves on screen.

### 19. The More sheet is a dialog (`x3_19`)
- **Seen:** `#gmMoreSheet` opens over the page with no role, no name and no move of focus. Only two layers in the app
  declare `aria-modal` (the lock, Make it yours).
- **Test first:** open More: the sheet has `role="dialog"`, `aria-modal="true"` and an `aria-label`; focus is on its
  first button; closing it returns focus to the More button in `#gmNav`.
- **The one step:** add those attributes and the two focus moves to the More sheet's open and close functions.
- **Done when:** the test passes; fix 2's Escape test still passes. Next slice: the same for `#gmOverlay`.

### 20. Restore asks for a typed word (`x3_20`) (hard gate)
- **Seen:** three paths overwrite everything on the device behind a browser `confirm()`: restoring the estate's snapshot,
  restoring from the cloud backup, and moving data onto an address that already has data. Erase already needs a typed
  word (`test46.js`); restore, just as final, does not.
- **Test first:** calling the snapshot restore with data on the device opens an in-page dialog that says how many items
  will be replaced, offers "Save a copy first" as its primary, and only proceeds when the word RESTORE is typed.
  `window.confirm` is never called on that path.
- **The one step:** add `gmTypedConfirm(word, message, safeStep)` built from the erase dialog's pattern, and use it on the
  snapshot restore. Next slices, one each: the cloud restore; the move.
- **Done when:** the test passes; `test46.js` still passes.

## Next, after the 20

Named so they are not lost; each becomes a brief when its turn comes.

- The 25 `alert()` calls become in-page notices (what happened, why, one step).
- The remaining `confirm()` calls use `gmTypedConfirm` or an in-page choice.
- `#gmOverlay` gets fix 19's dialog manners.
- The focus timer's end vibration goes through the haptics gate.
- Keys 1, 2 and 3 tick the daily three on a keyboard; `?` lists the keys.
- The 12 px floor on All, Career, Property and Map.
- `guiding-map/tests/manners_audit.py`: the real-browser checks A5 to A15 of the spec, reading `design-v3.json`.
- The same fixes in the kit (Vantage) through `lux.css` and `governance/oskit.py`.

## What the panel could not test

- No screen reader was run: findings 3, 4, 6, 15, 16, 18 and 19 come from the page's structure, not from VoiceOver or TalkBack.
- No real phone: one desktop Chromium at phone size. Battery cost in fix 5 is inferred from 30 running animations.
- Light theme and the kit apps were not measured in this round.
- Some inline terms measure small but may carry an invisible hit area; fix 11 lists only the four confirmed.
