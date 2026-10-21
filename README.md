# SecuRAX — Robust · Adaptive · eXcellence-driven

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/rohan2pt0/ai-cloud-cyber-range/actions/workflows/devsecops.yml/badge.svg)](https://github.com/rohan2pt0/ai-cloud-cyber-range/actions/workflows/devsecops.yml)
<!-- readme:badge:start -->
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)
<!-- readme:badge:end -->
![AI red-team defence](https://img.shields.io/badge/red--team%20defence-100%25%2F0%20FP-blue)
![Cost to start](https://img.shields.io/badge/cost%20to%20start-%E2%82%B90-success)
![Frameworks](https://img.shields.io/badge/mapped%20to-NIST%20%7C%20ISO%20%7C%20RBI%20FREE--AI%20%7C%20DPDP-informational)


## ▶ Start here (one step)

```bash
./securax go        # gets everything working and keeps it working; safe to run any time
```

`go` checks Docker, takes the latest code safely (backup first, automatic rollback), starts the estate, installs the schedules
(nightly safe update, backups, alerts, regulator watch), sets up phones over Tailscale when it is on, and ends with one screen:
what works, and the one fix if something does not. On Windows, double-click **`START-HERE-Windows.bat`**.

Your **Guiding Map** (http://localhost:8088, or https://hub.securax.localhost with `./securax tls on`) is the home screen:
tasks, your private AI, money, goals, and one-tap launch of the rest. Install it (Add to Home Screen) to use it like an app,
even offline. Your data stays on your device.

> Something not right: `./securax doctor` · `./securax why` · Which build am I on: `./securax version` · Stop AI at once:
> `./securax ai stop all --reason "..."` · AI allowance: `./securax ai budget` · Stop and free RAM: `./securax down`

<!-- features:start -->
## What you can do

**Practise and defend**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Cyber range](docs/securax/79-EXERCISE-RANGE.md) | Practise defending real-looking systems against a live red team, with scoring, judging and MITRE ATT&CK, D3FEND and ATLAS learning paths. | `./securax exercise` |
| 🟡 [Crisis response kit](docs/securax/78-CRISIS-RESPONSE-KIT.md) | Step into an incident: collect evidence properly, find what is wrong, and draft the reports. | `./securax respond` |
| 🟢 [Purple-team loop](docs/securax/30-PURPLE-TEAM-LOOP.md) | Attack your own AI channel, check that the attack was detected, and keep the evidence. | `./securax purple` |
| 🟢 [Check software before you trust it](docs/securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) | Look inside a third-party package or file, in a sandbox, and see what a new version can do that the old one could not. | `./securax inspect` |

**Comply and govern**

| | What it does | How to open it |
|---|---|---|
| 🟢 [BFSI control matrix](docs/securax/66-BFSI-CONTROL-LIBRARY-AND-NAVIGATOR.md) | Every Indian BFSI cyber obligation as one matrix: what applies to you, what is proven, and what to close next. Works with no file from you. | `./securax go` |
| 🟢 [Regulator incident clock](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every applicable regulator's reporting deadline for an incident, counting down, with the drafts ready. | `./securax incident` |
| 🟡 [Regulatory gap maps](docs/securax/35-REGULATORY-GAP-ASSESSMENT.md) | Requirement-by-requirement maps (RBI, SEBI CSCRF, NIST AI 600-1, post-quantum and more) with the evidence for each, checked on every change. | `./securax comply` |
| 🟡 [Risk register](docs/securax/67-RISK-REGISTER-NSCS-CII.md) | Your risks with owners and dates, linked to the controls that treat them, with an overdue lamp. | `./securax risks` |
| 🟢 [Cockpit](docs/securax/37-COCKPIT-STORAGE-PATCHING.md) | One page: what is at risk, what to do next, and the trends. Lamps light only when something needs you. | `./securax cockpit` |
| 🟡 [Govern (for decision makers)](docs/securax/94-GOVERN.md) | Where the organisation stands on governance, people, process and technology; the minimum basic and the highest possible; for each gap the 5W1H and an indicative budget; the team you need; a one-page Board report; and a pack of ready policies, SOPs, registers and an executive deck. | `./securax govern` |

**Use AI safely**

| | What it does | How to open it |
|---|---|---|
| 🟢 [AI security gateway](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every AI call is checked: personal data masked, prompt injection blocked, data kept in India when it must be, and every call logged. | `./securax doctor` |
| 🟢 [Private chat](docs/securax/53-THE-TWIN.md) | A ChatGPT-style assistant that runs through the gateway, with a private local model when the data must not leave. | `./securax open` |
| 🟡 [Accurate answers without prompt engineering](docs/securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) | Every question reaches the AI with today's date and the rules a careful expert would write: never make things up, say "I don't know", flag what may have changed, show the working. A weak model says so, and a weekly check catches an AI that starts to guess. | `./securax ai honesty` |
| 🟡 [Build with open models](docs/securax/83-BUILD-WITH-OPEN-MODELS.md) | Write and fix code with strong open models through the gateway, so no single AI subscription or its limits can stop the work. | `./securax opencode` |

**Keep it running**

| | What it does | How to open it |
|---|---|---|
| 🟢 [Go back to a working version](docs/securax/82-GO-BACK-TO-A-WORKING-VERSION.md) | Something broke? One command takes you back to the last version that worked; your edits and data are kept. | `./securax rollback` |
| 🟡 [Encrypted backups](docs/securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) | Backups that are encrypted, copied off the laptop, and proved to restore every quarter. | `./securax protect` |
| 🟡 [Storage that runs itself](docs/securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) | Every source of growth has a limit; clean-ups run every six hours, and your phone hears only when space is still short. | `./securax storage` |
| 🟢 [What broke, and why](docs/securax/27-INCIDENT-RUNBOOK.md) | Names the service that stopped and the reason, in plain words, with the fix. | `./securax why` |
| 🟡 [Crown jewels and risk](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | What SecuRAX cannot lose, how exposed each one is today, and the one thing to do next, worst first. It re-scores itself every run. | `./securax jewels` |
| 🟡 [Crisis and continuity plan](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Every crisis written down before it happens: how long it may stop you, how much it may lose, the steps, and safe drills that prove it. | `./securax continuity` |
| 🟢 [Ransomware-proof backups and recovery drills](docs/securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md) | Every backup first checks that your data is still readable. If ransomware got there first, the copy is quarantined, nothing clean is deleted and you are alerted. `restore latest` picks the newest clean copy, a restore twin proves it opens, and tabletop exercises test the plan. | `./securax continuity tabletop ransomware` |
| 🟡 [Many machines, one SecuRAX](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Run it on the laptop, a VPS, a Mac mini or any cloud at once: every machine holds the same data, and any one of them can stop. Each machine is an extra, never a dependency: with every other one off, this one carries on by itself (doc 90). | `./securax nodes` |
| 🟡 [The estate finds its own weak points](docs/securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md) | Every combination of your machines being off is checked: what still works, what slows down, what stops, and the fix for each single point of failure. A new weak point is pushed to your phone. | `./securax resilience` |
| 🟡 [The autopilot](docs/securax/92-THE-AUTOPILOT.md) | The estate learns from its own failures (a postmortem draft and an alert, escalated when one keeps coming back), drills itself every night where it most needs it, and warns days before disk space, backups or the AI allowance run out. | `./securax autopilot` |
| 🟡 [Stable and beta versions](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Keep the version you rely on (stable) while a new one is tried (beta), on its own address; switching is safe and never goes back. | `./securax channel` |

**Your own tools**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Your progress](docs/securax/93-PROGRESS-YOU-CAN-SEE.md) | Is SecuRAX making you better off? Your Life OS rhythm, what made the estate stronger this month, and the one next step, on your phone every Sunday. | `./securax progress` |
| 🟢 [Guiding Map](docs/securax/14-GUIDING-MAP.md) | Your daily cockpit for life and work: goals, check-ins and plans. Works offline, no AI needed. | `./securax open` |
| 🟡 [Life OS Inbox](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Capture one line; then each note becomes an action with a next step and a date, or stays a note. Reviews turn findings into actions; Google Keep notes come in too. | `./securax open` |
| 🟢 [Your AI history](docs/securax/51-YOUR-AI-HISTORY.md) | Years of chats from Claude, ChatGPT, DeepSeek or Gemini as one private library you can search. | `./securax knowledge` |
| 🟡 [Password manager](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Your own password vault (Vaultwarden) for the Bitwarden apps on laptop and phone, encrypted on your device before it is stored. | `./securax start passwords` |
| 🟡 [Sign in to AWS, Google Cloud, Azure](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | One command per cloud, nothing to install: open the link on any device, sign in, and start building. | `./securax cloud login aws` |
| 🟡 [SecuRAX on every device](docs/securax/85-USE-SECURAX-ANYWHERE.md) | Your own address on any phone, tablet or computer: sign in with Google and everything is there, synced, with the laptop off. One command sets it up. | `./securax online setup` |

This list is generated from [`features.json`](features.json); the Command Center, the website and the docs home page show the same one.
<!-- features:end -->

<!-- readme:whats-new:start -->
## What's new

**On main, in the next release:**

- [Govern, for decision makers](docs/securax/94-GOVERN.md)
- [Progress you can see, and the north star](docs/securax/93-PROGRESS-YOU-CAN-SEE.md)
- [The autopilot](docs/securax/92-THE-AUTOPILOT.md)
- [The estate finds its own weak points](docs/securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md)
- [Accurate answers without prompt engineering](docs/securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md)
- [Ransomware-proof backups and recovery drills](docs/securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md)
- [Many machines, one SecuRAX](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md)
- Stable and beta

**Release 0.2.0 - 2026-10-17:**

- [CI at agent scale](docs/securax/68-CI-AT-AGENT-SCALE.md)
- Nightly safe update
- A broken workflow file ran no checks at all
- Life OS: the new Inbox tab crowded calm mode and the phone bar (six tabs)
- `./securax start flows` reported failure although it worked
- A second home for the code, in one guided step
- "v0.1.0 never updates"
- A busy port 80/443 no longer leaves you with nothing running
- Risk registers with a one-row header lost their first risk
- No paths to type

Everything, with details: [`CHANGELOG.md`](CHANGELOG.md).
<!-- readme:whats-new:end -->

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
> 🌐 **Product site:** [cyberbaba.org](https://cyberbaba.org/) · 📘 **Documentation:** [cyberbaba.org/docs](https://cyberbaba.org/docs/) (source in `docs/`, built by `mkdocs.yml`). Every page is listed under [All documentation](#all-documentation) below.
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

## What it claims, and what it does not

Every capability SecuRAX claims has a written envelope (the conditions it holds under) and a proof: a test, or a journey that runs the
real estate in CI. `./securax fitness` fails if a proof goes missing ([`governance/claims.json`](governance/claims.json), [doc 55](docs/securax/55-ENGINEERING-STANDARD.md)).

It is a **single-host** estate for one person or a small team. It is not a Slack, not highly available, not multi-region, not
load-tested beyond its measured budgets, and not independently audited. The full "not claimed" list is in the same file.

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

<!-- readme:proofs:start -->
> **Proof, not claims:** 46 end-to-end journeys run the real estate (real containers, a real browser) on every merge and every night; pull requests run the ones their change can affect ([doc 68](docs/securax/68-CI-AT-AGENT-SCALE.md)).
<!-- readme:proofs:end -->

<!-- readme:docs:start -->
## All documentation

[SecuRAX — Overview](docs/securax/00-OVERVIEW.md) 🟢 · [SecuRAX — Design Principles](docs/securax/01-PRINCIPLES.md) 🟢 · [SecuRAX — Unified Architecture](docs/securax/02-ARCHITECTURE.md) 🟢 · [SecuRAX — Capability Catalog](docs/securax/03-CAPABILITY-CATALOG.md) 🟡 · [SecuRAX — Compliance & Standards Map](docs/securax/04-COMPLIANCE-MAP.md) 🟡 · [SecuRAX — Roadmap](docs/securax/05-ROADMAP.md) 🟡 · [Extending SecuRAX — how to plug in any future project](docs/securax/06-EXTENDING.md) 🟢 · [SecuRAX — Integrations & Connectivity](docs/securax/07-INTEGRATIONS.md) 🟡 · [SecuRAX — Operating Model](docs/securax/08-OPERATING-MODEL.md) 🟡 · [SecuRAX — Open-Core Model & Tiers](docs/securax/09-OPEN-CORE-TIERS.md) 🔴 · [SecuRAX — Full-Scale Mode (opt-in, turn-off-able)](docs/securax/10-FULL-STACK.md) 🟡 · [SecuRAX — Kaizen & Antifragility (the UPSC lens)](docs/securax/11-KAIZEN.md) 🟡 · [SecuRAX — Intelligent UX (the operator's lens: simple on top, disciplined underneath)](docs/securax/12-INTELLIGENT-UX.md) 🟡 · [SecuRAX — Global Intelligence (decide the community-proven way, before it commoditises)](docs/securax/13-GLOBAL-INTELLIGENCE.md) 🟢 · [SecuRAX — The Guiding Map (the life-OS cockpit)](docs/securax/14-GUIDING-MAP.md) 🟢 · [SecuRAX — Cost, models & never hitting a limit (the FinOps playbook)](docs/securax/15-COST-AND-MODELS.md) 🟢 · [SecuRAX — The agents army (stealth specialist advisors)](docs/securax/16-AGENTS.md) 🟡 · [SecuRAX — Enterprise Architecture alignment (the end-state blueprint)](docs/securax/17-ENTERPRISE-ARCHITECTURE.md) 🟡 · [SecuRAX — Future Financial Planner (sovereign, offline)](docs/securax/18-FINANCIAL-PLANNER.md) 🟢 · [Autonomous web research (the sovereign Manus / Clawbot)](docs/securax/19-AUTONOMOUS-RESEARCH.md) 🟡 · [Claude-subscription parity (the sovereign equivalents)](docs/securax/20-CLAUDE-PARITY.md) 🟡 · [Versioning & release policy](docs/securax/21-VERSIONING-AND-RELEASES.md) 🟢 · [Plugins & AI Providers](docs/securax/22-PLUGINS-AND-PROVIDERS.md) 🟢 · [Build SecuRAX without depending on Claude](docs/securax/23-BUILD-WITHOUT-CLAUDE.md) 🟡 · [Resilience & low-resource operation](docs/securax/24-RESILIENCE-AND-LOW-RESOURCE.md) 🟢 · [Fallbacks & elasticity — what happens when a piece is missing](docs/securax/25-FALLBACKS-AND-ELASTICITY.md) 🟢 · [Coverage check vs. the enterprise reference maps — and the 80/20 gaps](docs/securax/26-COVERAGE-AND-GAPS.md) 🟢 · [Incident runbook — what to do, in order](docs/securax/27-INCIDENT-RUNBOOK.md) 🟢 · [Status & traceability — every ask, what shipped, how it is proven, what is NOT done](docs/securax/28-STATUS-AND-TRACEABILITY.md) 🟢 · [Lifecycle — from a dormant seed to a multi-tenant forest (and back to sleep)](docs/securax/29-LIFECYCLE-SEED-TO-FOREST.md) 🟡 · [The purple-team loop — would anyone *know*?](docs/securax/30-PURPLE-TEAM-LOOP.md) 🟢 · [Supply-chain gate — `./securax vet`](docs/securax/31-SUPPLY-CHAIN-VET.md) 🟢 · [Powerful offline, sharp on a small machine — what we took from the most-starred repos, and what we measured](docs/securax/32-OFFLINE-AND-LOW-RESOURCE.md) 🟢 · [Fitness functions and game days — promises as numbers, resilience as rehearsal](docs/securax/33-FITNESS-AND-GAME-DAYS.md) 🟢 · [CCSP-aligned coverage (step 5)](docs/securax/34-CCSP-COVERAGE.md) 🟢 · [Regulatory gap assessment — RBI NBFC Directions 2026 and SEBI CSCRF](docs/securax/35-REGULATORY-GAP-ASSESSMENT.md) 🟡 · [Identity, incident clock, data residency](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) 🟢 · [Cockpit, storage growth, patching, impact](docs/securax/37-COCKPIT-STORAGE-PATCHING.md) 🟢 · [Engineering practices, research cues, and the friction audit](docs/securax/38-ENGINEERING-PRACTICES-AND-RESEARCH.md) 🟡 · [Growing from one person to many: live sync, team chat, and the scale ladder](docs/securax/39-PEOPLE-SCALE-LIVE-SYNC-CHATOPS.md) 🟡 · [Encryption in transit: HTTPS everywhere, by name, from the browser to the edge](docs/securax/40-ENCRYPTION-IN-TRANSIT.md) 🟢 · [Quantum readiness: what is protected, what is not, and what to do first](docs/securax/41-QUANTUM-READINESS.md) 🟡 · [OpenCode Go and the OpenCode terminal agent](docs/securax/42-OPENCODE-GO-AND-THE-TERMINAL-AGENT.md) 🟢 · [Look inside third-party software before you trust it (REA, sandboxed)](docs/securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) 🟢 · [The admission gate (`forge`) and the self-healing sandbox](docs/securax/44-ADMISSION-GATE-AND-SELF-HEALING-SANDBOX.md) 🟢 · [`./securax autobench`: measure each build model before you trust it](docs/securax/45-AUTOBENCH-MEASURE-YOUR-BUILD-MODELS.md) 🟢 · [Certification path: the hardest offensive and AI certifications, on 30 hours a week and ₹5 lakh a year](docs/securax/46-CERTIFICATION-PATH.md) 🔴 · [Calm mode: less input, more insight (the Guiding Map, reviewed as a user)](docs/securax/47-CALM-MODE-LESS-INPUT-MORE-INSIGHT.md) 🟢 · [The Guiding Map, freeze-ready: a quarterly system you will actually run](docs/securax/48-GUIDING-MAP-FREEZE-READY.md) 🟢 · [Career compass: choose the next job without betting the house](docs/securax/49-CAREER-COMPASS.md) 🟢 · [Reasoning budget: think less where it does not pay](docs/securax/50-REASONING-BUDGET.md) 🟡 · [Your AI history: years of chats as one library you own](docs/securax/51-YOUR-AI-HISTORY.md) 🟢 · [Automation that works on day one, and the SuperApp plan](docs/securax/52-AUTOMATION-PACK-AND-SUPERAPP-PLAN.md) 🟡 · [The Twin: a Claude-like assistant you own](docs/securax/53-THE-TWIN.md) 🟢 · [SecuRAX technical gist (for another engineer or AI assistant)](docs/securax/54-TECHNICAL-GIST.md) 🟢 · [The engineering standard: no claim without proof](docs/securax/55-ENGINEERING-STANDARD.md) 🟢 · [Pool your machines: what we took from RAMDeck, and what we did not](docs/securax/56-POOL-YOUR-MACHINES.md) 🟡 · [Compute, memory and storage: the smart way round the limits (global and Indian options)](docs/securax/57-COMPUTE-STRATEGY.md) 🟡 · [Phones over Tailscale, and a shell on the laptop from your phone](docs/securax/58-PHONES-AND-REMOTE-SHELL.md) 🟡 · [The end state, and how SecuRAX gets there](docs/securax/59-END-STATE-ARCHITECTURE.md) 🟡 · [Ship it on cyberbaba.org, and build SecuRAX with SecuRAX](docs/securax/60-SHIP-IT-AND-BUILD-WITH-SECURAX.md) 🟡 · [Run SecuRAX as a business, with a low profile](docs/securax/61-RUN-IT-AS-A-BUSINESS.md) 🟡 · [Strategy: what Cyera and the AI unicorns teach, and where SecuRAX can win](docs/securax/62-STRATEGY-LESSONS-FROM-CYERA-AND-AI-UNICORNS.md) 🟡 · [Engineering resilience audit: the backend fundamentals, checked against SecuRAX](docs/securax/63-ENGINEERING-RESILIENCE-AUDIT.md) 🟢 · [Success mantras: what the best organisations do, and where SecuRAX does it too](docs/securax/64-SUCCESS-MANTRAS.md) 🟢 · [Configuration, not code: nothing specific is hardwired](docs/securax/65-CONFIGURATION-NOT-CODE.md) 🟢 · [The BFSI control library, the navigator, and a dark cockpit](docs/securax/66-BFSI-CONTROL-LIBRARY-AND-NAVIGATOR.md) 🟢 · [Risk register, the NSCS audit baseline and national CII guidance, all linked](docs/securax/67-RISK-REGISTER-NSCS-CII.md) 🟡 · [CI at agent scale: prove what changed, not everything, every time](docs/securax/68-CI-AT-AGENT-SCALE.md) 🟡 · [Human-in-command for AI, and what the October 2026 fintech signals mean for SecuRAX](docs/securax/69-HUMAN-IN-COMMAND-AND-FINTECH-SIGNALS.md) 🟢 · [What national strategies teach a personal estate (80/20)](docs/securax/70-LESSONS-FROM-NATIONAL-STRATEGIES.md) 🟢 · [What 26 national strategies agree on, and what SecuRAX does about it](docs/securax/71-WHAT-26-NATIONAL-STRATEGIES-AGREE-ON.md) 🟡 · [Sync and backup without the laptop](docs/securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) 🟡 · [Finish setting up, and publish the site](docs/securax/73-FINISH-SETTING-UP-AND-PUBLISH-THE-SITE.md) 🟡 · [Pattern interrupt: in a heavy week, the Life OS subtracts](docs/securax/74-PATTERN-INTERRUPT.md) 🟢 · [Distribute, install, feedback: how SecuRAX reaches people and gets better](docs/securax/75-DISTRIBUTE-INSTALL-FEEDBACK.md) 🟡 · [Findings, repairs, restore, shortcuts: the best of four mature tools](docs/securax/76-FINDINGS-REPAIRS-RESTORE-SHORTCUTS.md) 🟢 · [OWASP and other global projects: what SecuRAX uses, what it adds now, what waits](docs/securax/77-OWASP-AND-GLOBAL-PROJECTS.md) 🟢 · [Crisis response kit: step in, collect properly, find what is wrong, report](docs/securax/78-CRISIS-RESPONSE-KIT.md) 🟡 · [Exercise range: live-fire cyber defence exercises](docs/securax/79-EXERCISE-RANGE.md) 🟡 · [Storage that grows with you: bounded by design, tiered, and run by itself](docs/securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) 🟡 · [The range against the market, and how it teaches: MITRE frameworks, learning paths, players and badges](docs/securax/81-RANGE-VS-THE-MARKET-AND-LEARNING.md) 🟡 · [Go back to a working version, at any time: first restore, then diagnose](docs/securax/82-GO-BACK-TO-A-WORKING-VERSION.md) 🟢 · [Build with open models: leave the Claude Code subscription without losing the rigour](docs/securax/83-BUILD-WITH-OPEN-MODELS.md) 🟡 · [Crown jewels, the crisis plan, and the foundation for scale](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) 🟡 · [Use SecuRAX from any device, like a SaaS app](docs/securax/85-USE-SECURAX-ANYWHERE.md) 🟡 · [Many machines, one SecuRAX, and the road to a lakh users](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) 🟡 · [Security review before the freeze](docs/securax/87-SECURITY-REVIEW-BEFORE-FREEZE.md) 🟡 · [Ransomware and disaster recovery, proven before shipping](docs/securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md) 🟢 · [Accurate answers without prompt engineering](docs/securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) 🟡 · [It works on whatever machine is on](docs/securax/90-WORKS-ON-WHATEVER-IS-ON.md) 🟢 · [Any machine can carry the estate, and the estate finds its own weak points](docs/securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md) 🟡 · [The autopilot: the estate learns, drills and looks ahead by itself](docs/securax/92-THE-AUTOPILOT.md) 🟡 · [Progress you can see: the point of all of it](docs/securax/93-PROGRESS-YOU-CAN-SEE.md) 🟡 · [Govern: for decision makers](docs/securax/94-GOVERN.md) 🟡

🟢 built · 🟡 partly built · 🔴 not built yet ([what the lights mean](docs/index.md#the-status-lights))
<!-- readme:docs:end -->
