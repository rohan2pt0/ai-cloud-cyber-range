# SecuRAX — Robust · Adaptive · eXcellence-driven

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
> [Compliance Map](docs/securax/04-COMPLIANCE-MAP.md) · [Roadmap](docs/securax/05-ROADMAP.md) · [Extending](docs/securax/06-EXTENDING.md).
>
> **Start using it:** [`GETTING-STARTED.md`](GETTING-STARTED.md).

---

# AI Cloud Cyber Range (SecuRAX · Pillar 1)

A multi-cloud, defence-in-depth **AI security cyber range** for hands-on mastery of secure-AI
engineering, **AI-for-security (Agentic SOC)**, adversarial ML / red teaming, AI-SPM
(CNAPP/CSPM/DSPM), guardrail/runtime security, and AI governance — built to demonstrate the
skills in eight senior AI-security JDs (PwC, EXL, CRISIL, UAE bank, Deloitte, C-DOT, RBI)
during interviews.

Runs **free on an HP Spectre x360** by default (Ollama + Docker + kind), and bursts into
**AWS + GCP + Azure** free tiers under a hard **₹2,500/month** ceiling with automated
kill-switches. Everything is code, tested, and mapped to **NIST AI RMF, ISO/IEC 42001, CSA
AICM/MAESTRO, Google SAIF, OWASP LLM & Agentic Top 10, and MITRE ATLAS**.

## Quick start (laptop, zero cost)
```bash
./local/scripts/bootstrap-laptop.sh          # gateway + router + db + smoke test
WITH_AI=1 ./local/scripts/bootstrap-laptop.sh # also pull local models + Llama Guard
./local/scripts/kind-up.sh                    # Kubernetes plane (Kyverno + NetPol + Falco)
python3 redteam/run_attacks.py --fail-under 0.9   # adversarial-ML scorecard
./local/scripts/teardown.sh                   # stop everything (costs nothing overnight)
```

## What's inside
| Path | What it is | Interview value |
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
| `docs/` | architecture, **JD traceability**, compliance crosswalk, cost controls, demo runbook | governance, the story you tell |
| `.github/workflows/` | DevSecOps: tests + red-team gate + SAST + secrets + SBOM + container/IaC scan | secure MLOps/LLMOps, CI/CD |

## Design principles
Secure-by-design · privacy-by-design · zero-trust · **fail-closed** · everything-as-code ·
**no single point of failure** (see `docs/architecture.md` §5).

## Documentation
- `docs/architecture.md` — reference architecture, control catalogue, resilience, threat model
- `docs/jd-traceability.md` — every JD line → the component that proves it + cert runway
- `docs/compliance-matrix.md` — NIST AI RMF / ISO 42001 / SAIF / CSA / OWASP / DPDP / RBI crosswalk
- `docs/cost-controls.md` — how it stays under ₹2,500/month
- `docs/demo-runbook.md` — the 15-minute interview walkthrough

> Status: 23 unit tests pass (`pytest` from repo root); all Terraform modules `validate`
> clean; red-team defence rate 100% with 0 false positives; AI-SPM posture 16/16. Figures/
> regulatory notes current to Oct 2026 — verify primary sources before client use.
