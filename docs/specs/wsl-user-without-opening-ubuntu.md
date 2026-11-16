# Spec: wsl-user-without-opening-ubuntu

Queue item `wsl-user-without-opening-ubuntu` in `governance/queue.json` · due 2026-12-02 · added 2026-11-11.

**The ask, as the queue holds it:** install.ps1 creates the Ubuntu user itself, so the person never opens Ubuntu to pick a username

## Outcome for the person

A person on Windows never opens Ubuntu to pick a username; install just continues.

## Data

The Windows username and one password the person sets once.

## Screen (one action)

The installer asks one thing, `Choose a password`, and goes on.

## Test that proves it

A real Windows run by the owner; a script test that the user is created non-interactively and no passwordless sudo is left.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A non-interactive user creation step in `install.ps1`.
- **Enterprise, when conditions call for it:** Managed installs through device management with the identity from the one door.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
