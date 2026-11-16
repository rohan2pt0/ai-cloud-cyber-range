# Spec: signed-official-content

Queue item `signed-official-content` in `governance/queue.json` · due 2026-12-10 · added 2026-10-22.

**The ask, as the queue holds it:** Official regulatory maps, recipes and evidence packs signed with the owner's key (ssh-keygen -Y), so customers and auditors can tell the official feed from a copy

## Outcome for the person

A customer or auditor can tell official maps and evidence packs from a copy.

## Data

Detached signatures made with the owner's key; the public key published.

## Screen (one action)

`./securax verify-content`: one line, official or not.

## Test that proves it

A test that a changed byte fails verification, and that unsigned content is labelled, not refused, in the free core.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Signatures on files.
- **Enterprise, when conditions call for it:** A signed feed with key rotation, transparency log and partner counter-signing.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
