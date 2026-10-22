# Gap assessment — RBI, Framework for Responsible and Ethical Enablement of Artificial Intelligence (FREE-AI), committee report

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Complete; every reference resolves (fitness `regulatory-maps`). Titles paraphrased from a summary of the report: confirm against the RBI text. Open gaps are listed inside. [What the lights mean](../../index.md#the-status-lights)
<!-- status:end -->

> The RBI FREE-AI committee report's 26 recommendations (six pillars) assessed against what the estate demonstrably does. Recommendations addressed to the RBI, the government or the industry are marked not applicable; those the board owns are entity duties and never counted as covered. The report is guidance from a committee, not a binding direction. Titles are paraphrased; the notes are our own assessment and can be wrong: challenge them.

Source: [RBI, Framework for Responsible and Ethical Enablement of Artificial Intelligence (FREE-AI), committee report](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=61018) — Reserve Bank of India, 13 August 2025; read 2026-10-22. Recommendation titles paraphrased from a professional summary of the report (the RBI's PDF could not be fetched from here); numbering is per pillar, not the report's own. Confirm against the RBI's text before relying on it. Status is our own judgement.

Applicability scope: all layers / categories (use `--category` to narrow).

**Software-scope coverage: 70.0%** of 10 requirements software can address (✅ 4 supported · 🟡 6 partial · ⬜ 0 gap), plus **3 obligations that belong to the regulated entity** (🏛, never counted as covered by software) and 13 not applicable (➖).

> This is **not** a compliance certification and a tool cannot make an entity "100% compliant"; it shows what the estate demonstrably does, what it does not, and what only the entity can do.

## Backlog — what to build or fix, highest priority first

- 🟡 **PRO-1** (high) Consumer protection: transparency, fairness and grievance redress — Answers say they come from AI; grievance redress is the entity's; there are no bias or fairness probes yet. **Next:** Bias and toxicity probes in the purple loop (doc 105, G5); a disclosure line the entity can set per channel.
- 🟡 **PRO-3** (high) Regular red teaming of AI systems — The red team runs in the purple loop and scores four of the ten OWASP LLM categories. **Next:** Every OWASP LLM and Agentic category, plus bias probes (doc 105, G5).
- 🟡 **ASR-2** (medium) Risk-based internal and third-party audits of AI — A hash-chained gateway log, a checksummed evidence pack and these machine-checked maps give an auditor something to test; the audit itself is the entity's. **Next:** An auditor's export of the AI controls with their evidence, in one file.
- 🟡 **GOV-2** (medium) Data lifecycle governance for data used in AI — Classification-aware routing keeps local data off cloud models, personal data is redacted, and stored data has limits and tiers; there is no record of which data sources feed which knowledge base. **Next:** A lineage record: each knowledge base and the sources it was built from, with owner and class (doc 105, G15).
- 🟡 **GOV-4** (medium) AI-specific risk checks in product approval — High-risk models need named approvers and evidence (threat model, red-team scorecard, DPIA) in the registry, and the inventory flags an unapproved model; no sign-off checklist is generated for the product committee. **Next:** A product-approval checklist generated from the registry, signed by the committee.
- 🟡 **PRO-5** (low) AI incident reporting and sector risk intelligence — AI incident runbooks start the right reporting clocks and keep sealed evidence; the sector-wide AI incident repository is the RBI's to set up, so no channel to it exists yet. **Next:** Add the sector AI incident channel to the regulators once the RBI names it.

## Every requirement

| | Ref | Requirement | Applies | Evidence / note |
|---|---|---|---|---|
| ➖ | INF-1 | Financial-sector data infrastructure | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | INF-2 | AI innovation sandbox | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | INF-3 | Incentives, funding and shared compute for smaller institutions | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | INF-4 | Indigenous AI models as public goods | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. The estate runs open models locally, so such models could be used when published. |
| ➖ | INF-5 | AI combined with digital public infrastructure | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | POL-1 | Adaptive policies, reviewed as AI risks change | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | POL-2 | AI for financial inclusion, with proportionate compliance | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | POL-3 | A flexible AI liability framework | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | POL-4 | A standing committee and institution for continuous AI oversight | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| 🏛 | CAP-1 | Training for the board and staff on AI governance and risk | all | The entity trains its people. The estate's board report and range exercises can serve as material. |
| ➖ | CAP-2 | Capacity building for regulators and supervisors | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | CAP-3 | A platform for sharing AI use cases and lessons | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| ➖ | CAP-4 | Awards and grants for responsible AI innovation | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. |
| 🏛 | GOV-1 | A board-approved AI policy | all | The board approves the policy. The estate supplies what the policy points to: the inventory, the approval tiers, the stop switch and the incident runbooks. |
| 🟡 | GOV-2 | Data lifecycle governance for data used in AI | all | `file:apps/llm-gateway/app/residency.py`, `test:apps/llm-gateway/tests/test_residency.py`, `journey:gateway_residency` — Classification-aware routing keeps local data off cloud models, personal data is redacted, and stored data has limits and tiers; there is no record of which data sources feed which knowledge base. |
| ✅ | GOV-3 | AI system governance across the model lifecycle | all | `file:governance/model-registry.yaml`, `test:governance/tests/test_aicontrol.py`, `test:governance/tests/test_modelcheck.py`, `test:apps/llm-gateway/tests/test_human_in_command.py` — Every model has a risk tier, owner, approval, validation date and decommission record; weights must match an approved digest; any model or all AI can be stopped at once. |
| 🟡 | GOV-4 | AI-specific risk checks in product approval | all | `file:governance/model-registry.yaml`, `test:governance/tests/test_aicontrol.py` — High-risk models need named approvers and evidence (threat model, red-team scorecard, DPIA) in the registry, and the inventory flags an unapproved model; no sign-off checklist is generated for the product committee. |
| 🟡 | PRO-1 | Consumer protection: transparency, fairness and grievance redress | all | `test:apps/llm-gateway/tests/test_human_in_command.py` — Answers say they come from AI; grievance redress is the entity's; there are no bias or fairness probes yet. |
| ✅ | PRO-2 | Cybersecurity against AI-specific threats, and AI for detection | all | `file:apps/llm-gateway/app/guardrails.py`, `test:apps/llm-gateway/tests/test_guardrails.py`, `journey:purple_loop`, `file:ai-soc/soc/triage.py` — Input and output rails against injection, leakage and exfiltration, proven by the red team; the AI-SOC triages alerts. |
| 🟡 | PRO-3 | Regular red teaming of AI systems | all | `file:redteam/run_attacks.py`, `journey:purple_loop` — The red team runs in the purple loop and scores four of the ten OWASP LLM categories. |
| ✅ | PRO-4 | AI contingencies in the business continuity plan | all | `file:governance/continuity.json`, `test:governance/tests/test_jewels_continuity.py`, `journey:key_wiring_and_failover` — An AI outage is a continuity scenario with its steps; a failed provider falls back to the next rung and the local model. |
| 🟡 | PRO-5 | AI incident reporting and sector risk intelligence | all | `file:governance/incident.py`, `test:governance/tests/test_ai_incidents.py`, `journey:incident_clock` — AI incident runbooks start the right reporting clocks and keep sealed evidence; the sector-wide AI incident repository is the RBI's to set up, so no channel to it exists yet. |
| ✅ | ASR-1 | An AI inventory, and a contribution to a sector repository | all | `file:governance/aicontrol.py`, `test:governance/tests/test_aicontrol.py` — ./securax ai inventory lists every model with tier, owner and validation due, and checks it against what the gateway actually serves. |
| 🟡 | ASR-2 | Risk-based internal and third-party audits of AI | all | `test:apps/llm-gateway/tests/test_audit_chain.py`, `journey:comply_evidence` — A hash-chained gateway log, a checksummed evidence pack and these machine-checked maps give an auditor something to test; the audit itself is the entity's. |
| 🏛 | ASR-3 | AI governance and use disclosed in annual reports | all | The entity discloses. The inventory and the board report give the numbers. |
| ➖ | ASR-4 | A standard AI compliance toolkit | all | Addressed to the RBI, the government or the industry, not to a regulated entity's own estate. For one entity, ./securax comply and ./securax readiness do this job. |

## Integrity
- ✅ every evidence reference resolves and every 'supported' item is proven by a journey or test.

_Status is our own assessment of a lab estate, against the regulator's text as read on the date above. Challenge it._

