# Spec: friction-meter

Queue item `friction-meter` · due 2026-12-15 · added 2026-11-17.

**The ask:** Find out how much friction SecuRAX causes, the Life OS first, and keep it at its least, prioritised by risk, without
losing anything useful or critical. Features keep being added because the owner needs them, so the growth must never defeat the
purpose. Friction the owner meets in real use should be easy to report, and should come back fixed.

## Outcome for the person

They report a hard moment in one tap, wherever it happens, and later see it fixed. Each screen keeps one obvious action, however many
features the estate gains. The things they use rise to the top by themselves, and the things they never use fold away without being deleted.

## Measure: four numbers, each held by a check that only lets them go down

1. **Steps to done, per vital journey.** These are taps, plus fields typed, plus decisions, for the ten things people do most: tick a habit,
   capture a thought, judge a call, renew something, open today's one action, back up, ask the AI, log a CPE, add a goal, and find a paper. The persona audit drives
   each one in a real browser and writes the counts. A journey may not get longer.
2. **Choice load, per screen.** This is the number of controls that look like actions, above the first fold, on a phone (Hick's law). The budget is one primary action
   and at most five others. Everything beyond that goes under "Later (n)" or More. Things critical by consequence (lock, backup, a red risk) are exempt and pinned.
3. **Dead ends.** These are steps that ask the person to act with no place to act (`step-doers` found 248 such steps). Counted from the data, the count only goes down.
4. **Open frictions.** The register `governance/frictions.json` holds these. The count only goes down, and each entry has a date.

## Sense: what real use shows, measured on the device and never sent anywhere

- **One-tap report:** "Something was hard here" in the More menu saves the screen, the sheet that was open, the time and an
  optional line (typed or dictated). It is kept on the device and carried to the estate by the person's own sync. It never goes into this public repository as text.
  The navigator turns it into a written entry in the register.
- **Quiet signals, counts only:**
  - a sheet opened and closed with no action (abandonment);
  - three taps on the same spot within a second (rage tap);
  - switching back and forth between two tabs within ten seconds (searching);
  - a feature not opened in sixty days.
  These signals only feed the review below. They never become a nudge.

## Act: the bloat guard (features earn their place)

- **New features arrive folded.** They earn a place on the first screen by use: opened on three different days in two weeks.
- **Unused features sink.** After sixty days unused, a feature moves one level deeper. It is never removed, and search and More always find it.
- **Positions stay stable.** A door moves at most once a week, and only during the weekly review, so muscle memory is not broken.
- **Ranking:** frequency × severity (steps, abandonment) × consequence. Hard gates (security, recoverability, regulation) are never folded.

## The loop (build-the-system)

- **Cue:** the friction button in the moment, and the monthly review.
- **Smallest step:** one tap.
- **Reward:** "Fixed: what you reported on 17 Nov", shown in What's new.
- **Feedback:** the four numbers in `./securax progress`.
- **Constraint:** the owner's time to report. That is why it is one tap.

## Slices

1. The one-tap report and the list of reports in Ops (test126).
2. The quiet signals, counted on the device, with a monthly review card that names the top three.
3. The journey audit: steps to done for the ten journeys, a ratchet in CI.
4. Choice load per screen: a budget check in jsdom on every tab.
5. Promotion by use and sinking by disuse in the More menu, at the weekly review.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one person, counts on the device.
- **Enterprise, when conditions call for it:** anonymous friction counts across a tenant, a product owner's top frictions, journey budgets per role. The same counts are built on the shared platform's metering and consent.
