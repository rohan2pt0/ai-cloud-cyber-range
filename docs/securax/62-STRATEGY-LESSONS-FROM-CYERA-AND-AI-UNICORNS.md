# 62 · Strategy: what Cyera and the AI unicorns teach, and where SecuRAX can win

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The strategy, the free AI-risk check, time-to-first-block, the agent guard and the regulator watch are done; the rest are queued. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Researched 16 Oct 2026 from public sources (linked). Figures are as reported and some are disputed. Treat them as
direction, not data.

## 1. Cyera in one page

| | What they do |
|---|---|
| **Position** | "Building the Trust Layer for the Agentic Era": *the data, identity and AI security platform* |
| **Wedge, then platform** | Started with **DSPM** (find and classify sensitive data across cloud and SaaS), then added Omni DLP, Cyera Identity (non-human identities), **Agent Guardian** (agents), AI SPM, AI runtime protection, browser shield and DataWatcher managed services |
| **Proof on the homepage** | "<1 day to value", "74 PB in 7 days", "95%+ precision", "80% less risk in 3 months"; named customer logos and CISO quotes; a Forrester Wave Leader badge |
| **Demand engine** | an "AI Security School" (10,000+ practitioners), its own conference (datasecAI), research reports, free assessments ("See data risk", "AI Readiness Assessment") |
| **Money** | enterprise subscriptions; valuation reported at $12B in June 2026 on roughly $150–200M ARR ([multiples.vc](https://multiples.vc/private-comps/cyera), [BankInfoSecurity](https://www.bankinfosecurity.net/blogs/cyera-eyeing-400m-funding-round-at-9b-valuation-p-4003)); reportedly still loss-making |

**Honest comparison.** Cyera scans petabytes across Fortune-500 clouds as a SaaS. SecuRAX is a **runtime control point**
for AI requests that runs on the customer's own hardware. We overlap with Cyera's *AI runtime / prompt security* module,
not with its core. We will not out-Cyera Cyera.

## 2. The warning in the market

In 2025 the standalone AI-firewall companies were bought by platforms: Check Point–Lakera, SentinelOne–Prompt Security,
Cato–Aim, F5–CalypsoAI (≈$180–300M each), after Cisco–Robust Intelligence and Palo Alto–Protect AI
([SiliconANGLE](https://siliconangle.com/2025/09/16/crowdstrike-check-point-extend-ai-security-capabilities-new-acquisitions/),
[Decryption Digest](https://www.decryptiondigest.com/blog/ai-guardrail-vendors-after-acquisition-lakera-prompt-security-aim-calypsoai)).
**A prompt firewall on its own is a feature, not a company.** To be more than that, SecuRAX has to own something the
platforms are structurally bad at.

## 3. Patterns shared by the AI and security unicorns

| Pattern | Who | What it means for us |
|---|---|---|
| **Own a category name** | Cyera "DSPM", Wiz "CNAPP", Glean "work AI" | name ours and repeat it everywhere |
| **Speed to value is the headline** | Cyera "<1 day", Wiz "minutes, agentless" | measure our time-to-first-block and publish it |
| **Narrow wedge, then a platform** | Cyera DSPM → DLP → identity → agents | Shield first; posture, agents and the evidence engine next |
| **Quantified proof from named customers** | every one of them | design partners exist to produce these numbers |
| **Education as distribution** | Cyera AI Security School, Snyk, HashiCorp | a free field guide and a regulator digest |
| **A free assessment as the front door** | Cyera "See data risk", Wiz free scan | a 2-minute AI-risk check on the website (built, below) |
| **Ride the next problem, not the last** | "agentic era" | agents calling tools with customer data is the next exposure |
| **Services where teams are thin** | Cyera DataWatcher, Palantir FDEs | "Shield Managed", sold through MSSPs |
| **Open source as the funnel** | Mattermost, Databricks, HashiCorp | already our model |

## 4. Where SecuRAX can be first: the sovereign, proof-native AI control plane

The platforms are SaaS-first, priced in dollars for the Fortune 500, and prove compliance with PDFs. Three gaps follow,
and SecuRAX already has the foundations for each:

1. **Sovereign by construction.** It runs on the customer's hardware, air-gapped if needed, with a local-model floor and
   residency that routes by data class. This fits regulated mid-market firms in India first, then markets with
   data-localisation rules: the GCC, South-East Asia and Africa.
2. **Regulator-native.** Evidence is mapped clause by clause to the local regulator (RBI, SEBI CSCRF, DPDP today; UAE,
   SAMA and MAS next). India-grade PII detection is part of it: PAN, Aadhaar with its Verhoeff checksum, UPI IDs.
3. **Proof-native.** Every claim names the test that proves it, and the evidence pack **re-runs**. Customers and
   auditors can verify instead of trusting a datasheet. No platform offers "run our proof yourself".

**The category name: the Sovereign AI Firewall,** with the promise *"Use any AI. Prove you stayed in control."*

## 5. The build order this implies

| # | Build | Why | Light |
|---|---|---|---|
| 1 | **Free AI-risk check** on the website: ten questions mapped to RBI, SEBI CSCRF and DPDP, an instant score and the top gaps | the front door, as with Cyera's "See data risk" | 🟢 built in this change (`website/assess/`) |
| 2 | **Time-to-first-block** measured in CI and published | our "<1 day to value" | 🟢 built: fitness checks `time-to-first-block` and `block-latency-p95` on every build |
| 3 | **Agent and tool-call guard**: the same policy applied to an agent's tool calls (MCP), not only to chat prompts | the next exposure; Cyera's Agent Guardian shows demand | 🟢 built: `inspect_tool_calls` in the gateway, policy via `TOOL_POLICY_FILE` |
| 4 | **Regulator watch and a monthly digest** (doc 60 queue #1), as the newsletter | education as distribution | 🟢 built: `./securax regwatch` (doc 60) |
| 5 | **UPI-ID and GSTIN detectors**, and GCC/SEA PII packs | regulator-native depth | 🔴 |
| 6 | **Admin console**: policies, keys, reports | buyers expect a screen | 🔴 |
| 7 | **MSSP partner kit**: multi-tenant packaging and reseller pricing | how India's mid-market buys security | 🔴 |
| 8 | **Independent penetration test** of Shield, with the report shared under NDA | trust before any analyst badge | 🔴 |

## 6. What we deliberately do not copy

- Logo walls and "trusted by" claims before we have customers.
- Analyst badges and certifications we do not hold.
- Precision percentages we have not measured on customer data.
- The "trust layer for the agentic era" wording, which is Cyera's.
