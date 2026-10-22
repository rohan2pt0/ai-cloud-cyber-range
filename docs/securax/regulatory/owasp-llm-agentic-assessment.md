# Gap assessment — OWASP Top 10 for LLM Applications (2025) and Top 10 for Agentic Applications (2026)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Complete; every reference resolves (fitness `regulatory-maps`). Open gaps are listed inside. [What the lights mean](../../index.md#the-status-lights)
<!-- status:end -->

> The OWASP Top 10 for LLM Applications (2025) and for Agentic Applications (2026) assessed against what the gateway and the estate around it demonstrably do. Deployer-side view: SecuRAX runs and governs models, it does not train them. Each title is OWASP's category name; the notes are our own assessment and can be wrong: challenge them.

Source: [OWASP Top 10 for LLM Applications (2025) and Top 10 for Agentic Applications (2026)](https://genai.owasp.org/) — OWASP GenAI Security Project, November 2024 and December 2025; read 2026-10-22. Category names from OWASP's lists (the agentic names as reported by secondary sources; confirm against the official page). Status is our own judgement.

Applicability scope: all layers / categories (use `--category` to narrow).

**Software-scope coverage: 72.5%** of 20 requirements software can address (✅ 9 supported · 🟡 11 partial · ⬜ 0 gap), plus **0 obligations that belong to the regulated entity** (🏛, never counted as covered by software) and 0 not applicable (➖).

> This is **not** a compliance certification and a tool cannot make an entity "100% compliant"; it shows what the estate demonstrably does, what it does not, and what only the entity can do.

## Backlog — what to build or fix, highest priority first

- 🟡 **ASI01** (high) Agent goal hijack — Tool results and retrieved context pass the same injection rails as user text, so an instruction hidden in content is caught; there is no separate check that a plan still serves the user's goal. **Next:** Red-team probes for goal hijack through tool output in the purple loop (doc 105, G5).
- 🟡 **ASI02** (high) Tool misuse and exploitation — Allow and deny lists with glob patterns, dangerous-argument rules, secrets in arguments blocked and personal data redacted. **Next:** The approval queue for calls that need a person (doc 105, G3).
- 🟡 **LLM06** (high) Excessive agency — Tool calls pass an allow, deny and approval policy that fails closed, dangerous arguments are blocked, and one command stops all AI; a call needing approval is refused rather than queued for a person. **Next:** An approval queue: the call waits for a person's yes from the Command Center or the phone (doc 105, G3).
- 🟡 **ASI05** (medium) Unexpected code execution — Untrusted files are inspected in a sandbox, and weight files are scanned for code that would run on load; agents themselves run no generated code. **Next:** Red-team probes that try to make an agent run code (doc 105, G5).
- 🟡 **ASI06** (medium) Memory and context poisoning — Context passed to a model is inspected; chat memories are not yet reviewable or switched off for shared accounts. **Next:** Chat memories off for shared accounts, reviewable, and inspected like any input (doc 105, G10).
- 🟡 **ASI08** (medium) Cascading failures — A failing detector fails closed, a provider failure falls back down the ladder, and one command stops all AI; there is no automatic breaker that stops a looping agent. **Next:** An automatic breaker that stops an agent whose calls repeat or fail in a loop.
- 🟡 **LLM04** (medium) Data and model poisoning — Poisoned weights are caught by the digest check; documents added to a knowledge base are not yet scanned or owner-tagged at retrieval. **Next:** Per-document owner and class at retrieval, and a scan of documents on ingestion (doc 105, G15).
- 🟡 **LLM08** (medium) Vector and embedding weaknesses — Retrieved text arriving as system context is inspected like any prompt; the vector store itself has no per-document access control. **Next:** Per-document owner and class checked at retrieval (doc 105, G15).
- 🟡 **LLM09** (medium) Misinformation — An honesty check that catches guessing, a careful check-and-rewrite pass, and stale-fact warnings; no answer-quality set runs on each model change. **Next:** An answer-quality set run on every model change, scored over time (doc 105, G6).
- 🟡 **ASI07** (low) Insecure inter-agent communication — Every service-to-service hop can run over internal TLS with verified names; agents do not yet sign or authenticate messages to each other. **Next:** Per-agent identity on calls between agents, checked by the gateway.
- 🟡 **ASI09** (low) Human-agent trust exploitation — Writes an agent proposes wait for a person (the approved-action executor), and the honesty check catches made-up answers. **Next:** Show the person the evidence behind each proposed action before they approve it.

## Every requirement

| | Ref | Requirement | Applies | Evidence / note |
|---|---|---|---|---|
| ✅ | LLM01 | Prompt injection | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `journey:purple_loop` — Input rails for injection, jailbreak and hidden-character smuggling on every text part, tool results and the system context; the red team scores it in the purple loop. |
| ✅ | LLM02 | Sensitive information disclosure | all | `file:apps/llm-gateway/app/residency.py`, `test:apps/llm-gateway/tests/test_residency.py`, `journey:gateway_residency` — India-aware PII redaction on the way in, secret and personal-data rails on the way out, and residency routing that keeps local data off cloud models. |
| ✅ | LLM03 | Supply chain | all | `file:governance/modelcheck.py`, `test:governance/tests/test_modelcheck.py`, `test:lifecycle/tests/test_vet.py`, `journey:vet_gate`, `test:governance/tests/test_licences.py` — Model weights must match an approved digest (ai check), pickle-format weights are scanned for code, third-party skills pass the vet gate, and every image is pinned and licence-listed. |
| 🟡 | LLM04 | Data and model poisoning | all | `file:governance/modelcheck.py`, `test:governance/tests/test_modelcheck.py` — Poisoned weights are caught by the digest check; documents added to a knowledge base are not yet scanned or owner-tagged at retrieval. |
| ✅ | LLM05 | Improper output handling | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py` — Output rails withhold exfiltration links, active HTML and leaked secrets before an answer reaches the caller. |
| 🟡 | LLM06 | Excessive agency | all | `file:apps/llm-gateway/app/main.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `test:apps/llm-gateway/tests/test_human_in_command.py` — Tool calls pass an allow, deny and approval policy that fails closed, dangerous arguments are blocked, and one command stops all AI; a call needing approval is refused rather than queued for a person. |
| ✅ | LLM07 | System prompt leakage | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `journey:purple_loop` — Canary tokens in system prompts are caught on the way out, and the red team probes for leakage. |
| 🟡 | LLM08 | Vector and embedding weaknesses | all | `file:apps/llm-gateway/app/main.py`, `test:apps/llm-gateway/tests/test_guardrails.py` — Retrieved text arriving as system context is inspected like any prompt; the vector store itself has no per-document access control. |
| 🟡 | LLM09 | Misinformation | all | `file:governance/honesty.py`, `test:governance/tests/test_honesty.py`, `test:apps/llm-gateway/tests/test_careful.py` — An honesty check that catches guessing, a careful check-and-rewrite pass, and stale-fact warnings; no answer-quality set runs on each model change. |
| ✅ | LLM10 | Unbounded consumption | all | `file:apps/llm-gateway/app/budget.py`, `test:apps/llm-gateway/tests/test_human_in_command.py` — Per-caller daily and monthly token allowances, request slots and timeouts; a caller over the allowance is refused. |
| 🟡 | ASI01 | Agent goal hijack | all | `file:apps/llm-gateway/app/main.py`, `test:apps/llm-gateway/tests/test_guardrails.py` — Tool results and retrieved context pass the same injection rails as user text, so an instruction hidden in content is caught; there is no separate check that a plan still serves the user's goal. |
| 🟡 | ASI02 | Tool misuse and exploitation | all | `file:apps/llm-gateway/app/main.py`, `test:apps/llm-gateway/tests/test_guardrails.py` — Allow and deny lists with glob patterns, dangerous-argument rules, secrets in arguments blocked and personal data redacted. |
| ✅ | ASI03 | Identity and privilege abuse | all | `file:apps/llm-gateway/app/identity.py`, `test:apps/llm-gateway/tests/test_identity.py`, `journey:gateway_identity` — Every caller is identified (signed tokens or hashed service keys, roles, an MFA claim, lock-out), and the audit log records who did what. |
| ✅ | ASI04 | Agentic supply chain | all | `file:lifecycle/vet.py`, `file:governance/inspector.py`, `test:lifecycle/tests/test_vet.py`, `journey:vet_gate` — Third-party skills and plugins are vetted before use, the MCP bridge is read-only, and model weights are digest-checked. |
| 🟡 | ASI05 | Unexpected code execution | all | `file:governance/inspector.py`, `test:governance/tests/test_inspector.py`, `journey:inspect_sandbox` — Untrusted files are inspected in a sandbox, and weight files are scanned for code that would run on load; agents themselves run no generated code. |
| 🟡 | ASI06 | Memory and context poisoning | all | `file:apps/llm-gateway/app/main.py`, `test:apps/llm-gateway/tests/test_guardrails.py` — Context passed to a model is inspected; chat memories are not yet reviewable or switched off for shared accounts. |
| 🟡 | ASI07 | Insecure inter-agent communication | all | `file:local/compose/tls-internal.yml`, `journey:tls_internal` — Every service-to-service hop can run over internal TLS with verified names; agents do not yet sign or authenticate messages to each other. |
| 🟡 | ASI08 | Cascading failures | all | `journey:key_wiring_and_failover`, `test:apps/llm-gateway/tests/test_human_in_command.py` — A failing detector fails closed, a provider failure falls back down the ladder, and one command stops all AI; there is no automatic breaker that stops a looping agent. |
| 🟡 | ASI09 | Human-agent trust exploitation | all | `file:governance/honesty.py`, `test:governance/tests/test_honesty.py` — Writes an agent proposes wait for a person (the approved-action executor), and the honesty check catches made-up answers. |
| ✅ | ASI10 | Rogue agents | all | `file:apps/llm-gateway/app/killswitch.py`, `test:apps/llm-gateway/tests/test_human_in_command.py`, `test:apps/llm-gateway/tests/test_audit_chain.py` — A per-model or all-AI stop with no restart, a per-agent allowance, and a hash-chained audit log that shows what each agent did. |

## Integrity
- ✅ every evidence reference resolves and every 'supported' item is proven by a journey or test.

_Status is our own assessment of a lab estate, against the regulator's text as read on the date above. Challenge it._

