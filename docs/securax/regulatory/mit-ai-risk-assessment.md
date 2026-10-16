# Gap assessment — MIT AI Risk Repository (domain taxonomy, seven domains / 24 subdomains, December 2025 update)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Complete; every reference resolves (fitness `regulatory-maps`). Open gaps are listed inside. [What the lights mean](../../index.md#the-status-lights)
<!-- status:end -->

> The MIT AI Risk Repository's seven risk domains, assessed against what the gateway and its surrounding estate demonstrably do. A coverage view of AI-specific risk, complementary to the regulatory maps.

Source: [MIT AI Risk Repository (domain taxonomy, seven domains / 24 subdomains, December 2025 update)](https://airisk.mit.edu) — MIT FutureTech / AI Risk Initiative; read 2026-10-14. Domain names are from MIT's published taxonomy as reported by secondary sources; this map is at DOMAIN level (not the 24 subdomains) and the status is our own judgement. Compare with the repository itself before relying on it.

Applicability scope: all layers / categories (use `--category` to narrow).

**Software-scope coverage: 58.3%** of 6 requirements software can address (✅ 1 supported · 🟡 5 partial · ⬜ 0 gap), plus **1 obligations that belong to the regulated entity** (🏛, never counted as covered by software) and 0 not applicable (➖).

> This is **not** a compliance certification and a tool cannot make an entity "100% compliant"; it shows what the estate demonstrably does, what it does not, and what only the entity can do.

## Backlog — what to build or fix, highest priority first

- 🟡 **1** (medium) Discrimination & toxicity (unfair discrimination, toxic content, unequal performance) — An optional Llama Guard detector can flag unsafe or toxic content; there is no bias or fairness testing and no per-group performance check. **Next:** Add bias/toxicity probes (garak/promptfoo categories) to the purple loop and report them.
- 🟡 **3** (medium) Misinformation (false or misleading information; degraded information ecosystem) — Output link allow-list and canary checks limit some harm; the research agent cites its sources. No factuality or grounding evaluation of answers. **Next:** Add a grounding check to the research agent (every claim has a retrieved source) and a small factuality probe set.
- 🟡 **4** (medium) Malicious actors & misuse (disinformation, cyberattacks, fraud, targeted manipulation) — Injection, tool-coercion and exfiltration rails and the purple loop cover attacks AGAINST the system; content policy against misuse BY users depends on the optional detector. **Next:** Add misuse prompts (fraud, malware writing) to the purple loop with expected refusals.
- 🟡 **7** (medium) AI system safety, failures & limitations (robustness, transparency, misalignment) — Detectors fail closed, answers fall back along a ladder to a local model, `bench` smoke-tests installed models on this machine, fitness budgets hold. No broad robustness evaluation suite; model behaviour is not explained to the user. **Next:** Add a small robustness suite (typos, long inputs, adversarial paraphrase) to `bench`.
- 🟡 **5** (low) Human-computer interaction (overreliance, loss of agency) — Agent write actions need an explicit human approval; answers are first drafts for a human. No calibration or uncertainty indicators. **Next:** Show a confidence/grounding badge on answers in the Command Center; keep approval for every write.

## Every requirement

| | Ref | Requirement | Applies | Evidence / note |
|---|---|---|---|---|
| 🟡 | 1 | Discrimination & toxicity (unfair discrimination, toxic content, unequal performance) | all | `file:apps/llm-gateway/app/providers.py` — An optional Llama Guard detector can flag unsafe or toxic content; there is no bias or fairness testing and no per-group performance check. |
| ✅ | 2 | Privacy & security (leaking or inferring sensitive information; attacks on the AI system) | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `journey:purple_loop`, `journey:gateway_identity`, `journey:gateway_residency` — PII/secret redaction, prompt-injection and exfiltration rails, authentication, residency routing and audit are proven by tests and real-container journeys. Scope: the AI channel through the gateway. |
| 🟡 | 3 | Misinformation (false or misleading information; degraded information ecosystem) | all | `file:apps/llm-gateway/app/guardrails.py`, `file:agents/web_research/researcher.py` — Output link allow-list and canary checks limit some harm; the research agent cites its sources. No factuality or grounding evaluation of answers. |
| 🟡 | 4 | Malicious actors & misuse (disinformation, cyberattacks, fraud, targeted manipulation) | all | `file:apps/llm-gateway/app/guardrails.py`, `journey:purple_loop` — Injection, tool-coercion and exfiltration rails and the purple loop cover attacks AGAINST the system; content policy against misuse BY users depends on the optional detector. |
| 🟡 | 5 | Human-computer interaction (overreliance, loss of agency) | all | `file:agents/web_research/executor.py` — Agent write actions need an explicit human approval; answers are first drafts for a human. No calibration or uncertainty indicators. |
| 🏛 | 6 | Socioeconomic & environmental (power concentration, job quality, environmental harm) | all | Strategic and organisational. Technically: small local models and dormant-by-default stages keep the footprint low. |
| 🟡 | 7 | AI system safety, failures & limitations (robustness, transparency, misalignment) | all | `cmd:bench`, `cmd:fitness`, `journey:model_self_correction` — Detectors fail closed, answers fall back along a ladder to a local model, `bench` smoke-tests installed models on this machine, fitness budgets hold. No broad robustness evaluation suite; model behaviour is not explained to the user. |

## Integrity
- ✅ every evidence reference resolves and every 'supported' item is proven by a journey or test.

_Status is our own assessment of a lab estate, against the regulator's text as read on the date above. Challenge it._

