#!/usr/bin/env bash
# Tear everything down so nothing keeps running (and nothing keeps costing) overnight.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
kind delete cluster --name range || true
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down -v ) || true
echo "[range] local plane destroyed. Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
