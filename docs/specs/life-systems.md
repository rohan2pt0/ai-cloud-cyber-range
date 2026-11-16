# Spec: life-systems

Queue item `life-systems` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: build systems (not tips) for everything in the Life OS, using
agentic AI, OSINT, open-source components and ready real-world templates (SEO, MarTech, FinTech and beyond), so they
run in reality, not as a formality.

This page replaces the one-page plan of 2026-11-15 with the content pass of 2026-11-16: the loops themselves now exist
as data in `guiding-map/levers/life-systems.json`, and six briefs to build the screen are in
[life-systems-briefs.md](life-systems-briefs.md). Money has its own files (`levers.json`, `landlord.json`).

## Outcome for the person

Each area of life (health, family, career, learning, home) runs as a loop that happens without willpower, so the
person keeps it up in a real week and sees it counted. This week, that means: the family's check-ups and doses have
dates, a parent over 70 has the cover they are owed, one paper that would have lapsed has a cue, and the home is ready
before the season, each from one tap.

## The three questions (north star)

1. **What gets better this week?** One health, family or home task that was "someday" gets a date and an owner.
2. **Where will they see it?** One Systems card on Today (the loop furthest behind), the calendar, and
   `./securax progress` (loops that ran this week).
3. **How does it draw them further in?** Each loop reads facts the profile already holds (birth dates, family, papers)
   and ends on one next step; nothing is asked twice (`ask-by-frequency`).

## The loops (content, written 2026-11-16)

Every loop has the same six parts. The one constraint is the part to fix first; everything else is 80/20.

| Area | Loop (`id`) | Cue | Smallest step | Its one constraint |
|---|---|---|---|---|
| Health | `health-checkups` | The birthday month | One tap: book the check-up | Booking: end on a slot, not a reminder |
| Health | `health-vaccines` | Each dose's due date; flu season | One tap: done today | Not knowing what is due |
| Health | `health-family-calendar` | First Sunday of the month | Book or tick the soonest item | One named owner per item |
| Family | `family-children` | The child's birthday month | Start this year's one milestone | Lead time: windows close |
| Family | `family-parents` | A weekly call slot; one month a year | The call, with one question | Agreement between siblings |
| Family | `family-partner` | The same slot every week | Ten minutes, one question | Protected time |
| Career | `career-ladder` | Last Friday of the quarter | One line: this quarter's result | Evidence, written while fresh |
| Career | `career-offers` | An offer arrives (on demand) | Two numbers | Time pressure: buy 48 hours |
| Career | `career-renewals` | Each paper's own expiry date | One tap: start the renewal | The date must be in the estate |
| Learning | `learning-skill-quarter` | The same 25 minutes on set days | Ten minutes of practice | Choosing one skill |
| Home | `home-monthly-reset` | First Saturday of the month | A five-minute walk with the phone | Starting |
| Home | `home-seasonal` | Six weeks before each season | Send one ready message | Lead time: trades are busy in season |

Each loop also carries its reward, its environment change and its review rhythm; these are in the data file.

## Four kinds of people

A loop that only works for the disciplined helps the people who need it least. Each loop says how it bends for four
cases; the rules that hold across all twelve are:

| Persona | What gets in the way | The rule the screen follows |
|---|---|---|
| The distracted | Too many things compete | One cue on a screen they already open; one tap; a miss is recalled once, then the cue moves |
| The person with ADHD | A far date does not pull; shame ends habits | The step is done now, in this screen; reward at once; no streak to lose, only "times done" |
| The novice | Does not know what good looks like | A filled-in default to correct; one line of why; the floor is enough |
| The expert | Already has a routine | Import in one pass; sources and the full table one tap down; every interval can change |

The persona is never asked as a label. The screen starts in the novice form (filled in, one tap), and adapts from
behaviour: two misses move the cue (the distracted and ADHD rules); "show the detail" opens the expert form and stays
open. A person may also choose "shorter steps" in settings. Nothing is called ADHD on screen.

## Facts, and how sure we are

Verified by web search on 2026-11-16; review by 2027-05-16. Each fact in the data file carries its sources. India
first; Global rows say what to do where no country is assumed.

**Confirmed from official or primary pages**

- India's programme for non-communicable diseases screens adults aged 30 and over for blood pressure, blood sugar and
  three cancers (mouth, breast, cervix), free at government centres.
- Girls aged 14 get one free HPV vaccine dose under the national programme (since February 2026).
- Everyone aged 70 or over can get the Ayushman Vay Vandana card (hospital cover up to Rs 5 lakh a year), whatever
  their income; helpline 14555.
