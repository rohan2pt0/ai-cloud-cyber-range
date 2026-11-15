# Spec: audit-round-1

Queue item `audit-round-1` in `governance/queue.json` · due 2026-11-15 · added 2026-11-11.

**The ask, as the queue holds it:** Audit round 1, safety: lock on phone and laptop, an encrypted backup and a test restore on another device, nothing private in the repository, sync after unlock (doc 134)

## Outcome for the person

The owner's private data is safe on the phone and laptop: locked, backed up encrypted, and proven restorable on a second device.

## Data

The lock state, the backup file and the escrowed phrase; nothing enters the repository.

## Screen (one action)

Settings shows one line, `Safety: 2 of 3 done`, with one button for the next step (`Turn on the lock`, `Make a backup`, `Test a restore`).

## Test that proves it

The owner restores one backup on another device and the data opens; `robustness_audit.py` and the lock tests stay green. Close the item only after the real restore.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A manual checklist of three steps, each one tap.
- **Enterprise, when conditions call for it:** A scheduled restore drill per household or tenant, with the result in the monthly briefing and in audit.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
