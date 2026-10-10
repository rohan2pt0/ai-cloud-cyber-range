<!--
  SecuRAX — Getting Started.
  The shortest path from "fresh laptop" to "using it daily". Written for the HP Spectre x360
  (Windows 11 + Docker Desktop with the WSL2 backend, or any Linux). Everything here is free.
-->

# Getting Started with SecuRAX

## ⭐ Just start it — one step

**Windows:** double-click **`START-HERE-Windows.bat`**.
**Mac / Linux:** run **`./securax up`**.

That is the whole thing. It brings the estate up, **opens your home screen immediately**
(`http://localhost:8088`), and downloads the local AI model in the background (first run only,
~2–5 min). You do **not** wait for it and you do **not** need to read anything else: the home
screen's **Ask** tab shows a live *"AI is ready / still warming up / off"* status in plain
words, and the planner, playbook and life-OS work the instant the page opens. To stop and free
memory later: `STOP-Windows.bat` (or `./securax down`).

*Prerequisite: Docker Desktop running (the green whale in the system tray; WSL2 backend on Windows).*

---

Everything below is **optional depth** for when you want to go further — you do **not** need it to start.

Three ways in, shortest first. You do **not** need to do them in order — pick what you need today.

## 0. See the whole thing in 30 seconds (no install)
Open **`portal/index.html`** by double-clicking it. That is your command center: the five
pillars, the data-classification rules, the principles, the capability catalog (searchable),
the roadmap, and the compliance coverage. Read it once; it is how you navigate everything.

## 1. Run the AI Security Range (Pillar 1) — the defensive core
Prerequisite: **Docker Desktop** running (WSL2 backend on Windows).
```bash
# from the repo root
./local/scripts/bootstrap-laptop.sh        # gateway + model router + DB + a self-test
./local/scripts/kind-up.sh                  # Kubernetes plane (admission control + runtime detection)
python3 redteam/run_attacks.py --fail-under 0.9   # adversarial-ML scorecard (should be 100%)
./local/scripts/teardown.sh                 # stop everything — costs nothing overnight
```
What you now have: a guardrail gateway, a red-team scorecard, an AI-SPM posture report, and a
board brief — the portfolio for the eight AI-security roles. Demo script: `docs/demo-runbook.md`.

## 2. Use the hybrid-AI daily driver (Pillar 3) — what you use every day
This is the private "ChatGPT + Claude + Gemini in one window, with your documents" on your laptop.
```bash
./local/scripts/daily-driver-up.sh          # first run pulls a local model (~1–6 GB, one-time)
```
Then open:
| What | URL | Use it for |
|---|---|---|
| **Unified chat** (local + cloud via guardrails) | http://localhost:3000 | daily questions, drafting; pick a `local-*` model for 🔴 Red data, cloud for 🟢 Green |
| **Private document chat** (RAG, never leaves laptop) | http://localhost:3001 | upload PDFs/Word/Excel and chat with them — safe for sensitive docs |
| **Automation** (n8n) | http://localhost:5678 | build the morning brief, email triage, the data-tier router |

**The one rule that keeps you safe:** confidential content → pick a **local** model. Cloud
models are for everything else. (This is the Red/Yellow/Green rule from the architecture.)

Add cloud models later by pasting free API keys into `local/compose/.env`
(`GEMINI_API_KEY=…`). Nothing routes to the cloud unless you pick a cloud model.

Stop and free RAM any time: `cd local/compose && docker compose --profile ai down`.

## 3. The human layer (Pillar 4) — self-OPSEC, finance, life-OS
```bash
python3 personal-rnd/self_opsec.py --footprint-file my_public_bio.txt   # what you over-share
python3 personal-rnd/fin_freedom.py --expense 150000 --corpus 2500000 --invest 200000  # FIRE plan
python3 personal-rnd/lifeos.py --review                                  # weekly-review template
```

## Daily rhythm (keeps it alive — 10 min/day)
Morning: open Open WebUI, let n8n's morning brief run. Evening: 10-minute shutdown note
(what got done, tomorrow's top 3). Friday: weekly review. See `docs/securax/05-ROADMAP.md`
for the full cadence. **Everything compounds because it is all captured in one base.**

## If something breaks
- `docker` errors → Docker Desktop isn't running; start it, wait for the green whale.
- Laptop slows while a model answers → use the lighter `local-fast` model; cap WSL2 RAM
  (see the uploaded SOP) at 10 GB.
- Open WebUI shows no models → the gateway booted before Ollama:
  `cd local/compose && docker compose --profile ai restart gateway`.
- Full troubleshooting + security posture notes: the uploaded `SOP-README.md`.
