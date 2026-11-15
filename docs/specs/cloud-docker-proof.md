# Spec: cloud-docker-proof

Queue item `cloud-docker-proof` in `governance/queue.json` · due 2026-12-05 · added 2026-11-08.

**The ask, as the queue holds it:** Cloud build sessions have the Docker CLI but no daemon, so a container change (like Postgres 18) is first booted only by the CI sandbox

## Outcome for the person

A container change is proven in minutes, before the long sandbox.

## Data

A fast job that boots only the changed service and runs its healthcheck.

## Screen (one action)

One check on the pull request.

## Test that proves it

A planted broken image fails the fast job.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One fast CI job.
- **Enterprise, when conditions call for it:** Build sessions with a container runtime.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
