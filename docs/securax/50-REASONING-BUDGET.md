# 50 · Reasoning budget: think less where it does not pay

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Per-provider reasoning effort is wired; adaptive budgets are not built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Prompt:** the paper *Hybrid Reasoning Agents* (Zou et al., Stanford / Together AI, arXiv 2610.18861, 13 Oct 2026). It reports 35-55% fewer tokens, 1.8-2.6× faster answers and 2.7-3.7× lower cost from reasoning in latent space and switching to text only to call a tool or answer.

## Verdict on adopting HybridAgent itself: not now

| Requirement | What the release needs | SecuRAX today |
|---|---|---|
| Runtime | Its own PyTorch generation engine (CUDA 12.8). No vLLM, SGLang, Ollama/GGUF or OpenAI-compatible server is mentioned. | Everything goes through LiteLLM and the gateway (OpenAI-compatible); local models run on Ollama on CPU |
| Hardware | One GPU per inference process; SFT 8-16 GPUs; RL 32 GPUs | Laptop-first, ₹0 to start |
| Models | HybridAgent-8B / 14B (Qwen3 base) plus a HybridLink adapter, MIT licence | Model choice is one catalog line |

Wiring it in now means a GPU and a custom server: over-engineering for this estate.

**How it would come in later:** if a host serves it behind an OpenAI-compatible API, it is **one entry in `plugins/catalog.json`** on the build ladder. `./securax autobench` measures it before it is trusted. Nothing else changes.

## What we took instead: the paper's lesson, at zero cost

Most visible reasoning on routine steps is waste. So:

1. **Measure it.** The gateway's `/metrics` now has `guardrail_tokens_total{kind="reasoning"}`, the thinking tokens inside each completion, next to the existing prompt and completion counts. Look before you optimise.
2. **Cap it where that is safe.** Set `<ID>_REASONING=<level>` in `.env` and run `./securax up` (or `./securax providers`). The router sends `reasoning_effort` for that provider only when:
   - its **current** model matches the catalog's `reasoning.model` pattern, and
   - the level is one the catalog lists for it.

   Otherwise the request is exactly as before. The cap is **off by default**.

| Provider | Model pattern | Levels allowed |
|---|---|---|
| `gemini` | `gemini/gemini-3*` | minimal, low, medium, high |
| `groq` | `groq/openai/gpt-oss*` | low, medium, high |
| `anthropic` | `anthropic/claude-*-5*` | low, medium, high |

The cap is refused elsewhere because LiteLLM 1.105 maps `reasoning_effort="low"` to **more** thinking or to an error:
- Ollama: `think: true`, and qwen2.5 cannot think.
- DeepSeek: thinking ON.
- Mistral: `high`.
- OpenAI gpt-4o-mini and Perplexity: unsupported.

This was checked against LiteLLM's own parameter mapping. It is why a single global "think less" switch was rejected: it would have raised cost or broken the always-on local rung.

Notes:
- With a cap set, LiteLLM sends temperature 1.0 to Gemini 3, as Google recommends for its thinking models.
- The cap follows the model, not the provider. If model discovery moves Groq to a non-reasoning Llama, the cap switches itself off.

## Where it helps, honestly

- **Chat (`bank-assistant`):** runs on free tiers only, so the gain is faster answers and more headroom on free-tier daily caps, not rupees.
- **Build ladder:** flat-rate or cheap. Leave reasoning at default there unless `autobench` shows no quality loss: hard build steps are where thinking pays.

**Suggested first step:** `GROQ_REASONING=low`. Compare the reasoning series on `/metrics` and the answers for a week, then keep or drop it.

## Proof

- `local/compose/tests/test_gen_litellm_config.py`:
  - the cap is off by default;
  - it applies only to the provider that asked;
  - it is refused on Ollama, DeepSeek, Mistral and coder;
  - it follows the model;
  - the shipped baseline never carries it.
- `apps/llm-gateway/tests/test_guardrails.py`: reasoning tokens are metered separately.
- Checked on the wire with the real LiteLLM 1.105 Router against a local capture server. `GROQ_REASONING=low` sends `reasoning_effort: low`; unset sends nothing.
