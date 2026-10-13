# 28 · Status & traceability — every ask, what shipped, how it is proven, what is NOT done

Honest ledger. ✅ = shipped **and** proven by an automated check · 🟡 = shipped, only partly proven (reason given) · ⬜ = not built (reason given) · 👤 = needs you.
"Proof" names the sandbox journey (`python3 sandbox/run.py -j <name>`) or unit-test file. The sandbox runs the real product in real containers with **fake cloud providers**, so provider *behaviour* (as opposed to wiring) is never proven by it.

## A. Asks from the conversation
| # | Ask | Status | Proof / note |
|---|---|---|---|
| 1 | Stop the repeated deployment failures | ✅ | `fresh_install`, `update_from_dirty_checkout`, `self_healing`, `blockers_are_explained` |
| 2 | One-step, free/local-first, security as an enabler | ✅ | `fresh_install`; Llama-Guard incident → `incident_stale_llama_guard` (harmless prompts answered, attacks still blocked) |
| 3 | Multi-device (phone/iPad) | 🟡 | Sync service + `BIND_HOST` + Tailscale guidance exist; **no second device in the sandbox** |
| 4 | Provider plugins (OpenAI, DeepSeek, Mistral, Grok, Perplexity, Groq, OpenRouter, Gemini) | ✅ | `key_wiring_and_failover` (right key → right provider, ladder, PII redaction) |
| 4b | Anthropic, Azure AI Foundry, AWS Bedrock | 🟡 | Config + docs; need real credentials (different request formats the fake does not speak) |
| 4c | ElevenLabs voice (`./securax say`), Colab/cloud-GPU heavy compute (`REMOTE_OLLAMA_BASE`) | 🟡 | Wired and documented; not exercised end-to-end |
| 5 | Provider **model names go stale** (found Oct 2026: Groq `llama-3.3-70b-versatile` retired 16 Aug, Gemini 2.5 / Grok 2 names reported retired) | ✅ | `model_self_correction`, `test_model_discovery.py`: `keys`, daily `up` and `./securax models --fix` replace a dead model with a live one; rejected keys are named |
| 6 | Make it work on an HP Spectre x360 (16 GB, no GPU), elastic resources | ✅/🟡 | `elastic_resources` (sizing for 3/9/24 GB). **Real CPU speed unmeasured here**; expect ~10–60 s for local answers |
| 7 | Version badge, "blocked by AI security policy", Arena model | ✅ | `ui_guiding_map_and_hub`, `open_webui_chat`, `incident_stale_llama_guard` |
| 8 | A sandbox that tests as the user, so you stop being the tester | ✅ | 21 journeys, 250+ checks; CI job `sandbox` is a required-green gate |
| 9 | Windows: step-by-step that cannot go wrong | 🟡 | `WINDOWS-QUICKSTART.md`, `wsl-setup.sh`, `securax.cmd` — **no Windows/WSL in the sandbox**; you are the first real test |
| 10 | Fallbacks for every component, DR | ✅ | `docs/securax/25`, `backup_restore`, `watchdog_heals_and_alerts`, `self_healing` |
| 11 | Reduce dependence on paid Claude for building SecuRAX | 🟡 | Framework is real and proven: `./securax verify [--full]`, `build` (Aider), **`autobuild`** (agent → gate → retry → commit-only-if-green → rollback + escalation brief; `autobuild_loop`). **Unproven: how good a small local/cheap model is at producing passing changes** — measure it on a few real tasks before relying on it |
| 12 | Gap assessment vs the 7 reference maps, integrate best features by 80/20 | ✅ | `docs/securax/26`; built from it: backup/restore, watch, `.env` perms, runbook (27), **`evidence`** pack, **`scan`** |
| 13 | Docs / explainer / artefacts updated | ✅ | `portal/`, `docs/securax/00,22–28`, `CHANGELOG.md`, `DEPLOY.md`, `WINDOWS-QUICKSTART.md` |

## B. Roadmap phases (docs/securax/05) — all five stages now exist as code; see doc 29
Everything above the seed is **dormant by default** and wakes with `./securax grow <stage>`; `./securax hibernate <stage>` puts it back to sleep keeping its data.
| Phase | Scope | Status |
|---|---|---|
| 0 CRAWL / seed | Laptop foundation | ✅ shipped, 17 sandbox journeys |
| 1 WALK / sprout | Keycloak, OpenBao, SeaweedFS (S3), Prometheus + Alertmanager | ✅ **proven with real containers** (`lifecycle_sprout`): grow → write data → hibernate with verified backup → wake → data intact → prune |
| 1 organs | Wazuh (SIEM/XDR), MISP, TheHive | 🟡 pinned upstream refs fetch, prepare and `compose config`-validate in CI/sandbox (`lifecycle_organs`); mechanics proven with a stand-in organ. **Their real images were not run here** (6–8 GB each). Suricata and Shuffle are **not included** |
| 2a BURROW / own hardware | k3s on 1–3 machines you own (embedded etcd → HA later), optional GPU node, power-cut reflex, Argo CD; **Docker twin** rehearses it | 🟡 **twin proven with real k3s** (`lifecycle_burrow`, 27 checks: join, GPU-pinned scheduling, power reflex + etcd snapshot, hibernate/wake keeps the cluster's memory, prune). Spore installers are syntax- and structure-tested only: **never run on real hardware**; NUT/UPS and NVIDIA driver steps untested; twin proves scheduling, not real disks/NICs/GPUs |
| 2 RUN / tree | One cloud VM running k3s + Argo CD, persistent encrypted data disk | 🟡 Terraform validated; offline plans proved (dormant = no VM; awake = VM + disk); security invariants checked. **Never applied** (no cloud account here) |
| 3 RUN+ / canopy | EKS Auto Mode / GKE Autopilot / AKS, Argo CD, Kyverno, Falco, cert-manager, KEDA, Velero, Prometheus; hibernate removes cluster+NAT, keeps the vault | 🟡 AWS: plan-proved + invariants; GCP: plan-proved; Azure: validated only. GitOps charts render and pass Kubernetes schema validation. **Never applied.** Chaos/DR drills and Prowler are **not included** |
| 4 FLY / forest | Multi-tenant cells: namespace, quota, zero-trust network policy, gateway, RBAC, per-tenant metering + SLA rules + dashboard; AWS per-tenant key + bucket | 🟡 chart renders for every tier and validates; tenant→Terraform mirroring tested; metering metrics unit-tested. Per-tenant **SSO realm, billing/invoicing and the MSSP business layer are not built** |
| IaC safety | Dormancy and security invariants | ✅ `prove.py` (mutation-checked), CI job `lifecycle-genome`; a latent bug in the old `lab` Terraform (it could not `init`) was found and fixed |

## C. Things only you can do 👤
1. **Rotate every key pasted into chat** (xAI, `sk-or-v1-…` OpenRouter, the UUID-like one). Runbook: doc 27, section A.
2. `git tag v0.1.0 && git push origin v0.1.0` (this environment gets 403 on tags).
3. Run the Windows steps and send the output if any step fails.
4. Copy `./securax backup` files off the laptop (3-2-1).

## D. Known limits (not bugs)
- Local 1.5B model ≠ frontier quality; free cloud keys are the speed *and* quality path.
- Free-tier quotas and model lineups change monthly; `./securax models` self-corrects names, not quotas.
- The sandbox cannot prove: real provider behaviour, Windows/WSL/Docker Desktop quirks, real CPU speed, phones.
