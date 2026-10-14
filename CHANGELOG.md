# Changelog

All notable changes to SecuRAX are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md)
for the versioning and release policy.

## [Unreleased]
### Added
- **Offline power-ups** (doc 32): `./securax offline sync|status` + `./securax kev` (CISA KEV and MITRE ATT&CK snapshots, streamed and slimmed, work with no network; the AI-SOC names ATT&CK techniques and `scan` flags known-exploited CVEs from them) and `./securax bench` (measures your installed local models for RAM fit / accuracy / tokens-per-second and recommends one). Verified repo ledger: llama.cpp, BitNet, whisper.cpp, llamafile, Atomic Red Team, Sigma, osv-scanner, sqlite-vec. Journey `offline_power`.
- **Behavioural rules + `./securax diffcheck`** (docs 31): the four rules popularised by Karpathy's LLM-coding observations, in our own words, in `BUILD-CONTRACT.md`; `diffcheck` enforces the contract's mechanical hard rules on the diff and gates `autobuild` (journey `diffcheck_gate`). Adoption ledger for agent-skills, ECC (vet: BLOCK, ideas only), karpathy-skills, freellmapi, context-mode.
### Fixed
- The gateway's output rails raised on a malformed URL in a model reply (`http://[abc`); it is now treated as an untrusted host and removed. `vet` no longer crashes on files that break its scanner.
- **Supply-chain gate** (`./securax vet`, doc 31): pin + licence + executable-surface + guardrail-engine text scan of third-party agent skills/plugins/MCP servers; BLOCK can't be pinned; vendored copies must be byte-identical to upstream and are hash-verified (part of `./securax verify`); `escalate` attaches vetted skills only while they verify. First use: agent-skills (2 skills vendored). The purple loop gained a `skill-poisoning` attack (13 attacks). Sandbox journey `vet_gate`.
- **Purple-team loop** (`./securax purple`, doc 30): attacks through the real gateway → captured audit log → real AI-SOC → prevented / logged / alerted report with a detection backlog. Found and fixed: only 3/12 attacks alerted (new SOC rules `injection-probe`, `agentic-tool-coercion`, `output-exfil-channel`, `pii-harvesting`) and PII redaction audited as `allow` (now `sanitise`). CI gate in `devsecops.yml`; sandbox journey `purple_loop`.
- **Range** (`./securax range soil|plan|fetch|install|wake|hibernate|snapshot|reset|status|prune`): a dormant Active Directory practice lab for OSCP-style training, wrapped around GOAD pinned to a verified commit. Says which lab fits this machine (real RAM numbers, re-derived from upstream in CI), refuses cloud providers without explicit cost consent, same lifecycle verbs as the rest. Sandbox journey `lifecycle_range` (28 checks). Never run against a hypervisor here.
- **Burrow (stage 2a, own hardware)**: `./securax grow|hibernate|prune burrow`, `burrow power`, `spore server|agent`. A Docker twin of real k3s (1 server + 2 agents) rehearses your future machines from the same `lifecycle/burrow.json`; spore writes the bash/cloud-init installer (optional GPU label, NUT power reflex, Argo CD hand-over). Sandbox journey `lifecycle_burrow` (27 checks).
- **Lifecycle: the whole ladder as dormant, wake-on-demand code** (doc 29). `./securax stages|soil|grow|hibernate|prune|scale|rhythm|tenant|organ`.
  - **Phase 1 sprout** (`local/compose/stage-sprout.yml`, profile `sprout`, never started by `up`): Keycloak, OpenBao (auto-unsealed on wake), SeaweedFS S3, Prometheus + Alertmanager; optional upstream organs Wazuh / MISP / TheHive fetched at pinned commits (`lifecycle/organs.json`) with ports pinned to localhost. Backups now include the sprout secrets.
  - **Phases 2-4 Terraform** (`infra/terraform/lifecycle/{aws,gcp,azure}`): `awake=false` plans only the seed bank (vault with object lock, KMS key, data disk, budget); `awake=true` germinates one k3s VM (tree), a managed cluster (EKS Auto Mode / GKE Autopilot / AKS) or a multi-tenant forest with per-tenant key + bucket. `prove.py` proves the dormancy logic and security invariants with offline plans (mutation-checked).
  - **GitOps genome** (`gitops/`): Argo CD app-of-apps, platform (cert-manager, KEDA, Kyverno, Falco, Prometheus, Velero), shared router, a tenant chart stamped per `gitops/tenants/*.yaml`, per-tenant metering rules + dashboard. Gateway now exports token and latency metrics.
  - CI job `lifecycle-genome`; `./securax verify --full` runs the Terraform proofs; sandbox journeys `lifecycle_sprout`, `lifecycle_organs`, `lifecycle_cloud_is_safe`.
