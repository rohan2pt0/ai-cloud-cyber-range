# Spec: lens-future-senses

Queue item `lens-future-senses` in `governance/queue.json` · due 2026-12-31 · added 2026-10-23.

**The ask, as the queue holds it:** Grow the on-device lens (doc 104 section 7) into more senses, each a plug-in through gmLensRegister, keeping the no-upload promise: (a) a real on-device ML classifier behind gmLensRead when heuristics plateau; (b) ambient voice capture on a wearable turning spoken commitments into Inbox actions; (c) a …

## Outcome for the person

The app reads more of what the person already has (a photo, a spoken promise, two offers) and turns it into the next step, without uploading anything.

## Data

A lens is `{id, name, test, read}` registered with `gmLensRegister`; inputs stay on the device.

## Screen (one action)

After a share or a capture: the reading with one button, `Accept`.

## Test that proves it

`test35.js` per lens: fixtures in, expected reading out, and a network spy proving nothing leaves the device.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Heuristic lenses.
- **Enterprise, when conditions call for it:** An on-device model behind the same interface, and a paid scam lens with its own evidence.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
