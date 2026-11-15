# Spec: discreet-mode

Queue item `discreet-mode` in `governance/queue.json` · due 2026-11-25 · added 2026-11-11.

**The ask, as the queue holds it:** Discreet mode for private families: a neutral app name and icon the family chooses, nothing revealing on the lock screen or in notifications, a quick privacy screen

## Outcome for the person

Nobody glancing at the phone learns what the app is or what it holds.

## Data

One setting (`~discreet`), a neutral name and icon chosen by the family, generic notification text.

## Screen (one action)

Settings: one switch, `Discreet mode`. A quick privacy screen is one tap from anywhere.

## Test that proves it

A test per app: with the setting on, the manifest name and icon are neutral and no notification carries content; a real-browser check of the installed app.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A build-time swap and a setting.
- **Enterprise, when conditions call for it:** Policy-set discreet mode for a household or office, with decoy-free neutral branding per edition.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
