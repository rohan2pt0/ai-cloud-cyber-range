# 56 · Pool your machines: what we took from RAMDeck, and what we did not

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The home rung is built and tested; splitting one model across machines is not built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Prompt:** RAMDeck, a crowdfunded hub (Indiegogo, Oct 2026), pools the RAM of the PCs, Macs and phones you already own to run models
too big for any one of them. It has an OpenAI-compatible API and a one-click benchmark. Is there anything for SecuRAX?

## How it works (from its own page)

The primary machine splits a model's layers across devices once, at load time. When generating, devices pass the activations along
like a relay (about 650 KB per token). That is the model-splitting approach of llama.cpp's RPC backend.

Its own disclaimer is the honest part:
- pooled memory trades speed for capacity;
- Wi-Fi nodes hurt performance;
- node traffic is unencrypted HTTP/WebSocket by default.

## Taken: lend the estate a stronger machine you own (`home` rung)

Most of the benefit comes from **running the whole model on your strongest machine**, not from splitting it. Splitting is slower,
by RAMDeck's own numbers. SecuRAX had this half-built: `REMOTE_OLLAMA_BASE` was a recipe that meant hand-editing the catalog, which
blocks the safe update's rollback. Its install line was `curl | sh` and it told you to bind to `0.0.0.0`.

Now it is a real provider, `home`:
- **One setting.** `REMOTE_OLLAMA_BASE=http://<Tailscale IP or name.ts.net>:11434`, plus `HOME_MODEL=ollama/<model pulled there>`, then `./securax up`.
- **In every chain, just before this laptop's model.** Chat, Twin and build all use it. The local floor stays last.
- **Counts as local for data residency**, because it is your machine (alias `home-local` matches the `*-local` zone).
- **Guarded for that reason.** Only loopback, private-LAN (10/8, 172.16/12, 192.168/16), Tailscale (100.64/10) or `*.ts.net` addresses enable it. A public address keeps it off, so it can never carry Red-tier data off your machines. Tested with public, look-alike and malformed addresses.
- **Encrypted in transit and authenticated by Tailscale** (WireGuard), unlike RAMDeck's default plain HTTP.
- **The benchmark button already exists:** `./securax bench --url http://100.x.y.z:11434` measures fit, accuracy and tokens/second on that machine.

Set up the other machine:
1. Install Ollama from its official installer or package (not `curl | sh`).
2. Join it to your tailnet.
3. Set `OLLAMA_HOST=<its Tailscale IP>:11434`. Never `0.0.0.0`, which opens it to everyone on your LAN.
4. `ollama pull <model>`.

**Never use the bank-issued laptop as a home machine.**

## Not taken (yet): splitting one model across devices (llama.cpp RPC)

1. **Security.** llama.cpp's own security policy says not to use the RPC backend or its server on an untrusted network. Its README calls the RPC feature a proof of concept. CVE-2026-39909 (published Aug 2026, CVSS 9.2) is an unauthenticated remote code execution in `rpc-server` before build b8585.
2. **Speed.** Splitting pools capacity; it does not add speed. Per-token latency across devices is the bottleneck, and RAMDeck shows 1.9 tokens/s for a 27B model on its weakest setup.
3. **Fit.** It only pays when *no single machine you own* can hold the model you need, and a sliced 30B model on a CPU-only Wi-Fi mix is rarely better than a cloud rung or the `home` machine.

If that day comes, it enters as a **dormant organ**, built only to these conditions:
- pinned at build b8585 or later;
- `rpc-server` bound to the Tailscale address and reachable only from the primary (Tailscale ACL);
- vetted with `./securax vet` / `inspect`;
- a claim in `governance/claims.json` with a journey that proves it.

## Buying the RAMDeck hub itself

It is a pre-campaign crowdfunded device: shipping is estimated for Feb–Mar 2027 from the US, and India is not on the list of shipping
countries it gives. The software is source-available (Apache 2.0 plus Commons Clause), not open source.

Its node traffic is unencrypted by default, which is the wrong default for sensitive data. Nothing in SecuRAX
needs it.
