# Spec: life-systems

Queue item `life-systems` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: build systems (not tips) for everything in the Life OS, using agentic AI, OSINT, open-source components and ready real-world templates (SEO, MarTech, FinTech and beyond), so they run in reality, not as a formality

## Outcome for the person

Each area of life (health, family, career, home, money, learning) runs as a loop that happens without willpower, so the person keeps it up in a real week and sees it counted.

In their words: "I did not have to remember my mother's check-up, my child's next vaccine or my licence renewal. It
came to me, it took two minutes, and I can see it is done."

## What exists now (2026-11-16)

The content is written as data in `guiding-map/levers/life-systems.json`: **12 systems, 14 sourced facts**. No screen
reads it yet; the six briefs in [life-systems-briefs](life-systems-briefs.md) are the slices that will.

| Area | System (`id`) | Its cue | Its smallest step | Its one constraint |
|---|---|---|---|---|
| Health | `health-checkups` | The birthday month | Book one slot | A weekday morning off |
| Health | `health-vaccinations` | Dates made from the birth date | "Done today", with a photo of the card | Knowing what is due |
| Health | `health-family-calendar` | The Sunday review | Read the next seven days aloud | One person carrying it all |
| Family | `family-children-milestones` | The child's birthday | Tick or book the one next item | Deadlines only veterans know |
| Family | `family-parents-care` | The weekly call | Ask this week's one question | Distance; one sibling doing it all |
| Family | `family-partner-time` | A shared weekly block | Twenty minutes, phones away | Tiredness |
| Career | `career-ladder` | The last Friday of the month | One line: a result, with a number | Being seen |
| Career | `career-offers` | An offer arrives | Fill the one-screen comparison | The recruiter's hurry |
| Career | `career-renewals` | 90, 30 and 7 days before expiry | Open the saved renewal page | Learning hours left late |
| Learning | `learning-quarter-skill` | A fixed 25-minute slot | Five minutes or one page | Too many choices |
| Home | `home-monthly-reset` | The first Saturday | Ten minutes on the top item | Repairs waiting for a free day |
| Home | `home-seasonal` | A month before each season | Book the one top job | Tradespeople booked out |

Money is not repeated here: the savings levers, the landlord desk and the expert council already carry it.

## Data

One loop record per area: cue, smallest step, reward, environment change, review date, the one constraint. Facts that change (check-up schedules, scheme rules) come from a watched content file per area, as `scheme-watch` does for levers.

The shape of `life-systems.json`:

- **`systems[]`**: `id` (permanent), `area`, `where` (`IN`, `GLOBAL`), `title`, `outcome`, and
  - `loop`: exactly six keys: `cue`, `step`, `reward`, `environment`, `review`, `constraint`;
  - `personas`: exactly four keys: `distracted`, `adhd`, `novice`, `expert`: how the same loop bends for each;
  - the system's own table where it has one: `schedule` (check-ups, vaccines), `milestones`, `entries`, `seasons`,
    `exit`, `list`, `questions`; a row may carry `where`, `cost`, `get` (where to get it), `fact` and `confirm`;
  - `template`: a ready message with `[blanks]`, never sent without a tap;
  - `global`: what differs when no country is assumed.
- **`facts[]`**: `id`, `where`, `t` (the fact in our own words), `sources` (https only), `verified`, `review`,
  `confidence`, and `confirm` when a primary source was not read. A row points to its fact by id, so a fact is written once.
- **`not_verified_this_round`**: what was looked for and not found. Nothing on that list is printed as a fact.

Rules the content keeps:

1. **A fact with `confirm` is shown as "check before you act"**, with the line that says what to check and with whom
   (a doctor, HR, the distributor, the official page).
2. **Health content never diagnoses and never frightens.** It says what the public programme offers, at what age, and
   that a doctor decides. A row shows only when the profile's age and sex fit it; sex is asked once, with "prefer not to
   say" showing every row.
