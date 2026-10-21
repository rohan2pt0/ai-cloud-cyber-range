# 54 · SecuRAX technical gist (for another engineer or AI assistant)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** A reference summary of what is built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Paste this whole file to a helper (DeepSeek, another model, a contractor). It is enough to propose changes that fit.
**Do not paste:** `local/compose/.env`, backups, `vault/`, Guiding Map exports or anything personal. The repository
is public; this file contains no secrets.

## 1. What it is

A **sovereign, laptop-first AI and security estate**: one CLI (`./securax`, bash, about 1,250 lines) over Docker Compose.
Built for people and firms who handle sensitive data, India first. It has three parts:
1. a guarded AI gateway and model router;
2. Chat, private document Q&A and automation;
3. a personal "life OS" PWA (Guiding Map).

It grows from one laptop to multi-tenant Kubernetes through dormant, code-defined lifecycle stages.

**Design constraints (do not break):**
- ₹0 to start; the cloud is opt-in and budget-capped.
- Red-tier data never leaves the machine.
- Fail-closed rails.
- No vendor lock-in: any model or tool swaps behind standard interfaces.
- Plain English for the user.
- Version 0.1.0, MIT licence.

## 2. Runtime (Docker Compose, `local/compose/docker-compose.yml`)

Ports bind to `127.0.0.1` by default (`BIND_HOST` / Tailscale IP to reach from a phone). `./securax up --lite` runs the core path only.

| Service | Image (pinned) | Port | Role |
|---|---|---|---|
| gateway | `vulnbank/llm-gateway:dev` (built here, FastAPI) | 8080 | the ONLY front door for model traffic: guardrails, authn, residency, audit, metrics |
| litellm | `ghcr.io/berriai/litellm:main-stable` | internal | router: one alias per provider, ordered fallback **chains**, `max_budget` 25 USD/30 d |
| ollama | `ollama/ollama:0.40.4` | internal | local models (default `qwen2.5:1.5b`, sized to RAM by `autosize`); one model loaded at a time; 8-bit context cache |
| open-webui | `ghcr.io/open-webui/open-webui:0.12.2` | 3000 | Chat (talks only to the gateway; `ENABLE_PERSISTENT_CONFIG=false`, so `.env` is authoritative) |
| anythingllm | `mintplexlabs/anythingllm:latest` | 3001 | Private Docs: RAG on local Ollama, LanceDB, native embeddings |
| n8n | `n8nio/n8n:1.74.1` | 5678 | optional automation (2.x upgrade pending) |
| estate-sync | `securax/estate-sync:dev` (built here) | 8089 | cross-device sync for the PWA: SQLite, bearer tokens, WebSocket push, daily snapshots |
| guiding-map | `nginx:1.27-alpine` | 8088 | serves the PWA, Command Center (`/hub.html`), cockpit |
| postgres, loki, grafana, trivy | pinned | (grafana 3000 under the `security` profile) | storage, logs, dashboards, scanning |

TLS (optional): `./securax tls on` puts a private name-constrained CA and one HTTPS edge (nginx 1.30, hybrid X25519+ML-KEM-768) on 443 with names `hub.`, `chat.`, `docs.`, `flows.`, `sync.`, `api.`; `tls internal on` adds per-service TLS sidecars.

## 3. A chat request, end to end

```
Open WebUI / PWA / OpenCode / scripts
   → gateway :8080  /v1/chat/completions (OpenAI format)
       authn (off | API keys hashed | OIDC JWT, roles, MFA claim, lock-out)
       input rails: prompt-injection + jailbreak (incl. smuggled/base64), PII redaction
                    (Aadhaar Verhoeff, card Luhn, PAN, IFSC, UPI, mobile, e-mail), size limits
       residency: data class → allowed zone (red → local only)
       optional detectors (Llama Guard via Ollama, cloud safety APIs), fail-closed
   → LiteLLM alias or chain → provider (or local Ollama)
   ← output rails: secret/credential leak, canary (system-prompt leak), exfil links,
                   markdown-image exfil, active content; withhold on block
   ← re-streamed as SSE only AFTER inspection (no token-by-token passthrough, by design)
   audit event (JSON) + Prometheus /metrics (incl. reasoning tokens) + W3C traceparent
```

