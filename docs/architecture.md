# AI Cloud Cyber Range — Reference Architecture

A multi-cloud, defence-in-depth AI security range built to demonstrate the capabilities
asked for across five senior AI-security JDs (PwC SM Cloud/AI Security, EXL SAVP Secure-AI
Engineering, CRISIL AI Security Engineer, Abu Dhabi Bank SM AI-Security Product Owner).
Runs on an HP Spectre x360 by default (free), bursts into AWS/GCP/Azure free tiers under
a hard ₹2,500/month ceiling.

> Design principles: **secure-by-design, privacy-by-design, zero-trust, fail-closed,
> everything-as-code, no single point of failure.** Every control maps to NIST AI RMF,
> ISO/IEC 42001, CSA AI Controls Matrix / MAESTRO, Google SAIF, OWASP LLM & Agentic
> Top 10, and MITRE ATLAS.

## 1. Logical architecture

```
                         ┌────────────────────────────────────────────────────┐
                         │                  CONTROL / GOVERNANCE                │
                         │  AI-SPM inventory · risk register · board brief ·    │
                         │  policy-as-code (OPA/Kyverno) · compliance matrix    │
                         └───────────────▲────────────────────────▲────────────┘
                                         │ evidence               │ policy
  client / analyst                       │                        │
      │  (mTLS)                          │                        │
      ▼                                                           ▼
┌───────────────┐   input rails   ┌──────────────────┐   OBO identity   ┌──────────────┐
│  AI Guardrail │───────────────▶ │  Model Router     │────────────────▶ │  Tools /     │
│  Gateway (PEP)│   LLM01/02/07   │  (LiteLLM):        │  C2/C3/C4/C5     │  back-ends   │
│  fail-closed  │◀─────────────── │  Ollama→Gemini→    │                  │  (bank APIs) │
└──────┬────────┘   output rails  │  Bedrock→Azure OAI │                  └──────────────┘
       │            LLM05/LLM10   └─────────┬──────────┘
       │ audit (JSON)                       │ no direct internet (NetworkPolicy)
       ▼                                     ▼
┌───────────────────────────────┐   ┌──────────────────────────────────────────────┐
│ Observability / SIEM          │   │ Model-based detectors (2nd layer, any cloud):  │
│ Loki+Grafana (local) →        │   │ Llama Guard (local) · GCP Model Armor ·        │
│ Wazuh / Sentinel / Chronicle  │   │ Bedrock Guardrails · Azure Prompt Shields      │
└───────────────────────────────┘   └──────────────────────────────────────────────┘
        ▲ runtime detection (Falco/ATLAS)            ▲ admission control (Kyverno), PSS restricted
        └──────────────── Kubernetes (kind local / EKS·GKE·AKS burst) ───────────────┘
```

## 2. Planes

| Plane | Local (laptop, free) | Cloud burst (free-tier / credits) |
|---|---|---|
| **Model** | Ollama (qwen2.5, llama-guard3) | Vertex/Gemini, Bedrock, Azure OpenAI via LiteLLM |
| **Guardrail (PEP)** | gateway container | Cloud Run / ECS / Container Apps |
| **Detectors (PIP)** | Llama Guard | Model Armor · Bedrock Guardrails · Prompt Shields |
| **Orchestration** | kind (3-node, audit on) | GKE Autopilot / EKS / AKS |
| **Policy** | Kyverno + OPA/conftest | same manifests, same rego |
| **Observability** | Loki + Grafana | Sentinel / Chronicle / Security Hub |
| **Posture (AI-SPM)** | `aispm_scan.py` | Defender for Cloud, Security Command Center |
| **IaC/CICD** | Terraform + GitHub Actions | same, OIDC-federated (keyless) |

## 3. Control catalogue (defence-in-depth)

The guardrail chain is intentionally layered so **no single control is a single point of
failure** — a bypass of one layer is caught by the next (see §5).

