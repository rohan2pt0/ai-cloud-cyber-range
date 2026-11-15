# Spec: income-needs

Queue item `income-needs` in `governance/queue.json` · due 2026-12-06 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: from my facts and figures, tell me dynamically how much we must earn to sustain ourselves with inflation, how much to raise rent, which expenses to cut, with fixed and variable expenses identified by a system

## Outcome for the person

The household sees, in one number, what it must earn each month to stay whole as prices rise, and which one expense to cut first.

## Data

From the profile, loans and categorised bank messages: fixed costs, variable costs, the saving needed for the goals, an inflation rate the person can change. All derived; nothing new asked.

## Screen (one action)

One card on Money, `What we must earn`: the monthly take-home needed now and in five years, the gap to today, and one button, `Show the first thing to cut`.

## Test that proves it

A unit test of the arithmetic with fixed inputs (including zero income and no loans), and a jsdom test that every input is clamped with `saneNum` and the card never shows a negative or absurd rate.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One formula on the device with an India default for inflation, editable.
- **Enterprise, when conditions call for it:** Scenarios (a job loss, a second child, a move abroad) and regional price series from a watched source, shared with an advisor by consent.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
