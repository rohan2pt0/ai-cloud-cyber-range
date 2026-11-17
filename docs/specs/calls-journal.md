# Spec: calls-journal

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Slice 1 shipped (2026-11-17): the calls journal on the Plan tab, one tap to judge a call, calibration per confidence (test121). Next: calendar entries for each call, and a folded list of calls I got wrong with the lesson. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Queue item `calls-journal` in `governance/queue.json` · due 2026-11-24 · added 2026-11-17.

**The ask:** Take the best of LifeOS/TELOS and similar projects, 80/20, into the Life OS. First pick: a calls journal.
TELOS keeps predictions with a confidence and a standing list of "things I've been wrong about". We turn that into a loop.

## Outcome for the person

They learn how good their judgement really is, by area, without keeping a spreadsheet. Over-confident calls show up as a number, not a feeling.

## Data

`gm_calls` on the device: text, confidence (60, 70, 80 or 90%), check date (90 days ahead by default), outcome (yes, no or open),
an optional one-line lesson. At most 200 calls; the oldest finished ones drop first.

## Screen (one action)

A card on the Plan tab. When a call's date has passed, that call is the one open action: "Did it happen?" with Yes and No.
Otherwise the action is "Make a call". The calibration line reads "At 80% you were right 3 of 4". Everything else is folded under Later (n).

## Test that proves it

`guiding-map/tests/test121.js` (slice 1). Slice 2 adds a calendar entry for each call through `gmCalendarDated`, and a folded
"Calls I got wrong" list with the lesson from each.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one person, on the device, offline.
- **Enterprise, when conditions call for it:** a team's decision log (an investment committee or a risk committee) with Brier scores per
  person, built on the shared platform's roles and audit.
