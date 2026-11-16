# Spec: ref-bar-supply-chain

Queue item `ref-bar-supply-chain` in `governance/queue.json` · due 2026-12-19 · added 2026-11-08.

**The ask, as the queue holds it:** Signed release artefacts and an SBOM published with every release

## Outcome for the person

A person installing a release can prove it is ours and see what is in it.

## Data

An SBOM and signatures made in the release workflow.

## Screen (one action)

The installer prints one line, `Verified release`.

## Test that proves it

A test that a tampered artefact fails verification in `install.sh`.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Keyless signing and an SBOM.
- **Enterprise, when conditions call for it:** Provenance attestations and policy on admission.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
