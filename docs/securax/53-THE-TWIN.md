# 53 · The Twin: a Claude-like assistant you own

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Twin chain, memory and web search configured; `open_webui_chat` journey. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Goal:** daily chat that feels like Claude (web search, memory, projects, your standing instructions, your past work),
running inside your estate, so no single AI vendor is a point of failure.

## What changed in Chat (Open WebUI 0.12.2), and why

Everything is set in `docker-compose.yml` / `.env`. Admin-screen changes are lost on restart because
`ENABLE_PERSISTENT_CONFIG=false` (that keeps `.env` authoritative).

| Setting | Before | Now | Why |
|---|---|---|---|
| Sign-in key `WEBUI_SECRET_KEY` | made anew whenever the container was recreated (every `./securax update`) | created once by `up`, kept in `.env` (and in your backups) | you stayed signed in only until the next update, and tool tokens broke |
| Session length `JWT_EXPIRES_IN` | 4 weeks | **7 days** (`OWUI_JWT_EXPIRES_IN`) | without Redis, signing out does not end a session; matters once your phone reaches Chat |
| Web search | off | **on** (DuckDuckGo, no key; `OWUI_WEB_SEARCH_ENGINE`) | the globe toggle in a chat. Off per chat until you click it; then the search text goes to DuckDuckGo |
| Memory, notes, folders (projects), code runner | defaults | switched on explicitly | folders hold their own instructions and knowledge; Python runs in your browser (Pyodide), not on the server |
| Profile-image forwarding | on | **off** | avatars fetched from outside sites leak your IP address |
| Memory cap | 1 GB | **1.5 GB** (`OPENWEBUI_MEM`) | document search embeds inside Chat (local, about 0.5 GB). Doing it in Ollama would evict your chat model (one model at a time keeps CPU laptops from swapping) |

Search results and uploaded documents still pass through the gateway, so the injection and leak rails inspect them like any prompt.

## The brain: model `twin`

`twin` is a model in the picker with its own ladder:

**strong open model (paid, opt-in) → Gemini free → Groq free → OpenRouter free → local**

- **Until you opt in, it costs ₹0.** The paid rung is off, so `twin` behaves like `bank-assistant`.
- **To opt in:**
  1. Run `./securax providers add openrouter_pro`.
  2. Paste your OpenRouter key.
  3. Type `yes` for `OPENROUTER_PRO_OK`.

  Default model: GLM-5.2, about $0.45 in / $3.31 out per million tokens on OpenRouter (checked 15-Oct-2026; confirm on the site). Switch with `OPENROUTER_PRO_MODEL=openrouter/<id>`; `./securax models` repairs a retired name itself.
- **Spend is capped.** The router's `max_budget` (doc 15) stops cloud calls once the monthly cap is reached, and the ladder carries on with the free rungs.
- **DeepSeek is left out of `twin`**, because Chat carries personal data and DeepSeek is hosted in China. It stays on the build ladder.
- **Red-tier data stays local** (`./securax residency`, doc 36).

## Make it yours (about 5 minutes, once)

1. **Standing instructions.** Settings → General → System prompt: paste your own instructions (who you are, how you want answers). They apply to every chat. Keep personal details out of the repo; your copy lives only in Chat's database (and your backups).
2. **A Twin preset.** Workspace → Models → **+**:
   - name: `Twin`, base model: `twin`;
   - paste the same instructions;
   - tick Web search and Code interpreter;
   - attach your knowledge (step 4).

   Make a second preset, `Twin-private`, on `bank-assistant-local`, for anything personal or bank-related.
3. **Memory.** Settings → Personalization → Memory: on. Tell it durable facts ("I am moving to NABARD on contract", "Indian tax context"), and it carries them into new chats.
4. **Knowledge.** Workspace → Knowledge:
   - create **Handbooks** and upload your handbook files;
   - create **AI history** and upload `vault/knowledge/out` (doc 51).

   Attach Handbooks to `Twin-private`. Attach AI history to `Twin` only if you are happy for the relevant excerpts to go to the cloud model.
5. **Projects.** A folder in the sidebar can carry its own instructions and knowledge: one per project (career, CCSP, SecuRAX).

## Not in this step (vetted add-ons, later)

| Add-on | What it adds | Gate |
|---|---|---|
| **mcpo** (Open WebUI) | SecuRAX's own tools as buttons in chat: data-tier check, redaction, SOC triage, FIRE plan | `./securax vet` + `inspect`; authenticated tool server |
| **Open Terminal** | the AI runs code and hands you files, in a sandbox | a locked container, approval per action |
| **Voice ("Jarvis")** | talk to it; local speech-to-text (Whisper) | to verify on 0.12.2; text-to-speech engine choice |
| Open WebUI Computer | an agent on your real machine | **not recommended** on a machine that holds bank material |

## Proof

The sandbox journey `open_webui_chat` checks all of the following on the real stack:
- the `twin` model is listed;
- web search is on from `.env`;
- `up` created the sign-in key;
- **you are still signed in after Chat's container is recreated**, as every update does.
