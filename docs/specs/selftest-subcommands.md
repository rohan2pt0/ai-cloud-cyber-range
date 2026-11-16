# Spec: selftest-subcommands

Queue item `selftest-subcommands` in `governance/queue.json` · due 2026-11-30 · added 2026-10-26.

**The ask, as the queue holds it:** Extend ./securax selftest (doc 117) from top-level commands to the common SUBCOMMANDS (e.g. tls status/render/reconcile, ai check/share, comply <map>, os check), so the proof covers the whole surface the user quoted (~123), not only the ~55 top-level commands. Add a weekly selftest routine that reports a green/red …

## Outcome for the person

The owner can trust that every command and common subcommand works as printed, checked weekly.

## Data

Each module's list of safe, read-only probe forms.

## Screen (one action)

`./securax progress` shows one line: `Selftest: n of n green` or the one that is red.

## Test that proves it

A test that only read-only forms run; a planted failing subcommand turns the line red.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Probes declared per module, run locally.
- **Enterprise, when conditions call for it:** The same probes as a health contract across nodes, reported to the door.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
