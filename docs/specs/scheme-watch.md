# Spec: scheme-watch

Queue item `scheme-watch` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: keep the schemes and tax rules current by themselves, intelligently: they change on known dates (the Union Budget, state budgets, the quarterly small-savings reset, the new tax year), so fetch from standard official sources then and update without the person needing to know, using OSINT and agentic …

## Outcome for the person

Schemes and tax rules shown to the person are current without the person tracking budgets or circulars; a stale one is labelled, never silently wrong.

## Data

`guiding-map/levers/watch.json` (hash and date per official source), an event calendar of when rules change, and the allow-list of hosts taken from the content itself. Fetched pages are data only (threat model `scheme-watch`).

## Screen (one action)

On a lever whose source changed: one line, `Being re-checked since <date>`, and one button, `Open the official page`. For the owner, one PR per change to review.

## Test that proves it

`governance/tests/test_levers.py`: only allow-listed hosts are fetched, redirects elsewhere are refused, a changed hash opens a review and never edits content by itself.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A scheduled workflow that compares hashes and opens a PR for a human.
- **Enterprise, when conditions call for it:** A signed content feed per country with a named reviewer, a published change log, and tenants choosing which packs they trust.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
