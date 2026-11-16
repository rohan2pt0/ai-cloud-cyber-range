# Spec: family-security-programme

Queue item `family-security-programme` in `governance/queue.json` · due 2026-12-09 · added 2026-11-11.

**The ask, as the queue holds it:** A family security programme inside the apps: five-minute lessons for each family member, family code words against deepfake and impersonation calls, and a yearly impersonation drill

## Outcome for the person

Each family member can spot an impersonation call and knows the family code word, proven by a yearly drill.

## Data

Five-minute lessons as data per language, the family's code word practice (never stored in clear), drill results as done or not.

## Screen (one action)

Today, once a week: one lesson with one button, `Start (5 min)`. The yearly drill has `Add to calendar`.

## Test that proves it

A jsdom test: one lesson in view, completion counted per member, the drill in the calendar registry with a permanent id; lesson content reviewed for safety.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Lessons on one device.
- **Enterprise, when conditions call for it:** Family or staff roll-up by role, lessons fed by `threat-intel-engine`, completion evidence for insurers.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
