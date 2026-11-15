# Spec: ai-gap-g9

Queue item `ai-gap-g9` in `governance/queue.json` · due 2026-11-19 · added 2026-10-22.

**The ask, as the queue holds it:** Close AI architecture gap G9 (doc 105): Provider keys out of plaintext .env into an encrypted file unlocked at start

## Outcome for the person

A copied disk or a stray backup does not expose provider keys.

## Data

Keys in an encrypted file, unlocked at start by a secret the estate holds.

## Screen (one action)

Nothing new for the person; `./securax keys` shows `encrypted`.

## Test that proves it

Tests: no key in plain text on disk, start fails closed with a plain message, rollback works.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One encrypted file.
- **Enterprise, when conditions call for it:** A secrets manager with rotation and per-service identities.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
