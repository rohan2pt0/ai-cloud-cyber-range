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
| 8 | A sandbox that tests as the user, so you stop being the tester | ✅ | 17 journeys, 140+ checks; CI job `sandbox` is a required-green gate |
| 9 | Windows: step-by-step that cannot go wrong | 🟡 | `WINDOWS-QUICKSTART.md`, `wsl-setup.sh`, `securax.cmd` — **no Windows/WSL in the sandbox**; you are the first real test |
| 10 | Fallbacks for every component, DR | ✅ | `docs/securax/25`, `backup_restore`, `watchdog_heals_and_alerts`, `self_healing` |
| 11 | Reduce dependence on paid Claude for building SecuRAX | 🟡 | Framework is real and proven: `./securax verify [--full]`, `build` (Aider), **`autobuild`** (agent → gate → retry → commit-only-if-green → rollback + escalation brief; `autobuild_loop`). **Unproven: how good a small local/cheap model is at producing passing changes** — measure it on a few real tasks before relying on it |
| 12 | Gap assessment vs the 7 reference maps, integrate best features by 80/20 | ✅ | `docs/securax/26`; built from it: backup/restore, watch, `.env` perms, runbook (27), **`evidence`** pack, **`scan`** |
| 13 | Docs / explainer / artefacts updated | ✅ | `portal/`, `docs/securax/00,22–28`, `CHANGELOG.md`, `DEPLOY.md`, `WINDOWS-QUICKSTART.md` |

## B. Roadmap phases (docs/securax/05)
| Phase | Scope | Status |
|---|---|---|
| 0 CRAWL | Laptop foundation: gateway, router, local+cloud models, chat, Guiding Map, sync, automation, red-team, AI-SOC, AI-SPM, governance | ✅ shipped (this document's A-table) |
| 1 WALK | Always-on core: Keycloak, Wazuh, Suricata, MISP, TheHive, Prometheus/Grafana/Loki, OpenBao | 🟡 Observability profile ships; the heavy SOC stack is **documented upstream recipes** (doc 10), not integrated, and wants ≥16–32 GB RAM and an always-on host. Not built into the laptop estate on purpose |
| 2 RUN | Cloud + orchestration: k3s, Argo CD, Prowler, Shuffle, immutable audit | ⬜ Terraform/OPA/Kyverno/Falco skeletons exist; **not deployed or tested** (no cloud accounts here); each is gated by a "trigger" in the roadmap (client SLA, HA need) |
| 3 RUN+ / 4 FLY | Multi-cloud hardened k8s; multi-tenant MSSP, billing | ⬜ Not built. These are business-triggered (paying clients), not engineering-complete-able on one laptop |

## C. Things only you can do 👤
1. **Rotate every key pasted into chat** (xAI, `sk-or-v1-…` OpenRouter, the UUID-like one). Runbook: doc 27, section A.
2. `git tag v0.1.0 && git push origin v0.1.0` (this environment gets 403 on tags).
3. Run the Windows steps and send the output if any step fails.
4. Copy `./securax backup` files off the laptop (3-2-1).

## D. Known limits (not bugs)
- Local 1.5B model ≠ frontier quality; free cloud keys are the speed *and* quality path.
- Free-tier quotas and model lineups change monthly; `./securax models` self-corrects names, not quotas.
- The sandbox cannot prove: real provider behaviour, Windows/WSL/Docker Desktop quirks, real CPU speed, phones.
