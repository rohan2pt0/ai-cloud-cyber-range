# 85 · Use SecuRAX from any device, like a SaaS app

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested here: the one-command Cloudflare setup (against a stand-in Cloudflare, re-runs repair), the sync service checking Access sign-ins (forged, expired, foreign and unsigned tokens refused; through the real nginx and container), the Life OS pairing itself on sign-in, the Command Center installable, the server installer on a fresh Ubuntu 24.04 (packages, Docker repository, user, clone, keys). Not yet run against a real Cloudflare account, a real VPS or a real Google sign-in: the first real setup is the proof. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:**
- Open SecuRAX on a phone, a tablet or any computer the way you open ChatGPT: sign in, and everything is there.
- No setup on each device, and no laptop that must stay awake.
- Simple enough that you, and anyone else, will actually use it.

**What you get:**
- One address, `https://hub.<your domain>`. Open it anywhere, sign in with Google (or a code sent to your e-mail), and you are in.
- The Life OS has your data on every device. It pairs itself when you sign in; there is no link or token to copy.
- Chat (`https://chat.<your domain>`) signs you in from that same sign-in.
- Install both as apps: on an iPhone, Share > Add to Home Screen; on Android, Windows or a Mac, the browser's Install app.
- It all runs on your own small server in India, which is always on. The laptop is only for heavy local models.

## 1. How it fits together

| Piece | What it does | Who runs it |
|---|---|---|
| **Your server** | A small VPS in Mumbai runs the estate, day and night. Its firewall lets in SSH only | You (a VPS provider rents you the machine) |
| **The tunnel** | Your server makes an outbound connection to Cloudflare, so no port is opened on the internet | `cloudflared`, pinned to 2026.10.0 |
| **The sign-in gate** | Cloudflare Access lets in only the e-mail addresses you list, signed in by Google or a one-time code | Cloudflare, free for up to 50 users |
| **The check at home** | The sync service checks Access's signed token itself (signature, team, application, expiry, e-mail), so a forged header gets nowhere | SecuRAX (`apps/estate-sync/syncsvc/access.py`) |

The password manager is not put online. The Bitwarden apps cannot pass a sign-in page, so it stays reachable on the server itself and over Tailscale (doc 58).

## 2. Set it up (about 30 minutes, once)

### 2.1 Rent the server

- **What to rent:** an Ubuntu 24.04 VPS in Mumbai with 8 GB of memory, 2 CPUs and at least 80 GB of disk.
- **One option:** Hostinger KVM 2, which has those specifications.
  - Price: its India page listed it at $8.99 a month, and Indian reviews quote about ₹799 to ₹929 a month on a 12-month term, before 18% GST.
  - Renewal: it renews higher (about ₹1,199 a month, per those reviews).
  - Check the price at checkout. These figures were checked on 20 October 2026.
- **Keep two things safe:** the server's IP address and the root password (or your SSH key). They go in your password manager.

### 2.2 Install SecuRAX on it (two commands)

1. **Sign in to the server:** from your laptop, `ssh root@<server IP>`.
2. **Download the installer and read it:** it is short.
   ```
   curl -fsSLO https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/install.sh
   less install.sh
   ```
3. **Run it:** the first part names the repository, because a downloaded copy has no brand.env beside it.
   ```
   sudo SECURAX_REPO=rohan2pt0/ai-cloud-cyber-range bash install.sh --server
   ```
   From the next release on, `releases/latest/download/install.sh` has the name built in, and `sudo bash install.sh --server` is enough.

It says each step as it goes:
- system packages and automatic security updates
- the time zone set to India, so the routines run at Indian times (change it with `SECURAX_TZ`)
- Docker, from Docker's own signed repository
- a firewall that lets in SSH only
- 4 GB of swap
- a user `securax` that runs everything (not root)
- SecuRAX installed and started, its schedules switched on

At the end it starts `./securax online setup` (section 2.3).

**Bring your data from the laptop** instead of starting empty:
1. On the laptop: `./securax backup`.
2. Copy the backup and its key file to the server: `scp backups/securax-*.tar.gz.gpg <your key file> root@<server IP>:`.
3. On the server: `sudo SECURAX_REPO=rohan2pt0/ai-cloud-cyber-range bash install.sh --server --restore securax-<date>.tar.gz.gpg --keyfile <your key file>`.

### 2.3 Your addresses and the sign-in gate

**First time only, in Cloudflare (about 5 minutes):**
1. **Zero Trust:** open `one.dash.cloudflare.com`, choose a team name and the Free plan.
2. **An API token:** `./securax online setup` shows the four permissions it needs. Create the token in My Profile > API Tokens, then paste it when asked.