### Fixed
- The legacy `infra/terraform/environments/lab` could not `terraform init` (a module with its own provider used `count`); fixed and now validated in CI.
- **Self-correcting provider model names** (`local/compose/model_discovery.py`, `./securax models [--fix]`): providers retire
  models every few months (Oct 2026: Groq `llama-3.3-70b-versatile`, older Gemini/Grok names) which silently killed ladder
  rungs. `keys` and a daily `up` now ask each provider which models your key can use and switch `<ID>_MODEL` to a live one;
  rejected keys are named; offline changes nothing. Shipped defaults refreshed (Groq → `openai/gpt-oss-120b`,
  Anthropic → `claude-haiku-5-5`, Grok → `grok-4.3`, Gemini → `gemini-3.5-flash-lite`) — treat as starting points.
- **`./securax autobuild`** — unattended build loop gated by `verify` (retry with feedback, commit only when green, rollback + escalation brief).
- **`./securax evidence`** (auditor pack, no prompts/keys) and **`./securax scan`** (Trivy over running images).
- `./securax backup|restore|watch`; `docs/securax/26` (coverage vs reference maps), `27` (incident runbook), `28` (status & traceability).
- Sandbox: journeys for model self-correction, autobuild, backup/restore, watchdog; more providers (Mistral, Grok, Perplexity).
- **`WINDOWS-QUICKSTART.md` + `local/scripts/wsl-setup.sh`** — blind-followable Windows install: WSL memory config, Docker WSL
  integration, one paste to install into WSL's fast disk (keeps your `.env` keys and model volumes). `securax.cmd` prefers it.
- **`./securax keys`** — guided free-key setup (Gemini → Groq → OpenRouter) ending in a live test (who answered, how fast).
- **Elastic resources**: every `up` sizes the local model, Ollama RAM cap and lite mode to what Docker can really use
  (`./securax size` to preview). **Preflight** names port conflicts / low disk / Docker-not-reachable; **layered start**
  retries without rebuild, then core-only. See `docs/securax/25-FALLBACKS-AND-ELASTICITY.md`.
- Sandbox: 5 new journeys (keys wizard, elastic sizing, explained blockers, self-healing after killing components, update
  from a dirty checkout).
- **`securax.cmd` — Windows launcher.** `.\securax.cmd up|update|doctor|providers add|…` from PowerShell runs the
  bash CLI in WSL, checking WSL/Docker/Docker-WSL-integration first and printing the exact fix. START/STOP
  `.bat` files now use it (they previously skipped router-config generation and the readiness wait).
- **`./securax verify [--full]`** — one definition of done (lint, unit tests, router-config baseline, compose
  validity; `--full` adds the sandbox). `./securax build` now uses it as its auto-test command.
- `.gitattributes` keeps `securax`/scripts LF so a Windows checkout can't break them.
- **User-perspective sandbox (`sandbox/`, `python3 sandbox/run.py`, CI `e2e-sandbox`)** — runs the real product from a fresh
  clone (no `.env`) with a real browser, real Ollama model and faked cloud providers; 8 journeys / 88 checks. It found and
  drove fixes for: readiness race, no config regeneration on `up`, one-shot Command Center status, gateway `stream:true`
  500s, and the router phoning huggingface.co.
- **`./securax update`** — `git pull --ff-only` then recreate the containers, so fixes actually run (a
  plain pull leaves the old containers running). `./securax doctor` now warns when you're behind `main`.
- **`./securax guard [status|on|off]`** for the optional Llama Guard detector; **`./securax up` auto-heals**
  the broken state (Llama Guard on but never installed → every request blocked) by switching it off, loudly
  and reversibly. The built-in rails enforce either way.
- The provider wizard now takes keys **silently** (a visible key ends up in screenshots/chat pastes), warns
  when a key looks like a *different* provider's (e.g. an OpenRouter `sk-or-` key under ElevenLabs) and
  refuses to store it unless you confirm, and rejects a typed command in the provider-id prompt.
- **Degradation ladders** — `bank-assistant` (Gemini → Groq → OpenRouter → local) and `builder`
  (DeepSeek → free tiers → local coder → local). Missing keys skip rungs; every chain ends in the
  always-on local model, so there is an answer even with zero keys and zero internet. Cloud rungs
  fail over in 40 s and cool down after repeated failures. New Groq plugin. `./securax build` now
  defaults to the `builder` ladder.
- **`./securax profile`** — detects RAM/CPU and right-sizes the local model, Ollama caps and lite mode
  (with WSL2 `.wslconfig` guidance); **`./securax up --lite`** runs only the core path.
  `./securax doctor` now probes the real ladder and reports which rung answered.
