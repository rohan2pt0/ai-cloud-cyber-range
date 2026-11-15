# Spec: life-papers-first-import

Queue item `life-papers-first-import` in `governance/queue.json` · due 2026-10-22 · added 2026-10-22.

**The ask, as the queue holds it:** Make the Life OS and the estate ready today: the life workbooks and private documents read in, every open issue tracked, the vital few first, alarms set

## Outcome for the person

The owner's workbooks and papers are read in once, so the Life OS starts from real facts.

## Data

Workbooks and documents in `vault/life/` (never committed); secret columns dropped and reported.

## Screen (one action)

`./securax lifeos import`: one command that finds the files itself, then one line of what was read.

## Test that proves it

Importer tests with synthetic files; the PII gate; nothing from `vault/` in git.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A local import.
- **Enterprise, when conditions call for it:** Upload from the app (`life-papers-upload`) and scheduled re-reads.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
