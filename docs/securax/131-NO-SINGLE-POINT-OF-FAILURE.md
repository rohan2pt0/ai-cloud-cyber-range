# 131 · No single point of failure — the front door, the machines, and what is still one

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The Command Center no longer needs a machine to open: a hosted door (command/, published with the site) keeps your list of machines on the device, asks each one are-you-up through one path each node answers itself (/_door.json, readable from any site, one fixed sentence, never cached), and opens the best one: the fastest of several primaries (active-active), a standby only when no primary answers (active-passive). Proved in a real browser against simulated machines including the two false-green traps (a dead tunnel page, a missing permission header), hostile and tampered setup links, offline reload and phone width, and by a real nginx -t and a real cross-origin request; test_command_door.py holds it. The single-point-of-failure register is honest about what is still one (the static host, Chat history, the password vault, the code home, the operator). Not yet run against your own machines; machines behind Cloudflare Access need their private-network address until a bypass for the one path is added (queued). Tests: test_command_door.py, test_pwa_publish.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The question.** The Command Center only opened if one of your machines was running. That made it the single point of failure
for everything behind it. The answer has two layers, and they are fixed in two different ways:

1. **The front door (the page)** needs no machine. It is hosted with the product site, and every device keeps its own copy.
2. **The services behind it** (Chat, the AI gateway, the other apps) need at least one machine up. So there must be **two or
   more**, and the door must find whichever one is up.

## 1. The door: `command/` on your site

Open `<site address>command/` (`./securax site` prints the address; add `command/`) and install it like the Life OS. It is a
small page that:

- keeps your list of machines **on this device** (nothing is sent anywhere but to the machines you list);
- asks each one "are you up?" every 15 seconds while you look at it;
- shows one calm card: **which machine is up, and the one button that opens its Command Center**;
- if none answers, says so plainly and gives the fixes in order, and still opens the Life OS and Vantage, which need no machine;
- opens from this device's own copy with the site host down, and says so when you are offline.

**It tells the truth about a machine.** Each node's web server answers one path, `/_door.json`, with one fixed sentence, readable from
any site. A "something answered" check would be fooled: a dead Cloudflare tunnel still serves an error page. The door believes a
machine only when it says the exact sentence. It carries no cookie and no data, and it is never cached.

**Roles give you both patterns.**

| Pattern | How you set it | What the door does |
|---|---|---|
| **Active-active** | Two or more machines set to **Primary** | Opens the one that answered fastest; if one dies, the other is already the choice |
| **Active-passive** | One or more **Primary**, plus a **Standby** | Uses the standby only when no primary answers, and says "this is your standby" |

**Set it up once** (about 5 minutes):

1. On each machine, get the new status path in: `./securax update`, then `./securax down` and `./securax up`.
2. Open the door, **Your machines → Add a machine**. For each, give the address where you open the Command Center on it.
   Use the private-network address that `./securax phones` prints (it looks like `https://<machine>.<tailnet>.ts.net/`).
3. **Copy a setup link for another device** and open it there. It shows what it wants to add and waits for your yes. It carries
   addresses only, never keys.

**Two limits, stated plainly.**

- A machine behind a **Cloudflare Access** sign-in looks "not answering" to the door, because the check sends no cookies on
  purpose. List its private-network address instead. Letting the single path `/_door.json` through Access is queued.
- A machine reachable only over **Tailscale** looks down from a device that is not on your tailnet. That is correct: you could
  not use it from there either.

## 2. The register: every layer, what it was, what it is, what is still one

| Layer | Was | Now | Still one? | Next |
|---|---|---|---|---|
| **Command Center page** | Served by one machine | Hosted with the site; each device keeps a copy; the door finds a live machine | The static host (GitHub Pages). A device that has opened it once still has its copy | A second static host, dated in the queue |
| **Life OS and Vantage** | One laptop | Hosted, on-device copy, your encrypted OneDrive copy, and node-to-node sync | No | — |
| **Gateway (the AI front)** | One machine | Stateless: any node answers (active-active) | No, once you have two nodes | — |
| **Chat history** | One node's database | Per node | **Yes**: a conversation lives on the node it started on | A shared database with a standby (doc 86) |
| **AI models** | One provider | A ladder of free and local providers; the local model is the floor | No | — |
| **The way in** | One tunnel | Cloudflare tunnel **and** Tailscale, independent of each other | No | — |
| **Passwords** | One vault | One vault on the always-on machine; the apps keep an offline copy | **Yes, accepted** (review 2027-01-31) | A standby |
| **Backups** | The laptop | Each node, your OneDrive, and the dormant cloud seed banks | The cloud banks are not applied yet (doc 29) | First live apply, dated in the queue |
| **The code and releases** | GitHub | GitHub, plus a private GitLab mirror once you run its guided step | **Yes** until the mirror is on | In the queue, waiting for you |
| **The domain** | github.io | github.io today; your own domain not live | Adding a domain adds a DNS dependency; keep both | — |
| **Where the apps live in the browser** | One shared origin (`rohan2pt0.github.io`), with no security headers (GitHub Pages ignores `_headers`) | Header rules for the apps are written (`website/_headers`) | **Yes**: every Pages site on the account shares this origin's storage | An origin of their own on a host that reads the headers, dated in the queue |
| **You, and the assistant** | You, and one paid assistant | A runbook, `./securax why`, `./securax next`, `./securax ask` on free keys | **Yes** for decisions only you can make | The emergency sheet in the Life OS |

**Be careful with one claim.** The reference estate (a laptop, a server, a cloud instance) has no unaccepted critical single
point of failure, and the fitness gate holds that on every change. **Your** estate is only as good as the machines you have
actually added. With one machine, `./securax resilience` correctly says everything depends on it. The step that makes it true
for you is the second node: `./securax nodes invite` on one, and paste the line it prints on the other.

## 3. A topology that fits what you have

- **Server (always on):** the primary. Runs the gateway, Chat, sync and the tunnel.
- **Laptop (HP 240 G9):** a second node on `./securax up --safe`, or just the door and the hosted apps.
- **Optional third:** a small always-free cloud instance, as a standby.
- **Door:** lists all of them. The server and the laptop are **Primary** (active-active); the cloud instance is **Standby**.

Then the checks:

```bash
./securax nodes
./securax resilience
```

`nodes` should show every machine "in step". `resilience` should name no critical machine that everything depends on.

## 4. What this does not do

- It does not make Chat history shared. That needs a replicated database, which is a real piece of work and is dated, not hidden.
- It does not put a chat client in the browser that calls a model with your own key. That would bypass the gateway's rails: the
  allowance, the audit chain and the data-class check. A hosted page is for finding the machine, not for skipping the controls.
- It does not stand up cloud machines while nobody is watching.
