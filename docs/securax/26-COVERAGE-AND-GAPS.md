# 26 · Coverage check vs. the enterprise reference maps — and the 80/20 gaps

Seven reference maps were compared with what SecuRAX actually ships (not what the roadmap promises): India's CyberTech capability map (TechSagar), the future-security-tech wheel, the cybersecurity vendor ecosystem, the 12-domain "secure systems" cheat sheet, the fault-tolerant-systems cheat sheet, the DevOps toolchain, and the AWS service guide.
Rule applied: **build the ~20 % that closes ~80 % of the real risk for a sovereign, single-user, laptop-first estate; write down why the rest is deferred or out of scope.**
Legend: ✅ shipped & tested · 🟡 partial · ⬜ not built · ➖ out of scope (with reason).

## 1. Secure-systems cheat sheet (12 domains)
| # | Domain | Status | Where / what | Gap → decision |
|---|---|---|---|---|
| 1 | Authentication | 🟡 | Open WebUI accounts; gateway principal; sync tokens; Keycloak = roadmap Phase 1 | MFA/SSO only matter once multi-user → **later** (Phase 1) |
| 2 | Authorization | ✅ | Data-tier routing, per-principal rate limits, least-privilege compose (`cap_drop`, `read_only`, `no-new-privileges`) | — |
| 3 | Encryption | 🟡 | PII/PAN redaction before egress; `.env` now `chmod 600`; backups `chmod 600` | TLS for LAN use → use Tailscale (documented) rather than self-managed certs |
| 4 | Vulnerability mgmt | 🟡 | Trivy/Semgrep/gitleaks in CI; `security` compose profile | **Next #1:** `./securax scan` for local images |
| 5 | Audit & compliance | ✅ | JSON audit line per decision → Loki; compliance matrix (RBI/CERT-In/DPDP/SEBI) | **Next #2:** `./securax evidence` one-file export for auditors |
| 6 | Network security | 🟡 | 3 networks (edge / modelplane / data); localhost-only host binds by default; only the gateway is the published front door; output rails catch exfiltration. The model network is *not* egress-blocked (the router must reach cloud providers) | Egress allow-list per provider host → **later** (needs a proxy container; low value on a single laptop) |
| 7 | Terminal/endpoint | ➖ | Not an endpoint product | Use your corporate EDR; SecuRAX covers the AI plane |
| 8 | Emergency response | ✅ **new** | `docs/securax/27-INCIDENT-RUNBOOK.md` (leaked key, everything blocked, suspected breach) | — |
| 9 | Container security | 🟡 | Gateway/sync hardened (`cap_drop`, `read_only`, `no-new-privileges`), Trivy image scan in CI, Kyverno/Falco manifests for k8s | **Pin floating tags:** `litellm:main-stable` and `anythingllm:latest` move under you (verify current stable tags, then pin) → part of Next #1 |
| 10 | API security | ✅ | Gateway: principal + per-minute rate limit, input/output rails, canary tokens, fail-closed detector | — |
| 11 | 3rd-party management | 🟡 | Provider catalog; PII redacted before any cloud call; Red-tier never leaves | **Next #3:** per-provider data-handling register in `providers list` (needs verified facts per vendor) |
| 12 | Disaster recovery | ✅ **new** | `./securax backup` / `restore` (verified, checksummed, owner-only, retention) — proven by the sandbox: volume destroyed → restored → same account signs in | Off-site copy is yours (3-2-1) |

## 2. Fault-tolerant-systems cheat sheet
| Pattern | Status | How |
|---|---|---|
| Replication | ➖ | Single-node by design; backups instead (DR above). HA = Phase 2/3 (k3s) |
| Redundancy | ✅ | Multiple model providers + a local floor (the ladder) |
| Load balancing | 🟡 | LiteLLM spreads/falls over across providers; no multi-instance LB needed on one laptop |
| Failover | ✅ | Ladder + `up` self-heal (sandbox: kill router/gateway/ollama) |
| Graceful degradation | ✅ | Lite mode, tiny/small model tiers, core-only start |
| Monitoring & alerting | ✅ **new** | `./securax watch` (heals + optional webhook alert); Command Center dots; `doctor` |

