# Laptop runbook: everything in one place

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Every command exists; the laptop, Tailscale phone and sync paths were verified on a real Windows + WSL install. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

This page is your checklist. Do part 1 once, then part 2 is all you need day to day. Parts 3 to 5 are once-only jobs you
can do whenever you have time.

## 1. One-time setup on the laptop (about 15 minutes)

All commands run in **Ubuntu (WSL)** unless the step says PowerShell.

| # | Step | Command or place | Done when |
|---|---|---|---|
| 1 | Get the latest code and start | `cd ~/securax && git checkout main && git pull && ./securax update` | it ends with READY |
| 2 | Check everything | `./securax doctor` | no red lines |
| 3 | Install the schedules (alerts, backups, regulator watch) | `./securax routines install` | `./securax routines list` shows them |
| 4 | Phone alerts | `./securax notify setup` | your phone buzzes on `./securax notify test` |
| 5 | Publish to your phones | `./securax phones --apply` | it prints `https://<laptop>.<tailnet>.ts.net` |
| 6 | **Sync, so your data is never typed in twice** | `./securax sync-link` | see below |
| 7 | Regulator watch baseline | `./securax regwatch fetch` | "nothing new (N items tracked)" |
| 8 | First backup | `./securax backup` | "Backup saved & verified" |

### Step 6 in detail: sync once, and your data follows you

The Guiding Map app keeps your data in the browser, and **every address is a separate store**. `http://localhost:8088`,
`https://<laptop>.ts.net` and the old `https://hub.securax.localhost` each start empty. Sync fixes that: your data lives
on the laptop's sync service, and every device pulls it back by itself.

1. Run `./securax sync-link`. It prints **two links**: one for this laptop and one for your phones.
2. Open the **laptop link** in Edge, in the same window or installed app you use every day, and press **OK** once.
3. Send the **phone link** to yourself over a private channel. Open it on each phone and press **OK** once.
4. That's all. After an update, a new browser or a new phone, open the link again: your data comes back. No forms.

Each link contains your sync token, so treat it like a password and never paste it into a chat.

### Which address to use

| Device | App | Chat |
|---|---|---|
| This laptop | `http://localhost:8088` | `http://localhost:3000` |
| Phones and other devices (Tailscale on) | `https://<laptop>.<tailnet>.ts.net` | `https://<laptop>.<tailnet>.ts.net:10000` |

With **NordVPN** on, the laptop cannot reach its own ts.net address (NordVPN takes the traffic). Use `localhost` on the
laptop; the phones are not affected.

### Chat (the Twin): what is kept and what is not

| Where you change it | Kept across updates? |
|---|---|
| **Settings** (your profile): system prompt, Personalization → Memory, your chats, Workspace models such as the "Twin" preset, knowledge | **Yes**, in Chat's database (and in every backup) |
| **Admin Panel** screens | **No**, on purpose: `.env` and `docker-compose.yml` are the source of truth, so a key rotation or update can never leave Chat half-configured |

To keep an Admin Panel setting permanently, put it in `.env` instead (the variable names are in doc 53), or ask for it to
be added there.

## 2. Every day

```bash
cd ~/securax && ./securax up          # after a restart; safe to run any time
./securax update                      # when there is a new version (backs up first, rolls back if it fails)
./securax why                         # something is not working
```

Backups run by themselves every Sunday at 2:30 am. To move to a new laptop: `./securax restore <file>`, then open your sync
link once.

## 3. The website on cyberbaba.org (once, about 30 minutes)

Do these in order. Step 3.1 keeps your name off the public product.

1. **Brand copy of the code.** On github.com create the organisation `cyberbaba` and an **empty** repository `securax`. Then:
   ```bash
   cd ~/securax && git pull && tools/publish-clean.sh cyberbaba securax
   ```
   Run the two commands it prints. It refuses to publish if a personal identifier is left. In the organisation: People →
   your membership → **Private**.
2. **Cloudflare Pages.** Workers & Pages → Create → Pages → Connect to Git → `cyberbaba/securax`, branch `main`. Build
   command `bash website/build.sh`, output directory `website`, variable `PYTHON_VERSION` = `3.12`. Save and deploy.
3. **Domain.** Custom domains → add `cyberbaba.org` and `www.cyberbaba.org`. SSL/TLS → **Full (strict)**, and turn on
   **Always Use HTTPS**.
4. **Email.** Email → Email Routing → forward `hello@cyberbaba.org` to your own inbox. The site's "Talk to an expert"
   buttons use it.
5. **Registrar privacy.** Namecheap → Domain List → cyberbaba.org → **WithheldForPrivacy: ON**. Leave the nameservers on
   Cloudflare.
6. Remove the GitHub environment named `DOCS_PAGES = true` (Settings → Environments). It is not used: Cloudflare serves
   the docs at `cyberbaba.org/docs/`.

The estate itself (chat, gateway, app) is **never** published on this domain. It stays on the laptop, behind Tailscale.

## 4. Building SecuRAX with SecuRAX (once, then the loop)

1. **Let git push as you:** `sudo apt install gh && gh auth login`.
2. **Protect `main`:** GitHub → the repository → Settings → Branches → add a rule for `main` → require status checks to
   pass. Nothing then reaches `main` without CI going green.
3. **The everyday build loop:**
   ```bash
   cd ~/securax && git checkout main && git pull
   git checkout -b feat/<short-name>
   ./securax autobuild "<what to build, and the tests that prove it>" --tries 3
   git push -u origin feat/<short-name>
   ```
   Open the pull request on GitHub and merge it when CI is green. `autobuild` uses your free models through the gateway
   and commits only when every check passes; it never pushes on its own.

## 5. The business side (with a CA, later)

Company (OPC or LLP, so the company name shows rather than yours), then GST, then Razorpay. Doc 61 has the order and the
questions to ask.
