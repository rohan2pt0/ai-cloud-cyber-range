<!--
  SecuRAX — Integrations & connectivity.
  How to connect the estate to the AI models and productivity tools you already pay for,
  honestly and safely. The golden rule stays in force: the Red/Yellow/Green data tier
  decides what any integration is allowed to send to a cloud service.
-->

# SecuRAX — Integrations & Connectivity

This is the practical "how do I wire it to my existing tools" guide. It is honest about what
is and isn't possible, lists the free path first, and gives the **data-classification rule**
for every connector so you never leak Red-tier data to a cloud API.

## 0. The one rule that governs every integration
> **A cloud integration may only ever see 🟢 Green (or sanitised 🟡 Yellow) data. 🔴 Red data
> stays on local models and on-prem tools — always.** Every workflow below enforces this with
> the data-tier router (`integrations/n8n/02-data-tier-router.json`): the router classifies the
> payload first, and only Green/sanitised content is allowed to reach a cloud node.

## 1. The honest truth about "using my subscriptions" ⚠️
A consumer **app subscription is not an API.** You cannot wire these into automation pipelines:
| You have | Can it drive pipelines? | What you use instead (for automation) |
|---|---|---|
| **Claude Pro / Max** (claude.ai app) | ❌ No | **Anthropic API key** (separate, pay-as-you-go) |
| **ChatGPT Plus / Go** (app) | ❌ No | **OpenAI API key** (separate, pay-as-you-go) |
| **Gemini Advanced** (app) | ❌ No | **Google AI Studio / Gemini API key** (has a free tier) |
| **Microsoft 365** (Office apps) | ⚠️ Indirectly | **Microsoft Entra app + Graph API** (OAuth) |
| **Google Workspace / One** | ⚠️ Indirectly | **Google Cloud OAuth client** (free to create) |

This is expected and fine: the estate is **local-first**, so 80% of work runs on free local
models (Ollama) and you only reach for a cloud API for the 20% that truly needs it.

## 2. AI model APIs (the brain)
All models are reached through the **guardrail gateway → LiteLLM router** at one URL
(`http://gateway:8080/v1`), so your workflows never hard-code a provider — swap keys, not code.

| Provider | How to get it | Cost | Data tier allowed |
|---|---|---|---|
| **Ollama (local)** | already running | ₹0, private | 🔴🟡🟢 all — default for sensitive work |
| **Google Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Create API key | free tier, then PAYG | 🟢 (🟡 after masking) |
| **Anthropic Claude** | [console.anthropic.com](https://console.anthropic.com) → API Keys | PAYG (not your Pro plan) | 🟢 (🟡 after masking) |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) → API Keys | PAYG | 🟢 (🟡 after masking) |
| **AWS Bedrock / Azure OpenAI / Vertex** | cloud console | PAYG / free credits | 🟢🟡 (region-locked for residency) |

**Setup:** paste keys into `local/compose/.env` (`GEMINI_API_KEY=…`, `ANTHROPIC_API_KEY=…`).
They appear automatically in Open WebUI and are callable from n8n. The LiteLLM
`max_budget` ceiling still caps total cloud spend under your ₹2,500/month limit.

## 3. Google Workspace (Gmail, Calendar, Drive, Docs, Sheets)
n8n has native Google nodes; connect them once with an OAuth client you create (free).
1. [console.cloud.google.com](https://console.cloud.google.com) → create a project (or reuse your GCP range project).
2. **APIs & Services → Enable APIs**: Gmail, Google Calendar, Google Drive, Google Sheets.
3. **OAuth consent screen** → External → add yourself as a test user.
4. **Credentials → Create → OAuth client ID → Web application**; add n8n's redirect URL
   (`http://localhost:5678/rest/oauth2-credential/callback`).
5. In n8n → **Credentials → Google OAuth2 API** → paste client ID/secret → authorise.
**Data-tier rule:** Gmail/Calendar/Drive content is often 🟡 or 🔴 — classify before any
cloud-LLM summarisation. The email-triage and meeting-notes workflows do this automatically.

## 4. Microsoft 365 (Outlook, OneDrive, Teams, Excel) + Windows
n8n has native **Microsoft** nodes backed by the **Graph API**.
1. [entra.microsoft.com](https://entra.microsoft.com) → **App registrations → New registration**.
2. Add a **client secret** (Certificates & secrets) and **delegated Graph permissions**
   (`Mail.Read`, `Calendars.Read`, `Files.ReadWrite`, `offline_access`).
3. Redirect URI → `http://localhost:5678/rest/oauth2-credential/callback`.
4. In n8n → **Microsoft OAuth2 API** credential → paste tenant/client/secret → authorise.
**Windows-native:** use **Task Scheduler** to auto-start Docker Desktop at login (so the estate
is always on), and **PowerShell** scripts (`local/scripts/*.ps1` style) for any OS-level glue.
Excel files are best processed **locally** (download → process with a local model) when they
hold 🔴 data.

## 5. GitHub (versioning + CI/CD)
Already wired: the repo uses **GitHub Actions** for the DevSecOps pipeline, and the Terraform
modules use **OIDC** (keyless) for cloud deploys. For local automation, create a
**fine-grained Personal Access Token** (repo scope) and add it to n8n's GitHub credential.

## 6. What to connect first (80/20)
1. **Gemini API key** (free) → cloud burst for Green tasks. 2 minutes.
2. **Google OAuth** → Gmail + Calendar for the morning brief and email triage.
3. **Microsoft OAuth** only if your work lives in Outlook/Teams.
4. Anthropic/OpenAI keys later, only if a task needs their quality and the data is Green.

## 7. Import the workflows
See `integrations/n8n/` — import each `.json` in n8n (**⋯ → Import from File**), open it, set the
credential on the cloud nodes, and toggle **Active**. Each workflow is documented in
`integrations/README.md`, calls the gateway (not a model directly), and respects the data tiers.

> Security note: every credential lives in n8n's encrypted store or `.env` (git-ignored) —
> never in a workflow export or in code. Rotate keys periodically; use least-privilege scopes.
