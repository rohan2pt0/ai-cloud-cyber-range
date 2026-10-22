# SecuRAX Integrations

How the estate connects to the AI models and productivity tools you already use — safely,
local-first, and under your cost ceiling. **Read [`docs/securax/07-INTEGRATIONS.md`](../docs/securax/07-INTEGRATIONS.md) first** for the full connectivity guide (which key/OAuth to get, what's free, and the data-tier rule for each tool).

## The golden rule
> A cloud integration may only ever see 🟢 Green (or sanitised 🟡 Yellow) data.
> 🔴 Red data stays on local models. Every workflow here enforces this.

## n8n workflow templates (`n8n/`)
Import each in n8n (**⋯ → Import from File**), set the credential on any cloud node, then **Publish** it (n8n 2 renamed Active).
All of them call the **guardrail gateway** (`http://gateway:8080/v1`, or `https://gateway.securax.internal:8443/v1` when internal TLS is on: the templates read `GATEWAY_URL`), never a model directly —
so you swap API keys, not workflows, and inherit every guardrail for free.
n8n 2 hides the environment from workflows by default; the estate allows it because nothing secret is in n8n's
environment (`lifecycle/tests/test_n8n_env.py` keeps it so). Keys go in n8n credentials, never in `$env`.

| File | What it does | Needs |
|---|---|---|
| `01-morning-brief.json` | 6 AM security brief, summarised via the gateway | nothing to start; add RSS + Gmail/Outlook to deliver |
| `02-data-tier-router.json` | **The hero.** POST text to a webhook → classifies Red/Yellow/Green → routes Red to local, Yellow/Green to cloud | nothing — works out of the box |
| `03-email-triage.json` | Classifies new mail (Urgent-Security / Admin / Normal / FYI) on the **local** model, then acts | Gmail or Outlook OAuth credential |

## Quick test (data-tier router)
Bring up the daily driver (`./local/scripts/daily-driver-up.sh`), import the router, activate it, then:
```bash
# Red data -> stays local
curl -s -X POST http://localhost:5678/webhook/classify \
  -H 'content-type: application/json' \
  -d '{"text":"Customer Aadhaar 2345 6789 0123 wants a loan"}'
# Green data -> may use cloud
curl -s -X POST http://localhost:5678/webhook/classify \
  -H 'content-type: application/json' \
  -d '{"text":"What is the RBI repo rate trend this year?"}'
```

## Credentials — where they live
- AI model keys → `local/compose/.env` (git-ignored). Appear automatically in Open WebUI + n8n.
- Google / Microsoft / GitHub → n8n's **encrypted credential store** (set once, never exported).
- Never put a secret in a workflow `.json` or in code. Rotate keys; use least-privilege scopes.
