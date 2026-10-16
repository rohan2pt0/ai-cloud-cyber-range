<!--
  SecuRAX — Compliance & Standards Map.
  One place that answers "which standard/regulation does this estate help satisfy, and how?"
  Compliance-by-design (Principle P-4): controls are mapped BEFORE they are built. This is
  the artefact you hand an auditor; it is deliberately honest about what is built vs planned.
-->

# SecuRAX — Compliance & Standards Map

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Mappings and evidence exist; no independent audit or certification. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Compliance-by-design: every capability is mapped to the frameworks it supports *before* it is
built, and evidence is generated automatically where possible. This is written so an auditor
(for example an ISACA-certified one) can trace a requirement to a control to evidence without
you scrambling. **Caveat:** verify against primary sources before any client/production use —
regulations move; notes here are current to Oct 2026.

## 1. Frameworks in scope (full-forms + what each governs)
| Framework | Full form / body | Governs |
|---|---|---|
| **NIST CSF 2.0** | National Institute of Standards & Technology Cybersecurity Framework | Govern/Identify/Protect/Detect/Respond/Recover |
| **NIST AI RMF** | NIST AI Risk Management Framework | Trustworthy AI lifecycle |
| **NIST AI 100-2** | NIST adversarial ML taxonomy | AI attacks & mitigations |
| **ISO/IEC 27001:2022** | Information Security Management System (ISMS) | security controls (Annex A) |
| **ISO/IEC 42001:2023** | AI Management System (AIMS) | governance of AI |
| **ISO 22301** | Business Continuity Management System (BCMS) | continuity & resilience |
| **PCI DSS 4.0** | Payment Card Industry Data Security Standard | cardholder data |
| **SWIFT CSP** | SWIFT Customer Security Programme | financial messaging security |
| **RBI CSF** | Reserve Bank of India Cyber Security Framework (2016+) | bank cyber resilience |
| **RBI FREE-AI** | RBI Framework for Responsible & Ethical Enablement of AI (Aug 2025) | responsible AI in finance |
| **RBI Master Directions** | KYC, IT Outsourcing, IT Governance (ITGC), Digital Payment Security Controls (DPSC) | operational mandates |
| **SEBI CSCRF** | Securities & Exchange Board of India Cyber Security & Cyber Resilience Framework | market participants |
| **CERT-In Directions 2022** | Indian Computer Emergency Response Team | logging (180 days), incident reporting (6 h) |
| **DPDP Act 2023 / Rules 2025** | Digital Personal Data Protection | personal data of Indian residents |
| **IT Act 2000** | Information Technology Act | legal basis, Sec 43A/72A |
| **PMLA** | Prevention of Money Laundering Act | AML/KYC obligations |
| **GDPR** | EU General Data Protection Regulation | personal data (EU) |
| **CIS Controls v8** | Center for Internet Security | prioritised safeguards |
| **TOGAF / COBIT 2019 / ITIL 4** | Enterprise architecture / IT governance / IT service mgmt | how it's run |
| **MITRE ATLAS / ATT&CK** | Adversarial Threat Landscape for AI Systems / enterprise TTPs | threat modelling |
| **OWASP LLM & Agentic Top 10** | Open Worldwide Application Security Project | AI app risks |
| **CSA AICM / CCM** | Cloud Security Alliance AI Controls Matrix / Cloud Controls Matrix | cloud & AI controls |
| **SOC 2** | Service Organization Control 2 (AICPA) | trust services criteria |

## 2. Control crosswalk — NIST CSF 2.0 as the spine
NIST CSF 2.0 is used as the backbone because every other framework maps cleanly onto its six
functions. Each row names the SecuRAX capability and the pillar that delivers it.

