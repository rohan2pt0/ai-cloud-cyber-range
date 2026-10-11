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
3. Start it:       Windows → double-click START-HERE-Windows.bat
                   Mac/Linux → ./securax up
4. It opens http://localhost:8088 automatically. That's it.
```
Everything after this point is optional depth.

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
| Your OS | Do this |
|---|---|
| **Windows** | Double-click **`START-HERE-Windows.bat`** |
| **macOS / Linux** | Run **`./securax up`** |

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
| `docker` / "cannot connect" errors | Docker Desktop isn't running — start it, wait for the green whale, retry. |
| "port is already allocated" | Another app uses 8088/8080/3000/5678 — stop it, or change the port in `local/compose/docker-compose.yml`. |
| Page opens but **AI says "warming up"** | First-run model download (~1 GB) — wait a few minutes; the Ask tab flips to "ready" on its own. |
| Laptop slow while a model answers | Use the lighter model / cap WSL2 RAM (see the uploaded SOP) — `./securax doctor` flags high usage. |
| "no space left on device" | Free disk, then retry — `docker system prune` removes unused layers. |

Full troubleshooting + security posture notes: [`GETTING-STARTED.md`](GETTING-STARTED.md)
("If something breaks") and [`docs/securax/`](docs/securax/).

---

## 7. Optional power-ups (only when you want them)
| Want… | How | Doc |
|---|---|---|
| Cross-device sync (phone ↔ laptop) | set up `estate-sync` + Tailscale | [doc 14](docs/securax/14-GUIDING-MAP.md) |
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
