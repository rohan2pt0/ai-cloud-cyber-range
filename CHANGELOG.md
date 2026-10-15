# Changelog

All notable changes to SecuRAX are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md)
for the versioning and release policy.

## [Unreleased]
### Added
- **`./securax knowledge`** (doc 51): imports the official exports of Claude (chats and projects), ChatGPT, DeepSeek and Gemini (Takeout) into one markdown file per conversation plus a dated index, for Private Docs. Read in memory (never extracted), credentials and Aadhaar/card/PAN redacted with the gateway's rules, your own flag terms route a conversation to `flagged/` for review, re-runs skip what has not changed; daily routine `knowledge-inbox` imports whatever you drop into `vault/knowledge/inbox` (git-ignored). The export request itself stays manual on purpose (no API; a browser robot would hold four live sessions).
- **Reasoning budget** (doc 50): the gateway meters thinking tokens (`guardrail_tokens_total{kind="reasoning"}`); optional per-provider cap `<ID>_REASONING=<level>` (Gemini 3, Groq gpt-oss, Claude 5), applied only when the current model matches and the level is listed, off by default. A global switch was rejected: LiteLLM 1.105 maps a 'low' effort to thinking ON on Ollama/DeepSeek and to 'high' on Mistral. Verdict on Hybrid Reasoning Agents (arXiv 2610.18861): not adoptable on this estate yet (custom CUDA engine, no OpenAI-compatible server); one catalog line when it is.
- **Career compass** (doc 49, Guiding Map → Career): one screen for a job decision. Floor (today's real value: net + employer-paid rent and perks + retirement; plus your own cover), honest CTC and the +30% target, FI need (corpus, SIP, in-hand), each offer's in-hand under the FY 2026-27 new regime (salary or fee; 44ADA only when ticked), break-even CTC per offer structure, must-have gates (any ✗ rejects, any ? = not decidable) then weighted good-to-haves, worst cases against the emergency fund, the BFSI security ladder worked backwards with proof per rung, and a dated plan (notice period → month 30) that shows in Due now. Personal numbers only via the screen or your own career file; nothing personal ships.
- **Guiding Map freeze-ready** (doc 48): quarterly check-in in about 5 minutes of taps (grade last quarter, 8-area wheel, up to 3 goals suggested from the lowest scores); "Add the rhythm to my calendar" (.ics, 5 repeating events with reminders); the After-Action Review is a monthly ritual; Kids: add in place, this quarter's three actions and the education SIP; Ops reorganised (advanced tools folded). Fixed: Undo kept a 10-day-old snapshot that would have wiped days of entries (now 30 min, dismissable); pausing asks first; integrations claimed auto-fill (now honest copy-in boxes with Indian/Android sources); 439 WCAG contrast failures across both themes (now 0); runway read 274219.5 months when a lakh field was typed in rupees. New journey `guiding_map_full_use` audits every tab in a real browser.
- **Guiding Map Calm mode** (doc 47, default; "Show everything" restores the full app): Today is one screen (1,603 px, was 3,675; first tap at 220 px, was ~700) with tap check-in plus optional energy, the one open action, due-now lines, a week insight computed on the device and an optional review by your estate AI (ID numbers never sent), and "From your estate" lines. Setup is 4 questions written once into both data models, and example people and loans are removed after it. 5 tabs plus More. **`./securax lifefeed`** feeds it from the cockpit, the certification planner and backups.
- **`./securax certs`** (doc 46): certification path planner for OSCP+/OSWE/OSEP/OSED/OSAI, CPTS/COAE, CRTP/CRTE/CRTM, CRTO and BSCP, ordered by shared skills and dated and costed against your hours and yearly rupee budget (retake reserve, carry-over, OffSec per-course vs Learn Unlimited compared). Prices are a dated snapshot with sources.
- **`./securax autobench`** (doc 45): measures each build model inside the autobuild loop on ten hidden-graded tasks (cheating detected, 95% interval, plain vs contract prompt, asks before a large paid run; `selftest` proves the benchmark with no model). Found and fixed on the way: the forge mutation gate could leave stale bytecode of a mutant behind (regression test added). The e2e workflow now installs pytest.
- **Less friction**: `./securax why [service]` (what stopped and why, in plain words; Windows: double-click `WHATS-WRONG-Windows.bat`), `./securax shortcut` (type `securax <command>` from any folder; installed by the WSL setup; undo with `shortcut off`), `UPDATE-Windows.bat`. Found and fixed on the way: `why` would have exited silently on a fully healthy estate.
- **Admission gate + self-healing sandbox** (doc 44): `./securax forge gate` (fail-to-pass, mutation check on the changed lines, complexity budget) now runs inside `autobuild`; failures are fed back as a short typed brief, and infrastructure-only reds (Docker/network) are re-run instead of "repaired". The sandbox re-runs a journey once when every failure is infrastructure, and records it.
- **REA (Reverse Engineer Anything) in a sandbox** (doc 43): `./securax inspect` reads third-party software (npm package, tarball, folder, file) and says in plain words what it can do and what is worth a look; `--diff` and a weekly `--watch` (your crontab, or the `supply-chain-watch` workflow) catch **capability drift**: a new version that can do what the old one could not (new install script, network, program launching, hard-coded address, native code); `./securax opencode --rea` gives the agent REA over MCP. REA 6.5.0 is pinned by lockfile with integrity hashes and no install scripts, and runs only in a container with no network, a read-only disk, no privileges and the target mounted read-only (`--selftest` proves it). Static only: running the target is never offered. Proven with the real REA on real packages and by journey `inspect_sandbox`; the real OpenCode 1.19.0 connected to it over MCP.
- **OpenCode Go and the OpenCode terminal agent** (doc 42): `./securax providers add opencodego` turns on flat-rate open models (DeepSeek V4.1 Flash, GLM Flash; US/EU hosted, zero retention) as the first rungs of the **build** ladder only (never Chat), with the provider's required user agent and a per-install session id; the router generator now supports any OpenAI-compatible `api_base` and fixed headers per provider; `./securax opencode` starts the OpenCode terminal UI with every model call routed through the SecuRAX gateway (its other providers off, asks before edits/commands, no auto-update, no public sharing; verified with the real OpenCode 1.19.0); journey `provider_opencode_go`.
- **Simpler protection** (doc 41): `./securax crypto` is now a plain-English check (needs you now / already protected / can wait / outside SecuRAX; `--full` keeps the technical CBOM); `./securax protect` (Windows: double-click `PROTECT-BACKUPS-Windows.bat`) does everything to encrypt backups with one question; the Cockpit shows "Backups locked" and "Quantum-resistant connections"; `./securax start|stop docs|flows|all` is remembered, so `up` and `update` no longer silently drop the add-ons.
- **Quantum readiness** (doc 41): the HTTPS edge now offers a **hybrid post-quantum key exchange (X25519 + ML-KEM-768)** first, with classical fallback (edge and sidecars move to nginx 1.30 / OpenSSL 3.5; proven against the real edge); `./securax crypto` - a ranked cryptography inventory read from the estate (`--cbom` CycloneDX 1.6, `--strict` for cron/CI, `keygen` for a backup key file); **encrypted backups** (OpenPGP symmetric AES-256, key file kept off the machine or a typed passphrase; wrong key and tampered files refused; restore verified in the journey `backup_encrypted`); `./securax comply pqc` (17 items, entity obligations separate). `restore` also no longer leaves the unpacked backup (it contains your keys) in /tmp when it restarts the estate.
- **`./securax start docs|flows|all`** starts the optional Private Docs / Automation add-ons that lite mode skips (with their TLS sidecars when internal TLS is on) and waits until they answer by name.
- **Encryption in transit, phase 2** (doc 40): `./securax tls internal on|off` - a per-service TLS sidecar (own certificate from the private authority, service listens on loopback only) for gateway, LiteLLM, Ollama, Open WebUI, n8n and the sync service; the edge verifies every upstream; plain HTTP between containers is refused; real-stack journey `tls_internal`. Known exceptions (AnythingLLM, Sprout stage, n8n env assumption) are listed in doc 40.
- **Ops without chores** (doc 39): the sync service keeps a daily snapshot of each user's merged state (30 days; list/restore endpoints) and the Guiding Map shows "Backed up automatically" with a restore-a-day control instead of nagging for a manual export; `./securax sync-link` prints a one-tap setup link for a phone or second computer (token after `#`, destination shown before saving, existing setup never replaced without a second confirmation).
- **Encryption in transit, phase 1** (doc 40): `./securax tls on|trust|status|renew|off` - a private, name-constrained certificate authority and ONE HTTPS edge (TLS 1.2/1.3, forward-secret ciphers) on port 443 that routes by NAME - `https://hub.securax.localhost`, `chat.`, `docs.`, `flows.`, `sync.`, `api.` (no port numbers; `--domain` for your own domain with one wildcard DNS record, so an IP change touches one record) - in front of the Command Center, Chat, Private Docs, n8n, the sync service (incl. wss) and the gateway; the plain web ports are no longer published while it is on; hub/PWA links follow the page and domain; **the cockpit's maturity chart is now readable**: plain-English area names, a how-to-read guide, a posture summary, and a weakest-first table with each area's next step; cockpit indicator; RBI 118/21(9) and CSCRF PR.DS.S1-S3 updated honestly. **Fixed**: the gateway (8080) and Grafana (3000) were published on every network interface; they now follow `BIND_HOST` (default: this machine only). Internal container-to-container hops are not encrypted yet and are listed by `tls status`.
- **Live sync, team chat, people-scale ladder** (doc 39): `estate-sync` WebSocket push (`/sync/ws`, signal-only, first-message auth) with Guiding Map client and polling fallback; Mattermost as a dormant pinned organ (`./securax organ mattermost up`); `./securax notify` (webhook digest to any chat, https-only off-LAN, secret-safe); `./securax capacity --people N [--bench]` (1 → 100,000 tier ladder with an enforced honest-gaps list); OpenSSF Scorecard workflow and SLSA build-provenance for released images.
- **Cockpit, storage, safe update, impact** (docs 37, 38): `./securax cockpit` (one self-contained page: vital signs, Eisenhower, 80/20, NIST CSF maturity radar, AI-risk coverage, trends; no script/port; linked from the Command Center), `./securax storage` (sizes, growth forecast, safe tidy; `SECURAX_BACKUP_DIR`), `./securax update` now backs up, health-checks and **rolls back** a release that does not start, `./securax impact` + a fitness rule (blast-radius map), `./securax regulated on` (one switch), W3C trace context through the gateway, `comply mit-ai-risk|nist-ai-600-1`, grouped `./securax help`, Dependabot for compose-pinned images and Terraform, Guiding Map gateway-key field for sign-in estates.
- **Identity-aware gateway, incident clock, data residency** (doc 36): `./securax gateway-auth` (OIDC/JWT from any provider + hashed service keys, roles, MFA for privileged roles, lock-out, authenticated audit; no new dependency), `./securax incident` (one detection starts RBI/SEBI/CERT-In… clocks; regulators are data; hash-chained case log; drafts; quarterly roll-up), `./securax residency` (classification-aware routing to allowed zones, cloud-region allow-list + attestation; jurisdiction is a file). The AI-SOC raises `auth-bruteforce`. Detectors now see redacted text only.
- **Regulatory gap assessment** (doc 35): `./securax comply` maps the RBI NBFC Cybersecurity/Technology Directions 2026 and SEBI CSCRF requirement by requirement (supported / partial / gap / entity / n/a), with verifiable evidence, a prioritised backlog and category filter; ships in `./securax evidence`, `verify` and `fitness`. Found: no caller authentication on the gateway, no incident-reporting clock, no data-localisation guard.
- **CCSP-aligned coverage** (doc 34): `./securax ccsp` maps the estate to ISC2's six CCSP domains / 38 sub-topics with verifiable evidence (stale references and unproven 'covered' fail the gate); included in `./securax evidence`, `verify` and `fitness`. A practice map, not exam content.
- **Fitness functions + game days** (doc 33): `./securax fitness` (rails latency over adversarial inputs = ReDoS guard, memory, cold start, dependency count, plus ratchets: no new critical supply-chain findings, no undocumented commands) and `./securax gameday list|run|all` (node loss, control-plane restart and an etcd snapshot-RESTORE disaster drill on the burrow twin, each with an SLO; twin left as found). `burrow.twin_restore` rewinds the control plane to a snapshot. Journey `gameday`; wake-time budgets in `lifecycle_burrow`.
- **Offline power-ups** (doc 32): `./securax offline sync|status` + `./securax kev` (CISA KEV and MITRE ATT&CK snapshots, streamed and slimmed, work with no network; the AI-SOC names ATT&CK techniques and `scan` flags known-exploited CVEs from them) and `./securax bench` (measures your installed local models for RAM fit / accuracy / tokens-per-second and recommends one). Verified repo ledger: llama.cpp, BitNet, whisper.cpp, llamafile, Atomic Red Team, Sigma, osv-scanner, sqlite-vec. Journey `offline_power`.
- **Behavioural rules + `./securax diffcheck`** (docs 31): the four rules popularised by Karpathy's LLM-coding observations, in our own words, in `BUILD-CONTRACT.md`; `diffcheck` enforces the contract's mechanical hard rules on the diff and gates `autobuild` (journey `diffcheck_gate`). Adoption ledger for agent-skills, ECC (vet: BLOCK, ideas only), karpathy-skills, freellmapi, context-mode.
### Fixed
- **A fixed Command Center looked unchanged after an update**: the web server sent no cache headers, so browsers kept an old `hub.html` for hours; the pages now always revalidate (and the service worker no longer trusts the browser's cache). The Windows launcher, the first-run script and the quick-start still pointed at `http://localhost:8088`, which is not published once HTTPS is on; they now open the right address.
- **Command Center behind the HTTPS edge**: the Guiding Map and Cockpit cards still pointed at `:8088` (refused: that port is no longer published); status dots showed a stopped service as running (a cross-origin fetch cannot read a 502) - the edge now answers a same-origin `/_up/<name>` probe; a stopped optional service shows a plain-English page with the exact start command instead of a bare nginx 502. Proven by `guiding-map/tests/test16.js` and the `tls_edge` / `tls_internal` journeys (which now also start an optional service).
- **No more `curl | sh` in our own installers** (doc 31): helm, kind, kubectl, Tailscale and k3s are now version-pinned and SHA-256-checked before they run; the WSL quick-start saves the script before running it. `vet` also catches `curl … | VAR=x sh`. The fitness ratchet tightened from 9 to 6 accepted findings.
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
