# 24 · Resilience & low-resource operation

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Sizing for 3 / 9 / 24 GB is proven (`elastic_resources`). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Design goal:** SecuRAX keeps answering when a key is wrong, a free tier is exhausted, a provider is
down, the internet is gone, or the laptop is short on RAM — degrading gracefully instead of failing.

## The honest hardware truth (i7, 16 GB, no GPU)

A local model on a CPU-only laptop is a **last resort, not an engine.** It is private and always
available, but slow, and the bigger the model the slower it gets. So:

- **Chat / daily use** → free cloud tiers first (fast), local only when they're all unavailable.
- **Building SecuRAX itself** (an edit → test → fix loop) → cheap/free cloud first. A local coder is the
  offline fallback, not the plan. Slow generation makes an agent loop stall.
- **Sensitive (RED-tier) data** → pick `bank-assistant-local` *explicitly*. Never rely on a ladder for that.

## The degradation ladder

```
 Chat (bank-assistant):  Gemini ─► Groq ─► OpenRouter(free) ─► LOCAL
 Build (builder):        DeepSeek ─► Gemini ─► Groq ─► OpenRouter ─► local coder ─► LOCAL
                         └── each rung only counts if its key is set; a missing key just skips it ──┘
```

- Every chain **ends in `local`**, which is always on — so with *zero* keys and *zero* internet there is
  still an answer.
- A cloud rung that hangs fails over in **40 s**; a failing deployment is cooled down for 30 s so
  requests skip straight to the next rung. The local rung is allowed **300 s** (CPU is slow but sure).
- **Paid providers (OpenAI, Claude, Grok…) are never in the default chat chain** — a cost guard. Pick
  them from the dropdown deliberately if you want them.
- See your live ladder any time: `./securax providers list` · test it end-to-end: `./securax doctor`.

### Why several free tiers instead of one
Free tiers are volatile — limits change, models are withdrawn, quotas run out mid-day. Examples from
current trackers (verify before relying; they move): OpenRouter's `:free` models are capped at roughly
50 requests/day ([comparison](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)); Groq's free
plan has a daily *token* cap that often runs out before the request cap
([limits](https://gravity.fast/data/free-llm-api-tiers/)); Gemini's free-tier limits are only visible in
AI Studio. A ladder across several of them turns "one provider ran dry" into "the next rung answered."

> **Sovereignty caution (BFSI):** free tiers can use prompts to improve the provider's products (Google
> says so for Gemini's free tier). The gateway redacts PII/secrets before anything leaves, but for
> client/regulated material use **`bank-assistant-local`** or a paid tier with data-protection terms.

## Right-size SecuRAX to your machine: `./securax profile`

```bash
./securax profile          # detects RAM/CPU, writes sane limits to local/compose/.env
./securax down && ./securax up && ./securax pull
```

| RAM Docker can use | Tier | Local chat model | Local coder | Mode |
|---|---|---|---|---|
| < 7 GB | tiny | `qwen2.5:1.5b` | off | lite |
| 7 – 11.5 GB | small | `qwen2.5:3b` | off | lite |
| 11.5 – 20 GB | medium | `qwen2.5:3b` | `qwen2.5-coder:7b` | lite |
| ≥ 20 GB | large | `qwen2.5:7b` | `qwen2.5-coder:14b` | full |

**Lite mode** (`./securax up --lite`, or `SECURAX_LITE=1`) runs only the core path — gateway, router,
local model, Chat, home screen, sync — and skips Private Docs and n8n, which together want ~3 GB.

### Windows + WSL2: the RAM you see is the cap
Inside WSL2 Docker lives under a limit that defaults to **half your laptop's RAM** (≈ 8 GB on a 16 GB
machine). `./securax profile` shows what it sees. To raise it, create `%UserProfile%\.wslconfig`:

```ini
[wsl2]
memory=11GB
swap=8GB
processors=8
```
then run `wsl --shutdown` in PowerShell, reopen Ubuntu and re-run `./securax profile`. (12 GB unlocks
the local-coder tier but leaves Windows only 4 GB — close heavy apps first.)

Ollama is also tuned for CPU: the model stays warm for 30 min (reloading is the slowest part), one
request and one model at a time (so a 16 GB box never starts swapping).

## Guarantees — and the tests that enforce them
These are checked in CI (`local/compose/tests/test_gen_litellm_config.py`), so they can't silently rot:

| Guarantee | Why it matters |
|---|---|
| Every chain ends in `local` | Zero keys + no internet still yields an answer |
| One deployment per alias | Two under one name get randomly load-balanced — a slow local model would answer half your traffic while a fast cloud model is healthy |
| Every fallback alias exists | A dangling fallback errors at the worst possible moment |
| **Every `os.environ/X` the config uses is passed into the LiteLLM container** | A key that never reaches the container makes that provider fail with an auth error — it once looked exactly like "no credits" |
| Paid providers never in the default chat chain | No surprise bills |
| Baseline config is deterministic | The committed config can't be changed by whatever env generated it |

## When something fails

| Symptom | Do this |
|---|---|
| Chat "Oops" / any error | `./securax doctor` — prints *who answered* or the *real* upstream error |
| A provider you added fails | Check the key first (`./securax providers list`), then its model id (`<ID>_MODEL` in `.env`) |
| Everything cloud is down | Nothing to do — the ladder lands on local. Pull it once: `./securax pull` |
| Machine crawls / swaps | `./securax profile` → `./securax down && ./securax up --lite` |
| Free tier ran dry | Add another rung: `./securax providers add` (Groq, OpenRouter, Gemini) |