## 4. Models: plugin catalog and ladders (`plugins/catalog.json` → `local/compose/gen_litellm_config.py`)

- **Providers:** gemini (default, free), groq and groq_qwen (free), home (your own stronger machine over Tailscale, residency-local), e2e_tir (Indian cloud, opt-in, in no chain, zone global until mapped), nvidia_nim (free, build chain only), cerebras (evaluation only, in no chain), openrouter (free models), openrouter_pro (**paid, opt-in** with `OPENROUTER_PRO_OK`), deepseek, opencodego (+_glm), openai, anthropic, mistral, grok, perplexity, azure, bedrock, local, coder (local Qwen coder), plus elevenlabs and compute recipes.
- **Enabling a provider:** it is ON only when all its `env` keys are set. `./securax providers add <id>` takes the key with hidden input. `<ID>_MODEL` overrides the model. `./securax models` discovers live models and repairs retired names.
- **Chains** (every chain must end in `local`; enforced by tests):
  - `bank-assistant`: gemini → groq → openrouter → home → local. The free default for Chat; a paid provider is never in it.
  - `twin`: openrouter_pro (opt-in) → gemini → groq → openrouter → home → local. Chat Twin; DeepSeek is excluded because it is China-hosted and Chat carries personal data.
  - `builder`: opencodego → opencodego_glm → groq → groq_qwen → nvidia_nim → deepseek → gemini → openrouter → home → coder → local. Coding only; reorder with `./securax providers chain builder ...` (stored as `CHAIN_BUILDER` in `.env`; Chat chains are not editable; local always last).
- **Reasoning cap:** `<ID>_REASONING=<level>` is applied only where the catalog verified that LiteLLM maps it to LESS thinking (doc 50).
- **Generated configs:** `litellm-config.yaml` (committed baseline), `litellm-config.generated.yaml` (git-ignored, from `.env`), `gitops/core/litellm.yaml` (re-render with `lifecycle/render_core.py`).

## 5. What the user runs (CLI groups; `./securax help`)

| Group | Commands |
|---|---|
| Start | `setup`, `up [--lite]`, `down`, `status`, `open`, `doctor`, `why`, `update` (backup → update → health gate → automatic rollback, exit 3), `start/stop docs\|flows\|all`, `shortcut` |
| AI | `keys`, `providers add\|list\|chain`, `models`, `pull`, `profile`, `bench`, `guard on\|off`, `ask <agent>`, `advisors`, `research "task" --allow site` (read-only, allowlisted web agent), `act` (one approved web action), `design` (local image generation), `opencode [--rea\|--check]` (terminal coding agent via the gateway; build chain only), `knowledge import\|status` |
| Safety | `backup` (verified, optional AES-256 OpenPGP), `restore`, `protect`, `watch` (self-heal), `scan`, `kev`, `offline`, `crypto [--full]` (CBOM), `purple` (attack your own rails), `vet` and `inspect` (third-party code; REA in a no-network container) |
| Regulatory | `comply rbi\|cscrf\|mit-ai-risk\|nist-ai-600-1\|pqc`, `ccsp`, `evidence` (checksummed pack), `incident` (RBI/SEBI/CERT-In clocks as data), `regulated on`, `gateway-auth`, `residency` |
| Ops | `cockpit` (vital signs, Eisenhower, 80/20, NIST CSF radar, KRIs), `storage`, `capacity`, `notify` (ntfy phone push or webhook; `digest --changed`), `routines list\|due\|run`, `lifefeed`, `sync-link`, `tls`, `certs` |
| Build | `build`, `autobuild` (build ladder), `escalate`, `diffcheck`, `forge gate` (fail-to-pass, mutation, complexity), `autobench` (models measured on 10 hidden-graded tasks), `verify`, `fitness`, `gameday`, `impact` |
| Grow | `stages`, `soil`, `grow`, `hibernate`, `prune`, `scale`, `rhythm`, `tenant`, `organ`, `burrow`, `spore`, `range` |

