<!--
  SecuRAX — Capability Catalog ("never re-research this again").
  For each capability the estate needs: the ONE recommended open-source tool to start with,
  at least one swappable alternative (Principle P-2), the phase it belongs to, and the
  standard/control it helps satisfy. Pick the primary unless you have a concrete reason not
  to. Everything in "Phase 0" is free and runs on the laptop.
-->

# SecuRAX — Capability Catalog

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Mixes built and planned capabilities; doc 59 gives each one its own light. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**How to use:** find the capability, use the **Primary** tool. Alternatives exist only so you
are never locked in (Principle P-2). The **Phase** column tells you when you actually need it
(don't build ahead of need — Principle P-1/80-20). All Phase-0 items are free and open-source.

> Selection rule: largest healthy community + open standard interface + runs on modest
> hardware wins. "Don't reinvent the wheel" (Principle P-3): these are globally
> tried-and-tested building blocks; you integrate, you don't re-implement.

## A. The brain — AI / ML
| Capability | Primary (start here) | Swappable alternatives | Phase | Satisfies |
|---|---|---|---|---|
| Local LLM runtime | **Ollama** | vLLM, LM Studio, llama.cpp | 0 | data residency (Red tier) |
| Local models | **Qwen 2.5 / DeepSeek / Llama 3** (Q4_K_M) | Mistral, Phi | 0 | NIST AI RMF, RBI FREE-AI |
| Multi-model router + budget | **LiteLLM** | OpenRouter (cloud), Portkey | 0 | cost control (P-1) |
| AI guardrails (PEP) | **this repo's `llm-gateway`** | NeMo Guardrails, Llama Guard | 0 | OWASP LLM Top 10 |
| Vector database (RAG) | **Qdrant** | pgvector, Chroma, Weaviate | 1 | knowledge retrieval |
| Private doc chat (RAG UI) | **AnythingLLM** | Open WebUI + pipelines | 0 | Red-tier Q&A |
| Unified chat (local+cloud) | **Open WebUI** | LibreChat | 0 | daily driver |
| AI red-teaming | **promptfoo + garak + PyRIT** | Giskard, Inspect | 0 | NIST AI 100-2, MITRE ATLAS |
| AI-SPM / model governance | **this repo's `aispm_scan.py` + `model-registry`** | Wiz/Prisma (paid) | 0 | ISO 42001 |

## B. Detect & respond — Security Operations (SOC)
| Capability | Primary | Alternatives | Phase | Satisfies |
|---|---|---|---|---|
| SIEM + HIDS + compliance | **Wazuh** | Elastic Security, Graylog | 1 | NIST CSF DETECT, PCI DSS 10 |
| Log pipeline / search | **OpenSearch** (or Elastic) | Loki, Graylog | 1 | CERT-In log retention |
| Threat intel platform (CTI) | **MISP** | OpenCTI | 1 | STIX/TAXII, CERT-In sharing |
| Incident response / case mgmt | **TheHive** | IRIS-DFIR | 1 | NIST CSF RESPOND |
| Analysis/enrichment engine | **Cortex** (pairs with TheHive) | n8n flows | 2 | SOAR enrichment |
| SOAR (playbook automation) | **Shuffle** | n8n, Tines (paid) | 2 | automated response |
| Network IDS/IPS | **Suricata** | Zeek (NDR), Snort | 1 | NIST CSF DETECT |
| Host visibility / DFIR | **OSQuery + Velociraptor** | GRR | 2 | forensics, hunting |
| AI-SOC triage (correlation) | **this repo's `ai-soc/`** | — (thin glue) | 0 | agentic SecOps |

## C. Protect — platform & application security
| Capability | Primary | Alternatives | Phase | Satisfies |
|---|---|---|---|---|
| Identity: SSO/MFA/RBAC | **Keycloak** | Authentik, Authelia, OpenBao | 1 | ISO 27001 A.5/A.8, RBI |
| Secrets management | **OpenBao** (HashiCorp Vault fork) | SOPS + age, Infisical | 1 | PCI DSS 3, DPDP |
| Vulnerability scanning | **OpenVAS/Greenbone** | Nuclei, Trivy | 1 | NIST CSF IDENTIFY |
| Web Application Firewall | **Coraza** (ModSecurity successor) + OWASP CRS | ModSecurity | 2 | OWASP, PCI DSS 6 |
| Container/image scanning | **Trivy** | Grype, Clair | 0 | supply chain (SLSA) |
| K8s admission policy | **Kyverno** | OPA Gatekeeper | 0 | CKS, ISO 42001 |
| Runtime threat detection | **Falco** | Tetragon | 0 | MITRE ATT&CK/ATLAS |
| Policy-as-code (general) | **OPA / Conftest** | Kyverno, Cloud Custodian | 0 | compliance-as-code |

## D. Posture & compliance automation
| Capability | Primary | Alternatives | Phase | Satisfies |
|---|---|---|---|---|
| Config/compliance scanning | **OpenSCAP + Wazuh SCA** | Lynis, CIS-CAT Lite | 1 | CIS Benchmarks, STIG |
| Cloud posture (CSPM) | **Prowler** | ScoutSuite, Steampipe | 1 | CSA CCM, cloud CIS |
| Cloud asset inventory | **CloudQuery / Steampipe** | — | 2 | asset mgmt |
| IaC misconfig scanning | **Trivy config / Checkov** | tfsec, KICS | 0 | secure IaC |
| Immutable audit log | **immudb** (start) → **Hyperledger Fabric** (scale) | WORM object-lock, Sigstore | 2 | ISACA audit, tamper-evidence |
| GRC register & evidence | **this repo's `docs/` + scanners** → **Eramba/GAPPS** | OpenGRC | 1 | ISO 27001 clause 6/9 |

## E. Data, platform & delivery
| Capability | Primary | Alternatives | Phase | Satisfies |
|---|---|---|---|---|
| Relational database | **PostgreSQL** | MariaDB | 0 | data integrity |
| Object storage (S3 API) | **MinIO** | SeaweedFS | 1 | backups, logs, WORM |
| Container runtime | **Docker / Podman** | — | 0 | portability (OCI) |
| Orchestration | **k3s** (light) / **kind** (test) → EKS/GKE/AKS | Nomad | 1 | HA, scale |
| Infrastructure as Code | **OpenTofu** (or Terraform) | Pulumi, Ansible | 0 | reproducibility |
| CI/CD | **GitHub Actions** | GitLab CI, Jenkins | 0 | DevSecOps |
| GitOps delivery | **Argo CD** | Flux | 2 | declarative deploys |
| Observability | **Prometheus + Grafana + Loki** | OpenTelemetry Collector | 1 | monitoring, SLOs |
| Workflow automation | **n8n** | Node-RED, Temporal | 0 | the "glue" |
| Agent orchestration (multi-step) | **n8n** → **CrewAI / LangGraph** | AutoGen | 1 | agentic SecOps, signal-from-noise |
| Team collaboration / ChatOps | **Mattermost** | Rocket.Chat, Matrix | 1 | coordination (G20 pattern) |
| Private cloud / virtualisation | **Proxmox VE** → **OpenStack** | oVirt, Harvester | 2 | sovereign compute at scale |
| Backup / BCDR | **restic / BorgBackup** (3-2-1) | Velero (K8s) | 0 | ISO 22301 |

## F. The human layer (Pillar 4)
| Capability | Primary | Alternatives | Phase | Satisfies |
|---|---|---|---|---|
| Knowledge base (second brain) | **Obsidian** (PARA + Zettelkasten) | Logseq | 0 | knowledge continuity |
| Life-OS / continuity app | **Guiding-Map PWA** (this estate) | — | 0 | family BCP, OPSEC |
| Personal OPSEC / self-OSINT | **this repo's `personal-rnd/`** | — | 0 | privacy-by-design |
| Personal finance / FIRE | **this repo's `fin_freedom.py`** + INDMoney | Firefly III | 0 | financial resilience |
| Tasks / automation triggers | **Todoist + n8n** | Vikunja (self-host) | 0 | GTD productivity |
| Community-signal decisions | **this repo's `intel/global_intel.py`** | manual Reddit/Amazon filters | 0 | wisdom-of-crowds + Lindy |

---
### Decision shortcuts
- **"I need X now and it's free + laptop-friendly"** → pick the Primary with Phase 0.
- **"This tool is dying / doesn't fit"** → switch to the listed alternative; the interface
  (P-2) means callers don't change.
- **"Is this worth adding yet?"** → only if a real need exists *and* a lower phase doesn't
  already cover it (P-1 / 80-20).
