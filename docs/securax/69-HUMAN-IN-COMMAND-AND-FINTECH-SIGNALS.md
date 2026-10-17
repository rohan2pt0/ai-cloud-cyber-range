# 69 · Human-in-command for AI, and what the October 2026 fintech signals mean for SecuRAX

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** The kill switch, the inventory checks, the AI disclosure header and the per-caller token budget are built and tested; the watch items are analysis only. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Ten posts, one filter: **does it change what an AI-security estate for Indian BFSI must do?** One does, directly: RBI's
draft model-risk guidance. One more changes how we run AI: the cost of agents. The rest are business and payments news for
a regulator watch, not for code.

## 1. RBI draft Model Risk Management guidance (built)

The *Draft Guidance on Regulatory Principles for Model Risk Management, 2026* (press release 2026-2027/528, June 2026;
comments closed 24 July 2026) covers commercial banks, NBFCs, co-operative banks, AIFIs, ARCs and credit information
companies. It is a **draft**: proposed expectations, not rules in force. Secondary coverage reports these expectations:

| Draft expectation | In SecuRAX now |
|---|---|
| **Human override, suspension, kill switch** | `./securax ai stop all\|MODEL --reason "..."` and `./securax ai resume`. The gateway refuses the model on the next request, with no restart, and tells the caller a person stopped it, why, and that a human handles it. The cockpit lights a lamp while anything is stopped. |
| **A living model inventory with risk tiers** | `governance/model-registry.yaml` now records owner, third-party source, explainability statement and last independent validation. `./securax ai inventory` flags a model that is unvalidated, overdue for re-validation (high tier: yearly), high-risk without an explainability statement, or unapproved. |
| **Decommissioned models: records for 10+ years** | `decommissioned:` in the registry; the inventory shows the date records may be destroyed (10 years on). Every stop and resume is appended to `vault/ai-control-log.jsonl`, which is never trimmed. |
| **Third-party models stay your accountability** | `third_party: true` on every model we did not build. Validation is our own red-team and journeys, independent of the developer. |
| **Customer-facing AI says it is AI and offers a human** | Every gateway answer carries `X-AI-Generated: true` for any client to show. The hand-off to a person is the organisation's process. |
| **Explainability for material decisions** | SecuRAX's models make no credit or fraud decision; the registry says so per model. A model that does must state how its output is explained, or the inventory flags it. |

**Why a file, not an API, for the kill switch:** whatever can call the gateway (an agent, a compromised client) must not be
able to switch AI back on. The switch is `local/compose/controls/ai-control.json`, written only by the CLI on the machine
and mounted read-only. An unreadable or malformed file stops all AI: when the stop signal is in doubt, stopping is the safe
reading.

The library gains three controls through the pack `governance/controls/packs/rbi-mrm-draft-2026.json` (ET-101 kill switch,
ET-102 inventory, ET-103 disclosure and human hand-off), and the navigator a regulator row for the draft. They apply to
every class (the ceiling rule) until the final text says otherwise.

## 2. The cost of agents (built)

"Actions are more expensive than words": agentic coding can use thousands of times the tokens of one question. A coder agent
in a loop can spend a month's budget in a night. The gateway now has a **daily token budget per caller**
(`TOKEN_BUDGET_PER_DAY` in `.env`, 0 = off). When a caller reaches it, the gateway refuses with 429 and a plain reason
until midnight, and the audit records `budget_exhausted`. The budget is counted in memory, so a gateway restart starts the
day afresh. Set it before you let agents run unattended.

"Cognitive surrender", accepting AI answers without deliberation, is the human side of the same risk. SecuRAX already keeps
a person in the loop for actions (the approved-action executor) and now for the AI itself (section 1).

## 3. The rest: watch, do not build

| Signal | Status | What would make it ours |
|---|---|---|
| **Account Aggregator pricing.** Sahamati moves the network to a standard fee from 1 November 2026. I could confirm the date; I could not confirm the per-account amounts quoted in the post. | Watch | a lender or FIP using SecuRAX to guard AA data flows: then add AA consent artefacts to the residency and audit rules |
| **Payments Vision 2028** (RBI, 27 March 2026): shared liability between remitter and beneficiary banks, a switch on/off for every payment mode, a payments switching service | Watch | the switch on/off is the same idea as section 1, for payments. If SecuRAX ever guards a payment flow, it reuses the kill-switch pattern |
| UPI MDR, tokenised bonds, cross-border rails, stablecoins, permissionless blockchain | Not ours | — |
| AI-native firms run 25% leaner; agentic AI at NPCI, Perfios and PayU | Context | confirms the direction: agents need the guardrails, budgets and kill switch built above |
| Agentic AI for exam fraud | Not ours | — |

## Limits

- The draft's exact kill-switch and explainability wording was not available to check; the rows above follow secondary
  coverage. Re-check against the final RBI text, and update the pack, when it is issued.
- The kill switch stops what goes through the gateway. A model called around the gateway is not stopped; the network rules
  and the residency guard are what keep callers on the gateway.
