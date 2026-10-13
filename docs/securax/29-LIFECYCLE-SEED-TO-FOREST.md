# 29 · Lifecycle — from a dormant seed to a multi-tenant forest (and back to sleep)

**The idea, borrowed from nature:** a seed carries the whole plant. It sits dormant at almost no cost, germinates when
conditions are right, grows only as far as the environment supports, goes back to dormancy through winter *keeping what it
learned*, and — when a part is no longer needed — sheds it deliberately. SecuRAX is built the same way: the **genome**
(this repository) already contains every stage, fully defined; nothing above the seed runs, and nothing is billed, until you
ask.

| Nature does… | SecuRAX does… | Where |
|---|---|---|
| **Genome** — every cell carries the full plan | One repo defines all five stages (compose, Terraform, GitOps) | `lifecycle/`, `infra/terraform/lifecycle/`, `gitops/` |
| **Seed bank** — what survives dormancy and regrows everything | Vault bucket (object-locked backups), encryption key, persistent data disk, budget alarm: the *only* things that exist while asleep | `modules/seedbank-*` |
| **Germination** — grow when conditions allow | `./securax grow <stage>` after a **soil test** (RAM, disk, tools, credentials) | `lifecycle.py soil/grow` |
| **Hibernation** — sleep, keep your memory | `./securax hibernate <stage>`: backup, then stop (laptop) or destroy compute but keep data (cloud). Wake = same code, one boolean flipped | `awake` switch |
| **Homeostasis** — self-regulation | `./securax up/watch` self-heal; HPA/KEDA; EKS Auto Mode / GKE Autopilot / AKS autoscaler add and remove nodes by themselves | doc 25, `gitops/platform` |
| **Differentiation** — identical cells specialise by which genes switch on | One tenant chart; a 5-line file under `gitops/tenants/` switches a whole tenant cell on | `gitops/charts/tenant` |
| **Apoptosis** — controlled cell death | `./securax prune <stage>`: the only destructive verb, typed confirmation, cloud data has deletion guards | `lifecycle.py prune` |
| **Circadian rhythm** | `./securax rhythm on --sleep 23:30 --wake 06:30` for the always-on core | `lifecycle.py rhythm` |
| **Metabolism** — energy budget | `monthly_budget_usd` with 50/80/100 % alerts (actual + forecast), refusal to wake without `--apply` | Terraform seed bank |
| **Immune system** | Kyverno admission policy, Falco runtime rules, zero-trust NetworkPolicies, guardrail gateway | `gitops/platform`, chart |
| **Mycelium** — a hidden network joining everything | Optional tailscale mesh: no inbound port is ever opened on any node | `tailscale_auth_key` |

## The ladder

| Stage | Gait | Nature | What it is | Wake / sleep |
|---|---|---|---|---|
| `seed` | 0 crawl | Seed | Today's laptop estate | `./securax up` / `down` |
| `sprout` | 1 walk | Sprout | Always-on core on **one machine**: Keycloak (SSO/MFA), OpenBao (secrets), SeaweedFS (S3), Prometheus + Alertmanager; optional organs **Wazuh · MISP · TheHive** fetched from their official upstream repos at pinned commits | `./securax grow sprout [--with wazuh,misp,thehive]` / `hibernate sprout` |
| `tree` | 2 run | Tree | **One cloud VM** running k3s + Argo CD; state on a persistent encrypted disk; no inbound ports (SSM / tailscale) | `grow tree --apply` / `hibernate tree --apply` |
| `canopy` | 3 run+ | Canopy | **Managed Kubernetes** (EKS Auto Mode · GKE Autopilot · AKS) + Argo CD, Kyverno, Falco, cert-manager, KEDA, Velero, Prometheus | `grow canopy --apply` / `hibernate canopy --apply` |
| `forest` | 4 fly | Forest | Canopy + **multi-tenant**: each tenant = namespace + quota + zero-trust network policy + its own gateway + RBAC + metering + (AWS) its own KMS key and bucket | `./securax tenant add …`, `grow forest --apply` |

`./securax stages` shows each as ● awake · ◐ partly · ◌ hibernating (data kept) · ○ dormant (never grown).
Aliases: `crawl walk run run+ fly`. Choose the cloud with `SECURAX_CLOUD=aws|gcp|azure` (default aws; the single-node `tree` is AWS-only).

