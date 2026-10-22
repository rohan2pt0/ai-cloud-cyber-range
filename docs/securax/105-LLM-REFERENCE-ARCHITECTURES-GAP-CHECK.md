# 105 · The AI plane against the world's reference architectures

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Checked against the code: every layer of the end-to-end LLM diagram and eleven frameworks (OWASP LLM and Agentic, NIST AI RMF and 600-1, ATLAS, SAIF, DASF, MAESTRO, ISO 42001, EU AI Act, RBI FREE-AI, MeitY). Two gateway holes found and closed (multi-part prompts, the system context). Fourteen smaller gaps dated in the queue; training layers out of scope by design. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** compare SecuRAX, layer by layer, with the standard end-to-end LLM architecture and with the frameworks the best
AI and security teams use, and leave no gap unseen.

**How it was checked:** against the code, not the docs. Each row below was traced to a file and a test (an inventory of 32
capabilities, 2026-10-22). Docs that say something exists without code count as "not built".

**The short answer:**
- SecuRAX is an AI *deployer's* estate. It runs, guards and governs models that others train. That is the right scope for a
  person, a team or a bank.
- **Two real holes were found and are closed in this change.** See section 1.
- Fourteen smaller gaps remain. Each has a date in `governance/queue.json` (section 4).
- Training layers (pre-training, RLHF, reward models, training clusters) are out of scope by design (section 5).

## 1. Fixed in this change

| Gap | What could happen | The fix |
|---|---|---|
| **G1.** A prompt sent as *parts* skipped every input rail | OpenAI's format allows `content` to be a list (`[{"type": "text", ...}]`), and chat apps use it for images. The gateway inspected only plain strings, so an injection or an Aadhaar number sent as a part went straight to the model and the cloud | Every text part of every message is now inspected, redacted and audited like a plain prompt (`_texts` in the gateway) |
| **G2.** The system message was never inspected | Chat apps put retrieved documents (RAG) in the system message. That is the usual road for *indirect* prompt injection (OWASP LLM01, Agentic ASI01 "goal hijack") and for personal data leaving in context | The system context is now inspected and redacted. Wording that is normal in a system prompt ("### Instruction", "you are now") is recorded but does not block. Hidden tag characters and an order to send data to an address always block (`inspect_context`) |
| AI-SPM check 14 passed on a name that existed nowhere | The posture scan reported RAG-chunk inspection because an endpoint existed, not because anything used it | The check now requires the inspection that the gateway actually runs |

Proof: `apps/llm-gateway/tests/test_guardrails.py`
(`test_a_prompt_sent_as_parts_meets_the_same_rails`, `test_the_system_context_is_inspected_never_blocked_for_ordinary_wording`).

## 2. Layer by layer: the end-to-end LLM diagram

The reference is the common five-layer picture of an LLM application: entry, inference, safety and output, training data,
and the cloud underneath.

