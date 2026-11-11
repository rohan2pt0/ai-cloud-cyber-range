# 135. Systems that deliver: one shelf, one loop, the vital few methods

**Status:** decided 2026-11-11 (owner's ask). Build after the feature freeze (doc 134), in small slices.

The owner asked for PARA and the best methods from great firms, consultancies and failed products, used across SecuRAX
and everything it ships. Diagnosis first: the estate already carries most of the methods. The Life OS glossary explains
62 of them (80/20, inversion, OKRs, WOOP, Eisenhower, RAPID, after-action review, Three Horizons, never miss twice), and
the apps already have an Inbox, Goals, Pillars, Guides and an Archive. What is missing is **one structure** over it all
and **one loop** through it. Today the More menu is a flat grid of twenty tiles, and a person has to know what each holds.
So this document adds three things, and is careful not to add a fourth.

## 1. One shelf: PARA, everywhere

PARA (Tiago Forte) sorts everything by how actionable it is, not by topic. It works because a person only ever asks one
question: "where does this go?" Every SecuRAX app uses the same four shelves, plus the Inbox in front of them.

| Shelf | What it holds | Life OS today | Kit apps (Vantage and others) |
|---|---|---|---|
| **Inbox** | anything captured, not yet decided | Inbox | Inbox |
| **Projects** | an outcome with an end date | Goals and quarterly goals, Commit, career moves, renewals | Goals, open risks with a due date |
| **Areas** | a standard kept for good, no end date | Pillars, Money, Health calendar, Kids, Property, Shield, Wheel | Registers, Scorecard, Rhythm |
| **Resources** | reference you may need | Guides, Playbook, Map, the glossary | Playbooks, Feeds |
| **Archive** | done, paused or no longer relevant | Archive | (to add: done and closed items) |

Rules that come with it:
- Every captured item leaves the Inbox to exactly one shelf. The default is offered, one tap (`best-default`).
- A project without an end date is an area in disguise; the app says so kindly.
- Nothing is deleted when it is finished: it moves to the Archive, and comes back in one tap.
- The More menu groups its tiles under these four headings, in this order.

## 2. One loop: capture, clarify, organise, review, act

The loop is GTD's (David Allen), with Forte's "distil and express" for knowledge:

1. **Capture** in one tap, anywhere (Inbox, the share sheet, a photo of a paper).
2. **Clarify** each item once: is it actionable, and what is the next step?
3. **Organise** it to a shelf (section 1).
4. **Review** on a rhythm that lives in the calendar: the daily one open action, the **Sunday Pulse** (already in the
   calendar registry), the monthly Money Date, the quarterly check-in.
5. **Act** on the one open action (`one-open-action`).
6. **Distil and express**: what a review teaches becomes a line in a playbook, a lesson or a friction, so the next loop
   is easier. This is the estate's own antifragility.

## 3. The vital few methods, each where its decision is made

Methods are useful only at the moment of a decision. Each sits in one place, not in a library to browse.

| Decision | Method | Where it lives |
|---|---|---|
| What to do next | the Stack's lowest layer, then risk × reach ÷ effort (80/20) | Today's one open action |
| Is this goal well formed | Outcome, obstacle, plan (WOOP); a measurable result (OKR) | Goals |
| Which problem first | MECE issue tree, hypothesis first, "answer first" (McKinsey, BCG, Bain) | Ask, the decision helper |
| How to say it | Pyramid principle, SCQA: the answer, then why | Board pack, briefing, weekly message |
| Is this decision reversible | one-way and two-way doors (Amazon) | `friction-by-consequence` |
| Is this the real need | working backwards: the person's outcome first (Amazon) | The three questions in every PR |
| What could kill it | pre-mortem and inversion (Klein, Munger) | Shield, threat models |
| What did we learn | after-action review (US Army), blameless | Lessons, frictions, the quarterly check-in |
| Is it getting better | small, daily improvement (Toyota kaizen); stop the line on a defect (jidoka); make the problem visible (andon) | The friction log, red CI stops a merge, one open action |
| Where effort goes | Three Horizons (now, 1-2 years, 3-5 years) | Optionality layer |

## 4. What great operators do, and what we take

- **Toyota and Danaher (the business-system conglomerates):** standard work, visual management, kaizen every day. We take:
  the friction log, the shared UI rules and the audits that run on every change.
- **Amazon:** working backwards, written narratives instead of slides, two-way doors decided fast. We take: outcome first,
  the decision record, speed on reversible choices and care on irreversible ones.
- **Berkshire Hathaway:** decentralise, keep few rules, hold managers to outcomes. We take: few principles that every app
  inherits, not many rules per app.
- **The strategy consultancies:** MECE, hypothesis first, 80/20, the "so what". We take: the answer first, then the
  evidence, on every screen and every report.

## 5. Products that were too good and still failed, and our guard

| Pattern | Example | The critical mistake | Our guard |
|---|---|---|---|
| Feature bloat buries the core | Evernote | Added chat, hardware and a marketplace; the note app slowed and lost focus | The feature freeze (doc 134), `one-open-action`, `calm`, this doc's "not to do" list |
| No clear job for a person | Google+, Google Wave | Built for the company's strategy, not a need people had | The three questions in every PR (`outcomes-declared`) |
| A great product with no real moment of use | Quibi | Content for a moment people did not have | `human-first`: the moment and the mood first |
| Missed the platform shift | Kodak, Nokia, BlackBerry | Protected the old core while the market moved | `amoeba` and `evolution.json`: grow the next form when conditions call for it |
| Numbers that were not true | Theranos; Wirecard | A green light with nothing behind it | Never fake a green; the invented-numbers fix (2026-11-11); evidence for every threat |
| Bought and switched off | Sunrise, Wunderlist | Users lost their tool and their data | Export always free, FSL licence to MIT, data on the person's device |
| Growth on debt and complexity | GE; Jet Airways | Too many units and too much leverage to steer | A modular monolith, no recurring cost lock-in, `pareto` |

## 6. Not to do (the Evernote guard)

- No new tab, app or method without retiring or folding an old one.
- No method shown without a decision it serves.
- No second place for the same fact (`ask-by-frequency`).
- No hook that works against the person (`human-first`, rule 4).

## 7. The 80/20 slices, after the freeze

1. **More grouped by PARA**: four headings over the existing tiles, no new screen (local tier).
2. **Clarify in the Inbox**: each item gets a one-tap default shelf (Project, Area, Resource, Archive) (local tier).
3. **Archive in the kit apps**: done and closed items move there and come back in one tap (local tier).
4. **The Sunday Pulse as the loop's review**: it walks the Inbox, the projects past their date and the one open action (local tier).
5. **Answer first** in the board pack and the weekly briefing (opencode tier).

Each slice is held by a test and by `para` in `governance/principles.json`.
