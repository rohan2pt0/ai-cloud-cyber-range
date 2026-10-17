# Laptop runbook: everything in one place

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Every command exists; the laptop, Tailscale phone and sync paths were verified on a real Windows + WSL install. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**One command does the whole setup and keeps it working:**

```bash
cd ~/securax && ./securax go
```

On Windows you can double-click **START-HERE-Windows.bat** instead; it runs the same command.

`go` is safe to run any time. Each step checks first and only acts when something is missing:

| What `go` does | When it acts |
|---|---|
| Updates to the latest version (backup first, automatic rollback) or starts SecuRAX | always |
| Installs the schedules: weekly backup, phone alerts, regulator watch | only if they are not running (asks your Linux password once) |
| Publishes the app and Chat to your phones over Tailscale | only if Tailscale is signed in and nothing is published yet |
| Starts the regulator watch and takes a first backup | only if there is none from the last 7 days |
| Opens the app in your browser with sync set up | press **OK** once the first time; later runs ask nothing |
| Sends the one-tap phone link to your phone through your ntfy alerts | only if you answer **y** |

It ends with **one status screen**: a ✔ line for everything that works, and for anything that does not, one ✗ line with
the single fix. Fix that line and run `./securax go` again.

Optional, once: phone alerts with `./securax notify setup`, and Tailscale on Windows and your phone (doc 58).

### The individual steps (what `go` runs for you)

| Step | Command |
|---|---|
| Update or start | `./securax update` or `./securax up` |
| Schedules | `./securax routines install` |
| Phones | `./securax phones --apply` |
| Sync links | `./securax sync-link` |
| Regulator watch | `./securax regwatch fetch` |
| Backup | `./securax backup` |
| Health and a real chat test | `./securax doctor` |

### Sync: why your data never needs typing in twice

The Guiding Map app keeps your data in the browser, and **every address is a separate store**. `http://localhost:8088`,
`https://<laptop>.ts.net` and the old `https://hub.securax.localhost` each start empty. Sync fixes that: your data lives
on the laptop's sync service, and every device pulls it back by itself.

1. `./securax go` opens the **laptop link** in your browser. Press **OK** once; later runs ask nothing.
2. For each phone, answer **y** when `go` offers to send the phone link through your ntfy alerts, tap the notification and
   press **OK** once. Without ntfy: `./securax sync-link` prints both links; send the phone one to yourself privately.
3. That's all. After an update, a new browser or a new phone, open the link again: your data comes back. No forms.

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
cd ~/securax && ./securax go          # after a restart, or any time: updates, starts, checks, fixes what is missing
./securax why                         # something is not working: what stopped and why
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