| Layer | Component | SecuRAX | Where |
|---|---|---|---|
| Entry | Web, mobile, public API | ✅ | Open WebUI, the Life OS PWA, the store apps, the gateway's OpenAI-compatible API |
| Entry | Load balancer | 🟡 | One gateway on a laptop. Replicas, autoscaling and disruption budgets on Kubernetes (`gitops/charts/tenant`), render-tested only. See G8 |
| Entry | API gateway | ✅ | The AI security gateway is the one front door: cross-site write guard, TLS edge, tunnel with sign-in |
| Entry | Authentication (IAM/OAuth) | ✅ | OIDC/JWT (RS256 via JWKS, "none" refused), hashed API keys, MFA claim, lock-out. Off on a single laptop, on with `regulated on` |
| Entry | Rate limiting | ✅ | Per-caller sliding window, in-flight shedding, day and month token allowances |
| Entry | User context manager | 🟡 | Open WebUI keeps chat history and memories. SecuRAX has no memory controls of its own. See G10 |
| Entry | Response router | ✅ | LiteLLM ladders with fallbacks that always end on the local model; the gateway records requested vs served model |
| Inference | Prompt pre-processing | ✅ | Injection, jailbreak and smuggling rails; India-aware PII redaction; optional model detectors (Llama Guard, Model Armor, Prompt Shields, Bedrock) behind a circuit breaker; now every part and the system context (G1, G2) |
| Inference | Context windowing, tokenisation | 🟡 | A size cap and the model's own window. No token-exact truncation. See G13 |
| Inference | Model registry | ✅ | Risk tier, approval, owner and validated model per entry; served-but-unlisted models flagged. Each shipped model's digest is approved in the registry; `./securax ai check` refuses a changed or unlisted one and scans pickle-format weights for code (G4, closed 2026-10-22) |
| Inference | LLM engine, GPU cluster | 🟡 | Ollama on CPU, a remote GPU box, cloud models through the ladder. GPU scheduling is out of scope on one machine |
| Inference | Post-processing: sampling, fact-checking, guardrails | 🟡 | Output rails for secrets, exfiltration links, active HTML and canary leaks; the "careful" check-and-rewrite pass; stale-fact notes. Toxicity only via the optional detector. See G5, G6 |
| Safety and output | Safety filters, toxicity | 🟡 | As above. Bias and toxicity probes are not yet in the red team. See G5 |
| Safety and output | Human preference feedback | ⬜ | No feedback capture of our own. See G7 |
| Safety and output | Reward model, PPO, training cluster | ➖ | Out of scope (section 5) |
| Safety and output | Evaluation platform | 🟡 | Autobench grades build models. No answer-quality regression set for the chat models. See G6 |
| Safety and output | Kill switch | ✅ | Read on every request, fails closed, logged, no restart (`./securax ai stop`) |
| Training data | Collection, cleaning, pre-training and fine-tuning sets, RLHF loop | ➖ | Out of scope (section 5). The knowledge importer builds private RAG files with PII redaction, not training data |
| Cloud | Storage (data lake, DBs) | ✅ | Tiered storage that cleans itself; encrypted, ransomware-checked backups; restore drills |
| Cloud | Monitoring and logging | ✅ | Tamper-evident audit chain, Loki and Grafana, Prometheus metrics with SLOs, per-caller anomaly baselines, traceparent. No full OpenTelemetry SDK (doc 38 sets the trigger) |

## 3. Framework by framework

| Framework (version) | What it asks for | SecuRAX today | Gap |
|---|---|---|---|
| OWASP Top 10 for LLM Applications (2025) | Ten risks, LLM01 to LLM10 | Rails cover LLM01, 02, 05, 06, 07, 10; supply chain (03) for code and plugins; the red team scores only 01, 02, 05, 07 | G5: red-team every category; G4: model artefacts (03); G12: a full machine-checked map |
| OWASP Top 10 for Agentic Applications (Dec 2025) | ASI01 goal hijack to ASI10 rogue agents | Tool allow, deny and approval policy; read-only MCP; SSRF-guarded web agent; kill switch; per-agent allowance | G3: an approval *queue* (today approval only blocks); G10: memory poisoning (ASI06); G12: a full map |
| NIST AI RMF 1.0 and the GenAI profile (AI 600-1) | Govern, map, measure, manage; 12 GenAI risks | 600-1 machine-checked in `comply`: 3 supported, 7 partial, 2 gaps (IP; bias and toxicity) | G5 closes most partials; G12 adds RMF functions |
| MITRE ATLAS | Adversary tactics against AI | Findings and red-team results tagged with ATLAS ids; AI-SOC triage maps audit events to ATLAS | G5 adds the missing techniques to the red team |
| Google SAIF (2.0, with the agent map) | Data, infrastructure, model, application controls | Labels in the AI-SPM scan | G12: requirement-level map |
| Databricks DASF (2.0 plus the agentic extension, 2026) | 13 components, 97 risks, 73 controls, incl. MCP client and server | Not mapped | G12: map the deployer-relevant components |
| CSA MAESTRO | Seven-layer threat model for agents | Not mapped | G12: one threat model of the gateway, MCP and the twin, layer by layer |
| ISO/IEC 42001 (AI management system) | Policy, roles, risk, impact assessment, lifecycle, supplier controls | Mentioned; the registry and the board report carry parts | G12: a control map in `comply` |
| EU AI Act | Risk classes, transparency, logging, human oversight | Mentioned | G12: deployer duties only (SecuRAX is not a provider of a general-purpose model) |
| RBI FREE-AI (Aug 2025) | 26 recommendations in six pillars, among them a board-approved AI policy, an AI inventory, product approval, AI in audits, consumer protection and incident reporting | Inventory, approval tiers, kill switch, audit and the incident clock exist; RBI model-risk draft control pack exists | **G11 and G12 first for a BFSI owner:** a FREE-AI map in `comply`, a board AI-policy template and an AI incident runbook |
| India AI Governance Guidelines (MeitY, Nov 2025) | Seven principles; accountability, disclosure, grievance redress, safety | Partly through the above | G12: principle-level map |

