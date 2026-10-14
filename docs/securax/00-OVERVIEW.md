<!--
  SecuRAX — Overview & "second brain" index.
  Purpose of this file: the single entry point that explains WHAT SecuRAX is, WHY it
  exists, and WHERE everything lives, so you never have to re-research the big picture.
  Read this top-to-bottom once; after that, jump straight to the pillar or doc you need.
  Every acronym is expanded on first use (full-forms everywhere, by design).
-->

# SecuRAX — Overview

**SecuRAX** = **Secu**rity · **R**obust · **A**daptive · e**X**cellence-driven.
It is the umbrella program that unifies everything you are building into **one lifelong,
zero-investment-to-start, vendor-agnostic foundation** that scales from a single laptop to
an enterprise / Managed Security Services Provider (MSSP) estate — without ever being
rebuilt from scratch.

> **North-star (the one sentence):** *A self-evolving, antifragile command center that uses
> open-source AI and security tooling to protect what matters, compound your advantage over
> time, and make you — and the people around you — a measurably better version of
> themselves, while satisfying every auditor on the first pass.*

## Why this document set exists
You have ~10 excellent but scattered design documents (a cyber range, a hybrid-AI SOP, a
Life-OS PWA, an MSSP SOC blueprint, a security-ecosystem vision, finance notes). Scattered
knowledge is a single point of failure: it gets stale, duplicated, and re-researched. This
`docs/securax/` set is the **consolidation** — your "second brain". Decide once, write it
down, link the proven tool, and move on.

## The five pillars (one estate, five faces)
| # | Pillar | What it is | Seed that already exists in this repo |
|---|--------|-----------|----------------------------------------|
| **P1** | **AI Security Range** — *security **for** AI* | Guardrails, red-teaming, AI-SPM, governance for LLM/ML systems | `apps/`, `redteam/`, `governance/`, `local/`, `infra/` |
| **P2** | **AI-SOC / SecOps** — *AI **for** security* | Detection, correlation, triage, threat-intel, incident response | `ai-soc/` (triage engine) → grows into Wazuh + MISP + TheHive |
| **P3** | **SENTINEL Command Center** — *the brain* | Hybrid local+cloud LLM, data-tier router, automation, knowledge base | `apps/llm-gateway/` + roadmap (Ollama + n8n + Obsidian) |
| **P4** | **Guiding Map / Life-OS** — *the human layer* | Personal & family operating system, continuity, OPSEC, finance | `personal-rnd/` + the Guiding Map PWA |
| **P5** | **Governance, Risk & Compliance (GRC)** — *the proof* | Control mapping, audit evidence, board narratives | `docs/compliance-matrix.md`, `redteam/aispm_scan.py`, this doc set |

All five share **one spine**: common identity, common data-classification (Red/Yellow/Green),
common policy-as-code, common observability, common audit trail. That shared spine is what
makes it an *ecosystem* and not five disconnected projects.

