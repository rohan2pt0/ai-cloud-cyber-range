# 37 · Cockpit, storage growth, patching, impact

For the person who does **not** want to read logs: one page that says whether things are fine, one report that says where the files are going, one safe way to update, and one command that says what a change can hurt. None of it adds a service, a port, a script or a login.

## The cockpit — `./securax cockpit`
Writes `portal/cockpit.html` (served at `http://localhost:8088/portal/cockpit.html`, linked from the Command Center; also refreshed by `./securax up`). It is a **snapshot**, stamped with its time. It contains no script and makes no external request (a test proves it).

| Section | What it answers | Where the numbers come from |
|---|---|---|
| Headline + *Do next* | Is it OK, and what are the three things to do? | worst status across the vital signs; urgent+important items first |
| **Vital signs** (KPI = doing its job, KRI = risk building up) | services healthy, gateway answering, who may call it, where sensitive data may go, key expiry, latest backup, free disk, days until full, oldest running software, threat-data age, incident clocks, requests/refusals in 24 h, engineering promises, compliance coverage | docker, the gateway's `/healthz` and audit log, `.env`, `storage`, `incident`, `fitness`, the maps |
| **Eisenhower** | urgent × important → *Do now / Schedule / Automate / Park* | urgent = a deadline or measured problem; important = moves risk or compliance most |
| **80/20** | which few themes close most of the weighted gap | all maps' backlogs weighted by priority (gap 1.5×), grouped by theme; the highlighted bars are the first ~80 % |
| **Maturity radar** | NIST CSF 2.0 categories (SEBI CSCRF is built on them): target vs *designed* (a mechanism exists) vs *demonstrated* (a test/journey proves it) | the SEBI CSCRF map; organisational duties are not scored |
| **AI-specific risk** | MIT AI Risk Repository domains and NIST AI 600-1 categories | `comply mit-ai-risk`, `comply nist-ai-600-1` |
| Trends | coverage, free disk, things needing action | history kept in `~/.securax/cockpit-history.jsonl` (needs a few days) |

`--ai` adds a short plain-English briefing written by your **local** model from the numbers (labelled a draft; it never changes a status). Thresholds live in `governance/cockpit.json`. `SECURAX_PROFILE=regulated` (or `./securax regulated on`) makes open sign-in and missing residency red; on a laptop they are "no data".
Honest limits: it shows only what this machine can see (not running = *No data*, never *OK*); green means "nothing measured is wrong", not "secure"; radar scores are our own assessment, not an audit; it does not update itself — run `./securax cockpit`.

## Where the files are, and how they grow — `./securax storage`
| What | Where | Grows? | Policy |
|---|---|---|---|
| Databases, chats, workflows, **model store** | Docker volumes | slowly; the model store is the big one | keep one or two models; `storage` flags any volume over 5 GB |
| Backups | `./backups` (or `SECURAX_BACKUP_DIR`) | one archive per backup | newest `BACKUP_KEEP` (default 7) kept; **copy one off the machine** (3-2-1) — a backup on the same disk is not a backup |
| Incident cases, offline threat data, history | `~/.securax` | very slowly | small; cases are append-only logs |
| Docker images and build cache | Docker | after every update | `storage --tidy` removes dangling images and old build cache; never volumes |
| Container logs | Docker | **bounded** | rotate by themselves (10 MB × 3 per container) |
`storage` reports sizes and free space, records a reading at most every 12 h, and forecasts the day the disk fills (needs 3 readings over 2+ days; says "learning" until then). It never deletes volumes or backups.

## Patching — what gets patched, how, and by whom
| Component | Mechanism | Your part |
|---|---|---|
| SecuRAX's own code | **`./securax update`**: backup → pull → recreate → check the estate really starts → **automatic rollback** to the version that worked (exit 3) if it does not | run it weekly |
| Third-party images (compose tags), Python, npm, GitHub Actions, Docker, Terraform providers | **Dependabot** opens pull requests (weekly; Terraform monthly); the sandbox and CI must pass before merge | merge when green, then `./securax update` |
| Pinned installers (k3s, helm, kind, kubectl, Tailscale) | version- and hash-pinned; a change is a reviewed commit | re-pin with the commands in the files when you bump a version |
| Local AI models | `./securax pull`; `./securax bench` says which installed model fits this machine | occasionally |
| Threat data (KEV, ATT&CK) | `./securax offline sync` | monthly (the cockpit warns at 14/45 days) |
| Third-party skills/plugins | `./securax vet` before use; re-vet on every bump | when adding one |
| Your OS, WSL, Docker Desktop | your operating system's updates | yes |
A suggested rhythm: **weekly** merge Dependabot PRs + `update`; **monthly** `offline sync` + look at the cockpit's "oldest running software"; **quarterly** restore drill + rotate keys; **half-yearly** disaster-recovery drill (`./securax gameday all`). `./securax rhythm` is where these are scheduled.
What the safe update does **not** do: roll back *data* (a code update does not touch your volumes; the pre-update backup is printed so `./securax restore` is always available) and it only rolls back automatically when your checkout had no uncommitted changes.

## What can this change hurt? — `./securax impact`
`lifecycle/impact.json` maps every tracked file to a component, what each component feeds, and which real-product journeys guard it. `./securax impact` turns your diff into: components touched → also affected downstream → the exact `sandbox/run.py -j …` line to re-prove it; a touched component with no guarding journey is called out as a **blind spot**. `fitness` fails if a file has no owner or a named journey does not exist, so the map cannot rot.

## Following one request
Every AI request carries a W3C `traceparent` from the caller through the gateway to the router (a valid inbound one is continued, otherwise a trace is started), is echoed in the response with `X-Request-ID`, and is named in the audit line (`trace_id`). Any OpenTelemetry-compatible tool can follow it; no SDK or dependency was added.

## How "Do now" and "Next 3" are ordered

Inside every Eisenhower quadrant the order is: **red before amber**, then **more important first**, then a **live vital
sign before a backlog item**, and for backlog items **high before medium**. "Next 3" reads the top of Do now, then
Schedule, so this order is the advice. A gap reported by two regulatory maps appears once.
Tests: `governance/tests/test_cockpit_priority.py`.
