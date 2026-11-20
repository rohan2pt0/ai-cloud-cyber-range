#!/usr/bin/env bash
# Starts the interview demo in a GitHub Codespace (or any Linux box): the cyber range portal with a played-out exercise of
# dummy data, and the red-team scorecard against the AI gateway's rails. Python standard library only; no Docker, no model.
set -u
cd "$(dirname "$0")/.." || exit 1
pkill -f "exercise.demo" 2>/dev/null || true
nohup python3 -m exercise.demo --host 0.0.0.0 --port 8000 --out DEMO-TOKENS.txt > /tmp/securax-demo.log 2>&1 &
for _ in $(seq 1 20); do [ -s DEMO-TOKENS.txt ] && break; sleep 1; done
# Let a phone open the portal without a GitHub sign-in; the role tokens still guard it. Ignored where gh cannot do it.
if [ -n "${CODESPACE_NAME:-}" ] && command -v gh >/dev/null; then gh codespace ports visibility 8000:public -c "$CODESPACE_NAME" >/dev/null 2>&1 || true; fi
echo "Red-team scorecard against the gateway rails:"; python3 redteam/run_attacks.py 2>&1 >/dev/null | tail -1 || true
echo
cat DEMO-TOKENS.txt 2>/dev/null || tail -5 /tmp/securax-demo.log
if [ -n "${CODESPACE_NAME:-}" ]; then
  echo "Open on any phone: https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}/"
fi
