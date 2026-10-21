# 86 · Many machines, one SecuRAX, and the road to a lakh users

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the same Life OS data on every node (two real containers: replicated, a stopped node caught up, clashing edits converged), pull-only beta nodes, a second machine serving the same addresses (join tested), stable and beta channels through the safe update (an older release changes nothing; a failing new one rolls back), signed-in people reaching the AI gateway as themselves with no key of their own. Chat history and Chat users' allowances are still per node; open sign-up, payments and the cluster stage are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:**
- Every kind of machine works together and stays in sync: the laptop, a VPS, a Mac mini with a GPU, AWS, GCP, Azure or a private cloud.
- No machine is a single point of failure, and none is needed to run the whole estate.
- It must stay as simple as WhatsApp or Telegram were in their early days, run by a small team, and good enough that people move from ChatGPT, Gemini or Claude.
- New users should not need their own API keys.
- The version you rely on stays available while a new one is tried as beta.

## 1. One estate on many machines (built)

A **node** is any machine running the estate:
- **Linux** (a VPS, a cloud instance, a private-cloud VM, a home server): `install.sh --server` (doc 85).
- **A laptop or a Mac mini:** `install.sh` (doc 75).

Each node is complete on its own. Nodes stand in for each other in three ways:

| What | How | Proven |
|---|---|---|
| **The same Life OS data everywhere** | Each node lists the others (`./securax nodes add`). Every 30 seconds it compares each person's data with theirs, pulls and merges what differs, and sends its own back. The merge gives the same result in any order, so there is no primary and nothing to lose when one node stops | Two real containers: a write on one reached the other; one was stopped, kept missing writes, and caught up by itself on return; clashing edits ended identical on both; a second round does nothing |
| **The same addresses everywhere** | `./securax online invite` on one node, `./securax online join` on another: both serve `hub.<domain>`. Cloudflare sends each visitor to the nearest node that is up, and retries another when one fails | Cloudflare's documented replica behaviour; the join is tested here, a real two-node failover not yet |
| **Private links between nodes** | Nodes reach each other over Tailscale, through the same address the phones use. Nothing new is opened to the internet | Configuration is tested; a real Tailscale link not yet |

**Add a second node (about 10 minutes):**
1. Install SecuRAX on it (doc 85 for a server).
2. Put both nodes on your Tailscale account (`./securax phones`).
3. On node A: `./securax nodes invite`. On node B, paste the line it prints. Then the same the other way round.
4. On node A: `./securax online invite`. On node B, paste the line it prints.
5. Check on either node: `./securax nodes` should show every node "in step".

**A Mac mini with a GPU** is a node like any other, with stronger local models. Today each node's Chat uses its own local model. Sending the heavy local work of every node to the GPU node is dated below.

### What is still kept per node (honest)

