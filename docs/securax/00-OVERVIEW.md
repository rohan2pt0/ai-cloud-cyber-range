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
