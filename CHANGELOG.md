# Changelog

All notable changes to SecuRAX are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md)
for the versioning and release policy.

## [Unreleased]
### Changed
- **Free/sovereign by default.** Chat (Open WebUI) now defaults new conversations to `bank-assistant`
  (free Gemini tier → local fallback), so you never accidentally land on a paid provider that errors
  with "Oops" when its key has no credits. Pick any other model from the dropdown any time.

### Added
- **`./securax pull`** — pull the local model in the foreground so you can be sure it's ready (the
  free/offline `bank-assistant-local`), instead of relying on the background pull.
- **`./securax doctor` now runs a REAL end-to-end chat test** through the gateway and prints the
  *actual* upstream error (not a chat UI's generic "Oops"), plus whether the local model is pulled.

### Fixed
- **The PWA self-updates now.** After a redeploy/`git pull`, the Guiding Map auto-reloads once when
  the new service worker takes control, so you never get stuck on a stale old version in the cache.
- **Clear WSL vs Windows guidance.** `START-HERE-Windows.bat` typed inside WSL gives "command not
  found"; docs + the Command Center now say to use `./securax up` in a terminal and only double-click
  the `.bat` in File Explorer. Added troubleshooting for "models won't list / old version after pull"
  (the containers need `./securax down && ./securax up` to recreate — a pull alone doesn't).

### Changed
- **`./securax up` is now true one-step setup:** if no Gemini key is set and you're in a terminal, it
  asks for a free key inline (Enter to skip) — no more hunting for `.env`.
- **Command Center is honest about scope:** Chat + Guiding Map are shown as "works out of the box";
  Private Docs (RAG) and Automation (n8n) are grouped as optional add-ons that need their own setup.
  The gateway is shown as a friendly security status ("every AI call is guarded"), not raw JSON.

### Previously fixed
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
- **AI provider plugins** (Mattermost-style). A catalog (`plugins/catalog.json`) drives a generator
  that builds the LiteLLM router config from whichever providers you enable, so adding
  **OpenAI, Anthropic, DeepSeek, Mistral, Grok (xAI), Perplexity, Azure AI Foundry, AWS Bedrock,
  OpenRouter** is one command — `./securax providers add` — and the model appears in Chat, still
  routed through the security gateway. The gateway `/v1/models` now mirrors the live router models.
  Model IDs are overridable per provider (`<ID>_MODEL`). Voice via ElevenLabs (`./securax say`),
  plus a heavy-compute (Colab / cloud GPU) recipe. See `docs/securax/22-PLUGINS-AND-PROVIDERS.md`.
- **Command Center** (`hub.html`, reachable at `/hub.html`, `/hub`, or the Guiding Map's **◆ All
  Apps** header button) — one front door with a clickable card + live status for every app, so you
  never type `:3000/:3001/:5678` again. `./securax up` opens it. It is served from the same mount as
  the PWA (no second mount/alias), so a restart can't 404 it; the old `/portal/hub.html` path
  redirects for existing bookmarks.
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
