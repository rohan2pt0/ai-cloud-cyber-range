# Spec: zero-friction-audit

Queue item `zero-friction-audit` in `governance/queue.json` · due 2026-12-15 · added 2026-10-23.

**The ask, as the queue holds it:** Make every experience-layer feature usable by the laziest procrastinator: a one-tap, zero-input default path on every capture and decision surface, and nothing that nags or guilts. Reverse-engineered friction fixes, newest first: (1) DONE in the Inbox — one-tap lens Accept + guilt-free Later (test35). Still to do: (2) …

## Outcome for the person

The person who puts things off still gets value: every capture and decision has a one-tap default, and nothing nags.

## Data

A list of capture and decision surfaces, each with its default path; entries in `governance/frictions.json`.

## Screen (one action)

On each surface: the suggested answer with one button, `Accept`; manual controls folded.

## Test that proves it

Per surface, a jsdom test that one tap completes it with no typing, and a copy check that no guilt or urgency wording appears.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Defaults added surface by surface.
- **Enterprise, when conditions call for it:** Defaults learned on the device from the person's past choices, with an off switch.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
