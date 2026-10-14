# Vendored third-party content — agent-skills (Addy Osmani)

- Source: https://github.com/addyosmani/agent-skills  ·  commit `aeac41d4d005999432bb7312f7ff06383a91d59d`  ·  licence MIT (see LICENSE; the notice must stay)
- Vendored: `skills/security-and-hardening`, `skills/code-review-and-quality` only. **Hooks, scripts and every other skill were deliberately NOT copied** (hooks run commands with your privileges).
- Gate: `./securax vet verify` proves this folder still hashes to what was vetted (`vendor/vetted/agent-skills.json`); `./securax escalate` includes it only when it does.
- Update: `./securax vet check <url> --ref <commit> --accept --vendored vendor/agent-skills --note "<what you read>"`, re-copy, re-vet. Never edit these files in place.
- Why the vet verdict was REVIEW: the repo ships agent hooks (not vendored) and two OTHER skills (not vendored) quote attack strings to teach agents to ignore them. Read in context: defensive text, not an attack.
