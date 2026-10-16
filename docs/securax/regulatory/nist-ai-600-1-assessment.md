# Gap assessment — NIST AI 600-1, Artificial Intelligence Risk Management Framework: Generative AI Profile (July 2024) — 12 risk categories

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Complete; every reference resolves (fitness `regulatory-maps`). Open gaps are listed inside. [What the lights mean](../../index.md#the-status-lights)
<!-- status:end -->

> NIST AI 600-1 (Generative AI Profile) risk categories assessed against what the gateway and its surrounding estate demonstrably do. Deployer-side view: a gateway operator, not a model builder.

Source: [NIST AI 600-1, Artificial Intelligence Risk Management Framework: Generative AI Profile (July 2024) — 12 risk categories](https://doi.org/10.6028/NIST.AI.600-1) — NIST, July 2024; read 2026-10-14. Category names from NIST's profile as reported by secondary sources; suggested-action IDs (e.g. GV-1.1-001) are not mapped. Status is our own judgement.

Applicability scope: all layers / categories (use `--category` to narrow).

**Software-scope coverage: 54.2%** of 12 requirements software can address (✅ 3 supported · 🟡 7 partial · ⬜ 2 gap), plus **0 obligations that belong to the regulated entity** (🏛, never counted as covered by software) and 0 not applicable (➖).

> This is **not** a compliance certification and a tool cannot make an entity "100% compliant"; it shows what the estate demonstrably does, what it does not, and what only the entity can do.

## Backlog — what to build or fix, highest priority first

- ⬜ **Bias** (medium) Toxicity, bias and homogenisation — No bias or homogenisation evaluation. **Next:** Add bias probes (garak) to the purple loop; report per category.
- 🟡 **Confabulation** (medium) Confabulation (confidently wrong output) — Research agent cites sources and the build contract demands tests, but answers are not checked for grounding. **Next:** Grounding check plus a small factuality probe set.
- 🟡 **Dangerous** (medium) Dangerous, violent or hateful content — Optional Llama Guard detector; not exercised by a journey. **Next:** Probe set in the purple loop.
- ⬜ **IP** (low) Intellectual property — No copyright or licence filter on generated text; `vet` checks licences of third-party content we vendor, not model output. **Next:** Decide the entity's position first; add an output similarity check only if required.
- 🟡 **CBRN** (low) CBRN information or capabilities — Depends on the optional Llama Guard detector; nothing specific is tested. **Next:** Include refusal probes in the purple loop.
- 🟡 **Environmental** (low) Environmental impacts — Small local models, dormant-by-default stages and hibernation keep consumption low; nothing is measured. **Next:** Report energy-relevant measures (model size, hours awake) in the cockpit.
- 🟡 **HumanAI** (low) Human-AI configuration (over-reliance, automation bias) — Human approval for agent write actions; no indicators of answer reliability. **Next:** Confidence/grounding badge on answers.
- 🟡 **InfoIntegrity** (low) Information integrity — Output link allow-list and canary leak checks; no provenance or watermarking of generated content. **Next:** Mark generated output as AI-generated in exports.
- 🟡 **Obscene** (low) Obscene, degrading and/or abusive content — Optional Llama Guard detector; not exercised by a journey. **Next:** Probe set in the purple loop.

## Every requirement

| | Ref | Requirement | Applies | Evidence / note |
|---|---|---|---|---|
| 🟡 | CBRN | CBRN information or capabilities | all | `file:apps/llm-gateway/app/providers.py` — Depends on the optional Llama Guard detector; nothing specific is tested. |
| 🟡 | Confabulation | Confabulation (confidently wrong output) | all | `file:agents/web_research/researcher.py` — Research agent cites sources and the build contract demands tests, but answers are not checked for grounding. |
| 🟡 | Dangerous | Dangerous, violent or hateful content | all | `file:apps/llm-gateway/app/providers.py` — Optional Llama Guard detector; not exercised by a journey. |
| ✅ | Privacy | Data privacy | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `journey:purple_loop`, `journey:gateway_residency` — PII redaction (Aadhaar, PAN, cards, UPI, mobile, e-mail), residency routing and audit, proven end to end. Scope: data through the gateway. |
| 🟡 | Environmental | Environmental impacts | all | `journey:lifecycle_sprout` — Small local models, dormant-by-default stages and hibernation keep consumption low; nothing is measured. |
| 🟡 | HumanAI | Human-AI configuration (over-reliance, automation bias) | all | `file:agents/web_research/executor.py` — Human approval for agent write actions; no indicators of answer reliability. |
| 🟡 | InfoIntegrity | Information integrity | all | `file:apps/llm-gateway/app/guardrails.py` — Output link allow-list and canary leak checks; no provenance or watermarking of generated content. |
| ✅ | InfoSecurity | Information security | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `journey:purple_loop`, `journey:gateway_identity` — Injection, exfiltration, tool-coercion rails, authentication, rate limits, audit, SOC correlation, red/purple testing, proven by journeys. |
| ⬜ | IP | Intellectual property | all | No copyright or licence filter on generated text; `vet` checks licences of third-party content we vendor, not model output. |
| 🟡 | Obscene | Obscene, degrading and/or abusive content | all | `file:apps/llm-gateway/app/providers.py` — Optional Llama Guard detector; not exercised by a journey. |
| ⬜ | Bias | Toxicity, bias and homogenisation | all | No bias or homogenisation evaluation. |
| ✅ | ValueChain | Value chain and component integration | all | `journey:vet_gate`, `test:lifecycle/tests/test_burrow_pinning.py`, `file:.github/workflows/devsecops.yml` — Third-party skills/plugins pass the `vet` gate; installers are version- and hash-pinned; SBOM in CI; supply-chain ratchet in the fitness functions. |

## Integrity
- ✅ every evidence reference resolves and every 'supported' item is proven by a journey or test.

_Status is our own assessment of a lab estate, against the regulator's text as read on the date above. Challenge it._

