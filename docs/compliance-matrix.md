# Compliance & Framework Crosswalk

One estate, mapped to every framework the five JDs name. This is the "working command of
NIST AI RMF, ISO/IEC 42001, CSA MAESTRO/AICM and Google SAIF" artefact.

## NIST AI RMF (GOVERN / MAP / MEASURE / MANAGE)
| Function | Implemented by |
|---|---|
| GOVERN | policy-as-code (OPA/Kyverno), risk register, board brief, ownership in IaC |
| MAP | AI-SPM inventory (models, detectors, clouds), threat model (ATLAS), data-flow in architecture.md |
| MEASURE | red-team scorecard (defense rate, false-positive rate), posture score, CI gates |
| MANAGE | fail-closed guardrails, HITL on high-impact, incident detection (Falco), kill-switches |

## ISO/IEC 42001 (AI Management System)
| Clause theme | Evidence |
|---|---|
| AI policy & objectives | architecture.md design principles; this repo as the AIMS |
| Risk & impact assessment | threat model + AI-SPM gaps + board brief |
| Controls & Statement of Applicability | control catalogue C0–C13 |
| Lifecycle controls | lifecycle coverage §4 (ingestion→inference→agentic) |
| Monitoring & improvement | CI re-runs scorecard every push; drift roadmap |

## CSA AI Controls Matrix / MAESTRO / CCM
Layered threat modelling (Mission→Agent→Env→Security→Tooling→Risk→Ops) is reflected in the
agent control set (C6) and the defence-in-depth chain. AICM control domains map to C1–C13; the
Cloud Controls Matrix (CCM) domains map to the Terraform modules + cloud-governance guardrails.

## NIST CSF 2.0 (GOVERN / IDENTIFY / PROTECT / DETECT / RESPOND / RECOVER)
| Function | Implemented by |
|---|---|
| GOVERN | model registry + approval gates, policy-as-code, risk register |
| IDENTIFY | AI-SPM inventory (models/detectors/clouds/governed models), threat model |
| PROTECT | gateway rails, IAM/OIDC least-privilege, Kyverno, NetworkPolicy, cloud-governance SCP/Policy/Org-Policy |
| DETECT | Falco runtime rules, CSPM/DSPM findings, **AI-SOC correlation** |
| RESPOND | AI-SOC incident cards + recommended actions, IR playbook handoff, kill-switches |
| RECOVER | everything-as-code (kind/IaC re-create in minutes), 3-2-1 backups (personal-rnd OPSEC) |

## Google SAIF
| SAIF element | Control |
|---|---|
| Strong security foundations (least privilege, egress) | C7, C8, OIDC |
| Detection & response for AI | C9 Falco, C10 audit, SIEM |
| Automated defences (guardrails) | C0–C4 gateway + detectors |
| Platform-level controls | Kyverno, PSS restricted |
| Adversarial testing | C13 red-team suite |

## OWASP LLM Top 10 (2025) & Agentic Top 10 (2026)
| Risk | Control |
|---|---|
| LLM01 Prompt Injection / ASI01 Goal Hijack | C0, C1, C4 |
| LLM02 Sensitive Info Disclosure | C2, C3 |
| LLM05 Improper Output Handling | C3 |
| LLM06 Excessive Agency / ASI02 Tool Misuse | C6 |
| LLM07 System Prompt Leakage | C3 (canary) |
| LLM08 Vector/Embedding Weaknesses | C1 |
| LLM10 Unbounded Consumption | C5, C11 |
| ASI03 Identity/Privilege abuse | C6 (OBO) |
| ASI06 Memory/context poisoning | C1 (taint) |
| ASI08 Cascading / runaway | C5 (action budget) |
| ASI09 Insufficient oversight | C6 (HITL) |

## India BFSI & global regulatory
| Regulation | How addressed |
|---|---|
| **DPDP Act 2023 / DPDP Rules 2025** (phased to May 2027) | PII redaction at gateway before any model call; audit trail for breach reporting; data residency India |
| **RBI FREE-AI (Aug 2025)** 7 Sutras / 6 pillars | fail-closed guardrails, HITL, full auditability, India-region data, assurance via red-team |
| **CERT-In Directions 2022** | ≥180-day log retention (audit JSON) |
| **EU AI Act** | risk-tiering + transparency + logging; high-risk controls via C0–C13 |
| **GDPR / UAE PDPL** | privacy-by-design (C2), DPO contact, lawful-basis documentation |
| **ISO 27001 / SOC2 / NIST CSF** | zero-trust, audit, change-as-code, supply-chain (C12) |

> Caveat: regulatory items reflect sources current to Oct 2026 (RBI FREE-AI is advisory;
> DPDP Rules notified 13 Nov 2025, substantive obligations from ~May 2027). Verify against
> primary texts before client use.
