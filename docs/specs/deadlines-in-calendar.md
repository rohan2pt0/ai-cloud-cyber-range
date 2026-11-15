# Spec: deadlines-in-calendar

Queue item `deadlines-in-calendar` in `governance/queue.json` · due 2026-11-26 · added 2026-11-12.

**The ask, as the queue holds it:** Owner, 2026-11-12: every deadline must reach the calendar by itself, not stay a promise on a screen; one countdown of all deadlines, the 80/20 way; a light focus timer used sparingly; fix such gaps everywhere

## Outcome for the person

No deadline is missed because it lived only on a screen: every one reaches the calendar by itself.

## Data

`datedItems()` as the one registry (career, renewals, commitments, Inbox due dates, goals), with stable ids and the device ledger for SEQUENCE.

## Screen (one action)

The Deadlines screen: the nearest deadline as the hero, one button, `Add all to my calendar`. The vital three below, the rest under `Later (n)`.

## Test that proves it

`test40.js` and a new test: every dated source appears once, UIDs are stable across edits, a done item goes out as CANCELLED.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A downloaded calendar file with stable UIDs.
- **Enterprise, when conditions call for it:** A subscribed calendar from the estate (`calendar-subscribe`), shared family and team calendars by role.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
