# Spec: ai-gap-g3

Queue item `ai-gap-g3` in `governance/queue.json` · due 2026-11-19 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G3 (doc 105): Tool approval as a queue: the call waits for a person's yes from the Command Center or the phone

## Outcome for the person

A risky tool call by an AI agent waits for a person's yes, given from the Command Center or the phone.

## Data

The approval queue, single-use grants and the audit chain (already built).

## Screen (one action)

One waiting call at a time: what it will do, and two buttons, `Approve once` and `Refuse`.

## Test that proves it

Gateway tests: approval needs one-door sign-in, a grant works once, refusal and timeout are audited.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Approve from the CLI.
- **Enterprise, when conditions call for it:** Approval policies by role and risk, with two-person approval for the highest tier.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