## 4. What remains, with dates

Each item is in `governance/queue.json`, so `./securax backlog` and the daily Backlog issue show it until it is done.

| # | Gap | Risk it closes | By |
|---|---|---|---|
| G3 | Tool approval becomes a queue: the call waits, a person approves or refuses it from the Command Center or the phone, the agent resumes | ASI02 tool misuse; LLM06 excessive agency | 2026-11-05 |
| G4 | The model registry records each model's digest (Ollama and pulled weights); `ai check` refuses a changed or unlisted digest; pickle-format files are scanned before load | LLM03 supply chain; LLM04 poisoning | done 2026-10-22 |
| G5 | The red team covers all ten LLM and ten Agentic categories, plus bias and toxicity probes (promptfoo, garak where it runs offline), in the purple loop | LLM01–10, ASI01–10; NIST 600-1 bias | 2026-10-29 |
| G6 | An answer-quality set for the chat models (BFSI questions with expected facts), run on every model change; the score shown in `progress` | LLM09 misinformation; drift | 2026-11-12 |
| G7 | Thumbs up or down in the chat flows into that set, so bad answers become test cases | Human feedback, without RLHF | 2026-11-12 |
| G8 | Rate limits, allowances and the audit chain move to a shared store when more than one gateway runs | Bypass by spreading calls over replicas | when a second replica is first used |
| G9 | Provider keys leave the plaintext `.env` for an encrypted file (age/SOPS) unlocked at start | Key theft from a copied disk | 2026-11-19 |
| G10 | Chat memories: off by default for shared accounts, reviewable, and inspected like any context | ASI06 memory poisoning | 2026-11-05 |
| G11 | An AI incident runbook (jailbreak in use, data leaked through a model, model abuse, poisoned document) and a tabletop for it, wired to the incident clock | Incident response; FREE-AI incident reporting | done 2026-10-22: `./securax incident runbook`, `incident open --kind`, tabletop `ai-incident` |
| G12 | Requirement-level maps in `comply` for OWASP LLM and Agentic, RBI FREE-AI, ISO 42001, EU AI Act (deployer), SAIF, DASF, MAESTRO and the MeitY guidelines; a board AI-policy template | Assurance and audit | FREE-AI and OWASP done 2026-10-22 (`./securax comply free-ai`, `comply owasp-ai`); the rest 2026-11-26 |
| G13 | Token-exact context management: count with the model's tokenizer, trim the oldest turns, never cut the system context | Silent truncation; LLM10 cost | 2026-12-10 |
| G14 | The audit chain survives restarts and is anchored daily to the off-site backup (append-only) | Log tampering after a compromise | 2026-11-26 |
| G15 | Retrieval checks: documents carry an owner and a class, and a person only retrieves what they may read; new documents are scanned before indexing | Data leakage across users; RAG poisoning | 2026-11-19 |
| G16 | Cost per request in rupees, from a price table, in the allowance and the cockpit | LLM10; spend you can see | 2026-12-10 |

## 5. Out of scope, and why

| Layer | Why not | What SecuRAX does instead |
|---|---|---|
| Pre-training, data crawlers, cleaning and de-duplication at corpus scale | Training a foundation model needs data and compute far beyond a person or a bank's AI team, and is not where the risk of using AI sits | Choose models from the registry, by risk tier |
| RLHF, reward models, PPO, a training cluster | The same. Alignment is the model provider's duty | Guard the model's input and output; measure it (G6); feed bad answers back as tests (G7) |
| Fine-tuning | Possible later on rented compute (doc 15), only with a clear gain over retrieval | Retrieval over your own documents first |
| GPU scheduling | One laptop, or one remote GPU box | The ladder falls back to cloud or a smaller local model |

## 6. Sources

Read on 2026-10-22, paraphrased, never copied:
- [OWASP Top 10 for Agentic Applications (Dec 2025)](https://genai.owasp.org/)
- [Databricks AI Security Framework and its 2026 agentic extension](https://www.databricks.com/resources/architectures/databricks-ai-security-framework)
- [CSA MAESTRO](https://cloudsecurityalliance.org/blog/2025/03/24/threat-modeling-openai-s-responses-api-with-the-maestro-framework)
- [Google SAIF](https://saif.google/secure-ai-framework)
- RBI FREE-AI committee report (13 August 2025), and the MeitY India AI Governance Guidelines (5 November 2025), on the RBI
  and MeitY sites. Check the primary text before citing a recommendation.
