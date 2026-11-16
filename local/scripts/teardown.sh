#!/usr/bin/env bash
# Stop the local plane so nothing keeps running (and nothing keeps costing) overnight. YOUR DATA IS KEPT.
#
#   ./local/scripts/teardown.sh           # stop the containers and the kind cluster; chats, documents, workflows and sync data stay
#   ./local/scripts/teardown.sh --erase   # ALSO delete every data volume. It cannot be undone, so it asks for a typed word first.
#
# It used to delete the volumes every time, while the docs called it "stop everything": a person who ran it each
# night lost their chats, private documents, workflows and synced Life OS data (review ledger, slice 2).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ERASE=0
case "${1:-}" in
  "") ;;
  --erase) ERASE=1 ;;
  *) echo "Unknown option: $1   (use no option to stop and keep your data, or --erase to delete it)"; exit 1 ;;
esac
if [ "$ERASE" = 1 ]; then
  echo "This deletes every SecuRAX data volume on this machine: chat history, private documents,"
  echo "automation workflows, the database and the synced Life OS data. It cannot be undone."
  echo "Safer first:  ./securax backup   (then run this again)."
  printf 'Type  erase  to delete them, or anything else to keep them: '
  _a=""; read -r _a || true
  if [ "$_a" != erase ]; then ERASE=0; echo "Nothing deleted: stopping only."; fi
fi
kind delete cluster --name range || true
if [ "$ERASE" = 1 ]; then
  ( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down --volumes ) || true
  echo "[range] local plane stopped and its data volumes deleted."
else
  ( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down ) || true
  echo "[range] local plane stopped. Your data is kept; start again with:  ./securax up"
fi
echo "Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
