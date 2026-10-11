# Changelog

All notable changes to SecuRAX are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md)
for the versioning and release policy.

## [Unreleased]
### Fixed
- **Models now work out of the box.** The `modelplane` network was `internal: true`, so Ollama
  couldn't pull models and LiteLLM couldn't reach cloud models — breaking every answer. Given egress
  (models still publish no host ports). LiteLLM now defaults to **fast cloud Gemini with a local
  fallback**, so answers are instant with a free key and private-local otherwise.
- **No more false "Blocked by the guardrail".** Llama Guard was enabled by default but its model
  wasn't pulled, so the fail-closed detector blocked *every* request. It's now opt-in; the fast
  deterministic rails (100% red-team defence) run by default. The PWA also stops mislabeling a
  model-unavailable error as a guardrail block.
- `fin_freedom.py` argparse crash from a literal `%` in help text (Python 3.14).
- The optional kind/k8s plane used host port 8080, clashing with the gateway; moved to 8081.

### Added
- **Command Center** (`portal/hub.html`) — one front door with a clickable card + live status for
  every app, so you never type `:3000/:3001/:5678` again. `./securax up` opens it.
- **`./securax setup`** — a 30-second wizard that writes `.env` (Gemini key, multi-device access,
  a generated sync token, strong service passwords) so you never hand-edit `.env`.
- Gateway **`GET /v1/models`** so Open WebUI / AnythingLLM can list and select a model.
- **`BIND_HOST`** to expose the UIs to your phone/iPad over Wi-Fi or Tailscale; `DEPLOY.md` gains a
  multi-device + sync section.



## [0.1.0] - 2026-10-11
First versioned public release. SecuRAX is a sovereign, local-first AI-security + life-OS estate.

### Added
- **AI Guardrail Gateway** — fail-closed Policy Enforcement Point for LLM traffic (prompt-injection,
  PII redaction, secret/exfil output rails, Red/Yellow/Green data classification), with pluggable
  detectors (Llama Guard / Model Armor / Bedrock / Prompt Shields) and a `/version` endpoint.
- **MCP control plane** — zero-dependency stdlib JSON-RPC server exposing 19 estate capabilities.
- **LiteLLM multi-model router** — OpenAI-compatible, local-first (Ollama) with capped free/cloud fallback.
- **Guiding Map PWA** — offline life-OS cockpit (8 pillars, cadence engine, wealth engine, inline help).
- **Sovereign cross-device sync** (`estate-sync`) — SQLite + server-side per-key merge, fail-closed Bearer auth.
- **Autonomous web-research agent** — read-only, allowlist + SSRF-gated, injection-safe, HITL; optional
  Playwright render engine and approved-action executor (write path, audited, per-action approval).
- **Advisor army** — 26 stealth specialist agents (first-draft opinions, anti-hallucination contract).
- **Global Intelligence** — community-consensus decision engine (replicate/edge, capability-fit, timing).
- **Financial planner** — sovereign retirement-corpus projection (India/BFSI defaults).
- **Routines** — sovereign scheduled estate tasks (the local "Claude Routines").
- **Local image generation** — sovereign text-to-image (opt-in `design` profile).
- **DevSecOps CI** — pytest + jsdom suites, gitleaks, Semgrep, Trivy (IaC + image), CycloneDX SBOM,
  OPA/Conftest, compose sanity + build-drift poka-yoke gates, AI red-team scorecard + AI-SPM posture.
- **Documentation set** — `docs/securax/` (vision, principles, architecture, capability catalog,
  compliance map, roadmap, cost/models, end-state enterprise architecture, Claude-parity, more).
- **One-step deployment guide** (`DEPLOY.md`) — install Docker, run one command, done.
- **Product scaffolding** — SemVer `VERSION`, `CHANGELOG`, `SECURITY`, `CODE_OF_CONDUCT`,
  `GOVERNANCE`, `MAINTAINERS`, `SUPPORT`, `CODEOWNERS`, issue/PR templates, Dependabot, ruff lint
  gate + pre-commit, and a tag-driven release workflow.

### Security
- Fail-closed everywhere; no secrets in the repo (pattern-based PII/secret CI gate); SSRF + DNS-rebind
  defenses on the web agent; append-only audit trail for approved actions.

[Unreleased]: https://github.com/rohan2pt0/ai-cloud-cyber-range/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rohan2pt0/ai-cloud-cyber-range/releases/tag/v0.1.0