- Ollama tuned for CPU-only machines (warm model, single request/model at a time).
- `docs/securax/24-RESILIENCE-AND-LOW-RESOURCE.md`.
- **`./securax pull`** — pull the local model in the foreground so you can be sure it's ready (the
  free/offline `bank-assistant-local`), instead of relying on the background pull.
- **`./securax doctor` now runs a REAL end-to-end chat test** through the gateway and prints the
  *actual* upstream error (not a chat UI's generic "Oops"), plus whether the local model is pulled.
- **Build SecuRAX with its own models** (reduce the Claude dependency). `./securax build "task"`
  drives [Aider](https://aider.chat) against the SecuRAX gateway with a cheap/local model (default
  `deepseek`, or the new sovereign `coder` = local Qwen2.5-Coder), loads the new **BUILD-CONTRACT.md**
  as always-on context, and runs `ruff + pytest` after every edit until green — rigor from the test
  loop, not just the model. `./securax escalate "task"` writes a tight brief (task + diff + rules) for
  the hard 10% that still needs a frontier model. New `coder` plugin + `ENABLE_LOCAL_CODER`/`BUILD_MODEL`/
  `CODER_MODEL` knobs. Full strategy: `docs/securax/23-BUILD-WITHOUT-CLAUDE.md`.
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

### Changed
- CPU-only default chat model is now qwen2.5:1.5b on 16 GB laptops (was 3b — about twice as slow for little gain).
- **Free/sovereign by default.** Chat (Open WebUI) now defaults new conversations to `bank-assistant`
  (free Gemini tier → local fallback), so you never accidentally land on a paid provider that errors
  with "Oops" when its key has no credits. Pick any other model from the dropdown any time.
- **`./securax up` is now true one-step setup:** if no Gemini key is set and you're in a terminal, it
  asks for a free key inline (Enter to skip) — no more hunting for `.env`.
- **Command Center is honest about scope:** Chat + Guiding Map are shown as "works out of the box";
  Private Docs (RAG) and Automation (n8n) are grouped as optional add-ons that need their own setup.
  The gateway is shown as a friendly security status ("every AI call is guarded"), not raw JSON.

### Fixed
- **`git pull` conflicted after every `up`** (found on a real Windows laptop): `up` rewrote the tracked
  `litellm-config.yaml`. The router now mounts a git-ignored `litellm-config.generated.yaml`; the tracked file is a
  baseline `up` never touches. Config generation failing is now reported, not swallowed. Sandbox asserts `up` leaves
  the checkout clean.
- **"400: Request blocked by AI security policy" on harmless prompts.** `.env.example` once shipped
  `LLAMA_GUARD_URL` enabled; existing `.env` files keep it (git pull never rewrites `.env`), and with the
  model not installed the fail-closed gateway blocked everything. The gateway now says a *detector is
  offline* (machine-readable `reason: detector_unavailable`) instead of implying the prompt was malicious,
  and the Guiding Map no longer calls it "an attack pattern".
- Open WebUI: the random "Arena Model" is off and the stack's config is authoritative
  (`ENABLE_PERSISTENT_CONFIG=false`), so `DEFAULT_MODELS=bank-assistant` now applies to existing installs.
- **The Guiding Map showed "v13.0.2".** That badge was a hardcoded legacy string (not stale cache —
  a fresh load showed it too) while the product is `VERSION` 0.1.0. `guiding-map/build.js` now stamps
  it from `VERSION`, and a CI test fails if it ever drifts or a hardcoded version returns.
- **Provider keys never reached the router.** The LiteLLM container was only given the Gemini/Azure
  keys, so OpenAI/Anthropic/DeepSeek/xAI/Mistral/Perplexity/OpenRouter always failed with an auth error
  (it looked like "no credits"). All provider keys are now passed through, and a CI test fails if the
  generated config ever references an env var compose doesn't wire in.
- **`bank-assistant` was randomly load-balanced** between Gemini and the slow local model (two
  deployments under one name + `simple-shuffle`). Every alias is now a single deployment; local is a
  fallback, never a coin-flip.
- AWS Bedrock now authenticates with the AWS key pair + region (it was sent the access-key id as an
  `api_key`); `LOCAL_MODEL` is now honoured by the router (bare tags get the `ollama/` prefix).
- **The PWA self-updates now.** After a redeploy/`git pull`, the Guiding Map auto-reloads once when
  the new service worker takes control, so you never get stuck on a stale old version in the cache.
- **Clear WSL vs Windows guidance.** `START-HERE-Windows.bat` typed inside WSL gives "command not
  found"; docs + the Command Center now say to use `./securax up` in a terminal and only double-click
  the `.bat` in File Explorer. Added troubleshooting for "models won't list / old version after pull"
  (the containers need `./securax down && ./securax up` to recreate — a pull alone doesn't).
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
