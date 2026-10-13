# SecuRAX sandbox — test the product as a user gets it

Unit tests prove functions work. They never saw the bugs that actually reached users: provider keys that
never reached the router, a fail-closed detector that blocked every prompt, a startup race that listed
half the models. **The sandbox runs the real product and checks what a user would see.**

```bash
python3 sandbox/run.py                      # every journey (≈10–20 min the first time, then faster)
python3 sandbox/run.py -j fresh_install     # one journey
python3 sandbox/run.py --list
python3 sandbox/run.py --keep               # leave the stack running to poke at it
```

Needs Docker + compose, Python 3.11+, `pip install pyyaml playwright && playwright install chromium`, `openssl`.
Results: `sandbox/out/results.json`, screenshots in `sandbox/out/shots/` (open them — that is the product).

## What is real, what is faked

| Real (the product as shipped) | Faked (and why) |
|---|---|
| A fresh copy of your working tree (incl. uncommitted changes) with **no `.env`** | Cloud providers (Gemini, Groq, OpenRouter, OpenAI, DeepSeek…): answered by `fakes/fake_providers.py` at the **network level** so no keys/spend are needed, yet the **unmodified** LiteLLM config, real provider prefixes and real env wiring are exercised. Each answer says `answered-by:<provider>`; every request (incl. the credential and body) is recorded |
| The real **`./securax`** CLI (`up`, `down`, `doctor`, `guard`, `providers add`, …) — run on a real pseudo-terminal when interactive | |
| The real **`docker-compose.yml`** and real images: nginx, LiteLLM, **Ollama with a real model** (`qwen2.5:0.5b`), **Open WebUI**, and the gateway / estate-sync built from your Dockerfiles | |
| A real **Chromium** driving the Guiding Map, Command Center and Open WebUI | |

The only additions are `docker-compose.override.yml` (auto-loaded by compose) and, behind a TLS-inspecting
proxy only, a base image that trusts that CA. The product's own files are never patched.

## Journeys

| Journey | The user experience it protects |
|---|---|
| `fresh_install` | New user, no `.env`, no keys: `./securax up` works, pages and redirects serve, models are listed |
| `local_model_answers` | Worst case (no keys, no cloud): the sovereign local model really answers |
| `incident_stale_llama_guard` | The real incident: stale `.env` with Llama Guard on → harmless prompts blocked → `doctor` explains → `up` heals → answers, and real attacks are still blocked |
| `key_wiring_and_failover` | Each key reaches **its** provider; Gemini→Groq→OpenRouter→local fail-over; PAN redacted before it leaves; attacks never reach a provider |
| `chat_streaming` | `stream:true` (what Open WebUI sends) works through the gateway |
| `providers_wizard` | Silent key entry, mis-pasted key caught, typed command rejected, new model appears in Chat |
| `ui_guiding_map_and_hub` | Version badge, Command Center, status dots, Ask box — in a browser, no JS errors |
| `open_webui_chat` | The chat UI itself: model picker, no "Arena Model", default model, send a message |

## What it cannot tell you (be honest)

* **Windows / WSL2 / Docker Desktop specifics** (bind-mount quirks, WSL memory caps, port clashes with your other
  software). Run `./securax doctor` on your machine for those.
* **Real provider behaviour** (a real OpenAI account with no credit, a model renamed by the vendor). Fakes cover
  *our* wiring, not their service.
* **CPU speed on your laptop** — the sandbox uses a 0.5B model to stay fast.
* The model **cache** persists between runs (Docker volume), so it is not a cold download every time.

## The rule

Anything that touches runtime behaviour (compose, `securax`, gateway, router config, UI served by nginx, the
Guiding Map) is **not done** until `python3 sandbox/run.py` is green — and a bug found by a human gets a
**journey that reproduces it first**, then the fix. CI runs the same thing (`.github/workflows/e2e.yml`).