## 3. DevOps toolchain (Code → Plan → Build → Test → Release → Deploy → Operate → Monitor)
| Stage | Status | SecuRAX |
|---|---|---|
| Code/Plan | ✅ | GitHub, BUILD-CONTRACT, CHANGELOG |
| Build/Test | ✅ | GitHub Actions: lint, 195 unit tests, gitleaks/Semgrep/Trivy, **user-perspective sandbox** |
| Release | ✅ | SemVer + `VERSION` stamped into badge/gateway (doc 21) |
| Deploy | ✅ | Docker Compose (local), Terraform AWS/GCP/Azure + OPA (cloud) |
| Operate/Monitor | ✅ | Prometheus/Grafana/Loki profile, `watch`, `doctor` |

## 4. Future-security-tech wheel & vendor ecosystem
| Area | Status | Notes |
|---|---|---|
| Data security (DLP, masking, DSPM) | ✅/🟡 | Redaction + data tiers + AI-SPM/DSPM scanners; no homomorphic/quantum-safe crypto (➖ 5+ yr horizon) |
| Cloud security (CSPM/CWPP/zero-trust) | ✅ | Terraform + OPA, AI-SPM CSPM checks, Kyverno/Falco manifests |
| AppSec (SAST/SCA/API) | ✅ | Semgrep, Trivy, gitleaks, gateway as API-threat protection |
| Network (NGFW/ZTNA/DDoS) | ➖/🟡 | Tailscale for ZTNA-style access; perimeter products are out of scope for a laptop estate |
| IAM | 🟡 | See domain 1 |
| Incident response / hunting | ✅/🟡 | AI-SOC triage with MITRE mapping; Wazuh/MISP/TheHive = roadmap Phase 1 |
| Advanced detection (AI SOAR, deception) | 🟡 | n8n workflows + AI-SOC; deception tech ➖ |
| **AI security (HiddenLayer / Protect AI / Robust Intelligence class)** | ✅ | The core of SecuRAX: guardrail gateway, red-team (promptfoo/garak/PyRIT), AI-SPM, model registry |

## 5. India CyberTech capability map (TechSagar)
In scope and covered: **ML & AI, NLP, Data Science, Cloud & Virtualisation, Cyber Security, Identity & Authentication, App Infra & Software, Mobility & Endpoint (PWA), Digital Forensics (🟡 audit trail; evidence export = Next #2), Cryptology (🟡 redaction/hash; PQC ➖)**.
Out of scope (not what this product is): IoT, blockchain (a roadmap option for the audit log), robotics, UAV, AR/VR, computer vision, wireless, semiconductors, materials, NextGen computing, HCI, location, software-defined networking.

## 6. AWS service guide
Where AWS matters here and how SecuRAX meets it: **Bedrock** (provider plugin ✅), **IAM/KMS/CloudHSM** (Terraform + OPA guardrails ✅), **GuardDuty/Inspector/Macie/Detective** (equivalents: AI-SOC, Trivy, DSPM scanner — cloud-native versions are used when you deploy to AWS, wired via Terraform), **S3/Backup** (target for the off-site copy of `./securax backup`), **SageMaker/Rekognition/Comprehend/Lex** (not needed: local + provider models cover the use cases; add as a provider plugin if you want them).

## 7. What was built from this analysis (this release)
1. `./securax backup` / `restore` — DR with integrity verification (sandbox journey `backup_restore`).
2. `./securax watch` — monitoring, auto-heal, alerting (sandbox journey `watchdog_heals_and_alerts`).
3. `.env` and backups owner-only (key management).
4. Incident runbook (doc 27).

## 7b. Built in the follow-up pass
5. `./securax evidence` — auditor pack (no prompts/keys; unit-tested for secret-freedom).
6. `./securax scan` — Trivy over the images in use (needs internet for the vulnerability DB; not exercised by the sandbox).
7. `./securax models` / daily self-correction of retired provider model names.
8. `./securax autobuild` — gated, rollback-safe build loop (the path to building SecuRAX without paid Claude).

## 8. Ranked next (80/20) — what is still open
1. **Pin the two floating image tags** (`litellm:main-stable`, `anythingllm:latest`) after verifying current stable tags, plus an SBOM (CycloneDX) in `scan`.
2. Provider data-handling register (domain 11) — only with vendor-verified facts, shown when you add a key.
3. Measure the build agent: run `autobuild` on ~10 real small tasks with the cheap/local ladder and record pass-rate and escalations (doc 23) — only then decide how much to lean on it.
