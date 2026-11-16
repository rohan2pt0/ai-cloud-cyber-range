# Spec: profession-packs

Queue item `profession-packs` in `governance/queue.json` · due 2026-12-13 · added 2026-11-15.

**The ask, as the queue holds it:** (Lower priority after expert-council, which is what the owner meant.) Owner, 2026-11-15: make the Life OS really useful for every profession on his list (about 50: founders, investors, CEOs, bankers, surgeons and doctors, AI and software engineers, CISOs, scientists, lawyers, civil servants, policymakers, diplomats, …

## Outcome for the person

A person in a licensed or unusual working life never lets a licence, registration or cover lapse, and sees the tax route and next rung that usually fit their kind of work.

## Data

`guiding-map/levers/professions.json` (about ten archetypes: renewals, risks and cover, income shape, next rung, three systems). The person's archetype comes from the profile (asked once); renewal dates are their own.

### The ten packs (2026-11-16)

`corporate`, `government`, `clinical`, `licensed` (the first four), then `founders`, `finance`, `uniformed` (aviation, defence,
intelligence), `volatile` (athletes, performers, media, authors), `research` and `technical`.

What a builder must handle in packs 5 to 10:

- **`every` is plain words:** `year`, `quarter`, `event`, or a number of years (`3 years`, `6 to 12 months`). Show it as written;
  the person's own date drives the calendar entry, never a date worked out from `every`.
- **`confirm` on a renewal:** show it under the renewal as `Check: …`. It names what is not verified and who to ask.
- **`where` on a renewal:** a country tag. In Global mode show only renewals with no tag, plus the pack's `global` note.
- **`verified`, `review`, `sources` on a pack:** show `Checked on` the date; after `review`, say the pack is due a check.
- **The secrecy rule (`uniformed`):** nothing classified or operational belongs in the app; the pack says so in its risks.

## Screen (one action)

On Career: `Your working life` shows the next renewal due, with one button, `Add to calendar`. Everything else for the archetype folds under `Later (n)`.

## Test that proves it

A jsdom test: each archetype shows only its own pack; a renewal date entered once reaches `gmCalendarDated` with a stable UID; a person with two roles sees both packs merged without duplicates.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Ten archetypes as static data; dates typed once by the person.
- **Enterprise, when conditions call for it:** A firm's own pack (its licences, mandatory training, declarations) loaded as an overlay, with completion reported through roles and audit.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
