<!--
  SecuRAX — Open-core model & subscription tiers.
  How to keep the base open-source (adoption + goodwill + a real community) AND get paid for
  the hard, high-value parts (scale, managed, assurance). This is the proven "open core" model
  used by GitLab, Mattermost, Elastic, GitPod and others — not reinvented.
-->

# SecuRAX — Open-Core Model & Tiers

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** A business model on paper; no tiers, billing or licensing are built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

> **Prices for the business product are now set in [doc 106](106-WHO-SECURAX-IS-FOR.md)** (a hypothesis to test with design partners). The tables below are kept as history.

The balance you asked for: **keep the core genuinely free and open so it spreads and earns
trust, and charge for the parts that take real work to run at scale.** This is the
**open-core** model — the same one GitLab, Mattermost, Elastic and HashiCorp use. The free
tier must be *actually useful on its own* (not crippleware), or the flywheel never starts.

## The principle
> Free users are not lost revenue — they are distribution, feedback, and credibility. You
> monetise **scale, convenience, and assurance**, never the ability to get started.

## The tiers
| Tier | Price (indicative, India) | Who it's for | What's included |
|---|---|---|---|
| **Community** 🟢 *(free to use; FSL-1.1-MIT, each release MIT after two years)* | **₹0, forever** | individuals, students, researchers, you | the whole single-node estate: guardrail gateway, AI-SOC, red-team, AI-SPM, Guiding Map PWA, MCP, local models, 3 cloud IaC modules, all docs |
| **Team** | ~₹1,500–3,000 / user / mo | small teams, consultants | multi-user SSO (Keycloak), shared dashboards, hosted Guiding Map sync, more n8n automations, email support |
| **Business** | ~₹8,000–15,000 / user / mo | SMB / regulated startups | the full SOC (Wazuh+MISP+TheHive), compliance report packs (RBI/DPDP/ISO), SLA alerting, audit-evidence export, priority support |
| **Enterprise / MSSP** | custom | banks, MSSPs | multi-tenant isolation, on-prem/air-gapped, custom compliance mappings, 24×7, dedicated engineering, white-label |
| **Managed (SaaS)** | usage-based | anyone who wants zero-ops | we run it; you just use it. Highest margin, lowest friction for the buyer |

## What stays free vs what's paid (the honest line)
**Always free (Community):** everything that helps one person or a small group *start and
succeed* — the engines, the PWA, the single-node deploy, the docs, the MCP control plane.
**Paid:** the things that cost *us* real effort and that *enterprises* happily pay for —
multi-tenancy, SSO at scale, managed hosting, compliance certifications, SLAs, and support.

This is the GitLab test: *"Would an individual feel cheated by what's behind the paywall?"*
If yes, it belongs in Community. Paywall scale and assurance, never the basics.

## The viral / adoption flywheel (how it spreads)
1. **Free core + a great first-run** (`./securax up` → Guiding Map in one step) = people try it.
2. **The visual tour + the PWA** are shareable; the repo is public (FSL-1.1-MIT; MIT up to v0.3.0).
3. **Content** (the LinkedIn posts, the explainer) drives awareness; GitHub stars = social proof.
4. **A "deploy to your cloud" button** and templates lower the barrier to the paid tiers.
5. **Community → Team → Business** as their needs grow. Land free, expand paid.

## Monetisation mechanics (proven, low-overhead)
- **Licensing:** from v0.4.0 the code is under **FSL-1.1-MIT** (free to use, no competing resale, each release MIT after two years; LICENSING.md); v0.3.0 and earlier stay MIT
  directory (the GitLab/Elastic pattern) so the open core is never compromised.
- **Billing:** Stripe / Razorpay (India) for subscriptions; usage metering for Managed.
- **Support/SLA** and **compliance report packs** are the easiest first paid products (high
  value, low engineering cost) — start there.
- **Sponsorship:** GitHub Sponsors / Open Collective for the Community tier's goodwill income.

## Guardrails for doing this right
- Never degrade the free tier to push upgrades — grow the paid value instead.
- Keep contributions welcome (CONTRIBUTING.md); a real community is the moat.
- Be transparent about what's open vs paid (this page).
- India-first pricing, globally competitive; discounts for students, non-profits, govt.

> Start by giving the best free tier in the category. Revenue follows adoption; adoption
> follows a product people love and can actually run. Free core, paid scale — that is the
> balance.
