# Spec: readiness-browser

Queue item `readiness-browser` in `governance/queue.json` · due 2026-11-12 · added 2026-10-22.

**The ask, as the queue holds it:** Readiness in the browser: mark items, attach evidence, second-person sign-off, same files as the CLI

## Outcome for the person

A compliance lead marks items, attaches evidence and gets a second sign-off in the browser, without a terminal.

## Data

The same assessment files the CLI uses; evidence by reference; sign-offs with who and when.

## Screen (one action)

The one item that most lowers the score, with one button, `Mark and attach`.

## Test that proves it

A journey: browser and CLI read and write the same files; a second person is required for sign-off; a foreign origin is refused.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One user on one machine.
- **Enterprise, when conditions call for it:** Roles, segregation of duties and audit for a team, per tenant.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
