# Spec: member-invitations

Queue item `member-invitations` in `governance/queue.json` · due 2027-01-15 · added 2026-11-11.

**The ask, as the queue holds it:** Invitation-only access: member-issued, single-use, signed invitation codes with a small yearly allowance and no rewards; an honest waitlist when onboarding capacity is full

## Outcome for the person

A member can bring in one trusted family, and nobody else can get in or be tracked.

## Data

Signed, single-use codes with a small yearly allowance; a waitlist count. Threat model first.

## Screen (one action)

Member screen: one button, `Create an invitation`; it shows once as a code to share.

## Test that proves it

Tests: a code works once, a forged or reused code is refused with a plain reason, and no record links inviter to invitee beyond the member's own view.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Codes signed by the owner's key, checked at the door.
- **Enterprise, when conditions call for it:** Invitations through the one-door identity with organisational approval and audit.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
