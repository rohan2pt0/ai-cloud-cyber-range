# Spec: one-door-aws-federation

Queue item `one-door-aws-federation` in `governance/queue.json` · due 2026-12-15 · added 2026-11-08.

**The ask, as the queue holds it:** Federate AWS to the one door through IAM Identity Center, and take aws off the separate-login list

## Outcome for the person

There is one fewer separate login: AWS opens through the one door.

## Data

SAML federation through IAM Identity Center; the separate-login baseline.

## Screen (one action)

Nothing new: the cloud console opens after the one sign-in.

## Test that proves it

The baseline in `lifecycle/fitness.json` goes down by one; fitness `signin-declared` stays green.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One account federated.
- **Enterprise, when conditions call for it:** All clouds federated with least-privilege permission sets.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