## What "dormant" guarantees — and how that is *proved*
* **Sprout:** every service is in the `sprout` compose profile; `./securax up` never starts one (unit test, with the stage file loaded too).
* **Cloud:** `awake=false` plans **only the seed bank**. `infra/terraform/lifecycle/prove.py` runs offline `terraform plan`s (no cloud account) for 9 scenarios (AWS and GCP) plus 5 refusal cases, and
  asserts, per scenario, which resource types exist: dormant → no `aws_instance`, `aws_eks_cluster`, `aws_nat_gateway`, GKE or AKS cluster; awake → exactly the stage's
  compute and nothing from a bigger stage; forest tenants persist through sleep. It also checks security invariants over the plan (no inbound rules, IMDSv2,
  encrypted disks, KMS rotation, every bucket public-access-blocked, EKS on STANDARD support). It is mutation-checked: breaking the switch makes it fail.
* **Hibernation keeps data (real containers):** sandbox journey `lifecycle_sprout` writes a secret to OpenBao and a realm to Keycloak, hibernates (with a verified backup),
  confirms nothing runs, wakes, and finds both intact — OpenBao re-unsealed automatically and no secret rotated.

## Elasticity — vertical and horizontal, inside limits
| | Vertical (bigger machine) | Horizontal (more machines) |
|---|---|---|
| seed / sprout | sized from what Docker can use on every start (doc 25); raise WSL/Docker memory | n/a (one host) → graduate to `tree`/`canopy` |
| tree | `./securax scale tree medium|large` (instance + disk tier) | one node by design → graduate to `canopy` |
| canopy / forest | EKS Auto Mode / Autopilot pick node shapes per pod; `scale` sets Azure pool shapes | **automatic**: nodes follow pods, down to zero; tenant HPA within its quota |

## Safety rails (so growth is never a surprise)
* Cloud commands **plan only** unless you pass `--apply`, then ask for confirmation (`--yes` to skip).
* Set `monthly_budget_usd` first; alerts at 50/80/100 % (actual) and 100 % (forecast).
* A managed control plane bills hourly even with zero nodes — which is *why* `hibernate canopy` removes the cluster and NAT and keeps only the vault. EKS is pinned to STANDARD support
  (older Kubernetes versions are billed at a much higher "extended support" rate).
* Vault: versioned, KMS-encrypted, **object-locked** (WORM) so backups survive even an administrator's mistake. Tenant buckets/keys and the data disk have deletion guards.
* Nothing is exposed: sprout binds to 127.0.0.1; cloud nodes have no inbound rules; organs' admin ports are remapped to localhost.

## Using it
```bash
./securax stages                         # what is awake / hibernating / dormant
./securax soil sprout --with wazuh       # is the soil ready? (names the exact fix for anything missing)
./securax grow sprout                    # Keycloak, OpenBao, S3, Prometheus, Alertmanager (secrets generated, owner-only)
./securax grow sprout --with wazuh,misp  # + the SIEM and threat-intel organs (≥14 GB Docker memory for both)
./securax hibernate sprout               # backup, then sleep; wake with grow again — data intact
./securax rhythm on                      # sleep 23:30 / wake 06:30 every day (opt-in, your crontab)
./securax grow canopy                    # PLAN only: shows what would be created
./securax grow canopy --apply            # creates it; installs Argo CD; the platform grows itself from gitops/
./securax tenant add acme --name "ACME Bank" --tier medium     # then commit + push; ./securax grow forest --apply
./securax hibernate canopy --apply       # Velero backup, then the cluster is removed; the vault keeps everything
```

## Honest limits (read before relying on it)
* **No cloud account was available when this was built.** Terraform is validated and its *plans* are proved offline; an actual `apply` of EKS Auto Mode / GKE Autopilot / AKS / the k3s node, the
  Argo CD bootstrap and Velero restores have **not** been executed. Expect small first-run fixes; the dormancy and plan logic will not be the surprise.
* Azure: validated, but its provider needs a real login even to plan, so no offline plan-proof. Per-tenant cloud isolation is implemented for AWS only.
* Velero here backs up cluster **objects** to the vault. Persistent-volume *data* on EKS Auto Mode uses a CSI driver the AWS Velero plugin may not snapshot — verify with a test restore before relying on it.
* Wazuh/TheHive ship **default credentials** upstream; they are bound to localhost here, but change them before exposing anything. MISP's admin password is generated.
* The Helm charts are pinned to major ranges, not exact versions (freeze them after the first healthy sync). The tenant gateway image (`ghcr.io/rohan2pt0/securax-llm-gateway`) must be published (see `publish-images` workflow) before tenants can start.
* The OpenBao unseal key sits in `~/.securax/sprout` (owner-only, in your backup) — lab-grade; use cloud-KMS auto-unseal for anything real.
* Costs are order-of-magnitude and come from third-party summaries (≈ 0.10 USD per cluster-hour for an EKS/GKE control plane; EKS Auto Mode adds a per-instance fee; AKS free tier has no SLA). **Check each provider's calculator for your region.**
* Wazuh needs `vm.max_map_count ≥ 262144` and ~6 GB; `soil` checks and tells you the command.
