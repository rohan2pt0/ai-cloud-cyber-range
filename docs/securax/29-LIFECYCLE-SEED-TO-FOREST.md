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
| `burrow` | 2a run- | Burrow | **Your own hardware** as a real Kubernetes cluster: k3s on 1–3 machines (embedded etcd, so 1 server grows to 3 with no rebuild), Argo CD pulling the same `gitops/`, an optional GPU node, a power-loss reflex (drain → etcd snapshot → stop). **Rehearsed on a Docker twin** (1 server + 2 agents, real k3s) before any machine exists | `./securax grow burrow` / `hibernate burrow`; real machines: `./securax spore server|agent --name …` |
| `tree` | 2 run | Tree | **One cloud VM** running k3s + Argo CD; state on a persistent encrypted disk; no inbound ports (SSM / tailscale) | `grow tree --apply` / `hibernate tree --apply` |
| `canopy` | 3 run+ | Canopy | **Managed Kubernetes** (EKS Auto Mode · GKE Autopilot · AKS) + Argo CD, Kyverno, Falco, cert-manager, KEDA, Velero, Prometheus | `grow canopy --apply` / `hibernate canopy --apply` |
| `forest` | 4 fly | Forest | Canopy + **multi-tenant**: each tenant = namespace + quota + zero-trust network policy + its own gateway + RBAC + metering + (AWS) its own KMS key and bucket | `./securax tenant add …`, `grow forest --apply` |

`./securax stages` shows each as ● awake · ◐ partly · ◌ hibernating (data kept) · ○ dormant (never grown).
Aliases: `crawl walk run- run run+ fly` (`run-` = burrow). Choose the cloud with `SECURAX_CLOUD=aws|gcp|azure` (default aws; the single-node `tree` is AWS-only).

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
./securax grow burrow                    # dig the Docker twin: 3 real k3s nodes (add --gitops for Argo CD)
./securax burrow power                   # rehearse a mains failure: drain, etcd snapshot, stop
./securax spore server --name burrow1 --gpu --ups   # installer for a REAL machine (script + cloud-init)
./securax spore agent --name burrow2 --join https://<server-ip>:6443
./securax grow canopy                    # PLAN only: shows what would be created
./securax grow canopy --apply            # creates it; installs Argo CD; the platform grows itself from gitops/
./securax tenant add acme --name "ACME Bank" --tier medium     # then commit + push; ./securax grow forest --apply
./securax hibernate canopy --apply       # Velero backup, then the cluster is removed; the vault keeps everything
```

## The burrow (stage 2a): own hardware, proven before it exists
* **One definition, two bodies.** `lifecycle/burrow.json` (k3s version and flags, GPU label, power policy) is read by both the Docker twin and the hardware installer, so the rehearsal cannot drift from the real thing (unit test: same flags in both).
* **Proven on the twin** (sandbox journey `lifecycle_burrow`, 27 checks): 3 nodes join and report Ready; a GPU-selecting workload is scheduled only onto the GPU-labelled node; a spread workload lands on all three; the power reflex drains and takes an etcd snapshot; hibernation stops every node but keeps the volumes; waking restores the **same** cluster (a ConfigMap written before sleep is still there) and uncordons it; `prune` needs the typed confirmation and removes the lot.
* **Spore:** `./securax spore` writes a bash installer and a cloud-init file (owner-only: they carry the join token). Ubuntu Server LTS + `sudo bash script`, or cloud-init on a USB labelled CIDATA. A 2nd/3rd server joins the first (HA) with `--join`.
* **GPU is an optional organ:** `--gpu` only labels the node `securax.io/gpu=nvidia`; nothing depends on it. The NVIDIA driver and container toolkit are your choice (they depend on the card) and are **not** installed or tested here. Buy a GPU from measured token demand, not guesswork.
* **Mumbai power cuts:** `--ups` installs NUT and a `SHUTDOWNCMD` snippet that calls the reflex. **Untested on real hardware or a real UPS** — the reflex script itself is proven on the twin.
* **Behind a TLS-inspecting proxy** (common in banks) containerd cannot pull images unless it trusts the proxy CA. The twin mounts the host's CA bundle (`SECURAX_BURROW_CA`, else `SSL_CERT_FILE`, else the system bundle); real nodes need the same CA installed in the OS trust store.
* **Limit of the twin:** it proves cluster mechanics and *scheduling*. A kernel that cannot nest containers (e.g. cgroup v1 micro-VMs) will show pods scheduled but not Running; Docker Desktop and GitHub runners can run them. It says nothing about real disks, NICs or GPUs.

## The range: a sleeping Active Directory lab for OSCP practice
OffSec's [OSCP+ exam](https://www.stationx.net/?p=2050639) is reported to have a mandatory Active Directory set (40 of 100 points, per one source: verify on OffSec's site), so an AD lab is the highest-value practice asset. **We do not rebuild one.** GOAD (Orange Cyberdefense) already is one, with providers for VirtualBox, VMware, Proxmox, AWS, Azure and Ludus, and native `start/stop/snapshot/reset/destroy` tasks. SecuRAX adds the lifecycle around it:
* **Pinned and verified:** `lifecycle/range.json` pins GOAD to a full commit; `range fetch` refuses anything else.
* **Honest sizing:** `./securax range soil` says which lab *fits this machine* using real numbers (sum of each lab's Vagrantfile; the sandbox re-derives them from upstream so they cannot drift): MINILAB 2 VMs/8 GB · GOAD-Light 3/12 GB · SCCM 4/16 GB · GOAD 5/20 GB, **plus ~6 GB for your OS and the seed**. On a 16 GB laptop that means MINILAB only; the full lab wants a ~32 GB box (your future burrow).
* **Same verbs:** `range plan|install|wake|hibernate|snapshot|reset|status|prune`. Hibernate stops the VMs and keeps their disks; `snapshot`/`reset` give you the known-good state back after you wreck a domain on purpose; `prune` needs a typed phrase.
* **Safety rails:** cloud providers are refused without `--i-accept-cloud-cost` (a deliberately vulnerable lab that bills); installing a lab that does not fit is refused; the isolation warning is printed before every install.
* **Not done / unverified:** the VMs were **never run here** (no hypervisor, and an install takes hours and many GB). GOAD uses 180-day Windows evaluation images (rebuild after). KubeVirt was considered and dropped: nothing I found shows GOAD supports it, and porting it would be the opposite of 80/20.

## Organs directly
`./securax organ wazuh up|stop|status|down` grows, sleeps, inspects or removes one upstream organ without touching the rest of the sprout. `./securax organ-check [name…]` fetches each pinned upstream ref, prepares it and runs `docker compose config` on it (no images are pulled): a cheap proof that the pins are still valid.

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
