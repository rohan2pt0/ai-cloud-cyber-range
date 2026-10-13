# 23 · Build SecuRAX without depending on Claude

**Goal:** evolve SecuRAX using its *own* models, at near-zero cost, with the rigor of a frontier
subscription — so a paid-Claude limit is never a single point of failure for the project.

## The core idea: rigor lives in the harness, not only the model

A 1.5B local model can't match a frontier model on hard, multi-file work. But most build work isn't
hard — it's tests, config, docs, single-file features, lint fixes. For those, a **cheaper model that
follows the [BUILD-CONTRACT](../../BUILD-CONTRACT.md), backed by SecuRAX's test + CI gates**
(pytest, ruff, gitleaks, Semgrep, build-drift), is reliable: the model *proposes*, the gates
*verify*, the loop repeats until green. That verification is what you were paying the subscription
for. You already own it.

So the strategy is three tiers + one discipline:

```
          cheap/local tier (80–90% of work)        frontier tier (the hard 10%)
   ┌──────────────────────────────────────┐     ┌──────────────────────────────┐
   │  ./securax build "task"   (Aider)     │ ──▶ │  ./securax escalate "task"    │
   │  DeepSeek / local Qwen-Coder          │     │  paste brief into Claude/Sonnet│
   │  + BUILD-CONTRACT + auto-run tests    │     │  (security design, gnarly bug) │
   └──────────────────────────────────────┘     └──────────────────────────────┘
                     every change passes ruff + pytest before it's "done"
```

## Tier 1 — the build models (pick by cost/sovereignty)

> **Default is `BUILD_MODEL=builder`** — a resilient *ladder* (cheap DeepSeek → free Gemini/Groq/OpenRouter →
> local coder → local). A dead key, a rate limit or an outage slides to the next rung instead of stopping
> your build. On a CPU-only 16 GB laptop treat the local coder as the offline fallback, not the plan.
> See [24 · Resilience & low-resource](24-RESILIENCE-AND-LOW-RESOURCE.md).

Model IDs change constantly; set `BUILD_MODEL` and the per-provider `<ID>_MODEL` overrides rather than
trusting any name here. Verify current pricing on each provider's page (it moves monthly).

| Use | Model (set `BUILD_MODEL=`) | Cost | Why |
|---|---|---|---|
| **Default build** | `deepseek` | ~1/6–1/7 of frontier per token | Strong coder, extremely cheap API. The workhorse. |
| **Sovereign / offline** | `coder` (local Qwen2.5-Coder) | **Free** | Runs on your box. Needs enough RAM (below). |
| **Free cloud** | `gemini` (free tier) / `openrouter` free models | **Free** | Zero cost; good for docs, tests, small changes. |
| **Alternates** | `mistral`, GLM/MiniMax/Kimi via OpenRouter | cheap | Diversify so no one provider is a SPOF. |

Enable any with `./securax providers add`. All of them route through the gateway, so the rails apply.

### Local coder by hardware (sovereign, free)
Enable with `ENABLE_LOCAL_CODER=1` in `.env`, then pull the model your machine can run:

| Your machine | Pull this | Set |
|---|---|---|
| 16 GB RAM, no GPU | `./securax pull qwen2.5-coder:7b` | (default) |
| 32 GB RAM / 12–16 GB VRAM | `./securax pull qwen2.5-coder:14b` | `CODER_MODEL=ollama/qwen2.5-coder:14b` |
| 24 GB+ VRAM / 32 GB+ Mac | `./securax pull qwen3-coder:30b` | `CODER_MODEL=ollama/qwen3-coder:30b` |

> Coding agents need context. Raise Ollama's context window (default can be ~4k): set
> `OLLAMA_CONTEXT_LENGTH=65536` for the ollama container, or a model `Modelfile` with `num_ctx`.
> Sources (verify current): [Ollama coding models 2026](https://www.morphllm.com/best-ollama-models),
> [best value coding](https://benchlm.ai/best/best-value-coding).

## Tier 2 — the agent: `./securax build`

```bash
# one-time: install the local coding agent (sovereign, runs on your box)
python3 -m pip install --user aider-chat        # or: pipx install aider-chat

# then build/evolve SecuRAX with its own models:
./securax build "add a /metrics endpoint to the gateway with a passing test"
BUILD_MODEL=coder ./securax build "refactor fin_freedom arg parsing"   # fully local/offline
```

`./securax build` points [Aider](https://aider.chat) at the SecuRAX **gateway** (OpenAI-compatible),
loads the BUILD-CONTRACT as always-on context, and runs **`./securax verify`** (lint + unit tests +
router-config + compose checks) **after every edit**, iterating until green (`--auto-test`). That edit→test→fix loop is the rigor — the same loop a
frontier agent runs, now driven by a cheap/local model behind your guardrail.

**Definition of done = `./securax verify` green** (seconds), and for anything touching compose, `securax`,
the gateway, the router or the UI, **`./securax verify --full`** (adds the user-perspective sandbox: a fresh
install, real browser, real local model — about 10 min, no tokens). A model that can't make `verify`
pass hasn't finished, however confident it sounds; this is what replaces trusting the model's own claims.

Prefer a GUI? Point **Cline** or **Continue** (VS Code) at `http://localhost:8080/v1` with your
`LITELLM_MASTER_KEY` and model `openai/deepseek` (or `openai/coder`). Same endpoint, same rails.

## Tier 2b — unattended: `./securax autobuild`

```bash
./securax autobuild "add a /metrics endpoint to the gateway with a test" --tries 3
```
Creates its own branch, runs the agent, runs **`./securax verify`**, and — if red — feeds the failure output back for
the next attempt. **Commits only when green** (you then review `git diff main..autobuild/…` and push). After N red
attempts it discards the work, returns your checkout to a clean state and writes `autobuild-failed-*.md` — an
escalation brief for the rare frontier-model hand-off. It refuses to start on a dirty tree (so rollback is always
safe), never touches your branch, and pushes only with `AUTOBUILD_PUSH=1`. Proven by the sandbox journey `autobuild_loop`
(with a stub agent) — **the quality of a real local/cheap model inside this loop is not yet measured**: try it on ~10 small
real tasks and record pass-rate before depending on it.

## Tier 3 — escalate the hard 10% (and only the 10%)

When the cheap/local tier can't satisfy the contract (new security design, a cross-cutting refactor, a
bug unfixed after 3 honest tries):

```bash
./securax escalate "the hard problem"     # writes escalation-brief.md (task + diff + rules)
```

Paste that tight brief into Claude/Sonnet. Because it's scoped and carries the diff + the contract,
one focused frontier call replaces many — that's how your weekly limit stops being a SPOF. Or run
`./securax enhance "…"` to have your **local** engineer persona draft it first, free.

## Why this preserves the rigor you care about
- **Tests are mandatory** (BUILD-CONTRACT step 4; `--auto-test`): no change lands red.
- **Security is non-negotiable** (hard rules): a model can't weaken a rail or commit a secret and pass
  — gitleaks/Semgrep/compose-config gates reject it.
- **Minimal diffs + self-review** keep a weaker model from sprawling.
- **The same CI** that guards your Claude-built PRs guards your DeepSeek/Qwen-built ones. Identical floor.

## The honest limits
- A local 7B won't one-shot a subtle concurrency bug or a novel architecture. That's what `escalate`
  is for — keep it rare.
- Bigger local coders need RAM/VRAM; without it, use `deepseek` (cheap cloud) as the default and keep
  `coder` for offline/sensitive work.
- Always keep **two** working build models configured (e.g. `deepseek` + `coder`) so a provider outage
  never blocks you. Diversity is the SPOF cure.
