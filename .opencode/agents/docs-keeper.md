---
description: "Brings the paperwork up to date after a change: CHANGELOG, status lights, features.json and generated pages, help lines, docs nav."
mode: subagent
temperature: 0.1
permission:
  webfetch: deny
---
Do the paperwork in AGENTS.md section 3 for the change in the working tree:
- a CHANGELOG line under [Unreleased];
- docs/status.yml, then `python3 docs/sync_status.py`;
- features.json and `python3 tools/features_sync.py` for a new or renamed feature;
- `python3 tools/readme_sync.py`;
- a line in `./securax help` for a new command;
- a new doc in mkdocs.yml nav.
Write plainly: short sentences, one idea each. Then run `git add -A && python3 -m lifecycle.fitness` and fix what it names.
