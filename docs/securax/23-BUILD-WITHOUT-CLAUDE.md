# 23 · Build SecuRAX without depending on Claude

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** verify, autobuild, forge, route, lessons and the Claude-share lamp are real and tested; Claude did 98% of commits when this shipped, so building mostly without it is not yet proven. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

> **Newer:** the step-by-step move off a Claude subscription, with the strong open-model chain, `./securax review` and October 2026 prices, is [doc 83](83-BUILD-WITH-OPEN-MODELS.md). Where this page and doc 83 differ, doc 83 is current.

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

> **Default is `BUILD_MODEL=builder`** — a resilient *ladder* (OpenCode Go's DeepSeek V4.1 Flash and GLM Flash → free Groq/NVIDIA →
> DeepSeek → Gemini/OpenRouter → local coder → local; the order is in `plugins/catalog.json`). Hard work uses `BUILD_MODEL=strong` (doc 83). A dead key, a rate limit or an outage slides to the next rung instead of stopping
> your build. On a CPU-only 16 GB laptop treat the local coder as the offline fallback, not the plan.
> See [24 · Resilience & low-resource](24-RESILIENCE-AND-LOW-RESOURCE.md).

Model IDs change constantly; set `BUILD_MODEL` and the per-provider `<ID>_MODEL` overrides rather than
trusting any name here. Verify current pricing on each provider's page (it moves monthly).

| Use | Model (set `BUILD_MODEL=`) | Cost | Why |
|---|---|---|---|
| **Default build** | `builder` (the ladder above) | flat $10 a month on OpenCode Go, then free tiers | Never stops: each rung falls to the next. |
| **Hard work** | `strong` (DeepSeek V4 Pro, Kimi K3, GLM 5.3) | inside the same Go plan, with smaller allowances | For what the router sends to the strong tier (doc 83). |
| **Sovereign / offline** | `coder` (local Qwen2.5-Coder) | **Free** | Runs on your box. Needs enough RAM (below). |
| **Free cloud** | `gemini` (free tier) / `openrouter` free models | **Free** | Zero cost; good for docs, tests, small changes. |
| **Alternates** | `mistral`, GLM/MiniMax/Kimi via OpenRouter | cheap | Diversify so no one provider is a SPOF. |

Enable any with `./securax providers add`. All of them route through the gateway, so the rails apply.

### Local coder by hardware (sovereign, free)
Run `./securax profile` (it sets `ENABLE_LOCAL_CODER=1` when there is room), then `./securax pull coder`. The model is picked on
every start from the catalog's `coder.sizing` tiers by **the memory Docker can see**, then stepped down if it would not fit beside the
rest of the estate (need = file size × 1.25, leaving 3.5 GB). Pin your own with `CODER_MODEL=...` and `CODER_MODEL_PIN=1`.

| Memory Docker sees | Model | Download | Why |
|---|---|---|---|
| 30 GB+ (and it fits) | `qwen3-coder:30b` | 19 GB | 256K context, best quality per GB (MoE, 3.3B active) |
| 15 GB+ (and it fits) | `gpt-oss:20b` | 13 GB | 128K context, quantization-aware MXFP4, Apache-2.0 |
| otherwise | `qwen2.5-coder:7b` | 4.7 GB | small and fast on constrained hardware |

**A 16 GB laptop gets `qwen2.5-coder:7b`.** `gpt-oss:20b` needs about 16 GB while running, and inside WSL/Docker the estate's other
services need room too. Profile says which model it would have picked and why it stepped down. On a CPU-only laptop expect single-digit
to low-tens tokens/s; measure with `./securax bench --models gpt-oss:20b` (it flags anything under 4 tokens/s as too slow to chat with).

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
safe), never touches your branch, and pushes only with `AUTOBUILD_PUSH=1`. The gate is `./securax verify` unless you set `AUTOBUILD_VERIFY="<command>"` (exit 0 = green). Proven by the sandbox journey `autobuild_loop`
(with a stub agent) — **the quality of a real local/cheap model inside this loop is now measurable**: run `./securax autobench run --models builder,coder`
(doc 45) and read the report before depending on it.

> **Stronger gate:** since doc 44, `autobuild` also runs `./securax forge gate` (fail-to-pass, mutation, complexity budget) and feeds back a typed brief; infrastructure reds are re-run, not "fixed".

## Tier 3 — escalate the hard 10% (and only the 10%)

