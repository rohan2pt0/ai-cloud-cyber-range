# 22 · Plugins & AI Providers

SecuRAX treats every AI provider as a **plugin** — like Mattermost plugins, you toggle one on by
adding its key, and it just shows up. No code, no hand-editing YAML.

## How it works (the architecture)

```
Chat / Guiding Map / n8n
        │  (OpenAI-compatible)
        ▼
   Security Gateway  ──►  LiteLLM router  ──►  OpenAI · Anthropic · DeepSeek · Mistral ·
   (guardrail PEP)        (FinOps PEP)         Grok · Perplexity · Azure · Bedrock · local …
```

- **`plugins/catalog.json`** is the single source of truth: one entry per provider (its label, the
  env var(s) it needs, its default model, where to get a key).
- **`local/compose/gen_litellm_config.py`** reads the catalog + your `.env` and writes
  `litellm-config.generated.yaml` with **only the providers you've enabled** (a key is present).
- The **gateway `/v1/models`** mirrors LiteLLM's live models, so an enabled provider appears in the
  Chat model dropdown automatically — still passing through the guardrail.

## Add a provider (the easy way)

```bash
./securax providers list      # see what's on/off
./securax providers add       # pick a provider, paste its key — done
```

`add` prompts for the provider id, shows you where to get a key, writes it to `.env`, regenerates
the router config, and restarts the router. Open **http://localhost:3000** and pick the new model.

> You can also just put the key in `local/compose/.env` and run `./securax up`.

## The provider catalogue

| id | Provider | Env var(s) | Default model (override with `<ID>_MODEL`) | Get a key |
|---|---|---|---|---|
| `gemini` | Google Gemini *(default)* | `GEMINI_API_KEY` | `gemini/gemini-2.5-flash` | aistudio.google.com/apikey |
| `local` | Ollama (sovereign) | — *(always on)* | `ollama/qwen2.5:1.5b` | — |
| `openai` | OpenAI (GPT) | `OPENAI_API_KEY` | `openai/gpt-4o-mini` | platform.openai.com/api-keys |
| `anthropic` | Anthropic (Claude) | `ANTHROPIC_API_KEY` | `anthropic/claude-3-5-haiku-20241022` | console.anthropic.com |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` | platform.deepseek.com |
| `mistral` | Mistral | `MISTRAL_API_KEY` | `mistral/mistral-small-latest` | console.mistral.ai |
| `grok` | xAI (Grok) | `XAI_API_KEY` | `xai/grok-2-latest` | console.x.ai |
| `perplexity` | Perplexity (Sonar) | `PERPLEXITYAI_API_KEY` | `perplexity/sonar` | perplexity.ai/settings/api |
| `azure` | Azure AI Foundry / OpenAI | `AZURE_API_KEY` + `AZURE_API_BASE` | `azure/<deployment>` | ai.azure.com |
| `bedrock` | AWS Bedrock | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` | `bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0` | console.aws.amazon.com |
| `openrouter` | OpenRouter (incl. free) | `OPENROUTER_API_KEY` | `openrouter/meta-llama/llama-3.3-70b-instruct:free` | openrouter.ai/keys |

> **Model IDs change often.** Each default is overridable with `<ID>_MODEL` in `.env`, e.g.
> `OPENAI_MODEL=openai/gpt-4o` or `GROK_MODEL=xai/grok-3`. If a model name 404s, check the
> provider's own model list and set the override — you never need to touch code.

### Azure AI Foundry — which model to select
Azure is different: you don't pick a *model name*, you pick the **deployment** you created in the
Azure portal/AI Foundry. So:
1. In Azure AI Foundry, deploy a model (e.g. `gpt-4o-mini`) — note the **deployment name** you give it.
2. Set `AZURE_API_BASE=https://<your-resource>.openai.azure.com`, `AZURE_API_KEY=…`, and
   `AZURE_MODEL=azure/<your-deployment-name>`.

### AWS Bedrock
Enable model access in the Bedrock console first (per-model, per-region). Then set
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` (e.g. `us-east-1`), and optionally
`BEDROCK_MODEL=bedrock/<model-id>`. Bedrock gives you AWS-hosted Claude/Llama/Titan in Chat.

## Voice (ElevenLabs — text-to-speech)
```bash
./securax providers add        # provider: elevenlabs
./securax say "Your morning brief is ready."   # writes securax-speech.mp3
```
Override the voice with `ELEVENLABS_VOICE_ID`. **Sovereignty note:** `say` sends the text to
ElevenLabs' cloud API — don't use it for RED-tier data.

## Heavy compute (Google Colab / cloud GPU) — recipe
This is **not** a chat provider; it's about running a *bigger local model faster* when your laptop
is slow. Two sovereign-friendly options:

1. **Bedrock / a cloud LLM** (simplest): add the `bedrock` (or any cloud) plugin above — the heavy
   lifting runs in the cloud, your sensitive data still gets PII-redacted by the gateway first.
2. **Remote Ollama on a GPU box or Colab** (keeps the model yours):
   - On the GPU machine / Colab: `curl -fsSL https://ollama.com/install.sh | sh`, then
     `OLLAMA_HOST=0.0.0.0 ollama serve` and `ollama pull <a-bigger-model>`.
   - Expose it securely (Tailscale, or an SSH/Cloudflare tunnel) and note its URL.
   - Set `REMOTE_OLLAMA_BASE=http://<that-host>:11434` in `.env`, then point the `local` plugin's
     `api_base` at it (or set `OLLAMA_BASE_PATH` for AnythingLLM). The estate now offloads inference
     to the GPU while everything else stays on your box.

> Colab notebooks are ephemeral (the VM is reclaimed) — fine for experiments, not for an
> always-on endpoint. For a persistent GPU, a small cloud VM or your own workstation is better.

## Security posture
Every chat provider is reached **through the gateway**, so prompt-injection / PII / secret-exfil
rails apply regardless of which model answers. Keys live only in your git-ignored `.env`. The
`local` model never leaves your machine; cloud providers receive only what the rails allow.
