#!/usr/bin/env bash
# Static build for the product site at / and the documentation at /docs/ (any static host: Cloudflare Pages, GitHub
# Pages, Netlify, S3...). Brand, domain and contact address come from brand.env (or the environment), never from here.
#   Build command  bash website/build.sh   ·   output directory  website
set -euo pipefail
cd "$(dirname "$0")/.."
eval "$(python3 governance/config.py env)"           # BRAND_NAME, SITE_DOMAIN, CONTACT_EMAIL ... from brand.env
# {{SITE_DOMAIN}}, {{CONTACT_EMAIL}}, {{BRAND_NAME}} ... in the pages become your values (in this build checkout only).
python3 governance/config.py render $(find website -maxdepth 2 \( -name '*.html' -o -name '*.js' -o -name '_headers' -o -name 'robots.txt' -o -name 'sitemap.xml' \) -not -path 'website/docs/*')
pip install -q -r docs/requirements.txt
python3 docs/gen_cli_reference.py
export DOCS_SITE_URL="${DOCS_SITE_URL:-${SITE_URL:+${SITE_URL}docs/}}"   # your domain once live, else GitHub Pages (doc 99)
export DOCS_COPYRIGHT="${PRODUCT_NAME}${BRAND_NAME:+ by $BRAND_NAME} · FSL-1.1-MIT (each release becomes MIT after two years) · no personal data in this repository"
mkdocs build --strict -d website/docs
python3 tools/linkcheck.py website        # every internal link and image on the built site must exist (doc 99)
echo "built: website/ (site) + website/docs/ (documentation) for ${SITE_URL:-<no address: set REPO_SLUG or SITE_DOMAIN>}"
