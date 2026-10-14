# 39 · Growing from one person to many: live sync, team chat, and the scale ladder

You asked three things: did live push (WebSockets) get built, where is Mattermost, and what happens if this has to carry a team of 5, 50, 5,000 or 100,000 people. Straight answers first.

| Question | Answer |
|---|---|
| WebSockets for the Life OS PWA? | **Not before this change** (doc 38 listed it as skipped). Now built: `estate-sync` has `/sync/ws`; the Guiding Map listens and pulls the moment another device writes. If the socket is unavailable everything works as before (pull on open, push on edit). |
| Mattermost? | **Not integrated before.** Now a **dormant organ**: `./securax organ mattermost up` fetches the official Mattermost Docker setup at a pinned commit, generates the database password, binds to `127.0.0.1:8065`. Nothing runs until you ask. |
| 5 … 100,000 people? | `./securax capacity --people N` prints the tier, who you need, what to switch on, and a list of **gaps — things not built**. Tiers 1–250 are well covered; above that this repository is a blueprint, and says so. |

## Live sync (WebSocket)
- **Server** (`apps/estate-sync`): `WS /sync/ws`. The first message is `{"token","user"}` (browsers cannot set headers on a WebSocket, and a token in the URL ends up in logs). Bad token → closed with 4401; over `SYNC_MAX_SOCKETS` (100) → 4429; idle sockets are dropped after `SYNC_WS_IDLE_SECONDS` (90).
- **What travels**: only `{"type":"changed","updated_at","origin"}`. No data. The device then pulls through the same per-key merge as before, so a missed message costs latency, never data. The writer's own `origin` is ignored, so there is no echo loop.
- **Client** (`guiding-map/ops.js`): reconnects with back-off up to 60 s; stops when you turn sync off.
- **Limit**: the socket registry lives in one process and storage is SQLite, so run **one** estate-sync. Several replicas need Postgres plus a pub/sub bus first (listed as a gap in the ladder).

## Ops without chores: automatic daily backups and one-tap phone setup
Two things the Ops tab used to ask you to do are now done for you; the app is still local-first and works fully offline, so the estate is never a single point of failure.
- **Daily snapshots.** Whenever sync pushes, the sync service keeps that day's merged state as a snapshot, 30 days by default (`SYNC_SNAPSHOT_DAYS`). Ops → System health shows "Backed up automatically — N daily snapshots", with **See / restore a day** (restoring takes one undo snapshot first). Server-side snapshots live in the same database as the rest of your estate data, so `./securax backup` covers them; a downloaded file is still the extra copy that survives losing the estate.
- **One-tap setup.** `./securax sync-link` prints a link; opening it on a phone or second computer sets sync up after one confirmation. The sync address and device token sit after the `#`, which browsers never send to a server; the app shows **where the data will go** before saving, removes the token from the address bar immediately, and refuses to replace an existing setup without a second yes (a link is a phishing vector, so it is treated as one). Treat the link like a password.
- Not built on purpose: predictions and cross-domain "insights". They need weeks of your real data to be worth anything; use the estate for 30 days first.

## Mattermost as a dormant organ
Why an organ and not a default service: a solo operator does not need a chat server, and every running service is attack surface and RAM. It follows the same pinned-upstream pattern as Wazuh, MISP and TheHive: fetched at an exact commit, `shipped_defaults` makes the upstream's placeholder database password count as "unset" so a random one is generated, volumes are created owned by the container user, the port is localhost-only.
- **Edition**: configured for Team Edition (free, open source). Single sign-on beyond the basics and high-availability clustering have been tied to paid licensed editions; **confirm the current terms with the vendor before you plan around them** — they change, and we have not priced anything.
- **ChatOps**: `./securax notify digest` posts a plain-words digest (status, next three actions, regulatory deadlines due within 24 h) to any chat with an incoming webhook — Mattermost, Slack, Rocket.Chat. Set `SECURAX_NOTIFY_WEBHOOK` in `.env` (it is a secret). Plain `http://` is refused except to localhost, a private address, `.local`, or `.ts.net`. Only labels, counts and deadlines leave the box — never prompts, case narratives or tokens. `--only-bad` keeps it silent while everything is green. A failed send never prints the URL. Schedule it with cron or an n8n schedule node; nothing is scheduled for you.

## The ladder (`./securax capacity`)
| People | Shape | Humans | Mostly already built |
|---|---|---|---|
| 1–5 | one machine, Compose | you | safe update, backups, cockpit, live sync |
| 6–25 | one strong server | owner + deputy | sign-in (API keys/OIDC), audit, Mattermost organ, digest in chat |
| 26–250 | gateway replicas, k3s | 2–3 platform people, on-call | SSO via OIDC, tenant quotas/policies, KEDA, Prometheus, Falco/Kyverno (dormant) |
| 251–5,000 | Kubernetes cells per unit/tenant, GitOps | platform team + SOC | tenant chart, metering, Velero, residency, incident clock, SIEM organs |
| 5,001–100,000 | multi-region cloud | an SRE organisation | cloud genomes; the rest is a blueprint |

**The principle behind "least human intervention"**: a change is a pull request; updates are backup → pull → health gate → rollback; Dependabot raises the patches; the cockpit says what needs a human and ignores the rest. Adding people should add *roles* (who may do what, already enforced at the gateway), not manual steps.

### Honest gaps (not built; each is listed with its next step in `governance/scale-tiers.json`)
Per-person usage quotas · SCIM joiner/mover/leaver · shared pub/sub for multi-replica live sync · Postgres pooling/read replicas · central log + trace backend (W3C trace context is already propagated) · canary/blue-green · multi-region active-active · a dedicated GPU inference tier · FinOps budgets · SLO tooling. The tests enforce that every "have/dormant" claim points at a file that exists and every gap states its next step, so the ladder cannot drift into marketing.
`./securax capacity --bench` measures the guardrail engine on your machine. Model throughput, not the guardrails, will be the limit; size that with your own load test before promising anything to anyone.

## Supply-chain visibility in CI
`.github/workflows/scorecard.yml` runs OpenSSF Scorecard weekly and on `main` and uploads to code scanning; the score is a to-do list, not a security guarantee. `publish-images.yml` now attaches a signed SLSA build-provenance attestation to each released image (verify with `gh attestation verify`). Neither has run yet: the first release tag (`git tag v0.1.0 && git push origin v0.1.0`) is the first real test, and the Scorecard badge needs a public repository.
