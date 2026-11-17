#!/usr/bin/env bash
# Stop everything so nothing keeps running (and nothing keeps costing) overnight. Your data is KEPT: chats, private
# documents, workflows, the password vault and your synced Life OS data live in Docker volumes, and this leaves them alone.
#   ./local/scripts/teardown.sh           stop the estate and the Kubernetes practice cluster (the cluster holds no data of yours)
#   ./local/scripts/teardown.sh --wipe    ALSO erase every volume. It cannot be undone, so it asks you to type a word first.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
case "${1:-}" in
  "") VOLS="" ;;
  --wipe)
    echo "This erases ALL SecuRAX data on this machine: chats, private documents, workflows, the password vault and your synced Life OS data."
    echo "Take a backup first:  $ROOT/securax backup"
    printf 'Type  erase  to go on (anything else stops here and keeps your data): '
    read -r _word || _word=""
    [ "$_word" = erase ] || { echo "Nothing was erased."; exit 0; }
    VOLS="-v" ;;
  *) echo "Unknown option: $1   (use no option to stop and keep your data, or --wipe to erase it)"; exit 2 ;;
esac
kind delete cluster --name range || true
( cd "$ROOT/local/compose" && docker compose --profile core --profile security --profile ai --profile passwords --profile online --profile studio down $VOLS ) || true
if [ -n "$VOLS" ]; then echo "[range] stopped, and every volume erased."
else echo "[range] stopped. Your data is kept; start again with:  $ROOT/securax up"; fi
echo "[range] Cloud resources (if any) are torn down with: cd infra/terraform/environments/lab && terraform destroy"
