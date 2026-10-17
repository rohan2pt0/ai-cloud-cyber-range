# 64 · Success mantras: what the best organisations do, and where SecuRAX does it too

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Each mantra names the file, command or test that proves SecuRAX applies it. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

The organisations and people named across this project's planning, each reduced to the **one practice that explains most
of their engineering success** (the 20% that does 80% of the work), and how SecuRAX applies it. Every "how" names the
file, command or test that proves it. The mantras are the organisations' own published practices, paraphrased.

## The 80/20: seven practices that cover almost all of it

If you keep only seven, keep these. Each one prevented a real failure in this project.

| # | Practice | Who it comes from | In SecuRAX |
|---|---|---|---|
| 1 | **Measure the tail and set a budget** | Google SRE, Atlassian (p99), NVIDIA "speed of light" | fitness budgets on every build (time to first block ≤ 5 s, block p95 ≤ 50 ms); `/v1/latency` p50/p95/p99; `/v1/slo` with the error budget left |
| 2 | **Stop the line on a defect, and make the mistake impossible** | Toyota (andon, jidoka, poka-yoke) | CI blocks the merge; `forge` and `diffcheck` gate every change; phone andon (`notify digest --changed`); `preflight` and `go` catch blockers before start-up |
| 3 | **Mechanisms, not good intentions** | Amazon | ratchets that only tighten (fitness baselines); `./securax postmortem` turns each outage into dated, owned actions, and `actions` flags the overdue ones |
| 4 | **Every claim is proven, and the proof re-runs** | Anthropic and OpenAI (evals before release), Perplexity (cite the source) | the red-team scorecard and claims ledger (`claims-proven` fitness check); status lights on every page; the regulator watch keeps source links only |
| 5 | **Secure and private by default** | Microsoft Secure Future Initiative, Apple (on-device), Tailscale (zero trust) | fail-closed rails; a local-model floor; residency routing; phones over Tailscale only, never public; placeholder secrets replaced on start |
| 6 | **Time to value is the product** | Cyera ("<1 day"), Wiz (minutes, agentless), Tailscale ("it just works") | `./securax go`: one command, one status screen; a cold start blocks its first attack in under 1 s |
| 7 | **Small, reversible changes, rolled out safely** | Amazon (two-way doors), Meta and GitHub (ship small, gradual rollout) | `update` backs up first, health-gates and rolls back by itself; one PR per change, merged only on green CI |

## Every organisation, one mantra each

| Organisation / person | Success mantra | How SecuRAX applies it | Proof |
|---|---|---|---|
| **Amazon** | Work backwards from the customer; mechanisms beat intentions; most decisions are two-way doors | the Shield page states the customer promise first and lights what is built against it (doc 62); blameless postmortems with tracked actions | `governance/postmortem.py`, `test_postmortem.py`; doc 01 (two-way doors) |
| **Google (SRE)** | SLOs and error budgets decide between new features and reliability; blameless postmortems; cap toil | `/v1/slo` reports the availability and latency budget left; repetitive work is a routine, not a person's job | `test_slo_reports_targets_and_the_error_budget`; `routines/jobs.json` |
| **Microsoft** | Secure by design, by default, in operation; threat-model first | fail-closed rails, identity-aware gateway, signed and pinned supply chain | doc 59 (trust boundaries); `supply-chain` fitness check; Scorecard + SLSA in CI |
| **Apple** | Simplicity; privacy built into the device | private data never leaves the laptop (local model, residency); one front door (Command Center) | `residency.py` tests; `go` |
| **NVIDIA** | Compare against the "speed of light", the theoretical best, not last year | latency budgets set against the measured floor, not a comfortable guess | `lifecycle/fitness.json` |
| **Anthropic** | Safety and capability measured together; evaluate before you deploy; do the simple thing that works | the red-team scorecard runs on every change; the agent and tool-call guard | `redteam/run_attacks.py` (100 % defence, 0 false positives) |
| **OpenAI** | Iterative deployment: ship, learn, tighten | small PRs, status lights that move from red to green | `docs/status.yml` |
| **Mistral** | Efficiency and open weights | the right-sized local model chosen for the machine, open models through OpenCode | `autosize`, doc 42 |
| **Perplexity** | Every answer cites its source | research agent cites; the regulator watch keeps only the regulator's own links | `agents/web_research`, `test_regwatch.py` |
| **Cursor** | Latency is the user experience; dogfood | SecuRAX builds SecuRAX (`autobuild`); p95/p99 watched | doc 60, `/v1/latency` |
| **Stripe** | APIs that are safe to retry: idempotency keys | `Idempotency-Key` on chat: a retry gets the first answer, never a second model call or a second tool call | `test_a_retry_with_the_same_idempotency_key_gets_the_first_answer_without_a_second_model_call` |
| **GitHub** | Ship small; CI is the gate | branch protection, required checks, merge on green | `.github/workflows/` |
| **Tailscale** | Zero config; identity, not IP addresses | `./securax go` publishes to your own devices only; no open ports | `go`, doc 58 |
| **Cloudflare** | Public, blameless postmortems; dogfood your own product | postmortem template; the product site runs on Cloudflare Pages | `postmortem.py`, doc 60 |
| **Mattermost** | Self-hosted, open core, built for regulated teams | the same model: open repository, sovereign deployment, paid Shield | doc 61 |
| **Supabase** | Developer experience; open source on proven parts | stock, pinned components (Open WebUI, LiteLLM, Ollama) rather than custom ones | `docker-compose.yml` pins |
| **Palantir** | Forward-deployed engineers inside the customer | the design-partner offer: deployment with the first customers | doc 61 |
| **Shopify** | Strong defaults; "do things, tell people" | defaults that work with no settings; CHANGELOG entry for every change | `CHANGELOG.md` |
| **Cyera** | Time to value as the headline; a free assessment as the front door | the 2-minute AI-risk check; time to first block published | `website/assess/`, doc 62 |
| **Meta** | Move fast on stable infrastructure: gradual rollout, instant rollback | `update`: backup → health gate → automatic rollback | `safe_update_rollback` sandbox journey |
| **Toyota** | Andon, jidoka, poka-yoke, kaizen | phone andon, CI stop-the-line, `preflight`, one improvement per PR | `notify.py`, `forge` |
| **Netflix** | Break it on purpose before it breaks itself (chaos engineering) | game days and the self-healing sandbox journey kill components and check recovery | `./securax gameday`, `self_healing` journey |
| **Atlassian (backend fundamentals)** | p99, pooling, backpressure, idempotency, breakers, DLQs | doc 63: 35 concepts audited, the gaps built | doc 63 |
| **Forbes AI 50 / IIM pattern analysis** | Own a category; narrow wedge, then platform; proof on the homepage | the Sovereign AI Firewall wedge (doc 62) | doc 62 |

## How to keep it true

- A new practice is added here only with a proof: a file, a command or a test.
- When a proof breaks, CI goes red, and the row is fixed or removed in the same PR.
- After any outage: `./securax postmortem new "what broke"`, then add the mechanism to the table above if it is new.
