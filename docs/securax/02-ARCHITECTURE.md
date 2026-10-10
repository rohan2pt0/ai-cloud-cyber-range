<!--
  SecuRAX — Unified Architecture.
  Shows the layered design, how the five pillars share one spine, the Red/Yellow/Green
  data-classification model, and the recognised design patterns in use. ASCII diagrams
  are used so the picture renders anywhere (terminal, GitHub, editor) with no tooling.
-->

# SecuRAX — Unified Architecture

One estate, five pillars, **one shared spine**. The spine is what prevents five disconnected
projects: common identity, common data-classification, common policy-as-code, common
observability, common audit trail. Everything plugs into that spine through open interfaces
(Principle P-2), so any single component is swappable.

## 1. Layered reference architecture (TOGAF-style, bottom-up)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  L6 · EXPERIENCE        Portal UI · Guiding-Map PWA · dashboards · chat         │  ← humans
├──────────────────────────────────────────────────────────────────────────────┤
│  L5 · INTELLIGENCE      Hybrid LLM brain (local Ollama ↔ cloud) · agents ·      │
│                         guardrail gateway (PEP) · AI-SOC triage · RAG           │
├──────────────────────────────────────────────────────────────────────────────┤
│  L4 · AUTOMATION        n8n workflows · CI/CD · policy-as-code · IaC            │
├──────────────────────────────────────────────────────────────────────────────┤
│  L3 · SECURITY SERVICES SIEM · CTI · SOAR/IR · IDS/IPS · vuln-mgmt · CSPM/DSPM  │
├──────────────────────────────────────────────────────────────────────────────┤
│  L2 · DATA & KNOWLEDGE  PostgreSQL · object store · vector DB · Obsidian vault  │
├──────────────────────────────────────────────────────────────────────────────┤
│  L1 · PLATFORM          Docker Compose → Kubernetes (k3s/kind→EKS/GKE/AKS)      │
├──────────────────────────────────────────────────────────────────────────────┤
│  L0 · FOUNDATION SPINE  Identity (OIDC/SAML) · Secrets (Vault) · Data tiers ·   │
│                         Observability (OTel) · Audit trail · Backup (3-2-1)     │
└──────────────────────────────────────────────────────────────────────────────┘
      Legend: PEP = Policy Enforcement Point · OTel = OpenTelemetry · IaC = Infrastructure as Code
```
Abbreviations (full-forms): **SIEM** = Security Information and Event Management · **CTI** =
Cyber Threat Intelligence · **SOAR** = Security Orchestration, Automation and Response ·
**IR** = Incident Response · **IDS/IPS** = Intrusion Detection/Prevention System · **CSPM** =
Cloud Security Posture Management · **DSPM** = Data Security Posture Management · **RAG** =
Retrieval-Augmented Generation · **OIDC** = OpenID Connect · **SAML** = Security Assertion
Markup Language.

## 2. The five pillars on the shared spine
```
                         ┌───────────────── L0 SHARED SPINE ─────────────────┐
                         │ identity · secrets · data-tiers · audit · OTel      │
                         └───▲────────▲────────▲────────▲────────▲────────────┘
                             │        │        │        │        │
                    ┌────────┴──┐ ┌───┴────┐ ┌─┴──────┐ ┌┴───────┐ ┌┴─────────┐
                    │ P1 AI-Sec │ │ P2 AI- │ │ P3 SEN-│ │ P4 Life│ │ P5 GRC   │
                    │   Range   │ │   SOC  │ │  TINEL │ │  -OS   │ │ (proof)  │
                    │ guardrails│ │ detect │ │ brain  │ │ human  │ │ controls │
                    │ red-team  │ │ CTI/IR │ │ +auto  │ │ +OPSEC │ │ +audit   │
                    └───────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```
Each pillar is independently useful and independently deployable, but they interoperate:
P2 (AI-SOC) consumes P1's audit logs; P3 (the brain) powers P2's triage and P4's assistants;
P5 (GRC) reads evidence from all of them.

## 3. Data classification — the Red / Yellow / Green model (the router's law)
Nothing moves until it is classified. This is the single most important control for a person
who protects banking-grade data; it is enforced *before* any processing (Principle P-4).

| Tier | Meaning | Routing rule | Examples |
|------|---------|--------------|----------|
| 🔴 **Red** | Restricted | **Local models / on-prem only.** Never leaves the machine. | Customer data, internal IPs, incident details, bank architecture, Aadhaar/PAN |
| 🟡 **Yellow** | Internal | Local preferred; cloud **only after sanitisation** (entity masking/redaction) | Security procedures, non-attributed analysis, career plans with employer context |
| 🟢 **Green** | General | Cloud AI acceptable | Public threat intel, certification study, general drafting |

The **data-tier router** (an automation/n8n node + the guardrail gateway) classifies each
request, masks sensitive entities with format-preserving redaction when needed, routes to the
correct model, and de-masks the response locally before it reaches you.

## 4. Design patterns in use (named, so the structure is predictable — Principle P-5)
| Pattern | Where | Why |
|---|---|---|
| **Policy Enforcement Point (PEP)** | `apps/llm-gateway` | One choke-point enforces policy on all AI traffic |
| **Strategy** | `providers.py`, model router | Swap detectors/models/clouds without touching callers |
| **Adapter** | tool/detector adapters | Wrap heterogeneous tools behind one interface |
| **Pipeline** | ingest → classify → route → act | Clear, testable stages for data flow |
| **Circuit-Breaker** | `FAIL_MODE=closed` | Fail safe when a dependency is down |
| **Sidecar** | observability/log shippers | Cross-cutting concerns without app changes |
| **Policy-as-Code** | OPA/Conftest, Kyverno | Governance is version-controlled and testable |
| **Event-driven correlation** | `ai-soc/` | Telemetry → incidents, decoupled producers/consumers |

## 5. How the existing repo maps onto this architecture (nothing is wasted)
| Architecture element | Already implemented in |
|---|---|
| L5 guardrail gateway (PEP) | `apps/llm-gateway/` |
| L5 AI-SOC triage | `ai-soc/` |
| L3/L5 red-team & AI-SPM | `redteam/` |
| L4 automation & CI/CD | `.github/workflows/`, `local/scripts/` |
| L1 platform (local) | `local/compose/`, `local/k8s/` |
| L1 platform (cloud) | `infra/terraform/` |
| L0 governance/audit | `governance/`, `docs/compliance-matrix.md` |
| P4 human layer | `personal-rnd/`, Guiding-Map PWA |

## 6. Scaling path (same estate, never rebuilt — Principle P-1/P-7)
```
Phase 0  Laptop (Docker Compose, Ollama, free tiers)                    ₹0
   │  trigger: need HA / always-on / family access
Phase 1  Mini-PC or home server (32–64 GB), laptop becomes a client     one-time HW
   │  trigger: remote access / multi-device / client pilot
Phase 2  Single cloud VM + managed Postgres + object store              pay-as-you-go
   │  trigger: multiple workloads / need orchestration
Phase 3  Kubernetes (k3s on-prem or EKS/GKE/AKS), GitOps (Argo CD)      elastic
   │  trigger: multiple clients / tenants (MSSP)
Phase 4  Multi-tenant MSSP: per-tenant isolation, SSO, billing, SLAs    revenue-funded
```
Each arrow is a documented trigger in [`05-ROADMAP.md`](05-ROADMAP.md); you never migrate
before the trigger fires.
