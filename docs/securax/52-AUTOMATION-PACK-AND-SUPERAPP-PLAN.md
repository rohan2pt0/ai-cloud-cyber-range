# 52 · Automation that works on day one, and the SuperApp plan

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The automation pack and alerts are built; the SuperApp is a plan. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Prompt:** "n8n is useless if I have to build every workflow myself. Automate what is repetitive, cut paid-AI dependency
to the minimum without a single point of failure, make SecuRAX a super life app (later a mobile app), a Jarvis, with the kind
of automation Japan and Israel are known for."

## 1. What "Japanese and Israeli automation" means here

These are the practices behind that reputation. This is how each one is built in SecuRAX:

| Practice | What it means | In SecuRAX |
|---|---|---|
| **Jidoka** (Toyota): machines stop and call a human on a defect | No silent failure | `./securax watch` self-heals; the cockpit turns a defect amber/red; **the andon below tells you** |
| **Andon** cord: one visible signal when something is wrong | One channel, only for exceptions | routine `andon`: a phone push **only when the picture changes** |
| **Poka-yoke**: make the mistake impossible | Guards, not reminders | the update backs up first and rolls back; the gateway is fail-closed; secrets are redacted on import; `diffcheck` and `forge` gate builds |
| **Kaizen**: small improvements on a fixed rhythm | Rhythm beats effort | monthly review and quarterly check-in nudges; the handbook versions (doc 11) |
| **Intelligence-cell discipline** (Israeli practice): collect, correlate, alert only on what matters | Signal over noise | the digest carries the top 3 actions and deadlines only; counts and labels, never content |

## 2. The automation pack (works with no setup except one phone app)

All of these are SecuRAX **Routines**: plain cron on your machine, no n8n workflow to build (`./securax routines list`).

| Routine | When | What it saves you |
|---|---|---|
| `andon` | every 15 min | A phone push only when something turns amber/red, a regulatory deadline nears, or it is **back to green**. Otherwise silent. |
| `daily-backup` | every night 02:30 | A verified backup (encrypted if a key file is set); the newest 7 are kept. You never think about backups again. |
| `knowledge-inbox` | daily 21:05 | Imports any AI-chat export you drop into the inbox (doc 51). |
| `monthly-review` | 1st, 08:50 | The 15-minute KPI/KRI review nudge. |
| `quarterly-checkin` | 1 Jan/Apr/Jul/Oct | The quarterly check-in nudge. |
| `morning-brief`, `weekly-posture` | weekdays / Mon | Existing: health check and AI-security posture. |

**Switch it on (2 minutes):**
1. Install the **ntfy** app (Android or iPhone).
2. Run `./securax notify setup`. It makes a long random topic (on the public server the topic name is the password),
   saves it, shows it, and sends a test once you have subscribed to it in the app. A fresh topic later: `--new`.
3. Run `./securax routines install`. It sets exactly one schedule line for this folder (lines for an old folder are
   removed) and starts cron. `./securax doctor` shows both as `phone alerts: on` and `schedule: on`.

**What leaves the box:** status colour, the top 3 actions and deadlines. Never prompts, chats, keys or file contents.
For zero third parties, run your own ntfy server later and add `SECURAX_NOTIFY_NTFY_TOKEN`.

**Why not n8n for these:** n8n is kept for flows that need an outside account (Gmail, Drive). The three shipped n8n
templates stay opt-in. The "morning brief" template asks the model for "today's developments" **without giving it
any news**, so a model would invent headlines. It will be rebuilt on real feeds (RBI, SEBI, CERT-In) in a later step.
It is not auto-imported.

## 3. The plan: SuperApp, in rails (each step usable on its own)

| Step | What you get | Status |
|---|---|---|
| **1. Automation pack + andon** | Section 2 | **this change** |
| **2. Your AI history** | All past chats searchable, privately (doc 51) | **done** |
| **3. The Twin** (chat that feels like Claude) | In Chat (Open WebUI 0.12): web search, memory, notes and the code runner switched on through `.env` (Admin-screen changes are lost on restart because of `ENABLE_PERSISTENT_CONFIG=false`); a "Twin" preset with your standing instructions and knowledge; "Twin-private" on the local model | **done** (doc 53) |
| **4. The brain** (small monthly budget, no single point of failure) | Model `twin`: a strong open model, pay-per-use and opt-in, under the router's monthly cap (LiteLLM `max_budget`), then the free ladder, then local | **done** (doc 53; opt in with `./securax providers add openrouter_pro`) |
| **5. Jarvis voice** | Voice calls in Chat (Open WebUI 0.12 lists realtime voice) with local speech-to-text where the machine allows | to verify on 0.12.2 |
| **6. Regulator watch** | RBI/SEBI/CERT-In pages fetched by the read-only research agent, summarised, sent by the andon only when something is new | planned |
| **7. Family Android app** | The Guiding Map wrapped as an installable Android app (works offline; syncs with your estate over Tailscale), built so a store release later is a packaging step, not a rewrite | planned |
| **8. Fly rails** | A store-ready app: licensing, privacy policy, DPDP consent and deletion, crash-free metrics, payments. Today "fly" means the multi-tenant MSSP stage (doc 29), and its business layer is not built (doc 28) | rails only, when you decide to sell |

## 4. The brain: options with a small monthly budget (prices checked 15-Oct-2026; confirm before paying)

| Option | Price (third-party sources) | Fit |
|---|---|---|
| **Pay-per-use open model via OpenRouter** (e.g. GLM-5.2, reported closest open model to Claude) | about $0.45 in / $3.31 out per million tokens (OpenRouter average) | **Recommended for Chat**: pay only for what you use, under the router's hard monthly cap; the model is swappable in one line |
| **DeepSeek API** (V4.1 Flash) | about $0.30 / $1.20 per million at peak, half off-peak | Cheapest; Chinese-hosted: keep personal/red-tier data local (`./securax residency`) |
| **OpenCode Go** | $10/month flat, with spend limits | Already wired, but **build ladder only**: the plan is sold for coding agents (doc 42) |
| **Gemini free tier, local model** | ₹0 | Stay as fallbacks, so no vendor is a single point of failure |

A typical personal month (a few million tokens) costs well under ₹1,000 on the first two. The local model alone will not
match Claude on a laptop; that needs a large GPU.
