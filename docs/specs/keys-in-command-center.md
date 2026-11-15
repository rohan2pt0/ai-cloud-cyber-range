# Spec: keys-in-command-center

Queue item `keys-in-command-center` in `governance/queue.json` · due 2026-12-02 · added 2026-11-11.

**The ask, as the queue holds it:** Paste the free AI provider keys in the Command Center instead of a terminal

## Outcome for the person

The person adds an AI provider key in the browser once, without a terminal or a file.

## Data

The key goes to one protected file (mode 0600), never echoed back; threat model first (same-origin only, foreign-origin refusal, write-only field).

## Screen (one action)

Command Center: one field and one button, `Save key`. The page then shows only `Saved` and `Replace`.

## Test that proves it

Gateway-style tests: a foreign Origin is refused, the key never appears in any response or log, the file mode is right.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A write-only page on the machine's own origin.
- **Enterprise, when conditions call for it:** Keys in an encrypted store (`ai-gap-g9`) handed out by the estate, per-team keys with rotation.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
