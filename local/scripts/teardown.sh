#!/usr/bin/env bash
# Stop the local plane so nothing keeps running (or costing) overnight. Your data is KEPT: chats, private documents,
# downloaded models, the database, saved passwords.
#   ./local/scripts/teardown.sh           stop everything, keep the data
#   ./local/scripts/teardown.sh --erase   also delete that data (it asks you to type ERASE first)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VOL=()
case "${1:-}" in
  "") ;;
  --erase)
    echo "This deletes the estate's data on this machine: chats, private documents, downloaded models, the database, saved passwords."
    echo "It cannot be undone. The safe step first:  ./securax backup"
    printf 'Type ERASE to delete the data, or press Enter to keep it: '
    read -r _word || _word=""
    [ "$_word" = ERASE ] || { echo "Nothing was stopped and nothing was deleted."; exit 0; }
    VOL=(-v) ;;
  *) echo "Unknown option: $1   (no option = stop and keep your data;  --erase = also delete the data)"; exit 2 ;;
esac
if command -v kind >/dev/null 2>&1; then kind delete cluster --name range || true; fi
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai down ${VOL[@]+"${VOL[@]}"} ) || true
if [ "${#VOL[@]}" -gt 0 ]; then echo "[range] local plane stopped and its data deleted."
else echo "[range] local plane stopped. Your data is kept; start again with:  ./securax up"; fi
echo "[range] Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
