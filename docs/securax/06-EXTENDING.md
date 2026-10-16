<!--
  SecuRAX — Extending the base (how future projects plug in).
  This answers the question: "the base stays the same — how do I add new projects to it later,
  quickly, without re-architecting?" The short answer: every new project connects to the SAME
  shared spine through the SAME open interfaces. You add a plug; you never rewire the house.
-->

# Extending SecuRAX — how to plug in any future project

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Plugin catalog + `./securax providers add`, tested. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The core idea:** SecuRAX is a *platform with a spine*, not a monolith. A new project is a
**plug** that connects to the shared spine (identity, data-tiers, AI gateway, secrets,
observability, policy, audit) through stable, open interfaces. You never modify the base to
add a project — you conform the project to the base's interfaces. That is what lets one
foundation serve you for years.

```
            NEW PROJECT (anything)                 SHARED SPINE (never changes shape)
        ┌───────────────────────────┐         ┌──────────────────────────────────────┐
        │  your code / tool / agent  │──OIDC──▶│  Identity (Keycloak)                   │
        │                            │──tier──▶│  Data classification (Red/Yellow/Green)│
        │  talk to AI via one URL ───┼──API───▶│  AI Gateway (guardrails)  :8080/v1     │
        │  secrets via one client ───┼────────▶│  Secrets (OpenBao)                     │
        │  emit logs/metrics ────────┼──OTel──▶│  Observability (Prometheus/Grafana/Loki)│
        │  ship security events ─────┼────────▶│  AI-SOC / SIEM                          │
        │  policies as code ─────────┼──Rego──▶│  OPA / Kyverno                          │
        └───────────────────────────┘         └──────────────────────────────────────┘
```

## The 7 connection points (the "plug contract")
A new project becomes a first-class SecuRAX citizen by using as many of these as apply. Each
is an **open standard**, so your project is never coupled to a specific product (Principle P-2).

| # | Spine service | Interface (the standard) | What your project does |
|---|---|---|---|
| 1 | **Identity** | OIDC / SAML | Delegate login to Keycloak; never build your own auth |
| 2 | **Data tiers** | Red / Yellow / Green label | Tag every data flow; route by the label |
| 3 | **AI** | OpenAI-compatible API at `http://gateway:8080/v1` | Call the gateway, never a model directly — you inherit all guardrails for free |
| 4 | **Secrets** | Vault/OpenBao API (or env injected from it) | Pull secrets at runtime; never hard-code |
| 5 | **Observability** | OpenTelemetry / Prometheus metrics + JSON logs | Emit traces, metrics, structured logs |
| 6 | **Security events** | JSON events the AI-SOC ingests (see `ai-soc/`) | Send findings/alerts to the SOC for correlation |
| 7 | **Policy & audit** | Rego (OPA/Conftest), Kyverno, Git history | Ship policies as code; all changes via PR = audit trail |

If a new project speaks these, it instantly gets security, privacy, cost control, monitoring,
and compliance **from the base** — you don't rebuild any of it.

## Repository convention (so it stays navigable — Principle P-5)
Add each project as a **top-level directory** that is self-contained and self-documenting:
```
<your-project>/
├── README.md          # what it is, which pillar, which spine services it uses
├── app/ or src/       # the code (thin glue; reuse OSS for the heavy lifting — P-3)
├── tests/             # at least a smoke test; wired into pytest from repo root
├── Dockerfile         # OCI image (portable laptop → K8s)
└── (optional) compose snippet / k8s manifest / terraform module
```
Then register it in three places so the "second brain" stays complete:
1. **`portal/securax.data.js`** → add it to the right pillar and/or the capability catalog.
2. **`docs/securax/03-CAPABILITY-CATALOG.md`** → add the capability row (tool, phase, standard).
3. **`docs/securax/04-COMPLIANCE-MAP.md`** → add which controls/frameworks it supports.

That is the whole ritual. The portal and docs update themselves from those edits.

## A 10-minute "new project" checklist
1. **Which pillar?** P1 (AI security) · P2 (SecOps) · P3 (brain/automation) · P4 (human) ·
   P5 (GRC). If it is cross-cutting, it lives on the spine.
2. **What data does it touch?** Assign the highest tier it handles (Red/Yellow/Green). That
   decides where its AI calls may go.
3. **Reuse before build (P-3).** Check `03-CAPABILITY-CATALOG.md` — is there already a tool?
   If yes, configure it. Only write code for the differentiated 20%.
4. **Wire the plug contract** (the 7 points above) that apply.
5. **Add the directory + a smoke test** (repo convention). `python3 -m pytest -q` must still pass.
6. **Register it** in the portal + catalog + compliance map.
7. **Ship via PR** → CI runs tests + SAST + secret scan + IaC scan automatically (audit trail).

## Three worked examples (patterns you will reuse)
- **A new autonomous agent ("your army").** It runs its tools through the AI gateway (point 3),
  gets a delegated identity (point 1), is capped by the gateway's action limits + guardrails,
  and streams its actions to the AI-SOC (point 6). → lives in a new top-level dir, Pillar 3.
  *You get safety and oversight from the base; you only write the agent's task logic.*
- **A new compliance module (e.g. SEBI CSCRF pack).** It is config + Rego policies + evidence
  queries, mapped in `04-COMPLIANCE-MAP.md`. No new infrastructure — it rides the existing
  policy-as-code and audit spine. → Pillar 5.
- **A new client/tenant (MSSP step).** Same images, new namespace + SSO realm + budget. The
  subscription model enables/disables modules per tenant. → platform scales (Phase 4), base
  unchanged.

## The rule that keeps this true forever
> **Add plugs, never rewire the house.** If a new project tempts you to change the spine's
> interfaces, stop — either the project should conform, or the interface genuinely needs to
> evolve (a deliberate, versioned, documented change, not a quick hack). The base is sacred;
> that discipline is exactly why it survives for years and why no auditor finds a seam.
