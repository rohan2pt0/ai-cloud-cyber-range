# Kaizen round 1: the Life OS through a person's eyes (2026-11-24)

**How it was measured.** A throwaway Playwright script opened every tab in `TABS` (the five calm tabs, More and the rest)
on a 390 x 844 phone at 1x, in light and dark. The profile was fake and realistic: the test155 household (two earners,
a child, a short personal loan and a home loan), two goals with three key results, a let-out flat and three month-end
check-ins. For each tab it counted these things:
- tappable things above the fold and in total;
- primary-styled buttons;
- words above the fold and in total;
- boxes (bordered or filled, rounded);
- colours on state chips;
- form fields;
- the page height in screens;
- NaN, "undefined" or "example" in the text.

Dark mode gave the same counts as light. The table shows light, before → after (one number = unchanged).

## Before and after, every tab

| Tab | Buttons above fold / total | Primaries | Words above fold / total | Cards (above fold) | State colours | Fields | Screens | Flags |
|---|---|---|---|---|---|---|---|---|
| today | 12 → 16 / 34 → 30 | 1 | 108 → 94 / 304 → 274 | 14 → 13 (6) | 2 → 1 | 0 | 3.1 → 2.7 | - |
| inbox | 6 / 6 | 1 | 40 / 40 | 1 (1) | 0 | 2 | 1 | - |
| deadlines | 1 / 1 | 1 | 23 / 23 | 1 (1) | 0 | 0 | 1 | - |
| ask | 33 / 34 | 1 | 65 / 70 | 7 (7) | 2 | 1 | 1 | - |
| guide | 6 / 7 | 0 | 64 / 104 | 8 (6) | 0 | 1 | 1.5 | - |
| stack | 6 / 11 | 1 | 103 / 164 | 7 (3) | 1 | 0 | 1.9 | - |
| systems | 14 / 35 | 1 | 98 / 235 | 15 (2) | 0 | 0 | 3.4 | - |
| life | 3 / 27 | 0 | 101 / 883 | 14 (4) | 3 | 0 | 5 | - |
| breaks | 4 / 4 | 1 | 39 / 39 | 2 (2) | 0 | 0 | 1 | example |
| career | 10 / 42 | 0 | 152 / 878 | 13 (4) | 0 | 3 | 4.6 | - |
| prop | 13 → 7 / 19 → 21 | 1 | 127 → 149 / 539 → 385 | 7 → 6 (4 → 2) | 0 | 16 → 8 | 4.6 → 3.4 | - |
| ops | 16 / 45 | 0 | 134 / 349 | 33 (8) | 1 | 0 | 2.7 | - |
| map | 1 / 3 | 0 | 77 / 205 | 10 (3) | 1 | 0 | 2.3 | NaN → - |
| book | 6 / 11 | 0 | 90 / 148 | 13 (7) | 0 | 0 | 1.8 | - |
| all | 5 / 5 | 0 | 89 / 376 | 30 (9) | 1 | 0 | 3.6 | NaN → - |
| score | 2 / 2 | 0 | 98 / 98 | 6 (6) | 0 | 0 | 1 | NaN → - |
| plan | 7 / 16 | 0 | 88 / 320 | 12 (4) | 1 | 2 | 3.1 | - |
| growth | 1 / 12 | 0 | 67 / 343 | 14 (5) | 1 | 1 | 2.9 | - |
| money | 4 → 5 / 37 → 38 | 0 | 97 → 96 / 1034 → 993 | 22 (3 → 4) | 3 | 4 → 3 | 7.3 → 7 | example |
| risk | 3 / 28 | 0 | 69 / 735 | 16 (4) | 2 → 3 | 6 | 4.6 | - |
| okr | 9 / 31 → 32 | 0 | 98 → 97 / 211 → 177 | 10 → 9 (5) | 3 | 0 | 2.5 → 2.2 | example |
| wheel | 4 / 92 | 1 | 84 → 86 / 237 → 236 | 12 (4) | 2 | 0 | 3.2 → 3.1 | NaN → - |
| commit | 2 / 2 | 1 | 29 / 29 | 2 (2) | 0 | 4 | 1 | - |
| cal | 2 / 2 | 1 | 99 / 99 | 6 (6) | 0 | 0 | 1.1 | example |
| kids | 6 / 6 | 0 | 87 / 87 | 3 (3) | 1 | 0 | 1 | - |
| arch | 1 / 1 | 0 | 30 / 30 | 2 (2) | 0 | 0 | 1 | - |

