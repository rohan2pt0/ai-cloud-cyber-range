# 69 · Human-in-command for AI, and what the October 2026 fintech signals mean for SecuRAX

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Checked against the June 2026 draft paragraph by paragraph; the kill switch, inventory checks (paras 21-54), disclosure, allowance and both RBI packs are built and tested; the watch items are analysis only. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Ten posts, one filter: **does it change what an AI-security estate for Indian BFSI must do?** One does, directly: RBI's
draft model-risk guidance. One more changes how we run AI: the cost of agents. The rest are business and payments news for
a regulator watch, not for code.

## 1. RBI draft Model Risk Management guidance (built, checked against the draft)

RBI released the draft *Guidance on Regulatory Principles for Model Risk Management* on 24 June 2026 (press release
2026-2027/528; comments closed 24 July 2026). It covers commercial, small finance, payments, local area and regional rural
banks, urban and rural co-operative banks, AIFIs, NBFCs, ARCs and credit information companies, and **all** their models,
including third-party and AI/ML models. It builds on the 2024 draft on credit models and the FREE-AI committee report
(August 2025). It is a **draft**: proposed expectations, not rules in force. The paragraph numbers below are the draft's.

| Draft paragraph | In SecuRAX now |
|---|---|
| **60-63: human oversight; override, suspension, deactivation "including kill-switch arrangements"; automation bias; staff able to challenge** | `./securax ai stop all\|MODEL --reason "..."` and `resume`. The gateway refuses on the next request with no restart and tells the caller who stopped it and why. The cockpit lights a lamp while anything is stopped. |
| **21: no model used unless it is in the inventory** | `./securax ai inventory` compares what the gateway actually serves with the registry and flags every model that is not listed. |
| **22: owners, developers, validators, approvers, tier, intended use, dependencies** | the registry records owner, provider, intended use, approver, validator and tier; a missing intended use or owner is flagged. |
| **23: decommissioned models kept at least ten years** | `decommissioned:` in the registry; the inventory shows the date the records may go. Stops and resumes are logged permanently. |
| **29-30: independent validation, before and after deployment and periodically** | `validated` and `validated_by` per model; unvalidated and overdue models (high tier: yearly) are flagged. |
| **38-42: change management; a material change re-starts validation** | `validated_model` per model: a model changed after validation is flagged. Every change goes through PR, CI and the impact map. |
| **43, 53: continuity when a model fails; dependence on few providers** | the failover ladder across providers ends in the private local model. |
| **45-48: third-party models stay your accountability; independent validation; audit rights** | `third_party: true` per model; our own red-team validates them. Contracts and audit rights are the organisation's. |
| **54: explainability thresholds; compensating controls where full explainability is not possible** | an explainability statement per model; a high-tier model without one is flagged. SecuRAX's models take no credit or fraud decision. |
| **54(2), 55, 59(i): hallucination boundaries, red-teaming, prompt-injection controls** | the gateway's rails, the red-team suite and the purple-team loop. |
| **59(ii)-(iii): tell users it is AI and its limits; switch to a human on request** | every answer carries `X-AI-Generated: true`; a stopped model tells callers a person handles it. The hand-off itself is the organisation's. |
| **9, 11-13, 17-20: board-approved framework, risk committee, tiering** | the organisation's; SecuRAX supplies the inventory and evidence they review. |

**Why a file, not an API, for the kill switch:** whatever can call the gateway (an agent, a compromised client) must not be
able to switch AI back on. The switch is `local/compose/controls/ai-control.json`, written only by the CLI on the machine
and mounted read-only. An unreadable or malformed file stops all AI: when the stop signal is in doubt, stopping is the safe
reading.

The library gains six controls through the pack `governance/controls/packs/rbi-mrm-draft-2026.json` (ET-101 human
oversight and kill switch, ET-102 inventory, ET-103 disclosure and hand-off, ET-104 third-party models, ET-105 change
management, ET-106 continuity), each citing its paragraphs, and the navigator a regulator row for the draft.

## 2. The cost of agents: an AI allowance per caller (built, on by default)

"Actions are more expensive than words": agentic coding can use thousands of times the tokens of one question, and a coder
agent in a loop can spend a month's budget in a night. Every caller of the gateway (a person's Chat, an agent, a script) now
has an **allowance**, set the way current AI services and gateways set theirs:

