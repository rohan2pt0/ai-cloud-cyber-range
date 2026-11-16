#!/usr/bin/env bash
# Stop the local plane so nothing keeps running (and nothing keeps costing) overnight. Your data stays.
#   ./local/scripts/teardown.sh           stop the containers and the kind cluster; every data volume is kept
#   ./local/scripts/teardown.sh --erase   ALSO delete the data volumes. It asks you to type ERASE; it cannot be undone.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ERASE=0
case "${1:-}" in
  "") ;;
  --erase) ERASE=1 ;;
  *) echo "Unknown option: $1   (no option stops and keeps your data; --erase also deletes it)"; exit 2 ;;
esac
if [ "$ERASE" = 1 ]; then
  echo "--erase deletes the SecuRAX data volumes on this machine: chat history, private documents, automation"
  echo "workflows, the Life OS sync copy, the gateway's ledger and the database. It cannot be undone."
  echo "The safe step first:  ./securax backup"
  [ -t 0 ] || { echo "Nothing was deleted: --erase needs a person at a terminal to type the word."; exit 1; }
  printf 'Type ERASE to delete them (anything else keeps them): '
  read -r _word || _word=""
  [ "$_word" = "ERASE" ] || { echo "Kept. Nothing was stopped or deleted."; exit 0; }
fi
kind delete cluster --name range 2>/dev/null || true
if [ "$ERASE" = 1 ]; then
  ( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down -v ) || true
  echo "[range] local plane stopped and its data volumes deleted."
else
  ( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down ) || true
  echo "[range] local plane stopped. Your data is kept; start again with:  ./securax up"
fi
echo "Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
