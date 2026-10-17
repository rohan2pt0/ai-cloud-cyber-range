#!/usr/bin/env bash
# Static build for the product site at / and the documentation at /docs/ (any static host: Cloudflare Pages, GitHub
# Pages, Netlify, S3...). Brand, domain and contact address come from brand.env (or the environment), never from here.
#   Build command  bash website/build.sh   ·   output directory  website
set -euo pipefail
cd "$(dirname "$0")/.."
eval "$(python3 governance/config.py env)"           # BRAND_NAME, SITE_DOMAIN, CONTACT_EMAIL ... from brand.env
# {{SITE_DOMAIN}}, {{CONTACT_EMAIL}}, {{BRAND_NAME}} ... in the pages become your values (in this build checkout only).
python3 governance/config.py render $(find website -maxdepth 2 \( -name '*.html' -o -name '*.js' -o -name '_headers' \) -not -path 'website/docs/*')
pip install -q -r docs/requirements.txt
python3 docs/gen_cli_reference.py
export DOCS_SITE_URL="${DOCS_SITE_URL:-${SITE_DOMAIN:+https://$SITE_DOMAIN/docs/}}"
export DOCS_COPYRIGHT="${PRODUCT_NAME}${BRAND_NAME:+ by $BRAND_NAME} · MIT licence · no personal data in this repository"
mkdocs build --strict -d website/docs
echo "built: website/ (site) + website/docs/ (documentation) for ${SITE_DOMAIN:-<no SITE_DOMAIN set>}"
