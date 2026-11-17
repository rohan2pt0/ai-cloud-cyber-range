#!/usr/bin/env bash
# Stop everything so nothing keeps running (and nothing keeps costing) overnight. Your data is KEPT.
#   ./local/scripts/teardown.sh            stop the estate and remove the practice cluster; chats, documents, workflows and models stay
#   ./local/scripts/teardown.sh --erase    also delete the estate's data, after you type the word (take a backup first)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ERASE=0
case "${1:-}" in
  "") ;;
  --erase) ERASE=1 ;;
  *) echo "Unknown option: $1   Run it with nothing (stop, keep the data) or with --erase (also delete the data)."; exit 1 ;;
esac
VOLS=""
if [ "$ERASE" = 1 ]; then
  echo "This deletes, for good, the data the estate keeps on this machine: your chats, private documents, automation"
  echo "workflows, synced Life OS data and the downloaded models. It cannot be undone."
  echo "The safe step first:  ./securax backup"
  printf 'Type  erase  to delete it (anything else keeps it): '
  read -r _word || _word=""
  if [ "$_word" = erase ]; then VOLS="-v"; else ERASE=0; echo; echo "Nothing was deleted."; fi
fi
if command -v kind >/dev/null 2>&1; then kind delete cluster --name range || true; fi
# $VOLS is empty or -v: left unquoted on purpose
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down $VOLS ) || true
if [ "$ERASE" = 1 ]; then echo "[range] stopped, and the estate's data on this machine is deleted."
else echo "[range] stopped. Your data is kept: start again with  ./securax up"; fi
echo "Cloud resources (if any) are removed with: cd infra/terraform/environments/lab && terraform destroy"