| CSF Function | SecuRAX capability | Pillar | Cross-maps to |
|---|---|---|---|
| **GOVERN** | model registry, risk register, policy-as-code, this doc set | P5 | ISO 27001 cl.5-6, ISO 42001, COBIT, RBI ITGC |
| **IDENTIFY** | asset/AI inventory (AI-SPM), vuln scanning, threat modelling | P1/P5 | CIS 1-2, ISO 27001 A.5, RBI CSF |
| **PROTECT** | guardrails (PEP), IAM/SSO, secrets, encryption, Kyverno, NetPol, WAF, data-tier router | P1/P3 | ISO 27001 A.8, PCI DSS 3-6, DPDP, GDPR, SWIFT CSP |
| **DETECT** | SIEM (Wazuh), IDS (Suricata), Falco, AI-SOC correlation | P2 | PCI DSS 10, CERT-In, MITRE ATT&CK/ATLAS |
| **RESPOND** | TheHive/Cortex, AI-SOC incident cards, IR runbooks, kill-switches | P2 | NIST SP 800-61, CERT-In 6-h reporting |
| **RECOVER** | everything-as-code, 3-2-1 backups, BCDR drills | P0-spine | ISO 22301, RBI BCP |

## 3. India-specific regulatory coverage (BFSI focus)
| Obligation | How SecuRAX addresses it | Evidence |
|---|---|---|
| **DPDP Act 2023** data minimisation & protection | PII redaction at the gateway before any model call; Red-tier never leaves prem; DPIA template | `llm-gateway` rules, data-tier router |
| **RBI FREE-AI** responsible AI | fail-closed guardrails, explainable rule-based decisions, human-in-the-loop on high-impact, India data residency, full audit | `governance/model-registry.yaml`, audit log |
| **RBI CSF / DPSC** | network segmentation, MFA, logging, incident response | Kyverno/NetPol, Keycloak, Wazuh, TheHive |
| **CERT-In 2022** | ≥180-day log retention, 6-hour incident reporting | audit JSON retention, IR playbook |
| **SEBI CSCRF** | governance, VAPT, SOC, cyber-resilience | P2 SOC stack, red-team suite |
| **PMLA / KYC** | (application-level) identity verification controls, auditable trails | Keycloak + immutable audit (immudb) |
| **IT Act 2000 (43A/72A)** | reasonable security practices (ISO 27001), data confidentiality | ISMS controls, encryption |

## 4. How evidence is produced (audit-ready by construction — Principle P-4)
| Evidence type | Generated by | Cadence |
|---|---|---|
| AI defence rate / false-positive rate | `redteam/run_attacks.py` | every CI run |
| AI-SPM posture score (16 controls) | `redteam/aispm_scan.py` | every CI run |
| Board-ready risk narrative | `redteam/board_report.py` | every CI run |
| IaC misconfig & policy pass/fail | Trivy config + Conftest/OPA in CI | every push |
| SBOM (software bill of materials) | CycloneDX in CI | every build |
| Model inventory & approval gates | `governance/model-registry.yaml` | on change (PR) |
| Config/compliance scan (planned) | OpenSCAP + Wazuh SCA | scheduled |
| Runtime detections | Falco → AI-SOC | continuous |

## 5. TOGAF / COBIT / ITIL alignment (how it is *run*, not just built)
- **TOGAF** (The Open Group Architecture Framework): the layered reference architecture
  (Architecture §1) and the capability catalog are the Architecture Building Blocks; the
  roadmap is the Architecture Roadmap / Transition Architecture.
- **COBIT 2019** (Control Objectives for Information & Related Technologies): the GOVERN row
  and the risk register map to COBIT's governance (EDM) and management (APO/BAI/DSS/MEA)
  objectives.
- **ITIL 4** (Information Technology Infrastructure Library): the daily/weekly/monthly/quarterly
  review loops are the Continual Improvement practice; IR playbooks are Incident Management;
  change-as-code is Change Enablement.

> This map is a living document. When a control is built, link its evidence here; when a
> regulation changes, update the row and the date. That discipline is what makes the estate
> pass an audit on the first pass.
