# Spec: calendar-subscribe

Queue item `calendar-subscribe` in `governance/queue.json` · due 2027-01-31 · added 2026-11-10.

**The ask, as the queue holds it:** The rail beyond a downloaded file: a calendar the person subscribes to once (webcal from their own estate, served by the hub), so every later version arrives by itself and nothing needs re-importing

## Outcome for the person

The person subscribes once and every later change arrives in their calendar by itself.

## Data

The same registry and UIDs, served by the hub; a threat model first.

## Screen (one action)

One button, `Subscribe`.

## Test that proves it

Tests: the served feed equals the downloaded file, UIDs are unchanged, access needs the person's token.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** The one-tap file.
- **Enterprise, when conditions call for it:** Per-member and shared feeds with revocation.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
