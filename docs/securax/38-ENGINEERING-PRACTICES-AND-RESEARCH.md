# 38 · Engineering practices, research cues, and the friction audit

Written to answer three questions without over-engineering: *what do well-run open-source products do that we do not, what do research bodies suggest, and where have we deviated from what you asked for?* The rule used throughout: **add only what removes real risk or friction for an actual stakeholder; every addition must not widen the attack surface; say plainly what is deliberately skipped and what would make us add it.**

## A · The Mattermost-style checklist
| Practice | State | Decision and why |
|---|---|---|
| Containerisation, Kubernetes | have | compose on a laptop; k3s/EKS/GKE/AKS stages as dormant code |
| Horizontal scaling, auto-scaling | have (dormant) | HPA/KEDA in the platform apps; a single laptop has nothing to scale |
| TLS | partial | loopback HTTP on one machine is acceptable; cloud stages use ingress + cert-manager. **Add** a reverse proxy only when you expose it beyond the LAN (trigger) |
| mTLS | skip | one host, one trust zone. Trigger: services on different hosts |
| OAuth 2.0 / OIDC / SSO | **added** | gateway sign-in from any OIDC provider (doc 36) |
| RBAC | **added** | gateway roles + MFA for admin/auditor; tenant cells already have Kubernetes RBAC |
| WAF | skip | the guardrail gateway *is* an application-level WAF for AI traffic. Trigger: public exposure → put Caddy/Coraza or a cloud WAF in front |
| Health checks | have | `/healthz`, `/readyz`, compose healthchecks, `watch` self-heal |
| Circuit breaker, retry | have | the router cools a failing provider down and falls back along the ladder; retries are bounded |
| Rate limiting | have | per principal, audited |
| Idempotency | skip | chat calls change nothing; a retry costs money, not correctness. Writes need a human `--approve`; incident filings are keyed by case. Trigger: agents performing autonomous writes |
| Replication, sharding, read replicas | skip | one small Postgres. The real first step for recovery is **WAL archiving** for a ≤15-minute RPO (on the backlog), not replicas. Trigger: sustained load or an RPO the backups cannot meet |
| Connection pooling | skip | no connection errors to cure. Trigger: "too many connections" in the logs → PgBouncer |
| Centralised logging | partial | audit JSON on stdout, ready for a shipper (Wazuh/Loki in the optional stages) |
| Metrics | have | `/metrics` (role-protected when sign-in is on), Prometheus in the sprout stage |
| Distributed tracing / OpenTelemetry | **added (light)** | W3C `traceparent` propagated and logged; no SDK. Trigger for full OTel: three or more services involved in a latency question |
| CI/CD | have | 17 required checks including the real-product sandbox |
| Blue-green, canary, rolling | **added (light)** | compose: `update` is a blue-green-lite (backup → new → health gate → rollback); Kubernetes rolls by default. Canary: trigger = more than one production tenant |

## B · Research cues taken
| Source | What it gives | What we did |
|---|---|---|
| **MIT AI Risk Repository** (7 domains, 24 subdomains; 1,600+ risks from 65 frameworks) | a neutral checklist of AI risk | `comply mit-ai-risk` (domain level) and a cockpit panel; honest gaps: bias/fairness, factuality, misuse content, robustness |
| **NIST AI 600-1** (Generative AI Profile, 12 risks) | deployer-side risk categories | `comply nist-ai-600-1`; gaps: IP, bias; partial: CBRN, confabulation, harmful content (depend on an optional detector) |
| NIST AI RMF, MITRE ATLAS/ATT&CK, OWASP LLM/Agentic | already mapped | unchanged |
| **OpenSSF Scorecard** and **SLSA** (build provenance, v1.2) | measurable project hygiene; signed build provenance | **recommended, not added**: they need CI permissions we cannot test from here. Suggested next: attest release images with GitHub Artifact Attestations, run the Scorecard action (note: scores are a process signal, not proof of fewer vulnerabilities) |
| **CISA Secure by Design** | secure defaults | tension noted: a laptop stays open (too much up-front security defeated the tool before). Resolved with **one switch** — `./securax regulated on` — for any regulated deployment |
| FIRST **EPSS** | exploit likelihood to prioritise patches | not added (a daily 7 MB feed for modest gain over CISA KEV which we already use offline); trigger: a patch backlog too long to triage by KEV alone |
Not found in this research pass: guidance specific to operating LLM gateways from CMU SEI or Stanford HELM (evaluation, not operations); treat the gateway design as ours, tested by the purple loop.

## C · The friction and deviation audit (all earlier prompts, 1 → today)
Method: re-read every request; for each ask who is affected (non-technical owner, Windows user, regulated operator, auditor, contributor, future self, tenant) and look for a place where the product no longer matches the ask or makes someone do extra work.
| # | Finding | Who it hurt | Fix |
|---|---|---|---|
| F1 | `./securax help` listed ~30 of ~65 commands (you asked for "the full list" earlier) | everyone | grouped, plain-English `help`; unknown commands point to it |
| F2 | `update` had no backup, no health check, no way back (your earlier update failures) | the non-technical owner | safe update with rollback, proven by a real-container journey |
| F3 | Turning sign-in on would have broken the browser clients (Guiding Map Ask, Command Center model list) | the browser/phone user | gateway-key field on the Ask page, clear 401 messages, hub handles 401 |
| F4 | No answer to "where do files go and how big will it get" | the owner | `storage` + forecast + doc 37; backups may go to another disk |
| F5 | No single view; six commands to judge health | the owner, an auditor | the cockpit, linked from the Command Center |
| F6 | New settings absent from `.env.example` | the operator | documented, one switch `regulated on` |
| F7 | Detectors were sent unredacted text (found while building residency) | the regulated operator | detectors now see redacted text only (fixed in the identity/residency PR) |
| F8 | Docs index and explainer lacked everything since doc 28 | new readers | index + explainer section "Run it, prove it, report it" |
| F9 | A change could break something far from where it was made | contributors | `impact` map + fitness rule |
| F10 | Dependabot did not cover the compose-pinned images or Terraform | the operator | added docker-compose and terraform (Dockerfile base images were already covered) |
| F11 | A browser opened by `--open` may not work from WSL | the Windows user | the cockpit prints the URL; the Command Center card opens it |
| — | Still open, yours: pushing the `v0.1.0` tag (this environment cannot; the pinned tenant image does not exist until you do) | you | `git tag v0.1.0 && git push origin v0.1.0` |
Earlier asks checked and found delivered: one-step Windows start, plugins for providers, free/local models and resource constraints, sync across devices (estate-sync), the sandbox that tests as a user, versioning, the lifecycle IaC, MCP, Claude-subscription-style routines, fallbacks for components, offline operation.
Deliberately not done: anything that adds a listening service or script to the new pages; full OpenTelemetry; replicas; a WAF in front of a laptop.
