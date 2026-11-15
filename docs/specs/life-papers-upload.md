# Spec: life-papers-upload

Queue item `life-papers-upload` in `governance/queue.json` · due 2026-11-15 · added 2026-10-22.

**The ask, as the queue holds it:** Upload papers straight from the Life OS (phone or laptop browser) instead of saving them into a folder

## Outcome for the person

A paper is added from the phone in one step, instead of being saved into a folder.

## Data

The file, saved to `vault/life/docs/` on the person's own estate; a threat model for the upload.

## Screen (one action)

Life OS: one button, `Add a paper`.

## Test that proves it

A journey: a signed-in upload lands and is read, an unsigned or foreign-origin upload is refused, size and type are bounded.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A drop zone on the hub.
- **Enterprise, when conditions call for it:** The share sheet as the entry, with virus scan and per-member folders.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
