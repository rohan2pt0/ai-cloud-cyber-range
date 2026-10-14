# 40 · Encryption in transit: HTTPS everywhere, by name, from the browser to the edge

The padlock warning in your browser ("Your connection to this site isn't secure") was true: every web address of the estate was plain HTTP. This document is what changed, what is proven, and what is **not yet** encrypted.

## Turn it on (Ubuntu, 3 minutes)
```bash
cd ~/securax
./securax tls on                 # private authority + certificate + the HTTPS edge (default domain: securax.localhost, no DNS needed on this machine)
./securax tls trust --apply      # Windows: trusts the authority for Edge/Chrome (confirm the Windows prompt), then close and reopen the browser
./securax down && ./securax up
./securax tls status
```
Every service now has a **name** and the estate listens on **one** port (443). No port number appears in any address:
`https://hub.securax.localhost` (home / Command Center), `chat.` (Chat), `docs.` (Private Docs), `flows.` (n8n), `sync.` (phone/PWA sync), `api.` (gateway API). The Command Center and the app link to each other by name. Old `http://localhost:3000` etc. **stop answering on purpose**: the plain web ports are no longer published at all. `./securax tls off` brings them back.

## Why names, not ports (and the AWS comparison)
Cloud providers give every service a stable name and keep the address behind it in one place (DNS, a load balancer). Here: the **name** is what people, bookmarks, the phone app and the Life OS use; the **address** lives in exactly one record. If the machine's IP changes, a service moves to another machine, or the estate grows into several machines, you change one DNS entry — nothing else. New services get a new name under the same wildcard certificate with no re-issue.
- **On this machine** `*.securax.localhost` needs no DNS: browsers resolve it to the machine itself.
- **For other devices / a team** use a domain you control: `./securax tls on --domain securax.example.in` (first time on a new domain it asks for `--new-ca`, because the old authority was restricted to the old names; every device must trust the new one) and create **one wildcard DNS record** `*.securax.example.in` pointing at the machine's private or Tailscale address. That record is the only place an IP lives. Phones: install `ca.crt` (see `tls trust`), then use `https://sync.securax.example.in/sync` in the app. Secure addresses also unlock "install as app" on the phone.
- A name that is not in the table (or a raw IP address) gets **no service** (HTTP 421), so the edge never serves the Command Center to a guessed host name.

> **Before you switch — one thing that will surprise you.** Browsers keep each web address's data separately. The Guiding Map (Life OS) stores its data in the browser **per address**, so `https://hub.securax.localhost` starts empty. Nothing is lost (the data stays under `http://localhost:8088` and comes back with `./securax tls off`), but do this first: on the old address open **Ops → System health → Export backup**, then import it on the new address — or turn **cross-device sync** on, which restores everything. Chat, Private Docs and n8n keep their data on the server; you only sign in to Chat again. Choose your domain **once**: changing it later changes the address again.

## What it builds
| Piece | Detail |
|---|---|
| Private authority | ECDSA P-256, 10 years, key in `~/.securax/tls` (mode 600), **never inside a container** |
| **Name constraints** | The authority can only vouch for `localhost`, loopback, Tailscale (`100.64/10`), private LAN ranges, `*.ts.net`, `*.local`, `*.securax.internal`, this machine's own name and the one domain you chose. Even a leaked authority key cannot forge a real website (a test proves OpenSSL rejects such a certificate) — which is what makes trusting it low-risk |
| Server certificate | ECDSA P-256, 397 days, wildcard for the domain plus `localhost`, `127.0.0.1`, `::1`, your machine name and the Tailscale IP; renews with `./securax tls renew`; the cockpit warns at 30 days |
| Edge | the nginx image the estate already uses (no new software), configuration **generated** from one table in `governance/tls.py`: TLS 1.2/1.3 only, forward-secret AEAD ciphers, no session tickets, HTTP/2, WebSockets and streaming answers pass through, 100 MB uploads for Private Docs; port 80 only redirects |
| Published ports | with the edge on: **443 and 80 (redirect)** plus the gateway's own plain port on **127.0.0.1** (the CLI's health checks use it). Everything binds to this machine unless you set `BIND_HOST` |
| Browser access to the API | the gateway allows exactly the estate's own HTTPS names (CORS) and `localhost`, nothing wider |
| Also fixed | the gateway (8080) and Grafana (3000) were published on **every** network interface; they now follow `BIND_HOST` like the rest (default: this machine only) |

