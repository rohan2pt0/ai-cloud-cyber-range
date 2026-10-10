#!/usr/bin/env bash
# Pillar 3 — SENTINEL hybrid-AI daily driver.
# Brings up the full local AI workspace on the laptop: gateway (guardrails) + LiteLLM
# (multi-model router) + Ollama (local models) + Open WebUI (unified chat) + AnythingLLM
# (private doc RAG) + n8n (automation). All bound to 127.0.0.1 — invisible to the network.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/local/compose"
log(){ printf '\033[1;36m[daily-driver]\033[0m %s\n' "$*"; }

[ -f .env ] || { cp .env.example .env; log "created .env from example — add cloud keys later if you want"; }

log "1/3 Building the guardrail gateway and starting the AI profile"
docker compose --profile ai up -d --build

log "2/3 Pulling local models into Ollama (one-time; ~1–6 GB each)"
CID="$(docker compose ps -q ollama)"
docker exec "$CID" ollama pull "${LOCAL_MODEL:-qwen2.5:1.5b}"
docker exec "$CID" ollama pull llama-guard3:1b || log "  (llama-guard optional — skipped)"

log "3/3 Ready. Open these on your laptop:"
cat <<URLS
  • Unified chat (local + cloud, through guardrails) : http://localhost:3000   (Open WebUI)
  • Private document chat (RED-tier, never leaves)   : http://localhost:3001   (AnythingLLM)
  • Automation workflows                             : http://localhost:5678   (n8n)
  • Guardrail gateway API                            : http://localhost:8080/healthz
Stop everything (free RAM):  docker compose --profile ai down
URLS