| Per node today | What that means | Plan |
|---|---|---|
| Chat history (Open WebUI's own database) | A conversation started on one node is not on the other | A shared, replicated database (Postgres with a standby), dated below |
| The password vault | Keep it on one node; it is in that node's nightly backup | Stays so: one vault, backed up, is simpler and safer |
| The AI allowance ledger | Each node counts separately, so with two nodes a person's allowance is effectively doubled | Count centrally once Chat moves to the shared database |
| The audit chain | Each node keeps its own tamper-evident log | `./securax audit verify` on each node |

## 2. The version you rely on, and the beta (built)

- **Two channels:** `./securax channel stable` follows releases only. `./securax channel beta` follows every merged change.
- **Safety:** switching goes through the same safe update as always: a backup first, a health check, and an automatic return to the previous version if the new one does not start. Stable never moves backwards. Tested here: an older release changed nothing, and a newer release that failed its health check was rolled back to the exact previous version.
- **A beta address of its own:** `./securax online setup --beta` on the beta machine gives it `beta-hub.<domain>` and `beta-chat.<domain>`. They have their own tunnel and sign-in gate, so the stable addresses never serve beta code.
- **A beta node never writes into stable data:** add the stable nodes to it with `--pull-only`. It takes your real data to test with, but nothing it does flows back.
- **Make beta the new stable:** when beta has run well for a week, cut a release (a `vX.Y.Z` tag; the release workflow builds it). Every stable node moves to it at its next nightly update.
- **Any time:** `./securax rollback` goes back to the last version that worked (doc 82).

## 3. New users without API keys (partly built)

The friction is real: nobody switches from ChatGPT if they must first sign up with three AI providers. The options:

| Option | For whom | Verdict |
|---|---|---|
| **You hold the keys; each person gets an allowance** | Family, a team, the first hundreds of users | **The default.** People sign in and use it. Your gateway calls the models with your paid keys and counts each person's daily and monthly tokens. The allowance already exists (`app/budget.py`, doc 36) |
| **Per-person keys minted for them** | When you need a hard money cap per person | OpenRouter can create a key per person with its own credit limit and reset, through its management API |
| **Bring your own key** | Power users | Keep as an option, never the requirement |
| **Local models** | A free tier at no cost per message | Already the fallback when an allowance runs out |
| **Free-tier keys for other people** | Nobody | **No.** Free tiers are for your own use: Google may use free-tier inputs to improve its models, and serving others on them is unclear under its terms. Serve others only on pay-as-you-go keys |

**Built in this round:**
- **Sign-in to allowance:** `online setup` tells the gateway how to verify a Cloudflare sign-in. nginx passes the signed sign-in to the AI gateway when the caller sent no key of its own, and a verified sign-in may chat as a `user`, never as admin.
- **Switch it on:** `./securax gateway-auth enable` turns it on. It also gives Chat and the CLI their own keys. From then on, the Life OS and the Command Center count each signed-in person's own allowance.

**Not yet:** Chat sends all its users under its one key, so they share one allowance. Fix: pass each Chat user through to the gateway (Open WebUI can forward the user's identity), dated below.

## 4. The road to a lakh users, kept small

WhatsApp served hundreds of millions of people with a few dozen engineers. They did it with a few proven parts, done well, not many parts. The same rule here: each stage adds one thing, only when the numbers call for it.

| Stage | Users | What changes | Trigger |
|---|---|---|---|
| **Now** | You and your family (Cloudflare Access is free up to 50) | Nodes, online addresses, allowances | Built |
| **Team** | Up to ~50 | `gateway-auth enable`; Chat users counted one by one; Chat history on a replicated database | When a second person uses it daily |
| **Open sign-up** | Hundreds to thousands | **Sign-in:** Keycloak (doc 84) takes over from the Access allow-list, so anyone can sign up with Google or Microsoft. **Money:** OpenRouter keys per person; a payment provider. **India:** the DPDP consent record; GST registration once turnover crosses the threshold (confirm with your CA) | When people you do not know ask for access |
| **Scale** | 10,000 to 1,00,000+ | **The cluster:** the burrow and forest stages (doc 29), Kubernetes across regions, the Life OS served from a CDN (it is static already). **Data:** the sync service on Postgres instead of SQLite (its merge is already order-independent). **Load:** a queue in front of AI calls. **Operations:** SLOs with alerts | When one region's nodes run above 60% for a week |

Two choices already made keep this path open:
- **The merge is order-independent.** Adding machines adds capacity, not conflicts.
- **The Life OS keeps working on the device when the network is gone.** A slow server is an inconvenience, not an outage.

## 5. Next steps (dated)

| By | Step |
|---|---|
| 2026-11-05 | Run two real nodes (laptop and VPS), with a failover drill in `./securax continuity` |
| 2026-11-20 | Count each Chat user separately: Open WebUI forwards the user; the gateway trusts it only from Chat's own key |
| 2026-12-10 | Chat history on Postgres with a standby on a second node |
| 2026-12-20 | Heavy local work routed to the GPU node when it is up, to the cloud chain when it is not |
| 2027-01-31 | Open sign-up: Keycloak with Google and Microsoft, OpenRouter keys per person, consent records |

## Sources

- [Cloudflare: tunnel replicas and failover](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/deploy-tunnels/deploy-cloudflared-replicas/)
- [OpenRouter: management (provisioning) API keys](https://openrouter.ai/docs/features/provisioning-api-keys)
- [Gemini API free tier: data use and commercial questions](https://discuss.ai.google.dev/t/clarification-regarding-commercial-use-can-i-sell-a-web-app-built-on-top-of-gemini-api-free-tier-w/120164)
- [Open WebUI: SSO and forwarded user headers](https://docs.openwebui.com/features/authentication-access/auth/sso/)
