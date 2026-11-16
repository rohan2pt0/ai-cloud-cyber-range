#!/usr/bin/env bash
# The open models build a task inside THIS machine (a Claude cloud session or a laptop), the same loop as autobuild.yml:
# OpenCode Go models -> the estate's gates -> retry -> a commit only when green. It is the second path, so a missing GitHub
# secret or a busy Actions queue never stops the work (the third is Claude itself, the fourth ./securax autobuild on local models).
#   bash lifecycle/delegate_here.sh "task in plain words" [tries]
# The key: OPENCODE_GO_API_KEY from the environment, or, in a Claude cloud session, a network secret saved once for
# opencode.ai (the proxy puts it on each request, so a placeholder is enough here and the key never touches the disk).
# It builds in a throwaway worktree of origin/main, so your branch is never touched. When green it pushes the branch
# autobuild/<slug>-here-<time> and prints PUSHED <branch>; the caller opens the PR. Exit 0 green, 1 red, 2 cannot start.
set -euo pipefail
TASK="${1:?usage: bash lifecycle/delegate_here.sh \"task\" [tries]}"
TRIES="${2:-3}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# A brief one model can finish alone is one step: short, its test named, no slow audit (.claude/skills/delegate/GOLDEN-BRIEF.md).
# Stop here, in a second, rather than after an hour of a model reading and planning. DELEGATE_FORCE=1 sends it anyway.
if [ "${DELEGATE_FORCE:-0}" != 1 ] && ! why="$(TASK="$TASK" python3 lifecycle/autobuild_ci.py check)"; then
  echo "CANNOT-START the brief is not one a model can finish alone:"; echo "$why"
  echo "Rewrite it from .claude/skills/delegate/GOLDEN-BRIEF.md (or send it as it is with DELEGATE_FORCE=1)."; exit 2
fi

command -v opencode >/dev/null 2>&1 || npm install -g -s opencode-ai@1.19.0 >/dev/null 2>&1 || {
  echo "CANNOT-START opencode could not be installed (npm blocked?)"; exit 2; }
export OPENCODE_GO_API_KEY="${OPENCODE_GO_API_KEY:-placeholder-the-proxy-adds-the-real-key}"
# the gates need what CI installs first (the gateway's packages, ruff); without them a correct change fails on an import
python3 -c "import fastapi, httpx, ruff" >/dev/null 2>&1 || python3 -m pip install -q -r "$ROOT/apps/llm-gateway/requirements-dev.txt" pyyaml ruff >/dev/null 2>&1 || {
  echo "CANNOT-START the gate's Python packages could not be installed"; exit 2; }

BASE="${DELEGATE_BASE:-origin/main}"   # a branch whose fixes are not merged yet can be the base
# two runs started together race for the same ref lock: retry the fetch a few times before giving up
for _try in 1 2 3 4; do git fetch -q origin "${BASE#origin/}" && break; sleep $((_try * 3)); done
WT="$(mktemp -d)/build"
git worktree add -q --detach "$WT" "$BASE"
trap 'git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1 || true' EXIT
cd "$WT"
# the Life OS tests need jsdom: a fresh worktree has none, and the model lost minutes finding that out and installing it
if [ -f guiding-map/package-lock.json ] && command -v npm >/dev/null 2>&1; then
  ( cd guiding-map && { npm ci --silent >/dev/null 2>&1 || npm install --silent >/dev/null 2>&1; } ) || echo "note: guiding-map packages not installed; the model will have to"
fi

cfg="$(mktemp)"
python3 lifecycle/autobuild_ci.py config > "$cfg"
export OPENCODE_CONFIG="$cfg" BUILD_MODEL=ci AUTOBUILD_AGENT="python3 lifecycle/autobuild_ci.py agent" TASK
export GIT_AUTHOR_NAME="SecuRAX autobuild" GIT_AUTHOR_EMAIL="autobuild@securax.local" GIT_COMMITTER_NAME="SecuRAX autobuild" GIT_COMMITTER_EMAIL="autobuild@securax.local"
start="$(git rev-parse HEAD)"
echo "delegate_here: started $(date -u +%H:%M) UTC on $BASE; a model silent for 6 min while it runs nothing is stopped, one running a command is not"
set +e; bash ./securax autobuild "$TASK" --tries "$TRIES" --force; rc=$?; set -e
if [ "$rc" != 0 ] || [ "$(git rev-parse HEAD)" = "$start" ]; then
  echo "RED after $TRIES tries (rc=$rc). The brief for a stronger model follows, if one was written."
  [ -f escalation-brief.md ] && tail -n 40 escalation-brief.md || true
  exit 1
fi
br="autobuild/$(python3 lifecycle/autobuild_ci.py slug)-here-$(date -u +%Y%m%d%H%M)"
git push -q origin "HEAD:refs/heads/$br"
echo "PUSHED $br"
