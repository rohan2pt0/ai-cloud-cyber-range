# Spec: one-door-accounts-panel

Queue item `one-door-accounts-panel` in `governance/queue.json` · due 2026-12-12 · added 2026-11-08.

**The ask, as the queue holds it:** One Accounts panel on the Command Center door: what you are signed in to, connect and disconnect for each, read from governance/identity.json

## Outcome for the person

The person sees every account they are signed in to, in one place, and can disconnect any.

## Data

`governance/identity.json` as the source.

## Screen (one action)

The Accounts panel: one list; per service one button, `Disconnect`.

## Test that proves it

A test that the panel matches the registry and a revoke takes effect.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A read-only list.
- **Enterprise, when conditions call for it:** Organisation-wide access review and offboarding in one action.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
