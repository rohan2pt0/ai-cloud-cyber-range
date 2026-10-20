# SecuRAX — Cost, models & never hitting a limit (the FinOps playbook)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Free-first ladders, the local floor and the monthly budget cap are generated and tested. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

> **For coding work**, the current plan (the open-model chains and October 2026 prices) is [doc 83](83-BUILD-WITH-OPEN-MODELS.md).

The goal: **you are never blocked by a usage limit, now or for the life of SecuRAX**, and the
best intelligence (Claude and other frontier models) is spent only where it earns its keep.
Everything here follows one rule: **local is the floor, free tiers fuel the build, paid frontier
is reserved for the hard 20%.** You swap any provider without touching a line of app code.

## 1. One endpoint, many brains (already built)
Every part of the estate calls a single logical model, **`bank-assistant`**, through the
**LiteLLM router** (`local/compose/litellm-config.generated.yaml`). LiteLLM is the OpenAI-compatible
switchboard: it decides which real model answers, load-balances, falls back, and enforces a
**hard monthly spend cap** (`max_budget`, ~₹2,100/mo) so cloud spend can never run away.

```
your apps / agents  ─►  LiteLLM  ─►  local Ollama (free)          ← default
                                 ├─►  Gemini / DeepSeek / Mistral  ← cheap/free cloud burst
                                 ├─►  OpenRouter :free models       ← many frontier models, free tier
                                 └─►  Claude / GPT / Bedrock        ← the hard 20% only
```

Add Sarvam (Indic), Perplexity (web-grounded), ElevenLabs (TTS), or any other the same way —
drop a block in the config with its key. **The app keeps calling `bank-assistant`.** That is
your lifetime no-lock-in guarantee: providers are config, not code.

## 2. Spending fewer Claude Code credits while building SecuRAX
Claude Code is the sharpest tool for **architecture, hard debugging, security reasoning, and
getting a foundation right** — that is the 20% worth its credits. Offload the routine 80%:

| Task | Run it on | Why |
|---|---|---|
| Boilerplate, renames, test scaffolding, docs first-draft | **local Qwen/DeepSeek via Ollama**, or **Gemini/DeepSeek free tier** | cheap/free, good enough |
| In-IDE autocomplete & small edits | **Continue.dev / Cline / Aider** pointed at LiteLLM or local Ollama | no Claude credits at all |
| "Which library / how do I X" lookups | **Perplexity / Gemini free**, or the estate's own `assist` | grounded, free |
| Bulk refactors across many files | **Aider** on a cheap model, Claude only to review | 1 Claude pass, not 50 |
| Architecture, threat modeling, tricky bugs, final review | **Claude Code** | this is where it wins |

Habits that cut credit burn hard:
- **Plan first, then execute in batches.** One well-scoped change beats ten speculative ones.
- **Let the estate draft, Claude polish.** Your own `assist` tool + agents (below) produce a
  first version on free/local models; Claude refines only the hard parts.
- **Reserve Claude for the diff, not the typing.** Generate with a cheap model, have Claude
  review the result — a review pass is a fraction of the tokens of co-writing.
- **Keep the context tight.** Point Claude at the specific files, not the whole repo.

## 3. Any IDE, cheaply
SecuRAX is plain files + a local OpenAI-compatible endpoint, so it works in any editor:
- **VS Code / Cursor / JetBrains** with **Continue.dev** or **Cline** → set the provider base URL
  to the SecuRAX gateway (`http://localhost:8080/v1`, so every call is guarded and audited) or local Ollama (`http://localhost:11434`). Free,
  local, private in-IDE AI.
- **Aider** (terminal) for multi-file edits on a cheap model.
- **Codex / Claude Code** kept for the hard 20%.
None of this defeats sovereignty: the default path is local; cloud is opt-in and capped.

## 4. Heavy compute (GPUs/TPUs) without buying any
When a task needs real horsepower — training/fine-tuning a small model, building embeddings for
your RAG, batch processing — the estate stays the **control plane** and the heavy job runs on
free compute:
- **Google Colab** (free T4 GPU) / **Kaggle** (free GPU/TPU hours) for notebooks, embeddings,
  fine-tunes. Pull data from / push results to the estate (MinIO/Postgres over Tailscale).
- **Keep secrets out of notebooks** — mount them from the estate, never paste keys into Colab.

## 5. The end state: your own RAG, less external dependency
As SecuRAX matures, the cheap/free providers fuel the base while you build the sovereign core:
- **Qdrant** (vector DB) + **local embeddings** + **Ollama** = a private RAG that answers from
  *your* documents, on *your* hardware, at zero marginal cost.
- The agents (below) and the Guiding Map `Ask` increasingly run on this local RAG; frontier
  cloud models become the exception, called only when the local answer isn't good enough.

> 80/20 restated: 80% of value comes from local + free tiers wired through one router; the last
> 20% of quality, on the hard problems, is worth a metered call to a frontier model — and even
> that is capped, logged, and swappable. You are never *blocked*; at worst you fall back to
> local and keep moving.
