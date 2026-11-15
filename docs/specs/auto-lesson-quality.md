# Spec: auto-lesson-quality

Queue item `auto-lesson-quality` in `governance/queue.json` · due 2026-11-26 · added 2026-11-12.

**The ask, as the queue holds it:** Found 2026-11-12: autobuild writes a lesson by itself when a red attempt turns green, but some are only the task title and the failure type, with no what-to-do-instead; such a line crowded a useful lesson out of the brief (test_brief failed)

## Outcome for the person

Every agent reads lessons that say what to do instead, so the same failure is not repeated and briefs stay short.

## Data

`LESSONS.md` and the autobuild run log.

## Screen (one action)

For the builder: `./securax lessons` lists only well-formed lessons; one line per lesson.

## Test that proves it

A unit test: an auto-lesson without a cause and a fix (no arrow) is refused and logged to the run instead; `test_brief` stays green.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A shape check in the autobuild loop.
- **Enterprise, when conditions call for it:** Lessons as structured records (cause, fix, check), deduplicated and replayed as evals (`failures-become-evals`).

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