HSTS is deliberately not sent: browsers key it on the host name, so it would pin the whole domain for a year and break unrelated local tools the day you switch the edge off.

## What is proven
- Unit tests: the certificate verifies against the authority, keys are owner-only, the name constraints really reject a certificate for a public name, issuing is idempotent (the IPv6 spelling bug found and fixed), a live handshake is TLS ≥ 1.2 and refuses a wrong name, the edge config and port table agree, the compose overlay publishes only the edge, and **no base-compose port is wider than loopback by default**.
- Real-stack journey `tls_edge` (21 checks): the estate is restarted behind the edge; Command Center, Chat, sync and gateway answer over **verified** TLS **by name on port 443**; an untrusted client is refused; an unknown name gets 421; TLS 1.1 is refused; TLS 1.3 works; port 80 only redirects; none of the old plain web ports and no per-service HTTPS port is published; the browser (CORS) may call the API from the Command Center's name only; a **WebSocket upgrade passes through** (live sync for the Life OS PWA); `tls status` is clean; `tls off` returns to plain.
- By hand during the build: a real `wss://` live-sync push through the edge to the sync service.

## Phase 2 — encryption INSIDE the estate (`./securax tls internal on`)
Each service gets a small nginx **TLS sidecar** that shares its network namespace, presents its own certificate (`<svc>.securax.internal`, issued by the same private authority — the CA key never enters a container) and forwards to the service on **loopback only**. The service itself no longer listens on the container network, so plain HTTP from another container is **refused**, not merely unused. Hops covered: edge → gateway / Open WebUI / n8n / sync; Open WebUI, n8n and AnythingLLM → gateway; gateway → LiteLLM; LiteLLM → Ollama; n8n → gateway. Containers trust a combined bundle (public CAs + ours) so calls to cloud providers still verify. The CLI reaches the gateway at `https://localhost` with the CA pinned. `./securax tls internal off` reverts.

Proven by real-stack journey `tls_internal` (19 checks): the estate restarts with sidecars; the gateway is ready via edge → sidecar; a chat completion flows gateway → router over TLS → provider; from inside the gateway container plain `http://litellm:4000`, `ollama:11434`, `estate-sync:8089`, `open-webui:8080` are **refused** while their `https://<svc>.securax.internal:8443` names answer with verified certificates.

## Honest limits — what is still NOT encrypted
1. **AnythingLLM** does not bind to loopback, so its plain port is still reachable inside the container network (its calls to Ollama are TLS).
2. The optional **Sprout stage** (Prometheus scraping `gateway:8080`, Wazuh/MISP/TheHive internals) is outside this overlay.
3. **n8n** reads the gateway address from an environment variable; this assumes env access is not blocked in workflow expressions (true for the pinned 1.74; re-test on upgrade).
4. A compromised container sharing a service's network namespace (the sidecar) can still see that service's plaintext on loopback — that is inherent to the sidecar pattern.
5. TLS to cloud AI providers is theirs; backups can be encrypted (doc 41; plain unless you set a key file); there is **no client-certificate (mTLS)** between services yet. Postgres is not used by this estate, so there is no database hop.
6. Quantum readiness: certificates are classical ECDSA P-256 (separate piece of work).

`./securax tls status` lists what applies to your current setup every time.

## When a page says "not running"
Private Docs (AnythingLLM) and Automation (n8n) are **optional**: on machines that `./securax profile` sizes as tiny/small/medium (lite mode) they are not started, so their names have nothing behind them. The edge now says so in plain English with the exact command instead of a bare `502 Bad Gateway`, and the Command Center shows them grey (not green).

    ./securax start docs      # Private Docs  (about 2 GB of memory)
    ./securax start flows     # Automation / n8n (about 1 GB)
    ./securax start all

The Command Center's dots over HTTPS come from `https://hub.<domain>/_up/<name>`, which the edge answers with the service's real status (a browser cannot read the status of a cross-origin request, which is why a stopped service used to look "running"). Every link on the Command Center follows the page's scheme: by name over HTTPS, `localhost:<port>` over plain HTTP. A bookmark such as `https://hub.<domain>:8088` is a leftover from plain-HTTP days; use `https://hub.<domain>/hub.html`.

## Regulators
RBI NBFC 118 (strong cryptography) and 21(9) (PKI) and SEBI CSCRF PR.DS.S1–S3 now cite this work with the shortfalls above stated; none was raised to "supported". The cockpit shows an **Encryption in transit** indicator (amber on plain HTTP, red when the regulated profile is on).
