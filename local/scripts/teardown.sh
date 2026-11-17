#!/usr/bin/env bash
# Stop everything so nothing keeps running (and nothing keeps costing) overnight. Your data stays.
#
#   ./local/scripts/teardown.sh                # stop the containers and the kind cluster; every volume is kept
#   ./local/scripts/teardown.sh --erase-data   # ALSO delete every volume: chats, documents, workflows, the database.
#                                              #   It cannot be undone, so it asks you to type a word first.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ERASE=0
case "${1:-}" in
  "") ;;
  --erase-data) ERASE=1 ;;
  -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
  *) echo "Unknown option: $1   (see: ./local/scripts/teardown.sh --help)" >&2; exit 2 ;;
esac
VOL=()
if [ "$ERASE" = 1 ]; then
  echo "This deletes every SecuRAX volume on this machine: chats, documents, workflows and the database."
  echo "It cannot be undone. A backup first is one command:  ./securax backup"
  [ -t 0 ] || { echo "Not a terminal, so nothing was erased. Run it yourself and type the word when asked." >&2; exit 1; }
  printf 'Type  erase  to go on (anything else stops here): '
  read -r _word || _word=""
  [ "$_word" = erase ] || { echo "Nothing was erased."; exit 1; }
  VOL=(-v)
fi
if command -v kind >/dev/null 2>&1; then kind delete cluster --name range || true; fi
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down ${VOL[@]+"${VOL[@]}"} ) || true
if [ "$ERASE" = 1 ]; then echo "[range] local plane stopped and its data erased."
else echo "[range] local plane stopped. Your data is kept; start again with:  ./securax up"; fi
echo "Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