3. **Costs are ranges with a source and a short review date** (three months for prices from sellers' pages).
4. **No helpline, brand or place name** is printed until verified; none is in this round.
5. **Other files are pointed to, not copied:** health cover for parents over 70 is the lever `ayushman-70`; each
   profession's renewals are in `professions.json`; session plans for learning are in `council-8-learning.json`.

### What was verified, and what was not

| Fact | Source kind | State |
|---|---|---|
| Public screening from age 30 (blood pressure, diabetes, mouth, breast, cervix) | Ministry guideline, press release | verified |
| Cervical VIA and breast examination, ages 30 to 65, every 5 years | Health-mission training module | verified |
| Child vaccines from birth to Td at 10 and 16 | Government portal, health-mission FAQ | verified in outline; `confirm` on each visit's exact set |
| Aadhaar biometric update at 5 and 15 | UIDAI release | verified; today's fee `confirm` |
| Preventive check-up, Rs 5,000 inside the health deduction (old regime; section 126 from 2026-27) | Tax explainers | `confirm` against the Act |
| Labour codes in force from 21 November 2025; gratuity and final dues | News, law-firm notes | `confirm` with HR |
| Cooking-gas hose and inspection, five years | Scheme pages | verified; fee `confirm` |
| Adult vaccines by age | A summary of the physicians' consensus | `confirm`: a physician's call |
| Private check-up prices | Sellers' pages | indicative; review in three months |
| Global: bowel screening 45 to 75, blood pressure from 18 | The US task force's pages | verified |

## Persona cases

The same loop, four people. Each case is a test, not a description.

- **The distracted:** the cue comes to a place they already look (the calendar, one phone message); the step is one
  tap; a miss is recalled once, kindly, then the loop helps. *Test:* a missed check-up month shows one recall next
  month and no second one.
- **The ADHD:** one item, never a list; a two-minute floor that counts; something to tick or see at once; a fixed
  slot or a second person; no streak that punishes. *Test:* a system card never shows more than one open step, and
  the floor closes the day.
- **The novice:** the default is chosen and already filled from the profile (birth dates, sex, home type); they
  correct, never set up. *Test:* with only a birth date entered, the next due item shows with no other input.
- **The expert:** their own schedule typed once replaces the default; only exceptions show. *Test:* with an
  override saved, the default rows are folded and only overdue items are in view.

## Screen (one action)

The Systems screen shows the one loop that is furthest behind, with one button for its smallest step. Other loops show a quiet state (running, resting, not started).

"Furthest behind" is chosen for the person: an overdue dated item first (a vaccine, a renewal), then the loop with the
longest gap against its own rhythm. Everything else folds under "Later (n)". Each repeating cue offers "Add to
calendar" from the one registry in `ops.js` (`CALENDAR`), under the `in-the-calendar` contract; dated items on the
person's own dates go through `gmCalendarDated`.

## Test that proves it

Per area, a jsdom test that the cue reaches the calendar registry, the two-minute floor counts as done, and a missed day is recalled once and kindly. `progress` counts loops that ran this week.

Content is held first, by a Python test (brief 1): every system has the six loop keys and the four personas, every
`fact` reference resolves, every source is https, dates parse, and a fact past its review date is reported.

## The 360 review, in short

- **Person:** a tired parent on a Sunday evening; they should feel "handled", not "behind".
- **First principles:** the need is not information (people know they should get a check-up); it is the cue and the
  two-minute step. So content is small and the loop is the product.
- **Whole system:** reads the profile (ask once), writes ticks on the device, uses the calendar registry and the
  scheme watch. No new login, no network call, no new dependency.
- **Craft:** empty state (no birth date: one line asking for it), a `confirm` fact, a past-review fact, both themes,
  right to left, a screen reader on the one button.
- **Proof:** loops run this week in `progress`; the content test; the persona tests above.
- **Ethics:** no guilt, no fake urgency, no health scare; every nudge shows why and has an off switch.
- **System:** the binding constraint is the cue reaching the person, so the calendar slice (brief 3) comes before any
  richer screen.

## Risks and how each is held

| Risk | Held by |
|---|---|
| A health fact goes stale or is wrong | `verified`, `review`, `confirm`; the scheme watch (brief 6); "a doctor decides" on every health row |
| Private health data leaves the device | Ticks and dates stay on the device, in the encrypted backup only; nothing in the repository |
| The list overwhelms | One open action; one item per card; "Later (n)" |
| A reminder nags | Recall once, then silence; every cue has an off switch |
| India-only content shown abroad | `where` on every system, row and fact; a `global` note per system |

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One area at a time, templates shipped as data, ticks on the device.
- **Enterprise, when conditions call for it:** Shared family loops (a parent's check-ups owned by two siblings) on sync, with ownership and hand-over through the roles service.

## Order of work

Briefs 1 to 6 in [life-systems-briefs](life-systems-briefs.md), in that order: hold the content, ship it with the
app, put the cues in the calendar, show the one furthest-behind loop, show what is due by age, keep the facts watched.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
