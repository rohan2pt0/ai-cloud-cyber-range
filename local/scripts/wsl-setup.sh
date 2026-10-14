#!/usr/bin/env bash
# SecuRAX one-paste installer for Windows (run INSIDE Ubuntu/WSL):
#   curl -fsSLo wsl-setup.sh https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/local/scripts/wsl-setup.sh && bash wsl-setup.sh
# (saved to a file first, not piped into a shell, so it can be read before it runs)
# Why inside WSL's own disk: the Windows drives (/mnt/c, /mnt/e) are several times slower for Docker bind mounts.
# Safe to re-run: it updates, keeps your keys (.env), keeps downloaded models (Docker volumes), and tells you
# the exact fix for anything missing instead of failing obscurely.
set -uo pipefail
C(){ printf '\033[1;36m%s\033[0m\n' "$*"; }
DEST="${SECURAX_HOME:-$HOME/securax}"
REPO="${SECURAX_REPO:-https://github.com/rohan2pt0/ai-cloud-cyber-range.git}"

grep -qi microsoft /proc/version 2>/dev/null || C "(Not WSL — continuing anyway; this also works on plain Linux.)"

# 1) Docker reachable from here?
if ! docker info >/dev/null 2>&1; then
  C "STOP — Docker isn't reachable from Ubuntu. Do this once, then paste the install line again:"
  echo "   1. Start Docker Desktop (Windows Start menu) and wait until it says 'Engine running'."
  echo "   2. Docker Desktop > Settings (gear) > Resources > WSL integration > turn ON 'Ubuntu' > Apply & restart."
  exit 1
fi

# 2) tools (apt needs your Ubuntu password once)
need=""; for t in git python3 curl; do command -v "$t" >/dev/null 2>&1 || need="$need $t"; done
if [ -n "$need" ]; then
  C "Installing:$need (Ubuntu will ask for your password — typing is invisible, press Enter)"
  sudo apt-get update -qq && sudo apt-get install -y -qq $need || { C "Could not install$need. Run:  sudo apt-get update && sudo apt-get install -y$need"; exit 1; }
fi

# 3) get/refresh the code (public repo: no login needed)
if [ -d "$DEST/.git" ]; then
  C "Updating $DEST …"
  git -C "$DEST" diff --quiet -- local/compose/litellm-config.yaml 2>/dev/null || git -C "$DEST" checkout -- local/compose/litellm-config.yaml
  git -C "$DEST" pull --ff-only || { C "git pull failed. Fix: rm -rf '$DEST' (your keys are copied again from the old folder) and re-run."; exit 1; }
else
  C "Downloading SecuRAX to $DEST …"
  git clone --depth 50 "$REPO" "$DEST" || { C "Download failed — check your internet, then re-run."; exit 1; }
fi

# 4) keep your keys: copy .env from a previous Windows-drive install, if there is one
if [ ! -f "$DEST/local/compose/.env" ]; then
  OLD="${SECURAX_OLD:-}"
  [ -z "$OLD" ] && for d in /mnt/?/DockerData/ai-cloud-cyber-range /mnt/?/*/ai-cloud-cyber-range /mnt/?/ai-cloud-cyber-range; do
    [ -f "$d/local/compose/.env" ] && { OLD="$d"; break; }
  done
  if [ -n "$OLD" ] && [ -f "$OLD/local/compose/.env" ]; then
    cp "$OLD/local/compose/.env" "$DEST/local/compose/.env" && C "Kept your settings and keys from $OLD"
  fi
fi

# 5) stop any older copy (same Docker project name; models + data volumes are KEPT), then start
( cd "$DEST/local/compose" && docker compose --profile ai down >/dev/null 2>&1 ) || true
cd "$DEST" || exit 1
chmod +x securax 2>/dev/null || true
./securax shortcut >/dev/null 2>&1 || true      # from now on you can type `securax <command>` from any folder
./securax up
rc=$?
if [ $rc -ne 0 ]; then
  C "Start-up needs attention — see the message above. Next:  cd ~/securax && ./securax doctor"
  exit $rc
fi
echo
C "DONE. Your Command Center opens in the browser (if not:  cd ~/securax && ./securax open  - it prints the right address)."
C "Next (2 minutes, makes answers instant):   cd ~/securax && ./securax keys"