| | Default | Why this number |
|---|---|---|
| **Daily limit** | 2,000,000 tokens | a heavy day of agentic coding; a normal day of chat uses a few tens of thousands |
| **Monthly limit** | 20,000,000 tokens | about US$15 a month on a Flash-class cloud model at list price (about 80% input at $0.30/M, 20% output at $2.50/M); the worst case, all output, is about $50 |
| **Warning** | at 80% of either | a soft line that only warns, before the hard stop (the pattern AI gateways such as LiteLLM use) |
| **Stop** | at 100% | the gateway refuses with 429, says which limit, when it resets, and how to extend it |
| **What counts** | cloud models only | the private local model costs no money, so it still answers when the cloud allowance is used up; the rate limit (30 a minute) still caps a local loop. `AI_BUDGET_COUNT_LOCAL=1` counts it too |

**Two windows, like AI subscriptions.** The day is the short window and the month the long one. Thirty full days would be
60M, three times the month, so one heavy day is fine but a runaway week is not. (AI subscriptions pair a short session limit
with a weekly one for the same reason.)

**Extending, instead of buying credits:**

```bash
./securax ai budget                                              # each caller: used today and this month, and what is left
./securax ai budget extend --day --tokens 1000000 --reason "release day"
./securax ai budget extend --month --tokens 10000000 --reason "migration project" [--caller ID]
```

An extension is for the current day or month only, needs a reason, and is logged in `vault/ai-control-log.jsonl`. It is
written to the same machine-only control file as the kill switch, so no caller can extend its own allowance. To change the
defaults for good, set `AI_BUDGET_DAY_TOKENS` and `AI_BUDGET_MONTH_TOKENS` in `local/compose/.env` (0 switches a limit off).

**Where you see it:**

- Every answer carries `X-AI-Budget-Day-Left` and `X-AI-Budget-Month-Left`, so an agent can slow down by itself.
- The cockpit lights a caution lamp at 80% and a warning when a limit is used up.
- The audit records `budget_warning` and `budget_exhausted`.
- Spend is kept on the gateway's own volume, so a restart does not reset the month.

"Cognitive surrender", accepting AI answers without deliberation, is the human side of the same risk. SecuRAX already keeps
a person in the loop for actions (the approved-action executor) and now for the AI itself (section 1).

## 3. The rest: watch, do not build

| Signal | Status | What would make it ours |
|---|---|---|
| **Account Aggregator pricing.** Sahamati moves the network to a standard fee from 1 November 2026. I could confirm the date; I could not confirm the per-account amounts quoted in the post. | Watch | a lender or FIP using SecuRAX to guard AA data flows: then add AA consent artefacts to the residency and audit rules |
| **Payments Vision 2028** (RBI, 27 March 2026) | Built as a pack | see section 4 |
| UPI MDR, tokenised bonds, cross-border rails, stablecoins, permissionless blockchain | Not ours | — |
| AI-native firms run 25% leaner; agentic AI at NPCI, Perfios and PayU | Context | confirms the direction: agents need the guardrails, budgets and kill switch built above |
| Agentic AI for exam fraud | Not ours | — |

## 4. RBI Payments Vision 2028 (a control-library pack)

Fifteen initiatives to the end of 2028. Most are to be explored; the **Cyber KRI framework for non-bank payment system
operators (3.9)** is to be developed and implemented, so it is the one to prepare for. The pack
`governance/controls/packs/rbi-payments-vision-2028.json` adds:

| Initiative | Control | SecuRAX |
|---|---|---|
| 3.9 Cyber KRI framework | RM-101 cyber KRIs with thresholds and trends | partly: the cockpit's KRIs, RAG bands and lamps |
| 3.11 AI-queryable payments data | ET-107 governed AI access to payments data | partly: residency, masking, audit and allowance at the gateway |
| 3.1 switch on/off for every digital mode | RM-102 | the organisation's |
| 3.5 shared responsibility for unauthorised transactions | RM-103 beneficiary-side mule detection | the organisation's |

## Limits

- The rows follow the June 2026 draft. Re-check against the final guidance when RBI issues it, and update the pack.
- The kill switch stops what goes through the gateway. A model called around the gateway is not stopped; the network rules
  and the residency guard are what keep callers on the gateway.
