# 137. Numbers that arrive by themselves: the automation plan

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Planned 14 November 2026: three routes ranked (SMS forwarder, the monthly CAS, Kite for the rebalance); share or paste is the working fallback today. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Owner, 2026-11-14:** "I can't depend on copy-pasting SMS; automation is one of the best features, even if it costs some money." Share or paste stays as the fallback ([#279](https://github.com/rohan2pt0/ai-cloud-cyber-range/pull/279), [#280](https://github.com/rohan2pt0/ai-cloud-cyber-range/pull/280)).

## The routes, ranked 80/20 (researched 14 November 2026)

| Route | What arrives | Cost | Decision |
|---|---|---|---|
| **An SMS forwarder on the phone**: open source, MIT, on F-Droid, filters by sender ([android_income_sms_gateway_webhook](https://github.com/bogkonstantin/android_income_sms_gateway_webhook)) | Every bank, card, UPI and EPFO message, in real time | Free | **Slice 1.** The forwarder posts only the chosen senders to the person's own estate, with a token. The Life OS picks them up on open and feeds them to the spend reader already built. |
| **The depositories' monthly CAS email** (NSDL/CDSL; [CDSL: the password is the PAN in capitals](https://www.cdslindia.com/cas/FAQ.html)), read with [casparser](https://github.com/codereverser/casparser) (MIT) | Mutual funds and demat holdings, monthly (half-yearly when there is no activity) | Free | **Slice 2.** The estate reads the statement from a mailbox the person points it at, parses it on the estate, and sends only the totals. |
| **Zerodha Kite Connect Personal** ([free since March 2025](https://www.marketcalls.in/fintech/zerodha-makes-trading-api-free-for-personal-use-bundles-historical-data-with-connect-api.html)) or the [official Kite MCP server](https://github.com/zerodha/kite-mcp-server) | Holdings, positions, funds, orders, GTT | Free; live data is ₹500 a month and not needed | **Slice 3: the birthday-month rebalance.** Read holdings, compare with the target mix, propose the trades; the person approves every order. Nothing trades by itself. |
| Account Aggregator (Finvu, OneMoney) | Bank data | — | Not for a personal app: data goes only to a regulated institution (FIU). |
| Fitbit | Health | — | The legacy API is switched off on 2 November 2026; the Google Health API takes no new projects. Revisit. |

## The rules every route keeps

1. **Least data:** only the senders and fields that feed a number. Card numbers and CVVs never; the last four digits at most.
2. **The person's own estate,** never a third-party cloud. A token per device, which one switch revokes (`one-door`).
3. **A threat model first** for each route (`governance/threat-models.json`); the forwarder crosses the phone-to-estate boundary.
4. **Nothing irreversible without a tap.** Rebalancing proposes; the person approves each order.
5. **The fallback always works:** share or paste a message, offline.

## Slice 1 is built: set it up in five minutes

1. **On the estate:** in `local/compose/.env`, set `SYNC_INBOX_TOKENS` to a new random token (for example `openssl rand -hex 24`) and `SYNC_INBOX_USER` to your Life OS sync id. Restart: `./securax up`. While the token is empty the door stays shut.
2. **On the phone:** install the open-source forwarder ([F-Droid or GitHub](https://github.com/bogkonstantin/android_income_sms_gateway_webhook)). Add one rule:
   - **Sender:** a pattern for your banks' sender ids, for example `.*-(HDFCBK|ICICIB|SBICRD|AXISBK|IDFCFB|BOBCRD|EPFOHO).*`;
   - **URL:** `https://<your estate's Tailscale name>/sync/inbox/sms?user=<your sync id>`;
   - **Header:** `Authorization: Bearer <the inbox token>`; **body:** `{"from":"%from%","text":"%text%"}`.
3. **Done.** Open the Life OS: new bank messages are read by themselves, a short note says how many, and the inbox is cleared.

**What the estate refuses:** any sender that is not a bank id, every one-time code (never stored), digit runs of 12 or more (masked), over 60 messages a minute, and any request without the inbox token. The inbox token cannot read anything.