Notes on the numbers:
- Today has more buttons above the fold (12 → 16) because a wrong red banner went away and the daily three, "Also today"
  and the energy taps moved up into view. That is the intended effect, not more clutter.
- Today now shows 1 state colour above the fold instead of 2, and no false red.
- Property now shows the verdict in the first screen; its 8 inputs fold once they are filled.
- Words on Goals fall by 34 (211 → 177).
- Money barely moved. It is still 7 screens long, and it is the first open item below.
- No page errors in either theme, before or after. The NaN on four tabs is gone.

## Top 25 findings, ranked by friction x reach / effort

| # | Where | What a person feels | Fix | Effort | State |
|---|---|---|---|---|---|
| 1 | Today, Shield | "Buffer 3.5m" tile, then a red "Buffer: 2.5 months" under it. Which is true? | Warning signs read the one money model | S | fixed |
| 2 | Pillars, Scorecard, Wheel, Map | "Financial independence NaN%": the app looks broken | A missing net worth counts as 0 | S | fixed |
| 3 | Today tiles | Red "needs care" on Stack for not having started: guilt on day one | 0% shows a calm "start" tile | S | fixed |
| 4 | Today, one question | Asked for bank balance already given in the profile | Profile savings answer it | S | fixed |
| 5 | Today | Five big answer buttons above "Your next step, most important" | The next step comes first | S | fixed |
| 6 | Money, budget bands | 21% fixed bills drawn as a red bar, although it is fine | Fixed = ceiling, saving = floor | S | fixed |
| 7 | Money, what we must earn | "Rs" beside "₹" on one screen | ₹ everywhere | S | fixed |
| 8 | Property | A 45-word index-fund lecture first, a 120-word tax note last | One outcome line + "Why?" folds | S | fixed |
| 9 | Property | The verdict sat under 16 fields | Verdict first, inputs fold once filled | M | fixed |
| 10 | Goals, Wheel | Gold frame and three buttons every day, even when done | Calm once done; calendar is a link | S | fixed |
| 11 | Money | An empty card form high on Money | One folded line until used | S | fixed |
| 12 | Money, savings levers | A 70-word paragraph before the steps | First sentence + "Why?" | S | fixed |
| 13 | Goals | A pre-mortem paragraph under every visit | One quiet line opens it | S | fixed |
| 14 | Life map | "My numbers" and "Your numbers" both ask income, net worth, emergency fund | One numbers card | M | open |
| 15 | Money | 7 screens; "Go to step 2" points to the bottom | Steps after the hero, rest folded | M | open |
| 16 | Money, two of you | 18 rows, mostly dashes | Show filled rows, fold blanks | M | open |
| 17 | Systems | Nine yes/no questions at once | One at a time | M | open |
| 18 | Property | Green "+1,000/mo" title over a "Weak" verdict | Title carries the verdict | S | open |
| 19 | Today tiles | Net worth 44% of an age benchmark red every day | Owner decision: amber unless falling | S | open |
| 20 | Ask | Primary "Ask" while the laptop is off | Lead with the status | S | open |
| 21 | Ask | 26 advisor chips, 33 taps above the fold | Five in view, rest under More | M | open |
| 22 | Career | 152 words above the fold | Package number + one action first | M | open |
| 23 | Ops | Theme chooser first, 33 boxes | Lock and rituals first | M | open |
| 24 | Money levers (content) | Lever text still says "Rs" | Switch the GM_LEVERS source to ₹ | S | open |
| 25 | Pillars | 30 boxes repeating "Plan steps: 0% ticked · Not started" | Badge only once started | M | open |

Each is an entry in `governance/frictions.json` (ids `kz1-*`): 13 are fixed, and 12 are open with a due date of 2026-12-20.

Repeated sentences across tabs (before):
- "Move a fixed amount into the emergency fund…" appeared on Today and on Shield. On Today it now shows only when the
  buffer really is red.
- "Your next step, most important" and its sentence appear on both Today and Stack. That is by design: they are the
  same one open action.

## Proof (2026-11-24)

- `npm test` in guiding-map: exit 0. On one run test15 (sync) failed while the UI audit ran beside it. It passes on its
  own, on main and here, and passed in the full run that followed. It is the known fixed-250 ms flake in LESSONS.
- `python3 guiding-map/tests/ui_audit.py OUT`: exit 0, 0 contrast failures, 0 UI-rule breaks.
- `device_audit.py`: PASS, 9 devices x 5 views, 0 issues. It ran against the preinstalled Chromium: this container's
  Playwright build did not match the default launch.