**Then one command, on the server:**
```
sudo -iu securax
cd ~/securax && ./securax online setup
```
It asks for your e-mail address, then creates:
- the tunnel
- `hub.<domain>` and `chat.<domain>`
- the sign-in gate (only your e-mail)
- the settings the estate needs

Then it restarts the estate with the tunnel. Running it again is safe: it repairs what is missing and makes nothing twice.

### 2.4 Sign in with Google (optional, about 10 minutes)

Until you do this, Cloudflare e-mails you a one-time code at each sign-in, which already works.

1. **Make a Google sign-in client:** in the Google Cloud console:
   1. Create a project.
   2. On the OAuth consent screen, choose External.
   3. Create an OAuth client of type Web application.
   4. Authorised redirect URI: `https://<your team>.cloudflareaccess.com/cdn-cgi/access/callback`.
2. **Connect it:** `./securax online google <client ID> <client secret>`.

The e-mail code stays switched on next to Google. If Google ever locks you out, you can still get into your own estate.

### 2.5 Each device

- **Open and install:** open `https://hub.<domain>`, sign in, then install it as an app (above).
- **Nudges on your phone:**
  1. Run `./securax notify setup` (subscribe to the topic it shows in the free ntfy app).
  2. Run `./securax routines on checkin-nudge`, for a check-in nudge at 7am and 7pm.

## 3. Who gets in, and how to change it

| To | Run |
|---|---|
| Let another of your accounts, or a family member, in | `./securax online allow name@example.com` |
| Take someone off the list | `./securax online remove name@example.com` (it never removes the last one) |
| See your addresses and whether the tunnel is up | `./securax online status` |
| Take the estate offline at once | `./securax online off` (nothing is lost; `online setup` brings it back) |

A sign-in lasts 30 days on a device (`ONLINE_SESSION=720h` in `.env`; a shorter value is safer, a longer one asks less often).

## 4. What this trades, plainly

- **Cloudflare sees the traffic.** It opens the encryption at its edge to check the sign-in, then re-seals it to your server. Keep regulated customer data out of this personal estate. The gateway's own residency rail (doc 36) still decides where AI calls may go.
- **Three outside parties are involved, and each has a fallback:**
  - **Cloudflare:** if it is down, use Tailscale (doc 58), which still works.
  - **The VPS company:** the nightly encrypted backup goes off the server (doc 72), and `install.sh --server --restore` rebuilds on any new VPS. That is the `laptop-lost` scenario in `./securax continuity`.
  - **Google:** the e-mail code stays switched on.
- **Chat trusts the sign-in only while every port is on 127.0.0.1.** If you later set `BIND_HOST=0.0.0.0` (the "use it on your phone" answer in `setup`), `up` switches that trust off and says so, because on your network the header could be forged. Chat then asks for its own password; `online setup` restores it.
- **One server is still one machine.** It restarts its services by itself after a reboot. Add a second machine (doc 86): both then hold the same data and serve the same addresses, so either one can stop.

## 5. Building it further without Claude Code

- **`./securax brief "the task"`:** writes the brief any model can act on:
  - the files the task most likely touches, each with its own one-line purpose
  - the lessons from earlier mistakes that share the task's words
  - the exact checks for those kinds of files
- **Where it is used:** `./securax autobuild` and `./securax build` send it to the model in place of the bare task, and hand it the top files.
- **Outside SecuRAX:** paste it into ChatGPT, Gemini or OpenCode.
- **Why it matters:** cheaper models mostly fail by editing the wrong file, repeating an old mistake, or stopping before the checks pass. The brief removes all three.

## 6. Cues taken from your material

| Cue | Taken as |
|---|---|
| "Log in and start working, like ChatGPT, Gemini or Claude" | One address, Google sign-in, sync that pairs itself, installable apps |
| "Many devices, mobile too, seamlessly" | Cloudflare Access in front of the hub and Chat; the Life OS pairs on sign-in; the Command Center installs as its own app |
| "No headache, like a SaaS tool pulling everything from the cloud" | An always-on server in India, set up by one installer, with schedules, swap, updates and a firewall |
| "I won't need much Claude Code after this" | The task brief, used by autobuild, build and escalate |

## Sources

- [Cloudflare: create a tunnel through the API](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel-api/)
- [Cloudflare: create an Access application](https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/applications/methods/create/) and [reusable policies](https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/policies/methods/create/)
- [Cloudflare: Google as a sign-in provider](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/google/)
- [Open WebUI: sign-in through a trusted header (Cloudflare Access)](https://docs.openwebui.com/features/sso)
- [Hostinger: VPS in India](https://www.hostinger.com/vps/servers/india) and [Hostinger India pricing review](https://hostadvice.com/hosting-company/hostinger-reviews/hostinger-india-pricing/)
- [Tailscale pricing](https://tailscale.com/pricing/) (the fallback path, free for 6 users)