| ID | Control | Layer | OWASP / ATLAS | Framework |
|----|---------|-------|---------------|-----------|
| C0 | Input rails: injection, jailbreak, ASCII-smuggling, base64 | Gateway | LLM01 / AML.T0051,T0054 | SAIF, NIST-AI-RMF MANAGE |
| C1 | RAG chunk sanitisation + spotlighting | Gateway/App | LLM08 / ASI06 | ISO 42001 |
| C2 | PII redaction (Aadhaar/PAN/card/UPI, Verhoeff+Luhn) | Gateway | LLM02 | DPDP, GDPR, ISO 27701 |
| C3 | Output rails: exfil links, secrets, canary, active content | Gateway | LLM05/LLM07 / AML.T0057 | SAIF |
| C4 | Model-based detectors (Llama Guard / Model Armor / Prompt Shields / Bedrock) | PIP | LLM01 | CSA AICM |
| C5 | Rate limit + resource caps | Gateway/K8s | LLM10 | CSA AICM |
| C6 | Delegated tool identity (OBO), beneficiary allow-list, HITL on high-impact | Tools | ASI02/ASI03/ASI09 | NIST AI RMF |
| C7 | Egress allow-list (models have no direct internet) | K8s NetPol | LLM02/LLM05 | Zero-trust / SASE |
| C8 | Admission hardening (non-root, RO-FS, no :latest, limits, signed registries) | Kyverno | — / supply chain | CKS, ISO 42001 |
| C9 | Runtime detection (shell-in-container, egress, token read) | Falco | — / AML.T0053,T0055 | MITRE ATLAS |
| C10 | Full decision audit (JSON, ≥180d) | Gateway/SIEM | — | CERT-In 2022, RBI |
| C11 | Cost kill-switch per cloud | Terraform | LLM10 (econ DoS) | FinOps / NIST AI RMF |
| C12 | Supply chain: SBOM, image scan, secret scan, SAST, IaC scan | CI/CD | — / supply chain | SLSA, NIST SSDF |
| C13 | Adversarial-ML assurance suite in CI | CI/CD | all LLM / ATLAS | NIST AI 100-2 |
| C14 | Model registry: inventory, risk tiers, approval gates | Governance | — | ISO 42001, NIST AI RMF MAP, EU AI Act |
| C15 | **AI-SOC**: correlate telemetry → incidents (AI-for-security) | Detection | all / ATLAS+ATT&CK | NIST CSF DE/RS, SAIF |
| C16 | Cloud governance guardrails (SCP / Azure Policy / Org Policy) | Org | — | NIST CSF PR, CSA CCM |

## 4. End-to-end AI lifecycle coverage (EXL/CRISIL "secure the whole lifecycle")

- **Data ingestion / RAG** — chunk scanning, provenance tainting, poisoned-doc quarantine (C1).
- **Training / fine-tuning** — dataset governance + Hugging Face model allow-listing (policy-as-code; registry pinned by digest, C8/C12).
- **Model management** — model registry entries inventoried by AI-SPM; SBOM per image.
- **Inference / APIs** — the gateway PEP in front of every model, every cloud (C0–C5).
- **Agentic** — tool-identity, HITL, action budget, taint-aware authorisation (C6).
- **Infra** — zero-trust K8s, admission control, runtime detection (C7–C9).
- **Governance** — model registry with risk tiers + approval gates governs which models/datasets reach prod (C14).
- **Detect & respond** — the **AI-SOC** (C15) consumes gateway audit + Falco + cloud findings, correlates
  per identity, maps to ATLAS/ATT&CK, and emits incident cards; it sanitises its own inputs through the
  guardrail engine (second-order injection defence) — this is the "AI-for-security / Agentic SOC" plane.

## 5. No single point of failure (resilience design)

| Dimension | How SPOF is removed |
|---|---|
| **Model availability** | LiteLLM fallback chain Ollama→Gemini→Bedrock→Azure; local model keeps the range working fully offline. |
| **Guardrail PEP** | ≥2 replicas, HPA 2–6, PodDisruptionBudget, topology spread across nodes; stateless so any replica serves. |
| **Detector outage** | `FAIL_MODE=closed` — if a cloud detector is unreachable the request is blocked, not silently passed; deterministic rails still run in-process so one layer is never the only layer. |
| **Cloud dependency** | Three independent clouds, each individually toggleable; none is required. Laptop plane is self-sufficient. |
| **Control plane** | kind can be re-created from code in minutes; all state is in Git + IaC, nothing precious on the node. |
| **Cost** | Per-cloud budget + kill-switch; no single runaway can breach ₹2,500. |
| **Secrets** | OIDC federation (no long-lived keys to lose); `.env` git-ignored; canaries detect prompt/secret leakage. |
| **Data residency** | Mumbai/Central-India regions on every cloud (RBI/DPDP), so no cross-border SPOF. |

## 6. Threat model (MITRE ATLAS tactics exercised)

| ATLAS tactic | Technique | Range exercise | Defended by |
|---|---|---|---|
| Reconnaissance | AML.T0051 prompt injection | red-team corpus + garak | C0, C4 |
| ML Attack Staging | AML.T0054 jailbreak | DAN/dev-mode probes | C0, C4 |
| Exfiltration | AML.T0057 LLM data leakage | canary + secret probes | C3 |
| Exfiltration | AML.T0024 via egress | Falco egress rule | C7, C9 |
| Credential Access | AML.T0055 SA-token read | Falco token-read rule | C8, C9 |
| Resource Hijacking | economic DoS | rate limit + budget | C5, C11 |

See `docs/compliance-matrix.md` for the full framework crosswalk, `docs/jd-traceability.md`
for how each JD requirement maps to a component, and `docs/cost-controls.md` for the budget design.
