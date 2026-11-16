# Spec: anthropic-messages-endpoint

Queue item `anthropic-messages-endpoint` in `governance/queue.json` · due 2026-12-05 · added 2026-11-07.

**The ask, as the queue holds it:** Let tools built for the Anthropic API point at the SecuRAX gateway: translate Anthropic Messages to the gateway's models, official providers only

## Outcome for the person

Tools written for the Anthropic API work against the estate's gateway, inside its rails.

## Data

A translation of Messages requests to the gateway's models; official providers only.

## Screen (one action)

One setting in the tool: the gateway's name as the base address.

## Test that proves it

Gateway tests: identity, allowance and audit apply to the adapter; streaming and tool calls round-trip; a second review before merge.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A thin adapter.
- **Enterprise, when conditions call for it:** Versioned API compatibility with contract tests.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
