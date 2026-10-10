# SecuRAX — The Guiding Map (the life-OS cockpit)

The Guiding Map is the one screen you use every day, and now the **cockpit for the whole
estate**. It began as a standalone, battle-tested life-OS PWA (v13, 69/69 tests green) and has
been folded into SecuRAX as the human-facing front door — kept local-first, sovereign, and
offline, with its Cloudflare/Supabase deployment model replaced by estate-native equivalents.

## What it is
A self-contained, installable PWA (`guiding-map/`) — `index.html` carries the entire app
(`ops.js` inlined by `build.js`), so it runs even if only that one file reaches a device. It
holds:

- **Eight pillars + an antifragility index** (fragile → robust → antifragile), with a North-Star
  forecast and a KGI→KPI→KAI→KRI→OKR→BSC metric hierarchy.
- **A cadence engine** — Sunday Pulse, Money Date, quarterly review, Red Team, April tax
  lock-in, August overhaul — each computes its own due date and pins to Today.
- **Never-Miss-Twice** habits (EMA strength + a 2-miss/month error budget), **WOOP** goal
  setting, **After-Action Review** with spaced resurfacing (7→14→28).
- **NIST CSF 2.0 self-score** (Govern→Recover), so the Security pillar is governed like the rest.
- **A dynamic 5-stage wealth engine** (PROTECT→AUTOMATE→EXPAND→SYSTEMIZE→MULTIPLY) computed
  live from your profile — EF 6× essentials, FIRE 25× annual, term 10–15× income, 20% savings
  gate, an avalanche list from your own loans, an 80/20 side-income ladder, risk-capped sleeves.
- **The consultant layer** — SCQA/Pyramid, MECE issue trees on drift alarms, Bain RAPID
  (household decision rights), Three Horizons — each placed at the moment a decision is made.
- Property economics, money-flow, continuity/spouse-emergency page, undo, system health.

First run seeds a **neutral EXAMPLE household** (clearly badged), so every tab is explorable
before you enter anything of your own.

## How it joined SecuRAX (what changed, and why)
| Original (standalone) | In SecuRAX | Why |
|---|---|---|
| Supabase sync (3rd-party SaaS, anon key in file) | **Estate sync endpoint** over Tailscale | sovereignty, zero-trust, no SaaS dependency |
| Cloudflare Pages + Access deploy | Served **locally** by the estate (nginx :8088) | local-first; optional remote later |
| `test13.js` PII scan with personal needles | **Pattern-based gate** reusing estate guardrails | a public repo must carry **no** personal data |
| Cloudflare Worker push nudges | Dormant (optional) | push needs a server; phone alarms are more reliable |

Nothing of the life-OS logic was lost — only the *plumbing* was swapped for estate-native,
sovereign equivalents. No secrets or PII live in any shipped file; CI enforces it.

## Cross-device sync — the sovereign fix (replacing Supabase)
The problem a PWA has: each device keeps its own `localStorage`, so something always-reachable
must be the shared rendezvous. The estate solution, in order of preference:

1. **Estate sync endpoint + Tailscale (shipped).** The `estate-sync` service
   (`apps/estate-sync`, in every compose profile) stores one per-user document in a **SQLite
   file on the `estatesync` volume** — your box only, no third party, zero external DB to go
   wrong. It is deliberately *not* on the gateway: the gateway is a read-only LLM policy
   enforcement point, and a writable state store has no business sharing that trust boundary.
   The app's **per-key timestamp merge** (integrity guard that refuses a merge which would halve
   your data; server-anchored clock) talks to it over plain fetch, and the **server merges
   per-key too** — so even if two devices race or a stale device pushes a whole blob, a field
   is overwritten only by a *newer* copy and existing keys are never silently dropped.
   Reach it over **Tailscale** (WireGuard mesh, free personal tier): every device gets a private
   IP, the endpoint is **never exposed to the internet**, access is identity-based.

   **Set it up (5 minutes):**
   ```bash
   # 1. generate one random device token per device, put them in local/compose/.env:
   #    SYNC_TOKENS=$(openssl rand -hex 24),$(openssl rand -hex 24)
   # 2. let other devices reach it — set SYNC_BIND to THIS host's Tailscale IP:
   #    SYNC_BIND=100.x.y.z        (localhost-only by default; never 0.0.0.0 unless you mean LAN)
   # 3. bring it up:  docker compose --profile ai up -d estate-sync
   # 4. install Tailscale on the host + each device, same tailnet
   ```
   Then in the PWA, **Ops → Cross-device sync**: URL `http://<tailscale-ip>:8089/sync`,
   paste the device token, pick a row id (anything, same on every device).
   Contract the endpoint implements (`apps/estate-sync/syncsvc/main.py`):
   ```
   HEAD {base}/                  -> 200  (its Date header anchors the client clock)
   GET  {base}/state?user=<id>   -> { payload:{k:v}, meta:{k:ts}, updated_at }  (404 if none)
   PUT  {base}/state?user=<id>   body { payload, meta, updated_at }  -> server-side merged
   Auth: Authorization: Bearer <device token>   (fail-closed: no SYNC_TOKENS -> 503, refuses all)
   ```
2. **CouchDB + PouchDB** — if you later want bulletproof multi-master conflict handling (MVCC).
   A *new* component, added only if the per-key merge proves insufficient. For a single human
   on a handful of devices, the shipped SQLite + dual-side merge is already ample.
3. **Syncthing** — for the dated JSON backups (P2P, no server), not for live state.

**The one real-world choice:** any option needs an always-on reachable host, since a laptop
sleeps. Either a small always-on box at home (Raspberry Pi / repurposed laptop, ~one-time cost)
or a **free Oracle Cloud ARM VM** — both keep it *your* service. Or accept "syncs when the host
is up," which matches the FREEZE rule below (phone = daily, laptop = monthly/quarterly). The
sync code is host-agnostic; you choose where it runs. **Export/Import JSON is always the
backstop** — the dated backups are your real version history.

> Sync is **live** (Phase 3 done): the `estate-sync` service implements the contract above, with
> server-side per-key merge and fail-closed Bearer auth, covered by `apps/estate-sync/tests`.

## The merge roadmap
- **Phase 1 (done):** the cockpit lives in the estate, Supabase stripped, PII/secret gate +
  jsdom suite in CI, served locally, neutral seed.
- **Phase 2:** re-add the SecuRAX superpowers as cockpit tabs — **Ask** (local LLM via the
  guardrail gateway), **Intel** (Global Intelligence, doc 13), **Guard** (guardrail PII
  redaction), **Launch** (estate). *(These were in the earlier lightweight Guiding Map and
  rejoin here as first-class tabs.)*
- **Phase 3 (done):** the sovereign `estate-sync` endpoint (SQLite, server-side merge,
  fail-closed Bearer auth) + Tailscale, host-agnostic.

## Build & test discipline
`ops.js` is the source; `index.html` is the built artifact. CI runs a **drift guard**
(`node build.js` must leave `index.html` unchanged), the **jsdom behaviour suite** (boot, every
tab renders, XSS-escaping, no NaN/Infinity, undo, EMA, drift alarms, dynamic playbook), and the
**PII/secret gate**. Bump `sw.js` `CACHE` on every change so installed devices pick it up.

## The freeze rule (kept, because it is the point)
> New features require a month of daily use demonstrating the gap first. The failure mode of
> this project was never missing capability — it was **surface area**. When in doubt, subtract.

The five things that can rot on their own and the annual 15-minute overhaul are tracked per the
original FREEZE discipline; in the estate, the Supabase/Cloudflare items are replaced by "is the
estate gateway reachable and backed up."
