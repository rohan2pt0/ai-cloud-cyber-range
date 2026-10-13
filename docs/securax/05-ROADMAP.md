<!--
  SecuRAX — Roadmap (crawl → walk → run).
  A gradual path with the end-goal fixed. Each phase is INDEPENDENTLY USEFUL: you can stop
  after any phase and have a complete, working system. Every "scale up" has an explicit
  TRIGGER so you never migrate before you need to (Principle P-1/P-7). Start cost: ₹0.
-->

# SecuRAX — Roadmap

Gradual, end-in-mind, each step independently useful. **Do not jump ahead of the trigger.**
Effort is "evenings/weekends" scale for one person; nothing here needs a team.

## Maturity ladder (the big picture)
```
CRAWL ───────────────▶ WALK ──────────────▶ RUN ──────────────▶ FLY
Phase 0: Laptop base   Phase 1: Always-on    Phase 2: Cloud +    Phase 3-4: K8s +
free, private AI +     home server + core    orchestration +     multi-tenant MSSP
range already built    SOC + identity        GitOps              (revenue-funded)
₹0                     one-time hardware      pay-as-you-go       elastic / funded
```

## Phase 0 — Foundation on the HP Spectre x360 (NOW · ₹0)
**Goal:** a private, working AI + security base you use daily. *Most of this already exists.*
1. **AI base (done):** guardrail gateway, red-team suite, AI-SPM, model registry, local K8s,
   multi-cloud IaC — all CI-green in this repo.
2. **Hybrid AI daily driver:** Ollama + LiteLLM + Open WebUI + AnythingLLM (private doc chat),
   per the SOP. Red/Yellow/Green rule enforced by model choice.
3. **Automation glue:** n8n with the five core workflows (morning brief, email triage,
   meeting notes, data-tier router, weekly review).
4. **Second brain:** Obsidian vault (PARA + Zettelkasten); Git auto-commit backup.
5. **Human layer:** Guiding-Map PWA for continuity/OPSEC; `personal-rnd/` tools; FIRE tracker.
- **Stop-here value:** a private AI, an automated day, a documented life-OS, an AI-security
  private AI, an automated day, a documented life-OS. Exit when you need always-on / family / remote access.

> **Build status (Oct 2026):** all five phases now exist as dormant code that wakes on demand — see [29 · Lifecycle](29-LIFECYCLE-SEED-TO-FOREST.md) and the honest per-phase ledger in [28](28-STATUS-AND-TRACEABILITY.md). Phase 1 core is proven with real containers; phases 2–4 are validated and plan-proved but not yet applied to a real cloud.

## Phase 1 — Always-on core (WALK · one-time hardware ~₹1.2–1.5L, optional)
**Trigger:** you want 24×7 availability, family access, bigger local models, or a real SOC.
1. **Hardware:** mini-PC / workstation (32–64 GB RAM, RTX 4060 Ti 16 GB class) running Ubuntu;
   laptop becomes a thin client. (Or skip hardware and use a single cloud VM — see Phase 2.)
2. **Identity spine:** Keycloak (SSO/MFA/RBAC) in front of every service.
3. **SOC core (Pillar 2):** Wazuh (SIEM+HIDS+compliance) + Suricata (IDS) + MISP (CTI) +
   TheHive (IR). Point the AI-SOC triage engine at their outputs.
4. **Observability:** Prometheus + Grafana + Loki.
5. **Secrets + backup:** OpenBao + restic (3-2-1).
- **Stop-here value:** a home MSSP-grade SOC + identity + monitoring. Audit-mappable.

## Phase 2 — Cloud + orchestration (RUN · pay-as-you-go, within ₹2,500/mo)
**Trigger:** multiple workloads, remote/team access, or a first client pilot.
1. **Platform:** k3s (lightweight Kubernetes) on-prem or a cloud VM; migrate compose services
   via the same OCI images (no rewrite).
2. **GitOps:** Argo CD for declarative, auditable deploys.
3. **Posture at scale:** Prowler (CSPM), OpenSCAP + Wazuh SCA (config compliance), immudb
   (immutable audit).
4. **SOAR:** Shuffle / Cortex playbooks for automated response.
5. **Data tier:** managed PostgreSQL + MinIO (S3) object store with WORM for logs.
- **Stop-here value:** an elastic, orchestrated, continuously-compliant platform.

## Phase 3 — Kubernetes hardened + multi-cloud (RUN+)
**Trigger:** need HA across zones, DR, or regulated-client SLAs.
1. Managed Kubernetes (EKS/GKE/AKS) with the existing Terraform/OpenTofu modules.
2. Zero-trust networking, service mesh (optional), full policy-as-code (Kyverno + OPA).
3. DR drills (ISO 22301), chaos testing (antifragility — Principle P-0).

## Phase 4 — Multi-tenant MSSP (FLY · revenue-funded)
**Trigger:** paying clients.
1. Per-tenant isolation (namespace/cluster), SSO federation, subscription-based
   module enable/disable (the SecuRAX licensing model), billing, SLA dashboards.
2. Thought-leadership + business-development engine (Pillar 4/5) turns the estate into a
   book of business.

---
## The 80/20 "do these first" shortlist (if you only do five things)
1. Run the existing range locally (`local/scripts/bootstrap-laptop.sh`) — you already have it.
2. Stand up Ollama + Open WebUI + the data-tier rule — private AI daily driver.
3. Wire n8n's five workflows — automate the shallow work.
4. Start the Obsidian second brain + Guiding-Map PWA — capture everything once.
5. Keep this `docs/securax/` set current — the compounding "never re-research" asset.

## Operating cadence (ITIL Continual Improvement — keep it alive)
| Rhythm | Do | Output |
|---|---|---|
| **Daily (10 min)** | shutdown ritual: tasks done, Eisenhower quadrant check | daily note |
| **Weekly (Fri, 30–60 min)** | GTD review, OKR progress, stale items | weekly review |
| **Monthly (60–90 min)** | PARA area review, posture scan, risk register update | posture report |
| **Quarterly (half day)** | OKR reset, Kaizen (fix one friction point), skills review | quarterly plan |
| **Annually (full day)** | 5-year roadmap refresh, major upgrades, DR drill | vision update |

> The roadmap is a two-way-door at every arrow: reversible, cheap to pause, nothing bets the
> foundation. That is calculated risk by design (Principle P-6).
