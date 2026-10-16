<!--
  SecuRAX — Operating Model.
  "How does this system RUN ITSELF properly, forever, under any constraint?"
  Answer: borrow the operating patterns that keep global institutions working, implement each
  with a proven open-source mechanism (never reinvented), and embed the personal principles
  (Eisenhower, Deep Work, Atomic Habits, antifragility, minimalism) as operating rules.
-->

# SecuRAX — Operating Model

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** A one-person operating model; team roles are described, not staffed. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

The world runs on a handful of durable patterns: a body that sets **standards**, a body that
**monitors compliance**, a body that **shares intelligence**, a body that **coordinates**, and
a body that **surveils health and resources**. SecuRAX copies those patterns so the system
keeps running properly with clarity and effective output — regardless of time, people, or
resource constraints. Each pattern is implemented with a battle-tested open-source tool, and
**no single tool is load-bearing** (every one has a named alternative, Principle P-2).

## 1. Institutional patterns → how SecuRAX runs itself
| Global analogue | Its job | SecuRAX mechanism (proven OSS, swappable) |
|---|---|---|
| **UN / ISO (standards)** | set the rules everyone follows | `docs/securax/` + policy-as-code (**OPA/Conftest**, **Kyverno**) — the rulebook is executable |
| **FATF (mutual evaluation)** | periodic independent assessment + a public scorecard | AI-SPM posture scan + red-team scorecard run in CI (**continuous mutual evaluation of yourself**) |
| **INTERPOL (intelligence sharing)** | share indicators across borders | **MISP** threat-intel (STIX/TAXII) + AI-SOC correlation |
| **IMF (surveillance & health)** | watch the vitals, warn early | `./securax doctor` + **Prometheus/Grafana/Loki** + alert thresholds (below) |
| **G20 / UNSC (coordination)** | coordinate action, decide together | **Mattermost** ChatOps + **n8n** orchestration + the MCP control plane |
| **Central bank (lender of last resort)** | absorb shocks, keep liquidity | fallback chains (local↔cloud, 3 clouds), 3-2-1 backups, kill-switches |
| **Audit bodies (CAG/ISACA)** | independent assurance, evidence | immutable audit log + auto-generated evidence (SBOM, board brief) |

The point: you are not holding the system together by willpower. The **standards are code**,
the **assessment is automated**, and the **coordination is delegated to agents** — so it runs
even when you are busy, away, or constrained.

## 2. Agentic AI — separating signal from noise (so you don't have to)
Repetitive, high-volume work is handed to agents; you only see the signal. Built on proven
tools, not a bespoke framework (Principle P-3):
| Agent role | Does the high-volume grind | Built on |
|---|---|---|
| **Triage agent** | reads every alert/log, raises only real incidents | AI-SOC (`ai-soc/`) + MCP `soc_triage` |
| **Classifier agent** | labels every inbound item, routes by data tier | n8n data-tier router + gateway |
| **Brief agent** | compresses the day's noise into a 5-bullet brief | n8n morning-brief + local model |
| **Assistant agent** | runs estate tasks you ask for in plain language | MCP server (Claude Desktop / Claude Code / local agent) |
| **(scale) Orchestrated agents** | multi-step autonomous workflows | **n8n** first; **CrewAI** / **LangGraph** when a task truly needs multi-agent planning |

Rule: an agent may *decide and act* only on reversible, low-blast-radius tasks; anything
high-impact stops for human approval (the HITL control, ASI09). Agents reduce noise; they
never get unbounded authority.

## 3. No single point of failure — the redundancy ledger
Every critical function has a fallback, so losing one component never stops the system:
| Function | Primary | Fallback(s) |
|---|---|---|
| Inference | local Ollama | Gemini → Bedrock → Azure (LiteLLM chain) |
| Cloud | one provider | three independent clouds + on-prem |
| Orchestration | Kubernetes | Docker Compose (same images) |
| Collaboration | Mattermost | email / Matrix |
| Secrets | OpenBao | SOPS + age files |
| State | PostgreSQL | restic/Borg restore, WORM object copy |
| Control | MCP / Guiding Map | plain scripts (`securax`, CLIs) |
| You | — | runbooks + the operating model so others can run it |

## 4. Health surveillance & alerting — global-standard thresholds
Monitored by `./securax doctor` (quick) and Prometheus/Grafana (continuous). Thresholds are
the widely-used SRE/industry defaults; alerts fire *before* pain:
| Signal | Warn | Critical | Action |
|---|---|---|---|
| Disk used | 80% | 90% | prune caches / old images |
| RAM used | 85% | 95% | use `local-fast` model, stop idle profiles |
| CPU sustained | 80% (5 min) | 95% | shed load, scale out |
| Service health | degraded | down >5 min | auto-restart, page via Mattermost |
| Error budget (SRE) | 50% burned | exhausted | freeze changes, stabilise |
| Guardrail detector | — | unavailable | fail **closed** |

## 5. The review cadence — ITIL continual improvement + Kaizen
A system that is not reviewed decays. The rhythm (also in the Guiding Map):
- **Daily (10 min):** shutdown ritual — what moved, what's next, one OPSEC gap closed.
- **Weekly (Fri):** GTD review, error-budget check, one friction point fixed (Kaizen).
- **Monthly:** posture scan, risk register, prune/patch, dependency health.
- **Quarterly:** OKR reset, mutual evaluation (full red-team + posture), threat-model refresh.
- **Annually:** architecture review, DR drill, major upgrades, 5-year refresh.

## 6. Operating principles — embedded, not aspirational
| Principle | Where it lives in the system |
|---|---|
| **Eisenhower matrix** | Guiding Map "Today" tags every task Q1–Q4; do Q1, delete Q4 |
| **Deep Work (Cal Newport)** | protect 90-min focus blocks; agents handle shallow work so you don't |
| **Atomic Habits (James Clear)** | Guiding Map habit streaks; 1% daily → 37× a year; make the good thing the default |
| **Antifragility (Taleb)** | every incident becomes a rule/test; the system strengthens from stress; capped downside, open upside |
| **Minimalism (Musk's "best part is no part")** | start simple; every component must earn its keep; delete ruthlessly |
| **80/20 (Pareto)** | ship the vital 20%; agents remove the 80% noise; free core, paid scale |
| **Assume breach / zero trust** | localhost-only binding, least privilege, fail-closed, least blast radius |

> This operating model is the difference between a project and a **system**. A project needs
> you. A system runs — and improves — whether or not you are watching.
