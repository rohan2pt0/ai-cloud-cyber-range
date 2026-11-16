# Spec: wheel-systems

Queue item `wheel-systems` in `governance/queue.json` · due 2026-12-05 · added 2026-11-12.

**The ask, as the queue holds it:** Owner, 2026-11-12: a working system, not theory, for every spoke of the Wheel of Life; first Fun: know every holiday and special day in advance, find the dates both partners are off with the least leave, plan where, how, what and the cost, and book early to save money; it must survive a job change; automate, least …

## Outcome for the person

Each spoke of the Wheel has a working system; first Fun: breaks are planned early, on the dates both partners are free, at a lower cost.

## Data

Work calendars per person (asked once, with periods when a job changes), public holidays as data with a `where` tag, the person's leave balance.

## Screen (one action)

Breaks planner: the best both-off window with the fewest leave days, one button, `Plan this break` (it goes to the calendar).

## Test that proves it

`test64.js` and a job-change case: windows are right across two employers; a pasted holiday list replaces the built-in one.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Built-in holidays and typed calendars on the device.
- **Enterprise, when conditions call for it:** Holiday packs per country kept current by a watch, and team leave planning through roles.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
