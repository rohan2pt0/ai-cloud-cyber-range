# 36 · Identity, incident clock, data residency

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Gateway identity, incident clock and residency journeys. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Three controls built from the gaps in [doc 35](35-REGULATORY-GAP-ASSESSMENT.md). They are **regulator-agnostic by design**: the rules are data, so the same code serves an NBFC, a bank, a broker, an insurer, or an entity under another jurisdiction. Each is off (or inert) by default on a laptop and is switched on for a regulated deployment.

## 1 · Identity-aware gateway — `./securax gateway-auth`
Before: the gateway's "principal" was a hash of whatever `Authorization` string (or IP) arrived.
Now (`AUTH_MODE=off|optional|required`, default off):
- **Who**: a signed JWT from *any* OIDC provider (Keycloak, Entra ID, Okta, Auth0…) verified in the standard library (RS256; HS256 only with an operator secret; `alg:none` and key-confusion refused), and/or **hashed service API keys** (shown once, expiry, revocable).
- **What they may do**: roles `user`, `analyst`, `auditor`, `admin`, `service`, enforced per endpoint (chat, models, inspect, metrics); your IdP's roles are mapped with `AUTH_ROLE_MAP` and `AUTH_ROLES_CLAIM`.
- **How strongly**: `admin` and `auditor` need an MFA-proven token (`amr`/`acr` from your IdP); machine keys can never hold those roles.
- **Lock-out**: repeated failures from one source lock it out (default 5 in 5 min → 15 min), audited; the AI-SOC raises `auth-bruteforce`.
- **Audit**: every line carries the verified subject, roles, method, MFA flag and source address; refusals are audited with the reason.
- `./securax gateway-auth enable` creates the keys the estate's own callers need (Open WebUI, the CLI/agents); `key add|list|revoke|rotate`; `check-token JWT` explains why a token is accepted or refused (IdP setup).
- No new dependency: the gateway still has 3 runtime packages; the fitness budgets hold.
Limits: it protects the gateway, not the other consoles (Open WebUI, n8n, Grafana keep their own logins); lock-out state is per gateway instance; behind a reverse proxy the source address is the proxy's unless you handle it; n8n/Prometheus/the browser PWA need a service key configured by you.

## 2 · Incident clock — `./securax incident`
One detection starts **every applicable regulator's clock at once**; it computes due times (continuous clock, shown in your time zone), flags overdue (`incident due` exits 2 for cron/n8n), drafts each notification from the case facts and lists what is still missing, records each filing as on time or late, keeps a **hash-chained, tamper-evident** case log (`verify`), seals evidence with hashes, and prepares the periodic report inputs (`rollup`).
- Regulators are files in `governance/regulators/`: **verified** against primary text — `rbi-nbfc` (DAKSH, 6 h), `sebi-cscrf` (6 h e-mail, 24 h portal, brokers/DPs also to the exchange, quarterly within 15 days), `cert-in` (6 h). **Unverified** (secondary sources; flagged on every output) — `rbi-bank`, `irdai`, `dpdp`. Add any other regulator or jurisdiction by copying `custom.example.json`; chain follow-ups with `from: "after:<obligation>"`.
- The rule in force when a case is opened is frozen in the case, so later edits do not move its deadlines.
Limits: it is a clock and a drafting aid — **you file**; nothing integrates with DAKSH or the SEBI portal; it does not page anyone by itself (wire `incident due` to your alerting); deadlines are only as right as the rule file (check `verified`).

## 3 · Data residency — `./securax residency`
Rules are data (`governance/residency/<JURISDICTION>.json`; `IN.json` ships; copy `TEMPLATE.example.json` for another country or sector).
- **Gateway**: each request is classified (highest wins; a caller can raise the class, never lower it) from what is found in the text (Aadhaar, PAN, card numbers…), the caller's default class (`data_class` on a key/token) and the `X-Data-Class` header. Each model alias lives in a **zone** (`local`, an attested in-country zone, `global`; unknown = global). Data of a class goes only to allowed zones: **rerouted** to the local model or **refused**, before anything leaves. Model-based cloud detectors are not sent restricted text, and detectors now see only the *redacted* text. A test proves no local model alias ever falls back to a cloud one.
- **Lifecycle**: when enforced, `grow` refuses a cloud region outside the allow-list (India: AWS ap-south-1/2, GCP asia-south1/2, Azure central/south/west India, Jio India) and refuses a cloud the entity has not **attested** (`residency attest aws --ref '<MeitY empanelment / STQC audit reference>'`). SecuRAX cannot verify the empanelment: it records your assertion.
- `monitor` mode logs what would have happened without changing anything — start there.
Limits: it classifies by patterns, caller class and header; it cannot know that free text is confidential; remote compute (e.g. a GPU box) must be zoned honestly; backups and the SOC feed are not yet covered.

## Effect on the gap assessment
RBI NBFC 42.6 % → **47.1 %**, SEBI CSCRF 42.7 % → **47.3 %** (software scope). Six high-priority gaps became *partial* (never *supported*: the entity's identity provider, alerting, filing and attestations remain theirs). Remaining largest gaps: encrypted/immutable backups and ≤15-minute RPO, hash-chained audit log and signed evidence packs, the CCI, patch-SLA clock.
