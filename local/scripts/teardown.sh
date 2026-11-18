#!/usr/bin/env bash
# Stop everything so nothing keeps running (and nothing keeps costing) overnight. Your data is KEPT: chats, documents,
# workflows, the sync store and the local models all come back on the next start.
#
#   ./local/scripts/teardown.sh           stop the kind cluster and every container; keep the data
#   ./local/scripts/teardown.sh --erase   the same, then DELETE the data volumes too (asks you to type a word first)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ERASE=0
case "${1:-}" in
  "") ;;
  --erase) ERASE=1 ;;
  *) echo "Unknown option: $1   (use no option to stop and keep your data, or --erase to delete it too)" >&2; exit 2 ;;
esac
VOLS=()
if [ "$ERASE" = 1 ]; then
  # Irreversible, so it is never the default, says what is lost, offers the safe step first and needs a typed word.
  echo "This deletes every SecuRAX data volume on this machine: chats, private documents, workflows, the password vault,"
  echo "the sync store (your Life OS data kept here) and the downloaded models. It cannot be undone."
  echo "Safe step first:  ./securax backup"
  [ -t 0 ] || { echo "Nothing was deleted: --erase needs a person at a terminal to confirm it." >&2; exit 1; }
  printf 'Type ERASE to delete the data, or press Enter to keep it: '
  read -r _word || _word=""
  [ "$_word" = "ERASE" ] || { echo "Nothing was deleted."; exit 0; }
  VOLS=(-v)
fi
if command -v kind >/dev/null 2>&1; then kind delete cluster --name range || true; fi
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai --profile passwords --profile online --profile studio down ${VOLS[@]+"${VOLS[@]}"} ) \
  || echo "[range] the containers could not be stopped (is Docker running?). Ask why:  ./securax why"
if [ "$ERASE" = 1 ]; then echo "[range] local plane stopped and its data deleted."; else echo "[range] local plane stopped. Your data is kept; start again with:  ./securax up"; fi
echo "[range] Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
