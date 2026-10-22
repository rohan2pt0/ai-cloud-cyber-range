# 87 · Security review before the freeze

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Internet-facing images are pinned by digest and checked weekly. Sync tokens are rate-limited per node and repeated refused sign-ins raise an alert. Eight findings fixed and proved (SSH keys-only on the VPS, cross-site writes refused by the gateway, a stored XSS in Inbox ids, security headers, encrypted server backups, the scanner no longer holding the Docker socket, no :latest image, no public router key). Accepted risks are listed with reasons. The deeper audit of logs and image hardening is dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** before freezing the setup, review it through every lens: the seven OSI layers, CISSP and CCSP domains, OffSec's attacker view, ISACA, OWASP, TOGAF and SABSA. Find any big blunder and fix it for good.

**The answer in one line:** the design held up. The biggest problems were at the joins: the new VPS facing the internet, a browser on the laptop, and data coming in from outside. Each one was found by testing, fixed, and proved fixed.

## 1. What was found and fixed

| # | Lens | Finding | Why it mattered | Fix (proved) |
|---|---|---|---|---|
| 1 | OSI 4/7 · OffSec · CIS | **SSH on the VPS accepted passwords, root included.** Many VPS images ship this way, and the installer left it | The one door open to the internet is guessed at all day; one weak password and the server is someone else's | `install.sh --server`: keys only, no root password login, `MaxAuthTries 3`, and SSH attempts rate-limited by the firewall. It applies only when a key is installed, so it can never lock you out. Checked with `sshd -t` before it applies. Proved in a fresh Ubuntu 24.04: without a key nothing changes; with a key `sshd -T` shows `passwordauthentication no` |
| 2 | OWASP A01 (CSRF) · OSI 7 | **A website open on the laptop could use the AI gateway.** CORS hides the answer from a foreign page, not the request. A plain POST reached `/v1/chat/completions`, and with sign-in off (the laptop default) it spent your keys and allowance | Any page you visit could run up your bill, blind | The gateway refuses a write that names a foreign origin. Browsers always send one on a cross-site POST; command-line clients send none, so nothing else changes. Your own pages (localhost, your domain, the address you came in on) still work. Tests: `test_cross_site.py` |
| 3 | OWASP A03 (XSS) | **A crafted id in an imported or synced Inbox item ran code.** Item ids went raw into `onclick="…('ID')"` | One poisoned Keep export or synced item could act as you in the Life OS | Ids are cut to safe characters where they are written; lookups match on the same cleaned id. `test30.js`: against the old code the injected code **ran** and the item could not be deleted; now neither |
| 4 | OWASP A05 · OSI 7 | **No security headers** on the front door every page goes through | Your Life OS and Command Center could be framed by another site (clickjacking) | `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, a closed `Permissions-Policy`, also on `/portal/`. Proved live with 0 page errors and 0 CSP refusals |
| 5 | CCSP data · CISSP D2 | **Backups on a server were not encrypted**, and every backup holds `.env` with all your keys | A provider's disk snapshot, or a copied backup, hands over every key | The server installer now runs `./securax protect` before going online. It makes the key, waits until you have saved it in your password manager, then proves the first encrypted backup opens. Off-site copies were already encrypted-only |
| 6 | OffSec (privilege) · CIS Docker | **The Trivy scanner stayed running, holding the Docker socket.** `:ro` does not limit the Docker API | A third-party image with host-level control, for days instead of seconds | It scans and exits (`restart: "no"`) |
| 7 | Supply chain (SLSA, OWASP A08) | **AnythingLLM ran `:latest`** | An image that changes under you, without review | Pinned to 1.18.0, not 1.17.0, so nobody's data is downgraded |
| 8 | ISACA · default credentials | **An empty router key fell back to `sk-range-dev`**, which is published in this repository | A known key inside the estate | `up` replaces an empty, placeholder or public key with a random one |
| 9 | CIS Docker · OffSec (privilege) | **Eleven services could gain privileges through setuid programs** (no `no-new-privileges`) | One exploited process could become root inside its container, a step closer to the host | Every service sets it; a test fails if a new one forgets it or uses `:latest`. `cap_drop: ALL` is set only where the image is ours, because Postgres and nginx need some capabilities to start |

## 2. Checked and found sound

- **Network (OSI 3/4):**
  - Every port listens on 127.0.0.1.
  - Online access is an outbound-only tunnel.
  - The data network is internal.
  - Containers drop capabilities and set `no-new-privileges`.
- **Identity:**
  - Cloudflare sign-ins are verified at the origin: signature, team, application, expiry and e-mail; RS256 only.
  - Gateway tokens refuse `alg: none` and algorithm confusion.
  - Default roles can never be admin or auditor.
  - Chat trusts the sign-in header only while ports are on loopback (`online_guard`).
- **Sync:**
  - Fail-closed without tokens.
  - A signed-in device reaches only its own data.
  - The merge is order-independent.
  - A beta node can be pull-only.
- **AI output (OWASP LLM02):** answers are escaped before a few safe tags (bold, lists, code) are added back. No links, no raw HTML.
- **Cryptography:** keys come from the operating system's random source (`secrets`), 256 bits, owner-only, never overwritten. Backups use AES-256 through GnuPG.
- **CORS:** only localhost and your own domain, with no cookies.

## 3. Accepted on purpose, and why

| Risk | Why it stays | What limits it | Review |
|---|---|---|---|
| Laptop backups are not encrypted until `./securax protect` runs once | An automatic key that nobody saved turns "someone may read it" into "nobody can restore it", the worse failure in a disaster | The crown-jewels check shows it as DO NOW; off-site copies are refused unless encrypted | When the first backup is taken |
| Cloudflare opens the encryption at its edge | It is what makes sign-in work with nothing to install | Keep regulated customer data out of this personal estate; the gateway's residency rail still decides where AI calls go | Doc 85, section 4 |
| The `securax` user on the server is in the `docker` group, which equals root | Docker needs it; a separate user still keeps the estate out of root's shell | SSH is keys only; nothing else listens | When the cluster stage starts (doc 29) |
| Images are pinned by version tag, not by digest | Digests make every update a manual edit | Dependabot proposes updates; Trivy scans; `:latest` is gone | Done 2026-10-22: the 13 services other devices or the internet reach are pinned by digest (`local/compose/digest-pins.json`); `tools/digest_check.py` reports a moved build every week |
| The Cloudflare API token stays in `.env` after setup | `online allow`, `remove` and `google` need it | `.env` is owner-only; the token is scoped to four permissions; deleting it in Cloudflare is safe | Any time: delete it, and paste a new one only to change who may sign in |
| A sign-in lasts 30 days on a device | Asked for: as simple as ChatGPT | Use `ONLINE_SESSION=24h` for a shared device | Your call |

## 4. The architecture view (TOGAF, SABSA)

- **The business attribute that drives everything** (SABSA: available, private, simple) is now traceable to a control:
  - **Available:** many nodes, failover, rollback.
  - **Private:** loopback ports, Access, encrypted backups.
  - **Simple:** one command per job.
- **No component is a single point of failure for your data:** nodes sync, backups go off-site, code is mirrored. Still single per node (Chat history, the vault) is listed in doc 86 with dates.
- **Defence in depth:** each layer refuses on its own:
  - **the network:** loopback ports and a firewall
  - **the edge:** Access
  - **the origin:** token checks
  - **the application:** escaping and headers
  - **the data:** encryption

  No single mistake opens the estate.

## 5. Next steps (dated)

| By | Step |
|---|---|
| Done | The deeper audit: no secret is printed or logged by the CLI; the gateway's audit log records who, what and the decision, never the prompt or the answer; every container log is capped (3 × 10 MB); every service has `no-new-privileges` (row 9) |
| ~~2026-11-30~~ done 2026-10-21 | Per-node rate limits for sync tokens (`SYNC_RATE_LIMIT`, default 600 a minute, then 429 with Retry-After), and an alert after 10 refused sign-ins in 15 minutes (`refused-signins.jsonl` next to the sync data; the count is on `/healthz`). Tokens are never stored or logged. Since 2026-10-22 the web servers pass the client address and the sync service believes it only from a trusted proxy (`SYNC_TRUSTED_PROXIES`). Still counted together: clients through the Cloudflare tunnel, and `hub.<domain>/sync` when internal TLS is off |
| ~~2026-12-15~~ done 2026-10-22 | The internet-facing images pinned by digest, checked weekly for a moved build |

## Sources

- [OWASP Top 10 (2021)](https://owasp.org/Top10/), [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/), [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker); [Docker: the daemon socket](https://docs.docker.com/engine/security/#docker-daemon-attack-surface)
- [OpenSSH `sshd_config` manual](https://man.openbsd.org/sshd_config)
