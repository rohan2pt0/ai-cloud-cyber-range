# The sandboxed REA (Reverse Engineer Anything, MIT, github.com/morluto/rea) used by `./securax inspect` and `./securax opencode --rea`.
# Built once from a LOCKFILE with integrity hashes and NO install scripts; run with no network, a read-only root, no capabilities, as a non-root user.
# The base image is pinned by digest (node:22-bookworm-slim); REA needs Node >= 22.19.
FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392
# REA refuses to start a JavaScript analysis without a procps-compatible `ps` on its PATH (it inspects process ownership).
RUN apt-get update && apt-get install -y --no-install-recommends procps && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/rea
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --omit=optional --no-audit --no-fund && npm cache clean --force
USER node
ENV HOME=/tmp NODE_ENV=production REA_DISABLE_UPDATE_CHECK=1
ENTRYPOINT ["node", "/opt/rea/node_modules/rea-agents/scripts/rea.mjs"]