**Routines** (`routines/jobs.json`, one cron line runs `./securax routines run` every minute):
- morning-brief, weekly-posture;
- andon (15 min, phone push only on change);
- daily-backup, code-mirror, continuity-drill, knowledge-inbox;
- monthly-review, quarterly-checkin.

## 6. Guiding Map (the life-OS PWA)

- **Build:** a single offline file. `guiding-map/ops.js` is inlined into `index.html` by `node guiding-map/build.js`; there is a service worker.
- **Storage:** data lives in `localStorage` on the device and syncs through estate-sync.
- **Calm mode** (default): Today is one screen. There are five tabs plus More: today, ask, life, money, ops (`CALM_TABS` in `ops.js`). Career compass appears while a job decision is active; Show everything restores all 15 tabs. Rhythm: quarterly check-in, monthly review, .ics calendar export.
- **Code rules:** function names share one IIFE scope, so a duplicate name silently overrides an earlier one. A section is visible only with `.section.active`.
- **Tests:** `guiding-map/tests/test*.js` (node) and `tests/ui_audit.py` (Playwright, WCAG contrast).
- **Next step:** an installable Android wrapper for the family, built so a store release later is packaging, not a rewrite.

## 7. Grow stages (`lifecycle/stages.json`, everything dormant until grown, reversible)

- **seed** (crawl): the laptop.
- **sprout** (walk): compose plus pinned organs Wazuh, MISP, TheHive; OpenBao secrets.
- **burrow** (run-): k3s multi-node twin, spore installer.
- **tree** (run): single cloud node, AWS.
- **canopy** (run+): AWS full, GCP and Azure.
- **forest** (fly): multi-tenant cells, each with namespace, quota, zero-trust network policy, own gateway, RBAC, metering and its own KMS key and bucket on AWS. Argo CD app-of-apps. The billing and MSSP business layer is not built.

## 8. Quality gates (a change is done only when these pass)

- `ruff check .`; `python -m pytest -q` (<!-- fact:tests -->850+<!-- /fact --> test functions; `pytest.ini` lists the test paths); `node` tests for the PWA.
- `./securax fitness`: latency, memory and dependency budgets; **every product claim proven** (`governance/claims.json`, doc 55); supply-chain ratchet; every CLI command documented; the impact map owns every tracked file; regulatory and CCSP maps resolve.
- CI (`.github/workflows`): lint, app-tests, SAST and secrets, IaC scan, container scan, Trivy, Scorecard, SLSA provenance, terraform/organs/gitops, and the **sandbox** (about 40 min). The sandbox brings the real estate up on a runner and runs **41 journeys**: fresh install, chat through Open WebUI, safe update with rollback, backup/restore (also encrypted), TLS, lifecycle stages and more.
- `BUILD-CONTRACT.md`. Hard rules:
  - never skip a test;
  - never weaken rails or widen egress;
  - never commit a secret;
  - no hard-coded model IDs (use the catalog);
  - the gateway is the only front door for model traffic.

## 9. Known gaps (good places to help)

1. **Unpinned images.** `anythingllm:latest` and `litellm:main-stable` should be pinned by version or digest.
2. **n8n 1.74 → 2.x.** A major upgrade; it needs a workflow export and migration notes first.
3. **SecuRAX tools inside Chat.** Use an MCP-to-OpenAPI proxy (mcpo) in front of `mcp/securax_mcp.py`, with authentication. Vet it first.
4. **Agentic execution in Chat.** Open Terminal in a locked container with per-action approval. Vet it first.
5. **Voice ("Jarvis").** Open WebUI 0.12 voice with local Whisper speech-to-text. Test it on a CPU laptop.
6. **Regulator watch.** Real RBI, SEBI and CERT-In pages through the read-only research agent, sending an andon only when something is new. The old n8n "morning brief" asked a model for news without feeding it any.
7. **Family Android app** from the PWA.
8. **Claude Code is not wired in.** Anthropic does not support routing it to non-Claude models (see 10). OpenCode is the supported open agent here.

## 10. Verdict on the "free Claude Code" plan (DeepSeek, 15-Oct-2026)

