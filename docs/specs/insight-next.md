# Spec: insight-next

Queue item `insight-next` in `governance/queue.json` · due 2026-11-30 · added 2026-10-26.

**The ask, as the queue holds it:** Grow ./securax insight (doc 115) at the experience layer: (1) a one-tap Life OS card — the week's idea with a 'done' tick on its action, tapping a weak Wheel spoke or an OKR to re-aim; (2) let the person ADD their own ideas to the library (a book they read, a lesson learned), kept on-device; (3) surface the week's …

## Outcome for the person

The week's one idea reaches the person where they already look, and doing it is one tap.

## Data

The insight corpus and seen-ledger, the person's own added ideas and done ticks on the device (bounded, tier declared).

## Screen (one action)

A Life OS card: the idea, its action, one button, `Done`.

## Test that proves it

A jsdom test: one idea a week, never repeated, aims at the weakest spoke, a tick is stored and counted.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A card reading the existing engine's output.
- **Enterprise, when conditions call for it:** Shared libraries for a family or team, with ideas proposed from their own lessons.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
