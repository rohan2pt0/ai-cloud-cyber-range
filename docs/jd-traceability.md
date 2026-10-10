# JD → Capability Traceability Matrix

How this range lets you *demonstrate* each requirement across all eight roles. Use this as
your interview crib: for any line an interviewer reads from their JD, point at the component.

Roles: **PwC** SM Cloud/AI Security · **EXL** SAVP Secure-AI Engineering · **CRISIL** AI
Security Engineer · **UAE** SM AI-Security Product Owner · **Deloitte** Mgr Cloud AI Security ·
**C-DOT** AI-Expert (Govt R&D, Agentic SOC) · **RBI** AI/ML Specialist & IT Security Expert.

| JD requirement | Roles | Where in the range | Artefact to show |
|---|---|---|---|
| OWASP LLM & Agentic Top 10 fluency | PwC, CRISIL, UAE | `apps/llm-gateway/app/guardrails.py` rule→OWASP map | per-rule category tags; red-team scorecard |
| MITRE ATLAS | PwC, EXL | `local/k8s/policies/falco-rules.yaml`, threat model §6 | ATLAS technique table |
| NIST AI 100-2 adversarial ML | PwC | `redteam/run_attacks.py`, notebook 01 | ASR ON vs OFF, evasion costs |
| Secure-by-design guardrails for LLM/RAG/Agentic | EXL, CRISIL, UAE | gateway PEP + C1 RAG rails + C6 agent controls | architecture §3/§4 |
| Secure MLOps/LLMOps, controls in CI/CD | EXL, CRISIL, UAE | `.github/workflows/devsecops.yml` | SARIF, SBOM, red-team gate |
| AI-SPM & cloud-native AI security | PwC | `redteam/aispm_scan.py` | posture scorecard (10/10) |
| Guardrails / runtime AI security | PwC, CRISIL | gateway + Model Armor/Prompt Shields/Bedrock + Falco | detector adapters |
| LLM firewall tools (Giskard/AI-Shield/Arthur) | CRISIL | `redteam/garak`, promptfoo, pluggable detectors | garak report |
| PII masking / privacy-by-design (DPDP/GDPR) | CRISIL, UAE | C2 redaction (Aadhaar/PAN/card/UPI) | redaction demo in notebook 01 |
| Python | all | entire `apps/` + `redteam/` | 13 passing unit tests |
| One cloud + Kubernetes security (CKS) | PwC | `local/k8s/*` kind+Kyverno+NetPol+PSS | admission-deny demo |
| Multi-cloud (AWS/GCP/Azure) | EXL, UAE | `infra/terraform/modules/*` | `terraform validate` clean |
| Data poisoning / model theft / supply chain | EXL | C1 quarantine, C8 signed registries, C12 SBOM/scan | Kyverno registry policy |
| Board-ready risk narratives & roadmaps | PwC, UAE | `redteam/board_report.py` | `docs/board-brief.md` |
| AI governance: NIST AI RMF, ISO 42001, SAIF, CSA | all | `docs/compliance-matrix.md` | framework crosswalk |
| EU AI Act / UAE / GDPR regulatory readiness | EXL, UAE | compliance matrix + residency design | regional config |
| Incident response / monitoring / anomaly detection | UAE, EXL | Falco + Loki/SIEM + audit log | runtime alerts |
| Product ownership / roadmap | UAE | this repo's roadmap + `docs/roadmap.md` | backlog |
| Azure AI Foundry / Azure OpenAI | CRISIL | Azure module + LiteLLM azure route + Prompt Shields | `azure-ai-security` module |
| Hugging Face / Copilot governance | CRISIL | Kyverno registry allow-list + model inventory | AI-SPM inventory |
| Agent identity / non-human identity | PwC | C6 SPIFFE-style tool identity, OBO | agent authorisation controls |
| **Agentic SecOps / AI-for-security / AI-SOC** | PwC, C-DOT, UAE | `ai-soc/` triage engine | incident cards, ATLAS+ATT&CK map |
| **Autonomous detection / alert correlation / threat summarisation** | C-DOT, UAE | `ai-soc/soc/triage.py` correlate+summarise | `samples/events.jsonl` → incidents |
| **CNAPP / CSPM / CWPP / DSPM posture** | Deloitte | AI-SPM AISPM-11/12 + Trivy config + conftest | `docs/aispm-report.json` |
| **Model inventory, risk classification, approval gates, traceability** | Deloitte, EXL, UAE | `governance/model-registry.yaml` | risk tiers + approval gate |
| **Vector store / RAG pipeline / orchestration security** | Deloitte | C1 RAG rails + gateway `/v1/guardrails/inspect` | AISPM-14 |
| **IAM: AWS IAM / Entra / Azure RBAC / GCP IAM, no long-lived keys** | Deloitte | OIDC federation + `automountServiceAccountToken:false` | AISPM-15 |
| **Cloud governance guardrails (Orgs/Control Tower/Azure Policy/Org Policy)** | Deloitte | `docs/cloud-governance.md` + Terraform budgets/OPA | policy-as-code |
| **IaC incl. CloudFormation/Ansible/Bash/PowerShell** | Deloitte | Terraform modules + bootstrap scripts | `terraform validate` |
| **Bedrock / SageMaker / Azure AI Foundry / Vertex AI familiarity** | Deloitte, CRISIL | LiteLLM routes + detector adapters + registry | `providers.py`, `litellm-config.yaml` |
| **ML frameworks (TensorFlow/PyTorch/Keras), model deployment** | RBI AI/ML | model registry + MLSecOps notebook path | `governance/model-registry.yaml` |
| **IS Audit / SOC operations / VAPT / PCI DSS** | RBI, UAE | audit log + AI-SOC + red-team + compliance matrix | `docs/compliance-matrix.md` |
| **Frontier-model risk assessment / adversarial AI research** | C-DOT | red-team corpus + NIST AI 100-2 notebook | `notebooks/01_*` |
| **Malware/RE, threat hunting, EDR/SOAR context** | C-DOT | AI-SOC correlation → ATT&CK + SOAR handoff | `ai-soc/README.md` |

## Certification runway (JDs "hold or earn")
Priority order given your current CISSP/CISM/CEH/Azure-Sec base and this lab as the hands-on vehicle:
1. **CKS** — the K8s plane (`local/k8s`) is your practice cluster.
2. **AWS Security Specialty** / **GCP Professional Cloud Security** — the Terraform modules are your study estate.
3. **ISO/IEC 42001 Lead Implementer** — the compliance matrix + AI-SPM is your management-system evidence.
4. **IAPP AIGP** / **ISACA AAISM** — governance; maps directly to `docs/compliance-matrix.md`.
5. **Practical DevSecOps CAISP** — the whole range is the portfolio.
