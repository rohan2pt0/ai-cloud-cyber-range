# Deploy SecuRAX on your machine

The goal: as easy as Mattermost or an OpenStack all-in-one — **install Docker, run one command,
done.** No account, no cloud bill, nothing leaves your machine.

> **You already own a working copy.** This is a public repository. As long as you can reach
> GitHub you can `git clone` (or download the ZIP) and run everything below — it does **not**
> depend on any AI assistant or usage limit.

---

## The 80/20 — if you only do this, you're running
```text
1. Install Docker Desktop and start it (wait for the green whale).
2. Get the code:   git clone https://github.com/rohan2pt0/ai-cloud-cyber-range.git
                   cd ai-cloud-cyber-range
3. (Mac/Linux/WSL) ./securax setup     # 30-sec wizard: paste a free Gemini key, say yes to phone access
   (Windows)       put GEMINI_API_KEY=... in local\compose\.env  (optional, for instant answers)
4. Start it:       Windows → double-click START-HERE-Windows.bat
                   Mac/Linux → ./securax up
5. Your Command Center opens automatically — ONE page that links every app.
```
Everything after this point is optional depth.

> **Want it 100% free / sovereign?** You need **no paid keys at all**. Run `./securax pull` once to
> fetch the local model, then in Chat pick **`bank-assistant-local`** (runs on your box, never leaves
> it). For fast free cloud answers, add a **free** Gemini key (`./securax setup`) and use
> **`bank-assistant`** (Gemini free-tier → local fallback). Chat now defaults to `bank-assistant`,
> so you never land on a paid model by accident. Other free options: **OpenRouter** free models
> (`./securax providers add` → openrouter). Paid providers (OpenAI, Anthropic, Grok…) are optional —
> if one shows "Oops", its key just has no credits; you don't need it.

