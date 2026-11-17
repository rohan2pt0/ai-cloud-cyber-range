# Spec: friction-meter

Queue item `friction-meter` · due 2026-12-15 · added 2026-11-17.

**The ask:** Find out how much friction SecuRAX causes, the Life OS first, and keep it at its least, prioritised by risk, without
losing anything useful or critical. Features keep being added because the owner needs them, so the growth must never defeat the
purpose. Friction the owner meets in real use should be easy to report, and should come back fixed.

## Outcome for the person

They never have to report anything: the app notices what is hard and what goes unused, and the hard parts come back fixed. Each screen keeps one obvious action, however many
features the estate gains. The things they use rise to the top by themselves, and the things they never use fold away without being deleted.

## Measure: four numbers, each held by a check that only lets them go down

1. **Steps to done, per vital journey.** These are taps, plus fields typed, plus decisions, for the ten things people do most: tick a habit,
   capture a thought, judge a call, renew something, open today's one action, back up, ask the AI, log a CPE, add a goal, and find a paper. The persona audit drives
   each one in a real browser and writes the counts. A journey may not get longer.
2. **Choice load, per screen.** This is the number of controls that look like actions, above the first fold, on a phone (Hick's law). The budget is one primary action
   and at most five others. Everything beyond that goes under "Later (n)" or More. Things critical by consequence (lock, backup, a red risk) are exempt and pinned.
3. **Dead ends.** These are steps that ask the person to act with no place to act (`step-doers` found 248 such steps). Counted from the data, the count only goes down.
4. **Open frictions.** The register `governance/frictions.json` holds these. The count only goes down, and each entry has a date.

## Sense: automatic, on the device, nothing for the person to do (owner 2026-11-17: "don't add one more task for me")

- **Usage ledger.** It records each tab, system sheet and card (`data-feat`) the person opens, and on which days. It keeps up to 30 days per feature and 300 features.
  It stays on the device, carried only by the person's own sync and backups.
- **Friction detected, not reported.** These are counted on the device:
  - a sheet opened and closed with no action;
  - three taps on one spot within a second;
  - switching back and forth between two tabs within ten seconds;
  - one field retyped three times;
  - a search with no result;
  - an error caught on a screen.
  A monthly review card names the top three. The navigator reads the same counts in the estate's copy and fixes them. Nobody is asked to file anything.
- **Resting.** A feature unused for 45 days (and not new in its first 14 days) folds into "Resting (n)" at the bottom of More.
  It comes back at once when it is used, searched for or woken. Pinned and never resting: Today, the lock, backups, a red risk, and anything due.
- **Woken by need (just in time).** A resting feature wakes by itself when the person's own data says it is needed:
  - a renewal inside its warning days wakes Renewals;
  - a birthday in the next 7 days wakes the friendships system;
  - January to March wakes the tax levers (India);
  - a trip date wakes the passport;
  - salary day wakes the money date.
- **Order by habit (frecency).** More doors and "Later" lists are ranked by how often and how recently they are used. They move at most once a week, so muscle memory holds.
- **Defaults learned.** The option chosen most often becomes the preselected one (a call's confidence, a renewal template).

## The loop (build-the-system)

- **Cue:** none needed; the app senses use and friction by itself.
- **Smallest step:** zero; nothing to do.
- **Reward:** "Fixed: what you reported on 17 Nov", shown in What's new.
- **Feedback:** the four numbers in `./securax progress`.
- **Constraint:** the owner's attention. That is why nothing is asked of them.

## Slices

1. The usage ledger (`gm_use`, test128).
2. Resting in More: frecency order, rest after 45 days, pinned exemptions, and one-tap return.
3. Woken by need: renewals, birthdays, tax season, trips, salary day.
4. Friction detected: the six signals counted on the device, and a monthly top-three card.
5. Steps to done and choice load as CI ratchets (the journey audit and a per-screen budget).

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one person, counts on the device.
- **Enterprise, when conditions call for it:** anonymous friction counts across a tenant, a product owner's top frictions, journey budgets per role. The same counts are built on the shared platform's metering and consent.
