# Spec: one-door-drive-consent

Queue item `one-door-drive-consent` in `governance/queue.json` · due 2026-12-19 · added 2026-11-08.

**The ask, as the queue holds it:** Google Drive sync for the Life OS, asked for only when turned on (the counterpart of OneDrive sync), with the narrowest permission

## Outcome for the person

A person who uses Google can sync the Life OS to their own Drive with one consent tap.

## Data

An OIDC code flow with PKCE and the narrowest scope (app data only); declared in `governance/identity.json` first.

## Screen (one action)

Settings: one switch, `Sync to my Drive`.

## Test that proves it

Tests: only the app-data scope is requested, guest use still works, one switch removes access.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One provider beside OneDrive.
- **Enterprise, when conditions call for it:** A provider-neutral sync contract with residency choice.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
