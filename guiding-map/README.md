# SecuRAX Guiding Map — the life-OS cockpit

The one screen you actually use every day. A self-contained, installable, **offline-first**
PWA that runs your whole personal operating system — and, inside SecuRAX, becomes the cockpit
for the estate.

**Eight pillars + antifragility index, OKRs, a cadence engine** (Sunday Pulse, Money Date,
quarterly review, Red Team, tax lock-in), **Never-Miss-Twice habits**, WOOP, After-Action
Review, **NIST CSF 2.0 self-score**, a **dynamic 5-stage wealth engine**
(PROTECT→AUTOMATE→EXPAND→SYSTEMIZE→MULTIPLY) computed live from your profile, property
economics, the consultant layer (SCQA, MECE issue trees, Bain RAPID, Three Horizons), drift
alarms, and a continuity/spouse-emergency page.

> **Your data lives only on your device** (browser storage). Nothing leaves it unless you turn
> on sync — and sync goes to **your own SecuRAX estate**, never a third-party SaaS.

## Files
```
index.html      the ENTIRE app, self-contained (ops.js inlined — open it anywhere, it runs)
ops.js          SOURCE of the ops layer — edit this, then `node build.js` to re-inline
build.js        re-inlines ops.js into index.html (keeps the single-file build honest)
sw.js           offline shell (network-first; cache fallback)
manifest.json   installable PWA metadata
icon-192.png / icon-512.png
tests/          jsdom behaviour suite + the python PII/secret gate
```

## Develop
```bash
# edit ops.js, then:
node build.js                      # re-inline into index.html (CI enforces they match)
npm install && npm test            # jsdom behaviour suite (test.js … test13.js)
python3 -m pytest guiding-map/tests/test_pii_gate.py   # PII + secret gate
```

## The PII / secret gate (why there are no personal needles here)
`tests/test_pii_gate.py` reuses the **estate's own guardrail detectors**
(`apps/llm-gateway/app/guardrails.py`) to scan every shipped file for India-BFSI PII and
leaked secrets (JSON web tokens, Supabase URLs and keys, VAPID, AWS, or private-key material).
It is **pattern-based**, so the
repo carries no personal-identifier list of its own — the successor to the old `test13.js` PII
scan, now safe for a public repo. CI fails if anything matches.

## Sync (sovereign, optional)
Cross-device sync talks to an endpoint on **your estate gateway** (Postgres-backed), reached
privately over **Tailscale** — see `docs/securax/14-GUIDING-MAP.md`. No keys live in these
files. The dated **JSON export** is always the real backup (3-2-1).

## Serve it
Locally it's served by the estate at `http://localhost:8088` (`./securax up`). Install it from
there on any device (Add to Home Screen / Install app) for a full-screen, offline cockpit.

## The one rule (kept from the original)
> New features require a month of daily use demonstrating the gap first. The failure mode of
> this project was never missing capability — it was **surface area**. When in doubt, subtract.
