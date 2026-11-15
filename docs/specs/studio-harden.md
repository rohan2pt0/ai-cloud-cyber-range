# Spec: studio-harden

Queue item `studio-harden` in `governance/queue.json` · due 2026-11-30 · added 2026-10-27.

**The ask, as the queue holds it:** Harden Code Studio (doc 119, ./securax studio) from the usable first version to estate-grade: run the code-server container as a NON-ROOT user with a scoped mount (not the whole home); offer Studio on its own subdomain code.<domain> as well as the /studio/ path (cleaner for the in-browser editor, which can be finicky …

## Outcome for the person

The in-browser editor is safe to leave running: least privilege, its own address, nothing more of the machine than it needs.

## Data

Container user and mounts, the route (subdomain or path), sign-in through the one door.

## Screen (one action)

`./securax studio` prints one name to open; the Command Center shows Studio's state.

## Test that proves it

The `studio_starts` journey extended: runs as non-root, the mount is scoped, the subdomain serves, a foreign origin is refused.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A single hardened container.
- **Enterprise, when conditions call for it:** Per-user workspaces with quotas and audit of what was opened.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
