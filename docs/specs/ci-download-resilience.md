# Spec: ci-download-resilience

Queue item `ci-download-resilience` in `governance/queue.json` · due 2026-11-26 · added 2026-11-08.

**The ask, as the queue holds it:** CI fails when GitHub Releases answers 504: gitops (kubeconform) and container-scan (syft) went red twice on 2026-11-08 for reasons outside the code

## Outcome for the person

CI goes red only for our own faults, not for an outside download failing.

## Data

Pinned tool binaries cached by version and checksum; retries with backoff.

## Screen (one action)

Nothing new; fewer false reds.

## Test that proves it

A workflow test that the checksum is still verified when the cache is used.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Cache and retry.
- **Enterprise, when conditions call for it:** An internal mirror of pinned tools.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
