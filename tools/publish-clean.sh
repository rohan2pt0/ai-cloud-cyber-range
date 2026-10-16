#!/usr/bin/env bash
# Publish SecuRAX under a brand GitHub organisation as a FRESH repository with no history (doc 61), so the public
# project carries the brand, not a person. Your own repository stays as it is (make it private afterwards).
#   tools/publish-clean.sh <github-org> [repo-name]        e.g.  tools/publish-clean.sh cyberbaba securax
set -euo pipefail
ORG="${1:?usage: tools/publish-clean.sh <github-org> [repo-name]}"; REPO="${2:-securax}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mktemp -d)/$REPO"; mkdir -p "$OUT"
git -C "$ROOT" archive HEAD | tar -x -C "$OUT"          # committed files only: nothing from .env, vault or backups
cd "$OUT"
rm -f tools/publish-clean.sh                           # this script names the private source; it stays private
# Point every link, badge and code owner at the new home.
grep -rlI "rohan2pt0/ai-cloud-cyber-range" . | xargs -r sed -i "s#rohan2pt0/ai-cloud-cyber-range#$ORG/$REPO#g" || true
grep -rlI "rohan2pt0.github.io/ai-cloud-cyber-range" . | xargs -r sed -i "s#rohan2pt0.github.io/ai-cloud-cyber-range#cyberbaba.org/docs#g" || true
grep -rlI "@rohan2pt0" . | xargs -r sed -i "s#@rohan2pt0#@$ORG/maintainers#g" || true
grep -rlI "ghcr.io/rohan2pt0" . | xargs -r sed -i "s#ghcr.io/rohan2pt0#ghcr.io/$ORG#g" || true
grep -rlI "github.com/rohan2pt0" . | xargs -r sed -i "s#github.com/rohan2pt0#github.com/$ORG#g" || true
# Refuse to publish while anything personal is left.
if grep -rnIiE "rohan|choudhari|nabard" . ; then echo "✗ personal identifiers remain (listed above); nothing published."; exit 1; fi
git init -q -b main
git -c user.name="CyberBaba" -c user.email="${BRAND_EMAIL:-hello@cyberbaba.org}" add -A
git -c user.name="CyberBaba" -c user.email="${BRAND_EMAIL:-hello@cyberbaba.org}" commit -qm "SecuRAX: public release"
echo "✔ clean copy ready: $OUT (one commit, author CyberBaba)"
echo "Next: create the EMPTY repository github.com/$ORG/$REPO (no README), then:"
echo "  cd $OUT && git remote add origin https://github.com/$ORG/$REPO.git && git push -u origin main"
echo "Then on github.com/$ORG: create the team 'maintainers', add yourself, and set your organisation membership to private."
