# Cost Controls — staying under ₹2,500/month

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The original cyber-range lab; superseded by doc 15. [What the lights mean](index.md#the-status-lights)
<!-- status:end -->

Design goal: **the range costs ₹0 by default** (laptop + always-free tiers) and can never
silently exceed ₹2,500/month. Cost is treated as a security control (economic DoS, LLM10).

## Default posture = free
| Component | Where | Cost |
|---|---|---|
| Models | Ollama on the laptop (qwen2.5:1.5b, llama-guard3:1b) | ₹0 |
| Gateway + router + DB + SIEM | docker compose on the laptop | ₹0 |
| Kubernetes | kind (local) | ₹0 |
| CI/CD, SAST, SBOM, container+IaC scan | GitHub Actions (free for public repos) | ₹0 |
| Notebooks | Google Colab free tier | ₹0 |
| Versioning | GitHub | ₹0 |

## Cloud burst — free tiers / credits (verify before relying; figures as of Oct 2026)
| Cloud | Free lever | Notes |
|---|---|---|
| **AWS** | New Free Plan: up to **$200 credit**, 6 months | EC2/RDS draw down credit (no more 750 free hrs); CloudTrail 1 trail, ECR scan, OIDC all cheap/free |
| **GCP** | **$300/90-day** trial + Always-Free e2-micro + Cloud Run free tier | Model Armor + Vertex/Gemini free tier; Cloud Run scales to zero |
| **Azure** | **$200/30-day** credit; AI Content Safety **F0** free SKU; Foundational CSPM free | Defender CSPM paid plan gated off |

Sources: [AWS Free Tier 2026](https://aws.amazon.com/free), [GCP pricing](https://cloud.google.com/kubernetes-engine/pricing), [Azure Defender for Cloud](https://learn.microsoft.com/en-us/azure/defender-for-cloud/tutorial-enable-cspm-plan).

## Hard guardrails (kill-switches)
1. **LiteLLM `max_budget: 25 USD/30d`** — blocks cloud model calls before the INR cap (router-level FinOps PEP).
2. **Per-cloud budgets** (`enable_paid=false` by default):
   - AWS `aws_budgets_budget` alerts at 50/80/100%.
   - GCP `google_billing_budget` → Pub/Sub topic → (optional) Cloud Function that **detaches billing** at 100% — the real "stop the bleeding" control.
   - Azure `consumption_budget_subscription` with action-group email at 50/90/100%.
3. **`enable_paid` flag** gates every billable resource (GuardDuty, Security Hub, Defender CSPM, Cloud Run, Content Safety S0). Default off ⇒ free SKUs only.
4. **OPA policy** (`policies/opa/terraform.rego`) **fails CI if a plan has no budget** — you cannot deploy a cloud slice without a ceiling.
5. **`teardown.sh`** destroys the local plane; `terraform destroy` removes cloud resources after each drill.

## Suggested monthly operating pattern (≈₹0–₹2,000)
- 90% of practice: laptop only (₹0).
- Cloud drills: spin up ONE cloud slice for a weekend, run the demo, `terraform destroy`. On free credits this is ₹0; worst case a few hundred INR of overage well under the cap.
- GCP Cloud Function billing-disable + Pub/Sub budget = your insurance that a forgotten resource cannot run up the bill.
