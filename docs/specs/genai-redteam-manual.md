# Spec: genai-redteam-manual

Queue item `genai-redteam-manual` in `governance/queue.json` · due 2026-12-02 · added 2026-11-11.

**The ask, as the queue holds it:** Owner, 2026-11-11: take the OWASP GenAI Security Project's GenAI Red Teaming Manual v1.0 (genai.owasp.org, cited by reference) into the range

## Outcome for the person

A team running AI can see, from a repeatable exercise, which attacks its estate stops and which it would not notice.

## Data

Probe definitions mapped to OWASP LLM and MITRE ATLAS in `redteam/`, results in the adversary ledger; the manual is cited by reference.

## Screen (one action)

`./securax redteam` ends with one line, the one unblocked attack to fix first, and its command.

## Test that proves it

Each new probe has a test that it fails against an unprotected stub and passes with the rail on; the purple loop reports block, log and alert for each.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Probes run locally against the gateway.
- **Enterprise, when conditions call for it:** Scheduled campaigns per tenant with evidence packs for auditors.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
