# Spec: estate-autostart

Queue item `estate-autostart` in `governance/queue.json` · due 2026-11-21 · added 2026-11-07.

**The ask, as the queue holds it:** Start the estate at sign-in on Windows and WSL, like a background daemon, so a restart needs no one

## Outcome for the person

After a restart the estate is simply there; nobody has to start it.

## Data

One scheduled task on Windows that runs `up` (or the safe mode on a small PC).

## Screen (one action)

`./securax autostart`: on, and `autostart off` to undo.

## Test that proves it

A script test of the task definition; the owner confirms after one real restart.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A sign-in task.
- **Enterprise, when conditions call for it:** A service per node managed by the fleet.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
