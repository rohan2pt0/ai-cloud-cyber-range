# Spec: setup-one-command

Queue item `setup-one-command` in `governance/queue.json` · due 2026-11-25 · added 2026-11-11.

**The ask, as the queue holds it:** Owner, 2026-11-11: make installation, configuration and setup of a laptop or node much easier; it is still tedious

## Outcome for the person

A new laptop or node is running after one command, with nothing to edit.

## Data

Install scripts, the machine's own facts (memory, OS), and the estate's generated secrets.

## Screen (one action)

The install ends with one line and one link by name: `Your estate is ready: open it`.

## Test that proves it

The `fresh_install` sandbox journey, plus a real Windows run by the owner reporting the first step that fails as printed.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One script per OS.
- **Enterprise, when conditions call for it:** Fleet enrolment: a node joins by a pairing scan and receives its configuration from the estate.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
