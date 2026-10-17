# 63 · Engineering resilience audit: the backend fundamentals, checked against SecuRAX

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Every row marked built names the test that proves it; the not-applicable rows name the trigger to build them. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

A checklist of distributed-systems fundamentals (from a widely shared list by a principal engineer, plus the classic
reliability patterns), each one checked against the real code. **N/A** means the pattern solves a problem SecuRAX does not
have at its current size (one gateway, one SQLite sync store, no message broker); it is listed so that the reason is
written down, not forgotten.

## Built in this change

| Concept | What was missing | What is there now | Proof |
|---|---|---|---|
| **p95 / p99 latency, "averages lie"** | `/metrics` exposed only a sum and a count, so only an average could be computed | a Prometheus **histogram** (`guardrail_request_latency_ms_bucket`, 12 buckets up to 300 s) and **`GET /v1/latency`** with p50 / p95 / p99 of the last 1,000 model calls; the average is shown only next to them | `test_latency_histogram_and_percentiles_are_exposed`, `test_percentile_is_the_tail_not_the_average` |
| **Connection pooling** | a new HTTP client (and TCP/TLS handshake) for every model call, readiness check and model list | one pooled client with keep-alive (64 connections, 16 idle, 30 s expiry); each call keeps its own timeout | `test_one_pooled_http_client_is_reused` |
| **Backpressure / load shedding** | no limit on concurrent model calls: a slow CPU model let requests pile up until all of them timed out | at most `MAX_INFLIGHT` (8) model calls at once; a request waits up to `QUEUE_WAIT_S` (20 s) for a slot, then gets a fast **503 + `Retry-After: 10`**; counted as `shed_overload`, `guardrail_inflight` gauge | `test_overload_is_shed_fast_with_retry_after` |
| **Circuit breaker** | a dead detector (Llama Guard, Model Armor, Bedrock) made *every* request wait for its timeout | per-detector breaker: open after 3 failures in a row, skipped for 30 s, then one half-open trial. The verdict is unchanged (fail-closed still blocks); only the waiting is gone | `test_circuit_breaker_skips_a_dead_detector_then_retries_after_cooldown` |
| **Rate limiting: tell the client when** | the 429 had no `Retry-After` | `429` now carries `Retry-After: 60` | `test_rate_limited_reply_says_when_to_retry` |
| **Retry with backoff + jitter** | a phone alert that hit a network blip was lost | 3 attempts, `0.5 s × 2ⁿ` plus random jitter, so senders do not retry in lockstep | `test_retry_backs_off_with_jitter_then_succeeds` |
| **Dead-letter queue, at-least-once delivery** | a failed alert was dropped | an alert that still fails is kept in `vault/notify-dlq.jsonl` (newest 50, owner-only) and re-sent, marked "(delayed)", before the next alert | `test_an_alert_that_cannot_be_sent_is_kept_and_resent_first_next_time` |

## Already in place

| Concept | Where |
|---|---|
| **Timeouts** | gateway upstream timeout (`UPSTREAM_TIMEOUT`), short cloud-rung timeouts and a long local-rung timeout in the router (doc 15), 3–5 s on health and auth calls |
| **Retries and failover in the model path** | the router's `retry_policy`, `allowed_fails_policy` and cooldown (a breaker per provider), and the ladder that ends on a local model |
| **Graceful degradation** | the local model floor; detectors fail-closed or fail-open by policy; optional add-ons simply show grey |
| **Bulkheads** | per-container memory and CPU limits in `docker-compose.yml`; the local model is capped so it cannot starve Chat |
| **Rate limiting** | per caller, per minute (`RATE_LIMIT_PER_MIN`) |
| **Correlation IDs + tracing** | W3C `traceparent` kept or started on every request, `X-Request-ID` echoed, both in the audit line |
| **Idempotency** | sync uses per-key timestamps with a deterministic tie-break, so replaying the same push changes nothing; backups and restores are verified by checksum before use |
| **Optimistic concurrency** | the sync merge: newest write per key wins, ties broken the same way on every device (tested in the app's test20) |
| **SLOs / error budgets** | fitness budgets on every build: time to first block ≤ 5 s, block latency p95 ≤ 50 ms, and the ratchets |
| **Write amplification (SQLite)** | the sync store runs in WAL mode with a busy timeout |
| **Change data capture / the outbox idea** | the audit trail is one append-only JSON line per decision, which the AI-SOC reads, rather than a second write that could disagree |

## Not applicable yet, and when it would be

| Concept | Why not now | The trigger to build it |
|---|---|---|
| Consistent hashing, sharding keys, hot partitions | one gateway and one sync store; nothing is partitioned | more than one gateway instance behind a balancer, or a multi-tenant MSSP deployment (doc 62 build 7) |
| Replication lag, strong vs eventual consistency | one database; phones are offline-first by design and converge through sync | a second sync node or a hosted multi-tenant store |
| Pessimistic locking | no multi-writer rows; per-key merge is enough | shared team records (one record edited by several people at once) |
| Read amplification, index selectivity, query plans | the sync store reads one row per user | per-record tables or reporting queries; then check with `EXPLAIN QUERY PLAN` |
| Cache invalidation, cache stampede | there is no cache in front of the models | a response cache for identical prompts (it would need per-tenant keys and a short TTL) |
| A real outbox and dead-letter queue for events | there is no message broker | webhooks to a SIEM or ticketing system (doc 62 build 6) |

## How to read your own numbers

```bash
curl -s http://localhost:8080/v1/latency       # p50 / p95 / p99 of the last 1,000 model calls
curl -s http://localhost:8080/metrics | grep -E "latency_ms_bucket|inflight|shed_overload"
```

Watch **p95 and p99**, not the average. A p99 far above p95 usually means the cloud rungs failed and the local model
answered; check the router with `./securax providers list`.
