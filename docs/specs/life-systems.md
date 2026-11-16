# Spec: life-systems

Queue item `life-systems` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: build systems (not tips) for everything in the Life OS, using agentic AI, OSINT, open-source components and ready real-world templates (SEO, MarTech, FinTech and beyond), so they run in reality, not as a formality

## Outcome for the person

Each area of life (health, family, career, home, money, learning) runs as a loop that happens without willpower, so the person keeps it up in a real week and sees it counted.

## Data

One loop record per area: cue, smallest step, reward, environment change, review date, the one constraint. Facts that change (check-up schedules, scheme rules) come from a watched content file per area, as `scheme-watch` does for levers.

## Screen (one action)

The Systems screen shows the one loop that is furthest behind, with one button for its smallest step. Other loops show a quiet state (running, resting, not started).

## Test that proves it

Per area, a jsdom test that the cue reaches the calendar registry, the two-minute floor counts as done, and a missed day is recalled once and kindly. `progress` counts loops that ran this week.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One area at a time, templates shipped as data, ticks on the device.
- **Enterprise, when conditions call for it:** Shared family loops (a parent's check-ups owned by two siblings) on sync, with ownership and hand-over through the roles service.
Queue item `life-systems` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15 · content written 2026-11-16.

**The ask, as the queue holds it:** build systems (not tips) for everything in the Life OS, with ready real-world
templates and facts that keep themselves current, so they run in reality, not as a formality.

This page replaces the one-page outline written on 2026-11-15. The content is in
`guiding-map/levers/life-systems.json`; the build briefs are in [life-systems-briefs.md](life-systems-briefs.md).
Money is not here: it has its own files (`levers.json`, `landlord.json`, `council.json`).

## Outcome for the person

Each area of life runs as a loop that happens in a real week without willpower. The person sees **one** next step,
takes it in two minutes or less, and sees it counted. Nobody in the family has to carry the list in their head.

## What a loop is

Every system in the file has the same six parts. A system missing one is not finished.

| Part | The question it answers | The rule |
|---|---|---|
| Cue | When and where does it start? | In the calendar or one phone message; never "when you remember". |
| Smallest step | What still counts on a bad day? | Two minutes or one tap. Booking counts; going is the next step. |
| Visible reward | What do they see at once? | A state that changes on the tap (due, booked, done until a date). Totals, never streaks. |
| Environment | What makes the right step easy? | Already filled from the profile; the free option named first; a ready message. |
| Review | When is the loop itself improved? | A fixed date, tied to a review that already exists. |
| Constraint | What one thing limits it? | Named, and the smallest step is aimed at it. |

## The twelve loops

| Area | Loop (`id`) | Cue | Smallest step | Its one constraint |
|---|---|---|---|---|
| Health | Check-ups by age and sex (`health-checkups`) | Each person's birthday month | Book it with the ready message | The appointment |
| Health | Vaccinations (`health-vaccinations`) | A dated item per dose | Tap "Given", photograph the card | The record |
| Health | The family health calendar (`health-family-calendar`) | First Sunday of the quarter | Book or tick the soonest line | One person carries it all |
| Family | Children's milestones and papers (`family-children`) | 60 days before each milestone | The item's one action | Dates set by others |
| Family | Parents' care (`family-parents`) | A weekly slot; the birthday month | The call; one question answered | The conversation |
| Family | The partner's weekly time (`family-partner`) | The same evening every week | Ten minutes, two questions | A shared free hour |
| Career | The ladder (`career-ladder`) | Last Friday of the quarter | One line: the result, with its number | Evidence |
| Career | Offers (`career-offers`) | "I have an offer" (an event) | Enter the fixed pay; see take-home | Pressure to decide fast |
| Career | Renewals (`career-renewals`) | A dated item per paper | Type one expiry date | The first entry |
| Learning | One skill a quarter (`learning-skill`) | Three fixed 25-minute slots a week | Five minutes of doing | Attention, not material |
| Home | The monthly reset (`home-monthly`) | First Saturday of the month | The top item of the list | Starting |
| Home | Seasonal maintenance (`home-seasonal`) | Four weeks before the season | Walk the home with the list | Tradespeople are booked out |

Three loops reuse what exists and add nothing of their own: the ladder and renewals read
`guiding-map/levers/professions.json`; offers uses the job-offer checklist in `guiding-map/levers/council.json`.

## The four persona cases

Each loop says how it behaves for four people. The rule for each is the same across loops:

- **The distracted:** the cue lives in something they already open, and the step is already chosen.
- **The person with ADHD:** the step is visible and under two minutes, the reward is immediate, a miss is recalled once
  and kindly, and there is no streak to break. A late item reads "due now", never "overdue by 12 days".
- **The novice:** the loop arrives partly done (the list for their age, the place, a rough cost). Nothing to read first.
- **The expert:** one tap says "I already do this"; the app then only keeps the dates and stays quiet.

## Data

`guiding-map/levers/life-systems.json`, version 1, verified 2026-11-16, review by 2027-05-16.

- `personas`: the four cases and their rule.
- `systems[]`: `id`, `area`, `title`, `outcome`, `loop` (the six parts), `cases` (the four personas), then the loop's own
  content (`schedule`, `costs`, `facts`, `milestones`, `questions`, `checklist`, `seasons`, `template`) and a proposed
  `calendar` entry (`id`, `rule`).
- Every country-bound line carries `where` (`["IN"]`, `["GLOBAL"]` or both). In Global mode the India facts are hidden
  and the loop's Global fact shows: "follow your own national programme".
- Every fact read this round carries `sources`. Every fact that is not settled carries `confirm`, in plain words, naming
  where to check.

**One rule for the builder:** a line with `confirm` never drives a number, a date or a deadline on screen without the
label "check before you act". Medical lines always end with "ask your doctor".

Nothing new is asked of the person. Birth dates, sex, partner, children and parents come from the profile
(`ask-by-frequency`). The only new values are dates the person owns: a last check-up, an expiry, a slot they pick.
Ticks and dates stay on the device, with the rest of the Life OS data, and travel in the same encrypted backup.

## What was verified, and what was not

Verified on 2026-11-16 by web search; sources are in the file.

| Fact (India) | Standing |
|---|---|
| The national screening programme covers everyone from 30 for blood pressure, diabetes and oral, breast and cervical cancer, free at government centres | Official guideline. The intervals (yearly; five-yearly for the cancers) come from a programme slide deck: `confirm` |
| Preventive check-ups: up to Rs 5,000 counts inside the section 80D cap, old regime only, cash allowed | Tax guides, not the Act: `confirm` |
| Free HPV vaccine for girls aged 14, national campaign launched 28 February 2026 | Government broadcaster and Gavi. One dose or two is reported differently: `confirm` |
| Adult vaccines: flu yearly, a tetanus booster every ten years, shingles from 50, pneumonia for older adults | Summaries of the physicians' 2026 consensus, not its text: `confirm` |
| Aadhaar biometrics must be updated at 5 and at 15 | UIDAI's own page. Today's fee: `confirm` (a free window was reported to end 30 September 2026) |
| A child's passport (under 15) lasts five years or until 18 | News reports of a September 2026 rule change: `confirm` |
| A health card for everyone aged 70 or more, up to Rs 5 lakh a year, whatever the income | News reports; the portal is named. State participation: `confirm` |
| The seniors' helpline 14567; the 2007 maintenance law | A government knowledge portal; the Act's text. Hours and state rules: `confirm` |
| Gratuity after five years; a fixed-term employee after one, from 21 November 2025 | Advisory firms and news, not the Code: `confirm` |
| The gas safety hose lasts five years | The official consumer guide. The inspection interval is unsettled: `confirm` |
| Private check-up packages cost roughly Rs 500 to Rs 5,000 | Lab listings; they vary by city: `confirm` |

**Not verified this round, and marked so in the file:** the full child vaccination table (the file tells the person to
use the card given at birth, not an app list), the girl-child savings account age limit, the school entry age, the
papers due at 18, the adult passport's term, the driving licence validity ages, the free-course platform's terms, and
every "common practice" interval (dentist, eyes, the checks from 40 and from 60). The Global lines are one country's
example or a general pointer; none is a rule.

## Screen (one action)

A proposal; nothing here is built.

- **Systems** shows the one loop furthest behind, chosen for the person (a hard date first, then risk × reach ÷ effort),
  with one button: its smallest step. The other loops show a calm state (running, resting, not started) and fold
  under "Later (n)".
- A loop that is not started shows example content to correct, not an empty form.
- A missed cue is recalled once, kindly, then waits for its next natural date.
- Each loop has "Add to calendar" from the one registry (`CALENDAR` in `guiding-map/ops.js`). The proposed ids are
  `ls-checkup`, `ls-flu`, `ls-family-health`, `ls-child`, `ls-parents`, `ls-partner`, `ls-ladder`, `ls-renewal`,
  `ls-learn`, `ls-home-month`, `ls-season`. An id is permanent once handed out: the brief that adds them also adds
  them to `tests/test38.js`.
- Off switch: each loop can be rested or turned off, and "I already do this" keeps only its dates.

## Test that proves it

- **Content:** `governance/levers.py check` fails a loop with a missing part, a missing persona case, a country-bound
  line with no `where`, a cited fact with no source, or a file past its review date (brief 1).
- **Per loop, in jsdom:** the cue reaches the calendar with a stable UID; the smallest step counts as done; a missed day
  is recalled once; a `confirm` line shows its label; Global mode shows no India fact (briefs 2 to 6).
- **For a person:** the persona audit plays the four cases on a phone: first win in two taps, no screen to read first.
- **Outcome:** `./securax progress` counts loops that ran this week. A loop nobody runs after a month is folded or cut.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one loop at a time, content shipped as data, ticks on the device, offline.
- **Next, when two adults share a home:** a row can be owned by another adult, who gets its cue (sync, already built).
- **Enterprise, when conditions call for it:** shared family loops with ownership and hand-over through the roles
  service (a parent's check-ups owned by two siblings); an employer's or a clinic's own loop loaded as an overlay; the
  facts watched like the savings levers (`scheme-watch`), so a changed rule labels its line by itself.

## Risks, and what holds them

- **A wrong medical or legal fact acted on.** Every unsettled fact has `confirm`; the builder rule above; a review date.
- **Health data on a device.** It stays on the device and in the encrypted backup; no loop sends it anywhere. A family
  calendar entry says "Check-up", never the condition.
- **Nagging.** One recall, then silence until the next natural date; every loop has an off switch.
- **One more list nobody opens.** Only one loop is ever in view; the measure is loops run, not loops listed.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