| Recommendation | Verdict | Why / what SecuRAX does instead |
|---|---|---|
| Route Claude Code through a proxy to free models | **No** | Anthropic's gateway docs say they don't support routing Claude Code to non-Claude models through any gateway. Features break as Claude Code evolves, and the estate's invariant is that all model traffic passes the gateway's rails. |
| `free-claude-code` proxy installed with `curl … \| sh` | **No** | a third-party process holding every provider key; curl-to-shell is banned here (doc 31); its own reviewers call the translation layer its main source of bugs. If ever wanted: `./securax vet` + `inspect` first. |
| A second, model-agnostic agent (OpenCode) | **Already built** | `./securax opencode`: pinned npm install, every call through the gateway, build chain only (`--check` proves it), asks before edits and commands, no auto-update (doc 42). |
| Router with fallback chains and local floor | **Already built** | LiteLLM chains ending in `local`; `models` self-repairs model names. |
| Eval suite to pick models | **Already built** | `./securax autobench` (10 hidden-graded tasks, cheating detection, 95 % interval). |
| Red/Yellow/Green rule for code and data | **Already built** | `./securax residency` + the gateway's classification routing. |
| Cost kill-switch | **Already built** | LiteLLM `max_budget`; every chain ends in local. |
| Audit trail of which model wrote what | **Already built** | gateway audit events + autobuild commit trail. |
| MCP tools `get/set_coding_model`, `coding_health` | **Not needed** | `./securax providers`, `models` and `bench` do this; adding MCP tools would duplicate them. |
| Keys in OpenBao instead of `.env` | **Later** | `.env` is owner-only and git-ignored; OpenBao exists in the sprout stage. Move when there are more people or machines. |
| NVIDIA NIM free tier | **Adopted, build chain only** (re-reviewed 15-Oct-2026) | NVIDIA's FAQ allows free use for "prototyping, research, development and testing" and calls anything else production. Building SecuRAX is development; daily Chat would not be, so it is never in a Chat chain. No published retention statement: Green-tier only. |
| Gemini free tier | **Kept** in Chat and build chains | the fastest generous free tier; its prompts may be used to improve Google's products and read by reviewers, so it is Green-tier. The gateway redacts Aadhaar/PAN/card/phone/e-mail before any cloud call, and `./securax residency enable` keeps Red-tier data on the local model. |
| Groq for coding | **Adopted (owner request)** | free, about 30 requests/min and 200K tokens/day per model (organisation-wide); first cloud rung after OpenCode Go, with a second model family (`groq_qwen`) on its own quota. Green-tier only. |
| Cerebras | **Evaluation only** | the 1M tokens/day free tier ended in July 2026; now a $5, 30-day trial at 5 requests/min with conflicting data terms. In no chain unless you add it (`./securax providers chain builder add cerebras`). |
| gpt-oss:20b as the 16 GB local coder | **Tiered, measured** | needs about 16 GB at run time; beside the estate inside Docker it does not fit on a 16 GB laptop, which gets qwen2.5-coder:7b. Larger machines get gpt-oss:20b or qwen3-coder:30b (catalog `coder.sizing`). |
| Aider | **Optional** | fine pair programmer; vet before installing. Not needed while OpenCode is wired. |
| "Your laptop can run qwen2.5-coder:14b" | **Measure first** | `./securax bench` tells you; on a 16 GB laptop without a GPU a 14B model is slow. |

**Free tiers are not private.** Google's Gemini API terms say free-tier prompts can be used to improve Google's products,
and human reviewers may read them. Paid tiers are excluded. Treat free tiers as Green-tier only.

## 11. How to ask a helper for a change (copy this)

> Here is the SecuRAX technical gist (above). Propose the smallest change that does X. Respect BUILD-CONTRACT: no new
> service without a pinned version, no weakening of the gateway rails, no hard-coded model IDs (use
> `plugins/catalog.json`), no secrets, plain-English user messages. Say which tests/fitness checks/journeys prove it and
> which files change. If you are not sure a fact about the repo is true, say so instead of assuming.
