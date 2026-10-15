# 55 · The engineering standard: no claim without proof

A well-known critique of AI-built software goes like this. Someone gets a working prototype in twenty minutes and announces they
have replaced Slack. In fact the prototype is a fraction of a percent of the product. The rest is concurrency, consistency, ordering,
failure handling and years of edge cases.

SecuRAX is built with AI help too. This document is how it earns trust anyway. **We do not claim what we have not proven, we state
the conditions each claim holds under, and we say plainly what we do not do.**

## 1. The rule, and how it is enforced

| Rule | Mechanism |
|---|---|
| Every product claim names its proof | `governance/claims.json`: each claim has an **envelope** (the conditions it holds under) and **evidence** (a pytest function, a test script, or a sandbox journey that runs the real estate in CI) |
| A proof cannot quietly disappear | `./securax fitness` → `claims-proven`: fails if an envelope is empty, a referenced test or journey does not exist, or `not_claimed` is empty |
| The limits are written down | `not_claimed` in the same file (see section 4) |
| A change cannot hurt another part silently | `./securax impact` + the impact map (every tracked file has an owner and guarding journeys) |
| Tests must really test | `./securax forge gate`: fail-to-pass and mutation check on changed lines |
| Security is never traded for green | `BUILD-CONTRACT.md` hard rules; `diffcheck` blocks the mechanical ones |

## 2. What applying it found this time: the sync service

The only genuinely distributed part of SecuRAX is cross-device sync: phone, laptop and tablet, with offline edits and retries. It was
held to the properties a distributed system needs, using new stdlib-only tests (`apps/estate-sync/tests/test_sync_properties.py`).
Each defect below was reproduced **before** it was fixed.

| Property | Before | Fix |
|---|---|---|
| **No lost update** under concurrent writers | 8 writers × 25 keys: **175 of 200 keys lost** (read → merge → write without a lock; harmless with today's single worker, a data-loss bug the day a second worker or container is added) | one `BEGIN IMMEDIATE` write lock around read-merge-write: 200 of 200 |
| **Convergence**: same edits, any arrival order, same result | 39 of 40 random seeds gave an order-dependent result when two devices wrote the same key in the same millisecond | deterministic tie-break: the larger value by Unicode code point wins |
| **Server and phone agree on a tie** | the PWA kept its own value on a tie while the server kept the larger one: two devices could show different values for ever | the PWA uses the same rule (`cpAfter`, code-point order; JavaScript's own `<` gets emoji wrong); `guiding-map/tests/test20.js` and a server test check the same pairs |
| **Status files are never half-written** (found by the sandbox while this work was in review) | two cockpit refreshes at once left `cockpit.json` mixed ("Extra data"); the old write gave 2,266 broken reads in the contention test | write to a unique temp file, then rename (atomic): 0 broken reads |
| **Bad input is refused, not a crash** | a non-numeric timestamp raised an exception (HTTP 500) | validated: a clear 400; stored data unchanged |

The merge is now a last-writer-wins register per key. It is commutative, associative and idempotent, and the tests check each of these.

## 3. Claims (from `governance/claims.json`)

| Claim | Holds under | Proof |
|---|---|---|
| Sync converges in any order | per-key LWW (no per-item merge inside one key); clocks corrected by the server's Date header; one SQLite host | property tests + `test20.js` |
| Concurrent saves never erase each other | one SQLite file on local disk (not network storage) | 8-writer concurrency test |
| Cockpit and feed files are never half-written | one filesystem | contention test + journey `cockpit_page` |
| Malformed sync input is refused | bodies under the size limit | test |
| Update backs up and rolls back a bad release | clean checkout, Docker running | journey `safe_update_rollback` |
| Backups verify and restore (encrypted too) | this estate's volumes on one host | journeys `backup_restore`, `backup_encrypted` |
| Rails fail closed when a detector is offline | the gateway is the only model path | test + journey `purple_loop` |
| An answer is always possible (local floor) | the local model is small on a laptop | test + journeys `local_model_answers`, `key_wiring_and_failover` |
| Chat stays signed in across updates | `WEBUI_SECRET_KEY` kept in `.env` | journey `open_webui_chat` |
| A crashed service is restarted and reported | one host, `watch` running | journeys `self_healing`, `watchdog_heals_and_alerts` |
| The scale ladder never over-promises | planning output, not a load test | test |

## 4. What SecuRAX does **not** claim

- **No high availability or multi-region.** Every service runs once, on one host. A host outage is an outage; recovery is restore-from-backup.
- **The sync service doesn't scale across hosts.** It is one SQLite file: correct with many workers on that host, not across hosts.
- **Team chat at scale is not something SecuRAX built.** Presence, message ordering across thousands of users and search over billions of messages belong to Mattermost, an optional pinned organ.
- **No load-tested capacity** beyond the measured fitness budgets. The capacity planner is planning, not a benchmark.
- **Model quality is not guaranteed.** The rails reduce risk; they do not make answers correct.
- **No independent audit or certification** (SOC 2, ISO 27001) has been done.
- **Multi-tenant production (forest) is not built.** Manifests render and validate; billing, per-tenant SSO and operations are not built.

## 5. When you add something

1. Write the claim in `governance/claims.json` with its envelope.
2. Write the test or journey that proves it. For anything concurrent or distributed, test the property (order, concurrency, failure), not one happy path.
3. Reproduce a bug before fixing it, and keep the reproduction as a test.
4. Run `./securax fitness`. If the claim cannot be proven yet, it goes in `not_claimed`, not in the README.
