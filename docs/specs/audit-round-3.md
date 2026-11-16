# Spec: audit-round-3

Queue item `audit-round-3` in `governance/queue.json` · due 2026-11-27 · added 2026-11-11.

**The ask, as the queue holds it:** Audit round 3, real-day use: one week of daily use, every annoyance in the friction log (Inbox notes starting 'friction:'), the top five fixed (doc 134)

## Outcome for the person

After a week of real use the daily routine takes under ten minutes and the five worst annoyances are gone.

## Data

Inbox notes starting `friction:`, copied into `governance/frictions.json` in our own words.

## Screen (one action)

In the Inbox: one button, `Note a friction`, that prefills the prefix. Nothing else.

## Test that proves it

The open count in `frictions.json` goes down by five; a timed run of the daily routine in the device audit stays under the budget.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Notes by hand for a week, then five fixes.
- **Enterprise, when conditions call for it:** Opt-in, on-device friction signals (a screen left unfinished, a repeated correction) summed without content, feeding the same register.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
