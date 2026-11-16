# Spec: 360-audit-rounds

Queue item `360-audit-rounds` in `governance/queue.json` · due 2026-11-25 · added 2026-11-11.

**The ask, as the queue holds it:** Owner, 2026-11-11: critical flaws survived several kaizen rounds; run multi-level, granular fault-finding from every relevant angle (360) and fix what is found asap, in multiple rounds

## Outcome for the person

Critical flaws are found by us, from every angle, before a person meets them.

## Data

A round log: angle, method, findings, fix, the gate added. Findings that wait go to the queue.

## Screen (one action)

`./securax progress` shows one line: rounds run, flaws found, flaws still open.

## Test that proves it

Each fixed flaw gains a test or audit rule that would have caught it; the open count only goes down.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Rounds by hand with the real-browser audits.
- **Enterprise, when conditions call for it:** Continuous audits in CI with fuzzing and a bounty-style external review.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
