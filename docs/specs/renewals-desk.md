# Spec: renewals-desk

Queue item `renewals-desk` · due 2026-12-12 · added 2026-11-17.

**The ask:** Keeping several global certifications (annual fees, CPE cycles, an exam voucher not yet booked) and every
expiring paper (insurance, PUC, driving licence, policies) costs time, money and worry. Build a frictionless system that
automates most of it, with agentic AI where it helps.

## Outcome for the person

Nothing lapses by surprise. Each thing that expires is typed once. The estate warns early enough to act calmly, puts the dates
in the calendar, and rolls each one forward when it is renewed. One CPE log feeds every certification.

## The loop (build-the-system)

- **Cue:** one calm line on Today when the most costly item enters its warning window, plus the calendar with its own alarm.
- **Smallest step:** pick a template, type one date, and you are done. "Renewed" is one tap, and it moves the date forward by itself.
- **Visible reward:** "All 9 renewals current" on the Risk tab, and the CPE ring per certification ("CISSP 64 of 120, on pace").
- **Environment:** templates with the rhythm, warning days, cost of a lapse, steps and official portal already filled in.
- **Feedback:** the monthly review shows what was renewed on time, and what nearly slipped.
- **Constraint:** remembering. The estate does the remembering.

## Slices

1. The desk on the Risk tab: add from a template with one date; sorted by urgency (lapse cost first, then date); one open action; "Renewed" rolls forward (test124).
2. The calendar and Today: each item joins the existing `renewals` calendar group (permanent uid `rn-<id>`, SEQUENCE raised on change); one calm line on Today.
3. One CPE log: an activity is logged once with hours, date and proof line, and is credited to every certification it fits; the pace per certification is shown.
4. **The agent (strong tier, human-in-command):** the estate's local model reads what already arrives (bank and insurer e-mails, SMS, the papers it reads) and *proposes* updates: "Health policy renewed until 14 Mar 2028: update?", "ISC2 invoice due 31 Jan". One tap accepts (the `gmReadAccept` pattern). It also suggests free CPE events for the cycle that is behind, and drafts the CPE entry from a webinar's confirmation e-mail. It never pays, books or submits anything by itself.

## Data

`gm_renewals` on the device: id, template, name, date, every, lead, notes, history of renewals. Content in `guiding-map/levers/renewals.json`, with `verified`, `confidence` and a `check` line on every template. Bounded at 200 items.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one person, templates, on the device.
- **Enterprise, when conditions call for it:** a team's credential register (who holds what, which fee falls due, CPE pace per person) for a CISO's compliance evidence, built on the shared roles and audit.
