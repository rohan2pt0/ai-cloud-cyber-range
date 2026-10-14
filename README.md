# SecuRAX — Robust · Adaptive · eXcellence-driven

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/rohan2pt0/ai-cloud-cyber-range/actions/workflows/devsecops.yml/badge.svg)](https://github.com/rohan2pt0/ai-cloud-cyber-range/actions/workflows/devsecops.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
![AI red-team defence](https://img.shields.io/badge/red--team%20defence-100%25%2F0%20FP-blue)
![Cost to start](https://img.shields.io/badge/cost%20to%20start-%E2%82%B90-success)
![Frameworks](https://img.shields.io/badge/mapped%20to-NIST%20%7C%20ISO%20%7C%20RBI%20FREE--AI%20%7C%20DPDP-informational)


## ▶ Start here (one step)

**On Windows:** double-click **`START-HERE-Windows.bat`** → your home screen opens at **http://localhost:8088**. That's it.

**On Mac/Linux:**
```bash
./securax up && ./securax open      # starts everything, opens your Guiding Map
```
Your **Guiding Map** (http://localhost:8088) is the home screen for everything — tasks, your local AI, money, OPSEC, and one-tap launch of the rest. Install it (Add to Home Screen) to use it like an app, even offline. Your data stays on your device.

> Health check any time: `./securax doctor` · Something not working: `./securax why` (Windows: double-click `WHATS-WRONG-Windows.bat`) · Update: `./securax update` (Windows: `UPDATE-Windows.bat`) · From any folder: `./securax shortcut` once, then `securax <command>` · Stop & free RAM: `./securax down`

---

> **SecuRAX** is the umbrella: one lifelong, **zero-investment-to-start**, vendor-agnostic,
> antifragile foundation that unifies AI security, AI-for-security (SecOps), a hybrid-AI brain,
> a life-OS, and governance/compliance — starting on one laptop and scaling to an MSSP, never
> rebuilt from scratch. This repository is **Pillar 1 (the AI Security Range)** and the home of
> the shared foundation.
>
> **Start here:** open [`portal/index.html`](portal/index.html) (the self-documenting command
> center — no install, just open it) and read the foundation in [`docs/securax/`](docs/securax/):
> [Overview](docs/securax/00-OVERVIEW.md) · [Principles](docs/securax/01-PRINCIPLES.md) ·
> [Architecture](docs/securax/02-ARCHITECTURE.md) ·
> [Capability Catalog](docs/securax/03-CAPABILITY-CATALOG.md) ·
> [Compliance Map](docs/securax/04-COMPLIANCE-MAP.md) · [Roadmap](docs/securax/05-ROADMAP.md) · [Extending](docs/securax/06-EXTENDING.md) · [Integrations](docs/securax/07-INTEGRATIONS.md) · [Operating model](docs/securax/08-OPERATING-MODEL.md) · [Tiers](docs/securax/09-OPEN-CORE-TIERS.md) · [Full-scale](docs/securax/10-FULL-STACK.md) · [Kaizen & antifragility](docs/securax/11-KAIZEN.md) · [Intelligent UX](docs/securax/12-INTELLIGENT-UX.md) · [Global Intelligence](docs/securax/13-GLOBAL-INTELLIGENCE.md) · [Guiding Map cockpit](docs/securax/14-GUIDING-MAP.md) · [Cost & models (never hit a limit)](docs/securax/15-COST-AND-MODELS.md) · [Agents army](docs/securax/16-AGENTS.md) · [Enterprise Architecture](docs/securax/17-ENTERPRISE-ARCHITECTURE.md) · [Financial Planner](docs/securax/18-FINANCIAL-PLANNER.md) · [Regulatory gap maps](docs/securax/35-REGULATORY-GAP-ASSESSMENT.md) · [Sign-in, incident clock, residency](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) · [Cockpit, storage, patching](docs/securax/37-COCKPIT-STORAGE-PATCHING.md) · [Practices, research, friction audit](docs/securax/38-ENGINEERING-PRACTICES-AND-RESEARCH.md) · [People scale, live sync, team chat](docs/securax/39-PEOPLE-SCALE-LIVE-SYNC-CHATOPS.md) · [Encryption in transit](docs/securax/40-ENCRYPTION-IN-TRANSIT.md) · [Quantum readiness](docs/securax/41-QUANTUM-READINESS.md) · [OpenCode Go + terminal agent](docs/securax/42-OPENCODE-GO-AND-THE-TERMINAL-AGENT.md) · [Inspect third-party software (REA)](docs/securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) · [Admission gate & self-healing sandbox](docs/securax/44-ADMISSION-GATE-AND-SELF-HEALING-SANDBOX.md) · [Measure your build models](docs/securax/45-AUTOBENCH-MEASURE-YOUR-BUILD-MODELS.md) · [Certification path](docs/securax/46-CERTIFICATION-PATH.md) · [Calm mode: less input, more insight](docs/securax/47-CALM-MODE-LESS-INPUT-MORE-INSIGHT.md).
>
> **Deploy it in 3 steps:** [`DEPLOY.md`](DEPLOY.md) (install Docker → `git clone` → one command) · **Start using it:** [`GETTING-STARTED.md`](GETTING-STARTED.md) · **See it visually:** [`portal/explainer.html`](portal/explainer.html) (one-page illustrated walkthrough).

---

# AI Cloud Cyber Range (SecuRAX · Pillar 1)

A multi-cloud, defence-in-depth **AI security cyber range** for hands-on mastery of secure-AI
engineering, **AI-for-security (Agentic SOC)**, adversarial ML / red teaming, AI-SPM
(CNAPP/CSPM/DSPM), guardrail/runtime security, and AI governance — built to demonstrate the
skills in eight senior AI-security JDs 

Runs on a Powerful laptop by default (Ollama + Docker + kind), and bursts into
**AWS + GCP + Azure** free tiers under a hard **₹2,500/month** ceiling with automated
kill-switches. Everything is code, tested, and mapped to **NIST AI RMF, ISO/IEC 42001, CSA
AICM/MAESTRO, Google SAIF, OWASP LLM & Agentic Top 10, and MITRE ATLAS**.

## Quick start (laptop, zero cost)
```bash
./securax up        # one command: start the whole live estate + print URLs
./securax demo      # red-team scorecard + posture scan (no cloud needed)
# or step-by-step:
./local/scripts/bootstrap-laptop.sh          # gateway + router + db + smoke test
WITH_AI=1 ./local/scripts/bootstrap-laptop.sh # also pull local models + Llama Guard
./local/scripts/kind-up.sh                    # Kubernetes plane (Kyverno + NetPol + Falco)
python3 redteam/run_attacks.py --fail-under 0.9   # adversarial-ML scorecard
./local/scripts/teardown.sh                   # stop everything (costs nothing overnight)
```

## What's inside
| Path | What it is | Why it matters |
|---|---|---|
| `apps/llm-gateway/` | OpenAI-compatible **guardrail gateway** (PEP): India-BFSI PII rails, injection/exfil/secret/canary detection, pluggable Llama Guard / Model Armor / Bedrock / Prompt Shields | secure-AI engineering, guardrails, privacy-by-design |
| `local/` | docker compose AI stack, kind cluster (audit on), **Kyverno + zero-trust NetPol + Falco/ATLAS**, bootstrap scripts | CKS, Kubernetes security, runtime detection |
| `infra/terraform/` | **AWS/GCP/Azure** modules, budget kill-switches, OIDC keyless CI, Model Armor / Content Safety | multi-cloud security architecture, FinOps-as-control |
| `policies/opa/` | conftest/OPA policies that **fail CI** on missing budgets, public buckets, disabled guardrails | policy-as-code, shift-left |
| `redteam/` | self-contained **attack suite**, promptfoo + garak configs, **AI-SPM scanner** (16 controls, CNAPP/CSPM/DSPM), **board-brief generator** | adversarial ML, AI-SPM, board-ready narratives |
| `ai-soc/` | **AI-SOC triage engine** (AI-for-security): correlate gateway+Falco+cloud telemetry → incidents, ATLAS+ATT&CK, guardrail-safe LLM summaries | agentic SecOps, autonomous detection, IR |
| `governance/` | **model registry**: inventory, risk tiers, approval gates, disallowed (shadow) models | model governance, ISO 42001, EU AI Act |
| `notebooks/` | Colab notebook: ASR with rails on/off, evasion, DPDP redaction | NIST AI 100-2, demos |
| `personal-rnd/` | **defensive** OPSEC / self-OSINT / LifeOS / FIRE tools (self-scoped) | privacy engineering, indirect-injection defence |
| `mcp/` | **MCP server** — let an AI assistant operate the estate (9 safe tools) | intelligent, hands-free control |
| `integrations/` | n8n workflows + Claude/Google/Microsoft connectivity | automation, API wiring |
| `docs/` | architecture, **JD traceability**, compliance crosswalk, cost controls, demo runbook | governance, the story you tell |
| `.github/workflows/` | DevSecOps: tests + red-team gate + SAST + secrets + SBOM + container/IaC scan | secure MLOps/LLMOps, CI/CD |

## Design principles
Secure-by-design · privacy-by-design · zero-trust · **fail-closed** · everything-as-code ·
**no single point of failure** (see `docs/architecture.md` §5).

## Documentation
- `docs/architecture.md` — reference architecture, control catalogue, resilience, threat model
- `docs/compliance-matrix.md` — NIST AI RMF / ISO 42001 / SAIF / CSA / OWASP / DPDP / RBI crosswalk
- `docs/cost-controls.md` — how it stays under ₹2,500/month
- `docs/demo-runbook.md` — a 15-minute guided walkthrough

> Status: 23 unit tests pass (`pytest` from repo root); all Terraform modules `validate`
> clean; red-team defence rate 100% with 0 false positives; AI-SPM posture 16/16. Figures/
> regulatory notes current to Oct 2026 — verify primary sources before client use.