> **Fast answers:** paste a **free** Google AI Studio key (https://aistudio.google.com/apikey) in
> step 3 — answers then come from cloud Gemini instantly. Without it, a private local model is used
> (slower on a laptop, fully offline). Sensitive data always stays local either way.
>
> **One front door:** you no longer juggle `:3000`, `:3001`, `:5678`. The **Command Center**
> (`http://localhost:8088/hub.html` — also reachable as `/hub`, opened for you) has a clickable
> card for every app with a live up/down dot, and the Guiding Map's **◆ All Apps** header button
> links straight to it.

---

## 1. One-time prerequisite — Docker (5 minutes)
SecuRAX runs in containers, so the only thing you install is Docker.

- **Windows 11 / 10:** install **Docker Desktop** (uses the WSL2 backend). Launch it and wait
  until the whale icon in the system tray is steady/green.
- **macOS:** install **Docker Desktop**, launch it, wait for the whale.
- **Linux:** install **Docker Engine** + the **compose plugin**
  (`docker` and `docker compose version` should both work).

**Recommended:** 8 GB RAM (works on less with the lighter model). ~5 GB free disk for the model.

---

## 2. Get the code
- **With git (recommended — lets you `git pull` to update):**
  ```bash
  git clone https://github.com/rohan2pt0/ai-cloud-cyber-range.git
  cd ai-cloud-cyber-range
  ```
- **Without git:** on the GitHub page → **Code → Download ZIP** → extract → open a terminal in
  the extracted folder.

---

## 3. Start it — one step
> **Windows? Use [WINDOWS-QUICKSTART.md](WINDOWS-QUICKSTART.md)** — copy-paste steps, fastest setup (runs inside WSL's own disk).

| Your OS | Do this |
|---|---|
| **Windows (simplest)** | In **File Explorer**, double-click **`START-HERE-Windows.bat`** |
| **Windows (PowerShell)** | `.\securax.cmd up` — every `./securax <command>` below works as `.\securax.cmd <command>` (it runs inside WSL). **Don't** type `./securax` in PowerShell: Windows can't run a bash script and asks "Select an app to open" |
| **Windows (WSL/Ubuntu terminal)** | Run **`./securax up`** — the `.bat` files only work when double-clicked, **not** when typed in WSL |
| **macOS / Linux** | Run **`./securax up`** |

> **Running inside WSL / a Linux terminal?** Use `./securax up` and `./securax down`. Typing
> `START-HERE-Windows.bat` there gives `command not found` — those are for double-clicking in
> Windows File Explorer. `./securax up` now also **asks for a free Gemini key right in the terminal**
> (press Enter to skip), so first-run setup is one step with no `.env` editing.
>
> **Windows prerequisites (one-time):** Docker Desktop running, WSL2 + Ubuntu (`wsl --install`), and Docker
> Desktop ▸ Settings ▸ Resources ▸ **WSL integration ▸ Ubuntu = ON**. `securax.cmd` checks each and tells you
> exactly which one is missing. For speed, keep the folder inside WSL (`~/ai-cloud-cyber-range`) rather than
> on a Windows drive (`/mnt/d/...` works but file access is several times slower).
>
> **Update:** `.\securax.cmd update` (Windows) / `./securax update` — pulls, recreates the containers. Your
> checkout stays clean (the router config is generated into a git-ignored file), so `git pull` never conflicts.
> If an older checkout still refuses to pull over `litellm-config.yaml`, run once:
> `git checkout -- local/compose/litellm-config.yaml`.
>
> **After a `git pull`, always recreate the containers** so the new code actually runs —
> `./securax down && ./securax up` (WSL/Mac/Linux) or double-click `STOP-Windows.bat` then
> `START-HERE-Windows.bat` (Windows). A browser tab left open updates itself automatically.

It brings the whole estate up, **opens your home screen immediately** at
**http://localhost:8088**, and downloads the local AI model in the background (first run only,
~2–5 min). You don't wait for it — the planner, playbook and life-OS work the instant the page
opens, and the **Ask** tab shows a live *"AI is ready / warming up / off"* status.

---

## 4. Verify it's running
- **Home screen:** http://localhost:8088
- **Everything at a glance:** `./securax status`
- **Health + version:** http://localhost:8080/healthz and http://localhost:8080/version
- **Resource/health check:** `./securax doctor`

### What you now have
| Service | URL | For |
|---|---|---|
| **Guiding Map (home)** | http://localhost:8088 | your daily cockpit / life-OS |
| Unified chat (guarded) | http://localhost:3000 | ChatGPT/Claude-style, local+cloud via the rails |
| Private document chat (RAG) | http://localhost:3001 | chat with your PDFs/docs, never leaves the box |
| Automation (n8n) | http://localhost:5678 | morning brief, triage, workflows |
| Guardrail gateway API | http://localhost:8080 | the OpenAI-compatible policy enforcement point |

---

## 4a. Use it on your phone & iPad (and keep them in sync)
1. **Let other devices reach it** — run `./securax setup` and answer **yes** to phone access (sets
   `BIND_HOST=0.0.0.0`), or edit `local/compose/.env` → `BIND_HOST=0.0.0.0`, then `./securax up`.
2. **On the phone/iPad (same Wi-Fi)** open `http://<your-laptop-IP>:8088`
   (find the IP: `hostname -I` on Linux/WSL, `ipconfig` on Windows).
3. **Install it like an app:** browser menu → **Add to Home screen** (iPhone/iPad: Share → Add to Home Screen).
4. **Sync all devices:** in the Guiding Map → **Ops → Cross-device sync**, paste the **same sync token**
   on every device (the one `./securax setup` generated, from `local/compose/.env` → `SYNC_TOKENS`).
   Your data stays on your own box — nothing goes to a third party.

> For secure access from **anywhere** (not just home Wi-Fi) and the full installable/offline PWA,
> install **Tailscale** on the laptop and each device, then set `BIND_HOST` to the laptop's `100.x`
> Tailscale IP. (Plain-HTTP Wi-Fi works as a web page; a secure URL unlocks full "install as app".)

---

## 5. Stop, update, back up
- **Stop (free RAM):** Windows → `STOP-Windows.bat`; Mac/Linux → `./securax down`
- **Update to the latest:** `git pull` then start again (Docker reuses what hasn't changed).
- **Your data:** the Guiding Map stores everything in your browser (localStorage) on this device.
  Make a backup any time from **Ops → System health → Export backup** (a dated JSON file). That
  export is your real version history and the safety net behind everything.
- **Pin a known-good version:** `git checkout v0.1.0` (any release tag) to run that exact release.

---

## 6. If something breaks (the handful that actually bite)
| Symptom | Fix |
|---|---|
| **`START-HERE-Windows.bat: command not found`** | You're in WSL/a Linux terminal. Use `./securax up` there (the `.bat` is only for double-clicking in Windows File Explorer). |
| **Chat shows "Model not selected" / no models; or an app shows an OLD version after a `git pull`** | The containers weren't recreated — a pull only updates files, not running containers. Run `./securax down && ./securax up` (WSL/Mac/Linux). The Guiding Map tab then self-updates; if an app page is still stale, press **Ctrl+Shift+R** once. |
| **"model qwen2.5:1.5b not found" (Private Docs / local chat)** | The local model is still downloading (first run, ~1 GB). Wait for it, or add a free Gemini key (`./securax up` asks for one) so Chat works instantly while it finishes. |
| `docker` / "cannot connect" errors | Docker Desktop isn't running — start it, wait for the green whale, retry. |
| "port is already allocated" | Another app uses 8088/8080/3000/5678 — stop it, or change the port in `local/compose/docker-compose.yml`. |
| **"model not found" / chat shows no model** | Add a free Gemini key (`./securax setup`) for instant cloud answers, OR let the local model finish downloading. The gateway now exposes `/v1/models` so Open WebUI/AnythingLLM list a model to pick. |
| **Chat says "Oops! There was an error"** | Run **`./securax doctor`** — it tests the real ladder and prints who answered or the *actual* error. (Earlier builds never passed provider keys into the router container, so paid providers always failed; fixed and now enforced by a test — `git pull`, then `./securax down && ./securax up`.) Meanwhile pick **`bank-assistant`** (free ladder, ends at local). |
| **"400: Request blocked by AI security policy" on harmless prompts** | Llama Guard (an *optional* extra detector) is switched on in your `.env` but its model was never installed, so the gateway — fail-closed — blocks everything. Old installs got this from an old `.env.example`; `git pull` never rewrites `.env`. **`./securax update`** fixes it automatically (it switches the broken detector off and says so); or run **`./securax guard off`**. The built-in rails still enforce. Use **`./securax guard on`** only if you want to install Llama Guard properly. |
| **A fix I just pulled "doesn't work"** | A `git pull` changes files on disk but running containers keep the old code. Use **`./securax update`** (pull + recreate in one step). `./securax doctor` tells you if you're behind `main`. |
| **Chat shows "Arena Model"** | Open WebUI's random-model picker; now disabled and Chat defaults to `bank-assistant`. |
| **Local chat fails / `bank-assistant-local` errors** | The local model isn't pulled yet. Run **`./securax pull`** (foreground, waits for it), then retry. |
| **Every question says "Blocked by the guardrail"** | That was a bug when no model was available — fixed. If you still see it, it's a *real* block (your text matched an attack/PII pattern); rephrase. The deterministic rails give 100% red-team defence without any model. |
| Answers are **slow** | That's the local CPU model. Paste a free Gemini key (`./securax setup`) — answers become instant; sensitive data still stays local. |
| "port is already allocated" | Another app uses 8088/8080/3000/5678 — stop it, or change the port in `local/compose/docker-compose.yml`. (The optional k8s plane now uses 8081, not 8080.) |
| "no space left on device" | Free disk, then retry — `docker system prune` removes unused layers. |

Full troubleshooting + security posture notes: [`GETTING-STARTED.md`](GETTING-STARTED.md)
("If something breaks") and [`docs/securax/`](docs/securax/).

---

## 7. Optional power-ups (only when you want them)
| Want… | How | Doc |
|---|---|---|
| Cross-device sync (phone ↔ laptop) | set up `estate-sync` + Tailscale | [doc 14](docs/securax/14-GUIDING-MAP.md) |
| More AI providers (OpenAI, Claude, DeepSeek, Mistral, Grok, Perplexity, Azure, Bedrock…) | `./securax providers add` | [doc 22](docs/securax/22-PLUGINS-AND-PROVIDERS.md) |
| Voice (text-to-speech) | `./securax providers add` → elevenlabs, then `./securax say "…"` | [doc 22](docs/securax/22-PLUGINS-AND-PROVIDERS.md) |
| Free cloud models as a fallback | paste free API keys into `local/compose/.env` | [doc 15](docs/securax/15-COST-AND-MODELS.md) |
| Autonomous web research | `./securax research "…" --allow site.com` | [doc 19](docs/securax/19-AUTONOMOUS-RESEARCH.md) |
| Scheduled tasks ("Routines") | `./securax routines list` | [doc 20](docs/securax/20-CLAUDE-PARITY.md) |
| Local image generation | enable the `design` compose profile | [doc 20](docs/securax/20-CLAUDE-PARITY.md) |
| Heavy SOC stack | `./securax full up` | [doc 10](docs/securax/10-FULL-STACK.md) |

---

## 8. All commands
```
./securax up        start everything (+ opens the home screen)
./securax status    health + URLs
./securax update                 git pull + recreate containers (the safe way to get fixes)
./securax guard [status|on|off]  the OPTIONAL Llama Guard detector (built-in rails always enforce)
./securax profile                right-size to your RAM/CPU (+ WSL2 .wslconfig advice); ./securax up --lite = core path only
./securax providers [list|add]   add an AI provider (OpenAI, Claude, DeepSeek, Grok, Azure, Bedrock…)
./securax say "text"             speak text aloud via ElevenLabs (voice plugin)
./securax version   print the version
./securax doctor    resource & health check
./securax down      stop everything (free RAM)
./securax research "…" --allow d.com [--render]   autonomous read-only web research
./securax act action.json --allow d.com --approve  run one approved web action (HITL)
./securax design "prompt"                           local image generation (opt-in)
./securax routines [list|due|run]                   scheduled estate tasks
./securax ask <agent> "q"   ·  ./securax enhance "q"  ·  ./securax intel  ·  ./securax plan
./securax mcp       run the MCP control-plane server
./securax full up   start the heavy full-scale SOC stack
```