When the cheap/local tier can't satisfy the contract (new security design, a cross-cutting refactor, a
bug unfixed after 3 honest tries):

```bash
./securax escalate "the hard problem"     # writes escalation-brief.md (task + diff + rules)
```

Paste that tight brief into Claude/Sonnet. Because it's scoped and carries the diff + the contract,
one focused frontier call replaces many — that's how your weekly limit stops being a SPOF. Or run
`./securax enhance "…"` to have your **local** engineer persona draft it first, free.

## The card, automated: route, lessons, share

Three small tools make the card below run by itself, so you do not have to remember it.

- **`./securax route "task"`** names the tier and why, from the words of the task, any paths it names, and (after the work) the files the diff actually touched. The rules are data in `lifecycle/route.json`:
  - **Claude:** security, crypto, identity, sync and merge logic, regulator mapping, a listed sensitive path, or more than 3 areas.
  - **OpenCode:** 2 or 3 areas, or a wiring job.
  - **Local:** the rest.
  - **autobuild asks first.** A task routed to Claude gets its escalation brief at once, instead of three wasted cheap attempts (`--force` overrides). A green autobuild whose diff touches a sensitive path says so, and asks for a Claude review before merge.
- **`AGENTS.md` and `LESSONS.md`:** how this repo works, and what went wrong before. Every builder reads both:
  - Aider loads them on every run.
  - OpenCode and Codex read `AGENTS.md`.
  - Claude Code reads `CLAUDE.md`, which imports both.
  - **When a red attempt turns green,** autobuild adds the lesson. You can add one with `./securax lessons add "…"`.
  - This is the claude-mem idea (memory across sessions) without a model call, and OpenJarvis's "learn from your own traces" in its simplest form.
  - Lines are cleaned to one plain line, because every agent reads them as context.
- **`./securax ai share`:** how much of the month's work Claude did, by commit: Claude co-authored, `autobuild:`, or you. The cockpit lights a caution lamp above 20%, once a month has at least 10 commits.
  - **The baseline when this shipped:** Claude 98% (October 2026).
  - **When to change your plan:** only after two months under the goal. Commits are a proxy for effort, not tokens.

## Which tier gets the task (the 80/20 card)

Decide by the task, not by habit. Default to the cheap tier and escalate only on evidence.

| Send it to | When the task is | Examples |
|---|---|---|
| **Local or cheap model:** `./securax autobuild "…"` | One area, a clear done-test, and a pattern that already exists in the repo | A new pack or regmap row, a doc, a CLI subcommand like an existing one, a fixture, a test for existing code, a UI copy fix, a dependency bump |
| **OpenCode, interactive:** `./securax opencode` | Several files, but the design is already decided | Wiring a feature through CLI, docs and tests; a refactor inside one module |
| **Claude, with a brief:** `./securax escalate "…"`, then paste `escalation-brief.md` | Security design, crypto, auth, sync or merge logic, a change across the estate, a red that three autobuild tries could not fix, or reading regulations into controls | New gateway rail, the OneDrive sync merge, a regulator map from a new circular |

**Three habits keep Claude to about a fifth of the work:**

1. **Escalate with a brief, not a chat.**
   - `escalate` packs the task, the diff and the rules.
   - One scoped call replaces many exploratory ones.
2. **Let the cheap tier do the follow-through.**
   - When Claude has designed something, hand the docs, changelog, tests for edge cases and small fixes to `autobuild`.
   - The gate (`verify` + `forge gate`) catches what a weaker model gets wrong.
3. **Measure, don't guess.**
   - `./securax autobench` scores each model on this repo's own tasks.
   - Promote a model to default only when its pass rate holds up (doc 45).

> **Prices checked on 19 Oct 2026; confirm before you buy, as they change often.**
> - **OpenCode Go:** US$5 for the first month, then US$10 a month. It has usage caps per 5 hours, per week and per month, and it offers open models (DeepSeek, Qwen, Kimi, GLM and others), not Claude ([docs](https://opencode.ai/docs/go/)).
> - **Claude Pro in India:** about ₹2,399 a month billed monthly, or about ₹2,000 a month billed yearly, GST included, according to press reports from July 2026 ([Business Today](https://www.businesstoday.in/technology/news/story/anthropic-introduces-india-pricing-for-claude-ai-plans-pricing-starts-at-542742-2026-07-14)). Check Anthropic's own pricing page before you rely on these figures.

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