- Elderline (14567) is the national helpline for senior citizens, 8 am to 8 pm.
- A child's Aadhaar biometrics must be updated at 5 and at 15.
- A gas cylinder is retested 10 years after it is made, then every five years.

**Carried with a `confirm` line (shown as "check before you act")**

- The yearly and five-yearly screening intervals: from a ministry training module, not the guideline's own table.
- The check-up tax deduction (Rs 5,000, old regime): the section number under the Income-tax Act, 2025 and its limits
  were not found in an official text.
- Adult vaccines (flu yearly, tetanus every 10 years, shingles from 50, pneumococcal from 65): secondary summaries of
  the physicians' 2024 consensus, not fully consistent.
- The children's dose-by-dose schedule: not confirmed from an official page, so the file holds no dates for it.
- Whether the Aadhaar update for children is still free after 30 September 2026.
- Private check-up prices (roughly Rs 500 to Rs 5,000): from labs' own pages.
- The gas tube's life (sources say one to five years), a minor's passport validity, the driving licence's renewal
  rule and each state's Class 1 entry age: not verified.
- The Global screening rows: United States recommendations read from secondary summaries; the task force was
  reconstituted in 2026 and several recommendations are being revised.

The file is not medical advice and says so; every health loop ends on "a doctor decides".

## Data

`guiding-map/levers/life-systems.json`: `about`, `version`, `verified`, `review`, four `personas`, and twelve
`systems`. Each system has `id`, `area`, `where`, `title`, `outcome`, a `loop` (cue, smallestStep, reward,
environment, review, constraint), the four `personas` cases, `facts` (each with `t`, `where`, `sources` and, when
unsure, `confirm`), and where useful a `schedule`, `milestones`, `seasons`, `checklist` or a ready `template`.

What the person adds is small and stays on the device: a tick with its date per loop, and the dates of what is
already done. Limit: one record per loop per person, the last 36 ticks each (doc 80, the device tier). Dates that
repeat come from the calendar registry (`in-the-calendar`); the eleven item ids proposed in the data file become
permanent only when a brief adds them to `CALENDAR` in `ops.js`. Dated papers follow `gmCalendarDated`.

## Screen (one action)

The Systems card shows the one loop that is furthest behind, with one button for its smallest step
(`one-open-action`). The other loops fold under "Later (n)" with a quiet state: running, resting or not started.
Order: a health or safety loop that is overdue first, then by how late. A guest sees example data to correct. A fact
past its review date, or one with a `confirm` line, is labelled "check before you act" with the place to check.

## 360 review

- **Person:** a tired parent on a Sunday evening; one card, one tap, done in under a minute; no guilt after a miss.
- **First principles:** the need is that the thing happens, not that it is tracked; so every loop ends on a booking,
  a message sent or a tick, never on a list to read.
- **Whole system:** reads the profile, Life Papers and the profession packs; writes ticks and calendar items only.
  No new sign-in, no network call, no new dependency.
- **Craft:** the empty state (no birth dates yet) offers one field, not a form; offline works; both themes.
- **Proof:** the briefs' jsdom tests; `progress` counts loops that ran this week.
- **Ethics:** health nudges invite, never frighten; no fake urgency; every loop has an off switch.
- **System:** the binding constraint across all twelve is the first booking; briefs 2 and 3 attack it.

## Enterprise lenses

- **Single point of failure:** content is a file in the repository; a damaged or missing file must leave the card
  hidden, not the page broken (brief 1 tests it).
- **Friction:** no sign-in; no second form for a fact the profile holds.
- **Security and privacy:** health and family facts are the most private data in the estate. They stay on the device,
  go through the existing lock and discreet mode, and are never sent to a hosted model. Sync of family loops crosses
  a trust boundary, so it needs a threat model before it is built (autopilot task 7); not in these briefs.
- **Operate:** content has a review date; a file past it is listed by a check (brief 6) so it cannot go stale unseen.

## Test that proves it

Per area, a jsdom test that the cue reaches the calendar registry, the two-minute floor counts as done, and a missed
day is recalled once and kindly. `progress` counts loops that ran this week.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One area at a time, templates shipped as data, ticks on the device.
- **Enterprise, when conditions call for it:** Shared family loops (a parent's check-ups owned by two siblings) on
  sync, with ownership and hand-over through the roles service; an employer's wellbeing edition reads counts only,
  never a person's health facts.

## What waits

- The children's national vaccine schedule as dated data: after it is confirmed from the ministry's own page.
- State-by-state Class 1 ages and licence rules: with the state schemes of autopilot task 3.
- A source watch for this file (as `scheme-watch` does for levers): after brief 6.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
