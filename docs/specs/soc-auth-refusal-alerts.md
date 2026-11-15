# Spec: soc-auth-refusal-alerts

Queue item `soc-auth-refusal-alerts` in `governance/queue.json` · due 2026-11-19 · added 2026-11-08.

**The ask, as the queue holds it:** SOC alerts for the three refused-caller rows the purple loop still names (forged key, privilege escalation, foreign-origin write)

## Outcome for the person

A forged key or a cross-site write is not only refused: someone is told.

## Data

A short hash of the offending key (never the key) on refusal events, correlated in triage.

## Screen (one action)

The SOC view: one alert with one action, `Open the incident`.

## Test that proves it

The three purple-loop rows leave the alert backlog; a test proves the key itself is never logged.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Alerts on one gateway.
- **Enterprise, when conditions call for it:** Correlation across nodes and export to an organisation's SIEM.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