## How to navigate this foundation
| If you want… | Read |
|---|---|
| The reasoning rules the whole thing obeys | [`01-PRINCIPLES.md`](01-PRINCIPLES.md) |
| The layered architecture + how pillars connect | [`02-ARCHITECTURE.md`](02-ARCHITECTURE.md) |
| "Which open-source tool do I use for X?" (never re-research) | [`03-CAPABILITY-CATALOG.md`](03-CAPABILITY-CATALOG.md) |
| "Which standard/regulation does this satisfy?" | [`04-COMPLIANCE-MAP.md`](04-COMPLIANCE-MAP.md) |
| "What do I do first, next, later?" (zero → scale) | [`05-ROADMAP.md`](05-ROADMAP.md) |
| A visual, browsable command center | open [`../../portal/index.html`](../../portal/index.html) |
| Add a *future* project to this same base | [`06-EXTENDING.md`](06-EXTENDING.md) |
| Connect it to Claude/Google/Microsoft APIs | [`07-INTEGRATIONS.md`](07-INTEGRATIONS.md) |
| How the system runs itself (governance) | [`08-OPERATING-MODEL.md`](08-OPERATING-MODEL.md) |
| Open-core model & subscription tiers | [`09-OPEN-CORE-TIERS.md`](09-OPEN-CORE-TIERS.md) |
| Go full-scale (opt-in, turn-off-able) | [`10-FULL-STACK.md`](10-FULL-STACK.md) |
| How failures become strengths (Kaizen/SI) | [`11-KAIZEN.md`](11-KAIZEN.md) |
| Expert answers without prompt-engineering (the "Ask" design) | [`12-INTELLIGENT-UX.md`](12-INTELLIGENT-UX.md) |
| Decide the community-proven way (Reddit/Amazon-style intelligence) | [`13-GLOBAL-INTELLIGENCE.md`](13-GLOBAL-INTELLIGENCE.md) |
| The daily cockpit (life-OS PWA, sovereign sync) | [`14-GUIDING-MAP.md`](14-GUIDING-MAP.md) |
| Never hit a usage limit (cost, models, free compute) | [`15-COST-AND-MODELS.md`](15-COST-AND-MODELS.md) |
| Regulatory gap maps (RBI, SEBI, CCSP, MIT, NIST) | [`35-REGULATORY-GAP-ASSESSMENT.md`](35-REGULATORY-GAP-ASSESSMENT.md) |
| Sign-in, incident clock, data residency | [`36-IDENTITY-INCIDENT-RESIDENCY.md`](36-IDENTITY-INCIDENT-RESIDENCY.md) |
| One-page health, storage growth, patching, impact | [`37-COCKPIT-STORAGE-PATCHING.md`](37-COCKPIT-STORAGE-PATCHING.md) |
| Live sync, team chat (Mattermost), growing from 1 to 100,000 people | [`39-PEOPLE-SCALE-LIVE-SYNC-CHATOPS.md`](39-PEOPLE-SCALE-LIVE-SYNC-CHATOPS.md) |
| HTTPS everywhere, the private certificate authority, what is not yet encrypted | [`40-ENCRYPTION-IN-TRANSIT.md`](40-ENCRYPTION-IN-TRANSIT.md) |
| Quantum readiness: cryptography inventory (CBOM), post-quantum key exchange, encrypted backups | [`41-QUANTUM-READINESS.md`](41-QUANTUM-READINESS.md) |
| OpenCode Go (flat-rate open models) and the OpenCode terminal agent, guarded | [`42-OPENCODE-GO-AND-THE-TERMINAL-AGENT.md`](42-OPENCODE-GO-AND-THE-TERMINAL-AGENT.md) |
| Look inside third-party software before you trust it (REA, sandboxed; capability drift) | [`43-INSPECT-THIRD-PARTY-SOFTWARE.md`](43-INSPECT-THIRD-PARTY-SOFTWARE.md) |
| Measure each build model on hidden-graded tasks before trusting it (`autobench`) | [`45-AUTOBENCH-MEASURE-YOUR-BUILD-MODELS.md`](45-AUTOBENCH-MEASURE-YOUR-BUILD-MODELS.md) |
| Prove a change is really done (admission gate: fail-to-pass, mutation, complexity) and a sandbox that retries infrastructure-only failures | [`44-ADMISSION-GATE-AND-SELF-HEALING-SANDBOX.md`](44-ADMISSION-GATE-AND-SELF-HEALING-SANDBOX.md) |
| What well-run products do that we skipped, research cues, friction audit | [`38-ENGINEERING-PRACTICES-AND-RESEARCH.md`](38-ENGINEERING-PRACTICES-AND-RESEARCH.md) |
| Summon a specialist advisor (first-draft opinion) | [`16-AGENTS.md`](16-AGENTS.md) |
| The end-state blueprint every build maps to | [`17-ENTERPRISE-ARCHITECTURE.md`](17-ENTERPRISE-ARCHITECTURE.md) |
| Plan your financial future (sovereign, offline) | [`18-FINANCIAL-PLANNER.md`](18-FINANCIAL-PLANNER.md) |
| Autonomous web research (sovereign Manus/Clawbot) | [`19-AUTONOMOUS-RESEARCH.md`](19-AUTONOMOUS-RESEARCH.md) |
| Claude-subscription parity (Projects/Artifacts/Routines/…) | [`20-CLAUDE-PARITY.md`](20-CLAUDE-PARITY.md) |
| How we version & release (SemVer, changelog, process) | [`21-VERSIONING-AND-RELEASES.md`](21-VERSIONING-AND-RELEASES.md) |
| Add AI providers (OpenAI, Groq, Bedrock…) like plugins | [`22-PLUGINS-AND-PROVIDERS.md`](22-PLUGINS-AND-PROVIDERS.md) |
| Build SecuRAX with its own models (no paid-Claude dependency) | [`23-BUILD-WITHOUT-CLAUDE.md`](23-BUILD-WITHOUT-CLAUDE.md) |
| Run on a modest laptop; the degradation ladders | [`24-RESILIENCE-AND-LOW-RESOURCE.md`](24-RESILIENCE-AND-LOW-RESOURCE.md) |
| What happens when each component fails + elastic sizing | [`25-FALLBACKS-AND-ELASTICITY.md`](25-FALLBACKS-AND-ELASTICITY.md) |
| Grow the estate: dormant seed → sprout → tree → canopy → forest, and back to sleep | [`29-LIFECYCLE-SEED-TO-FOREST.md`](29-LIFECYCLE-SEED-TO-FOREST.md) |
| Every ask, its status and proof (what is NOT done) | [`28-STATUS-AND-TRACEABILITY.md`](28-STATUS-AND-TRACEABILITY.md) |
| Install on Windows (copy-paste steps) | [`../../WINDOWS-QUICKSTART.md`](../../WINDOWS-QUICKSTART.md) |
| Test the product as a user would (sandbox) | [`../../sandbox/README.md`](../../sandbox/README.md) |
| Start using it today | [`../../GETTING-STARTED.md`](../../GETTING-STARTED.md) |

## The three promises this foundation keeps
1. **Start at ₹0.** Everything in Phase 0 runs on the HP Spectre x360 with free/open-source
   software. You only spend money when a specific need justifies it (see the roadmap's
   "trigger to scale" column).
2. **Never a dead end.** Every tool choice has a documented upgrade path (laptop → mini-PC →
   cloud → Kubernetes → MSSP multi-tenant). You grow the same estate; you do not rebuild it.
3. **Audit-ready by construction.** Controls are mapped to frameworks *before* they are
   built (compliance-by-design), evidence is generated automatically, and nothing is a
   single point of failure — so no auditor finds a gap you did not already document.

## Status
This is the **foundation layer**. Pillar 1 (AI Security Range) is already built, tested, and
CI-green. Pillars 2–5 have working seeds and a sequenced roadmap. Nothing here is
over-engineered: each phase is independently useful and you can stop after any phase with a
complete, working system.
