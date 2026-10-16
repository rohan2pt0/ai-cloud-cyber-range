# 22 · Plugins & AI Providers

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Key wiring and failover are proven; a few providers need real credentials to prove. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

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
| `gemini` | Google Gemini *(default)* | `GEMINI_API_KEY` | `gemini/gemini-3.5-flash-lite` *(auto-corrected to the live model)* | aistudio.google.com/apikey |
| `local` | Ollama (sovereign) | — *(always on)* | `ollama/qwen2.5:1.5b` | — |
| `openai` | OpenAI (GPT) | `OPENAI_API_KEY` | `openai/gpt-4o-mini` | platform.openai.com/api-keys |
| `anthropic` | Anthropic (Claude) | `ANTHROPIC_API_KEY` | `anthropic/claude-haiku-5-5` | console.anthropic.com |
| `opencodego`, `opencodego_glm` | OpenCode Go (flat-rate open models; **build ladder only**, doc 42) | `OPENCODE_GO_API_KEY` | `openai/deepseek-v4.1-flash`, `openai/glm-5.3-flash` | opencode.ai/go |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` | `deepseek/deepseek-v4-flash` | platform.deepseek.com |
| `mistral` | Mistral | `MISTRAL_API_KEY` | `mistral/mistral-small-latest` | console.mistral.ai |
| `grok` | xAI (Grok) | `XAI_API_KEY` | `xai/grok-4.3` | console.x.ai |
| `perplexity` | Perplexity (Sonar) | `PERPLEXITYAI_API_KEY` | `perplexity/sonar` | perplexity.ai/settings/api |
| `azure` | Azure AI Foundry / OpenAI | `AZURE_API_KEY` + `AZURE_API_BASE` | `azure/<deployment>` | ai.azure.com |
| `bedrock` | AWS Bedrock | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` | `bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0` | console.aws.amazon.com |
| `openrouter` | OpenRouter (incl. free) | `OPENROUTER_API_KEY` | `openrouter/meta-llama/llama-3.3-70b-instruct:free` | openrouter.ai/keys |

> **Model IDs change often — SecuRAX corrects them itself.** Providers retire models every few months (as of Oct 2026
> reports include Groq's `llama-3.3-70b-versatile` and older Gemini 2.5 / Grok 2 names). `./securax keys` and (once a day)
> `./securax up` ask each provider which models your key can use *today* and, if the configured one is gone, switch
> `<ID>_MODEL` in `.env` to the best live match (`plugins/catalog.json` → `discover.prefer`). Run it any time:
> `./securax models` (report) · `./securax models --fix` (repair + reload). It also tells you when a key is rejected.
> The table below is the shipped default — treat it as a starting point, not a promise.
>
> Each default is overridable with `<ID>_MODEL` in `.env`, e.g.
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
2. **Your own stronger machine** (keeps the model yours; doc 56): install Ollama there from its official installer or package
   (not `curl | sh`), join it to your Tailscale network, and bind Ollama to its Tailscale address only
   (`OLLAMA_HOST=100.x.y.z:11434`; never `0.0.0.0`, which opens it to everyone on your LAN). Pull a model there, then set
   `REMOTE_OLLAMA_BASE=http://100.x.y.z:11434` and `HOME_MODEL=ollama/<that model>` in `.env` and run `./securax up`. The `home`
   rung joins every chain just before this laptop's model. Only loopback, private-LAN, Tailscale or `*.ts.net` addresses are
   accepted, because the rung counts as local for data residency. Measure it first: `./securax bench --url http://100.x.y.z:11434`.

> Colab and Kaggle notebooks are ephemeral (the VM is reclaimed) and your data goes to Google: use them for restartable,
> Green-tier batch jobs only, never as an always-on endpoint (tunnelling a server out of a notebook is a grey area in their terms).
> Never join a rented or cloud machine to your Tailscale as the `home` rung: it would count as local for residency (doc 57). For a persistent GPU, a small cloud VM or your own workstation is better.

## Security posture
Every chat provider is reached **through the gateway**, so prompt-injection / PII / secret-exfil
rails apply regardless of which model answers. Keys live only in your git-ignored `.env`. The
`local` model never leaves your machine; cloud providers receive only what the rails allow.
