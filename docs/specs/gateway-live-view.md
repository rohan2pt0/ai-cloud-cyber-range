# Spec: gateway-live-view

Queue item `gateway-live-view` in `governance/queue.json` · due 2026-11-28 · added 2026-11-07.

**The ask, as the queue holds it:** A live terminal view of the AI gateway: which model answered, the day's allowance left, and a log of recent calls (the good idea in the Antiglaude TUI)

## Outcome for the person

The owner watches which model answered, what allowance is left and recent calls, live.

## Data

The gateway's audit chain and counters; read-only, no new network call.

## Screen (one action)

`./securax gateway tui`: one screen.

## Test that proves it

A test that the view only reads and shows no prompt text or key.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A terminal view.
- **Enterprise, when conditions call for it:** A cockpit panel with history and alerts.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
