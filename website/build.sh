#!/usr/bin/env bash
# Cloudflare Pages build for cyberbaba.org: the product site at / and the documentation at /docs/.
#   Pages settings: build command  bash website/build.sh   ·   output directory  website
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -q -r docs/requirements.txt
python3 docs/gen_cli_reference.py
DOCS_SITE_URL="${DOCS_SITE_URL:-https://cyberbaba.org/docs/}" mkdocs build --strict -d website/docs
echo "built: website/ (site) + website/docs/ (documentation)"
