# 25 · Fallbacks & elasticity — what happens when a piece is missing

Rule: **no single missing component stops you from using SecuRAX**; it degrades, tells you, and `./securax up` repairs it.
Rows marked ✅ are exercised end-to-end by the sandbox (`python3 sandbox/run.py`); 📄 = covered by unit tests only; ⚠ = documented, not automatable.

| Layer | If it's missing / broken | What SecuRAX does instead | Proof |
|---|---|---|---|
| Cloud model (Gemini/Groq/OpenRouter/…) down, rate-limited, key dead | Router walks the ladder: next free cloud → private local model | ✅ `key_wiring_and_failover` |
| All cloud down / no internet | Private local model (CPU) answers; nothing leaves the machine | ✅ `local_model_answers` |
| Local model not downloaded yet | Cloud ladder answers; model pulls in the background | ✅ |
| Local model + cloud all down | Clean 502 (no hang); recovers when any layer returns | ✅ `self_healing` |
| Router (LiteLLM) or gateway container dies | `./securax up` restores it and waits for READY | ✅ `self_healing` |
| Ollama dies | Cloud ladder still answers | ✅ `self_healing` |
| Llama Guard enabled but never installed | Auto-switched OFF (announced); built-in rails keep enforcing | ✅ `incident_stale_llama_guard` |
| `python3` missing / config generator fails | Shipped baseline config used; user told why | ✅ `blockers_are_explained` |
| Docker "created a directory" at the config mount | Detected, removed, file regenerated | ✅ `blockers_are_explained` |
| Port 8080/8088/3000 already taken | Named before start-up, with the command to find the owner | ✅ `blockers_are_explained` |
| Image build fails / offline | Retry without rebuild → retry core-only services | 📄 start-up chain in `securax up` |
| Dirty checkout blocks `git pull` | `./securax update` restores the generated file first | ✅ `update_from_dirty_checkout` |
| Low disk (<8 GB free) | Warning before pulling images/models | 📄 |
| Docker not running / WSL integration off | Plain-English fix steps (Windows launcher + `wsl-setup.sh`) | ⚠ (needs real Windows) |
| Windows-drive slowness | Installer puts the repo on WSL's own disk; launcher prefers it | ⚠ |
| Open WebUI / Command Center / Guiding Map down | Gateway API + `./securax say/ask` CLI still work; dots on the hub show state | ✅ `ui_guiding_map_and_hub` |

| Stage above the seed is asleep / never grown | Nothing runs and nothing is billed; waking restores data (laptop: volumes + secrets in the backup; cloud: vault, data disk, tenant keys) | ✅ `lifecycle_sprout`, `prove.py` |
| Cloud apply interrupted / bad plan | Cloud commands plan only without `--apply`; hibernate/wake is one boolean on the same code; seed bank is never destroyed by sleep | ✅ `lifecycle_cloud_is_safe` |

## Elastic resources
On **every** `./securax up`, `autosize` reads what **Docker** can actually use (inside WSL2 that VM cap is the real limit, not your laptop's RAM) and sets:

| Docker sees | Local chat model | Ollama RAM cap | Lite mode |
|---|---|---|---|
| < 7 GB | qwen2.5:0.5b | 45 % of it (min 1.8 GB) | on |
| 7 – 12 GB | qwen2.5:1.5b | 45 % | on |
| 12 – 20 GB | qwen2.5:1.5b | 45 % | off |
| ≥ 20 GB | qwen2.5:7b | 45 % (max 12 GB) | off |

CPU threads = cores − 1 (min 2). Raise the WSL memory (`%UserProfile%\.wslconfig`) and restart → it uses the extra automatically; no config edit.
Overrides: `LOCAL_MODEL_PIN=1` (keep your model), `SECURAX_LITE_PIN=1`, `SECURAX_AUTOSIZE=0` (hands control back). Preview without starting: `./securax size`.

## The honest limits
- A CPU-only 1.5B model answers in ~10–60 s and is not a frontier model. **Free cloud keys are the speed path** (`./securax keys`); local is the guaranteed floor.
- Free-tier quotas and model lineups change often; if a provider 404s, `./securax doctor` shows the real error and `./securax providers add` re-points it.
