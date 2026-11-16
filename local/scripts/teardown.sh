#!/usr/bin/env bash
# Stop the local plane so nothing keeps running (and nothing keeps costing) overnight. Your data stays.
#
#   ./local/scripts/teardown.sh           stop the kind cluster and every container; keep every volume
#   ./local/scripts/teardown.sh --erase   also delete the volumes: chats, documents, automations, the synced Life OS
#                                         state, the password vault and the database. It cannot be undone: type ERASE.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ERASE=0
case "${1:-}" in
  "") ;;
  --erase) ERASE=1 ;;
  -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
  *) echo "Unknown option: $1   (see: $0 --help)" >&2; exit 2 ;;
esac
VOLUMES=()
if [ "$ERASE" = 1 ]; then
  echo "This deletes every SecuRAX volume on this machine: chats, documents, automations, the synced Life OS state,"
  echo "the password vault and the database. It cannot be undone. The safe step first:  ./securax backup"
  printf 'Type ERASE to delete them, or anything else to keep them: '
  read -r _answer || _answer=""
  if [ "$_answer" != "ERASE" ]; then
    echo "[range] nothing was erased. Run this without --erase to stop everything and keep your data."
    exit 1
  fi
  VOLUMES=(-v)
fi
if command -v kind >/dev/null 2>&1; then kind delete cluster --name range || true; fi
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down ${VOLUMES[@]+"${VOLUMES[@]}"} ) || true
if [ "$ERASE" = 1 ]; then echo "[range] local plane stopped and its volumes erased."
else echo "[range] local plane stopped; your data is kept (start again with ./securax up)."; fi
echo "[range] Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
