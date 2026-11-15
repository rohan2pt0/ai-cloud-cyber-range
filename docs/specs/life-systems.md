# Spec: life-systems

Queue item `life-systems` in `governance/queue.json` · due 2026-12-20 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: build systems (not tips) for everything in the Life OS, using agentic AI, OSINT, open-source components and ready real-world templates (SEO, MarTech, FinTech and beyond), so they run in reality, not as a formality

## Outcome for the person

Each area of life (health, family, career, home, money, learning) runs as a loop that happens without willpower, so the person keeps it up in a real week and sees it counted.

## Data

One loop record per area: cue, smallest step, reward, environment change, review date, the one constraint. Facts that change (check-up schedules, scheme rules) come from a watched content file per area, as `scheme-watch` does for levers.

## Screen (one action)

The Systems screen shows the one loop that is furthest behind, with one button for its smallest step. Other loops show a quiet state (running, resting, not started).

## Test that proves it

Per area, a jsdom test that the cue reaches the calendar registry, the two-minute floor counts as done, and a missed day is recalled once and kindly. `progress` counts loops that ran this week.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One area at a time, templates shipped as data, ticks on the device.
- **Enterprise, when conditions call for it:** Shared family loops (a parent's check-ups owned by two siblings) on sync, with ownership and hand-over through the roles service.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
