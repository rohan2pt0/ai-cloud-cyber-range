# 130 · Go-live runbook — a new laptop, a server, your phone, and AI without paid Claude

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The Life OS and Vantage are now published with the product site (tools/pwa_publish.py, run by website/build.sh), so they open and install on every device with no machine of yours running: proved in a real browser under the GitHub Pages subpath (service worker active and scoped, manifest valid, renders, reloads fully offline, no page errors) and by test_pwa_publish.py. The runbook for the new low-memory laptop (RAM-aware WSL setting), the always-on server, the three clouds (sign-in only) and SecuRAX AI on free keys with no paid Claude is assembled from commands that already exist and were each checked to exist, but the laptop, server and cloud steps themselves have not been run on real machines here. Tests: test_pwa_publish.py, test_doc_recipes.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The situation this is for.** The one machine that served the Life OS has died. The fix is not a better laptop. It is to stop
depending on any one machine: the app is now **hosted as a static site** (opens on every device, even with all your machines
off), the **always-on work moves to a server**, and the laptop becomes a thin client that can be low on memory. The AI side
runs on the free providers and your own local model, so nothing in the estate needs a paid Claude plan to run, update or fix.

Everything here uses commands that already exist. Do the steps in order. Each ends with a check.

## 0. First, protect what you have (10 minutes, before anything else)

Your Life OS data lives in three places. Find out which of them still has it, and do not delete any.

1. **The installed app on your phone.** Do **not** uninstall it or clear its site data. Open it: **Ops → Export backup** saves a
   file. Keep that file somewhere safe (not only on the phone).
2. **Your encrypted OneDrive copy**, if you ever turned on sync (doc 72). It is safe there. You need your sync passphrase.
3. **The broken laptop's disk.** The machine is dead, the disk probably is not. A Windows laptop usually has **BitLocker** on:
   the disk can only be read in another machine with its **recovery key**. Get it from your Microsoft account
   (`account.microsoft.com/devices/recoverykey`) *before* you take the disk out. If you ran `./securax backup offsite`, you may
   not need the disk at all (section 2, "Bring your data back").

## 1. Open the Life OS on every device (5 minutes, no machine needed)

The Life OS and Vantage are published with the product site. Find the address:

```bash
./securax site
```

It prints `The site answers at: <address>`. Add `app/` for the Life OS and `vantage/` for Vantage:

| App | Address |
|---|---|
| Life OS | `<site address>app/` |
| Vantage (the CISO edition) | `<site address>vantage/` |

Install each on each device:

- **Chrome or Edge (laptop, Android):** the install icon in the address bar, or the menu → **Install**.
- **iPhone or iPad (Safari):** Share → **Add to Home Screen**.

Check: switch the phone to airplane mode and open the app. It opens and works. That is the point: no machine of yours has to be
running. A new release is picked up by itself the next time the device is online.

**Bring your data in.** On the new copy: **Ops → Restore from file** (the file from step 0.1), or connect OneDrive sync (below)
and **Restore newest backup**.

**Keep your data across devices** (doc 72, about 5 minutes once). In your Azure app registration, add these as
**Single-page application** redirect URIs: `<site address>app/` and `<site address>app/index.html` (the same for `vantage/`).
Then on each device: **Ops → Microsoft 365 → Connect → Turn on OneDrive sync**, and use the **same passphrase** everywhere. Write
the passphrase in your password manager: without it nobody can read the copy, you included.

> **One address, kept.** An installed app belongs to the address it was installed from. If you later put your own domain on the
> site (`./securax site live`), the apps move to the new address and start empty, then fill from OneDrive sync. So turn sync on
> first, and install from the address you will keep.

## 2. The new laptop (HP 240 G9, little memory)

This laptop is a **thin client**. It does not need to carry the estate: the always-on work goes on the server (section 3), and it
opens the hosted apps in a browser. If you still want the estate on it:

1. Update Windows. Install **Docker Desktop** and the **Ubuntu** app from the Microsoft Store.
2. Follow [the Windows quickstart](../../WINDOWS-QUICKSTART.md) from Step 1. Step 1 now reads the PC's memory and gives SecuRAX a
   safe share by itself (an 8 GB PC gives it 3 GB). The estate sees how little it has and starts only its core.
3. In Docker Desktop → Settings → General, turn on **Start Docker Desktop when you sign in**, so the estate comes back after a restart.
4. If it still struggles, run only the AI gateway and the Command Center:

```bash
cd ~/securax && ./securax up --safe
```

**Bring your data back** (only if you have a backup file; otherwise skip):

Download `install.sh` as in section 3, then run `bash install.sh --restore <your backup file>` (add `--keyfile <your key file>` for an
encrypted backup, the `.gpg` kind).

Check: `./securax why` says what is wrong, in plain words, or that nothing is.

## 3. The always-on server (about 30 minutes, once)

This is the machine that does not die with a laptop. Doc 85 has the full detail; the commands are:

First sign in to the server from your laptop with `ssh root@<server IP>`. Then, on the server:

```bash
curl -fsSLO https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/install.sh
less install.sh
sudo SECURAX_REPO=rohan2pt0/ai-cloud-cyber-range bash install.sh --server
```

It installs Docker, a firewall that lets in SSH only, updates, swap and a user `securax`, then starts SecuRAX. Rent a small Ubuntu
24.04 server in Mumbai (8 GB, 2 CPUs, 80 GB; doc 85 has a priced example, so check the price at checkout).

**Reach it from your devices without opening any port.** Use Tailscale (private, free for a few devices):

```bash
sudo -iu securax
cd ~/securax && ./securax phones
```

It checks what is in the way and prints the exact steps with your address. If you also want your own address for it, `./securax
online setup` does that (doc 85, section 2.3).

**Two machines, one set of data** (once the laptop is up): on the server `./securax nodes invite`, and on the laptop paste the
line it prints, then the same the other way round. `./securax nodes` shows each machine "in step" (doc 86).

Check: `./securax nodes` and `./securax resilience` show no machine that everything depends on.

## 4. AWS, Google Cloud and Azure: sign in now, wake nothing yet

The cloud Terraform has been proved by offline plans only, never applied to a live account (doc 29). So, while you are away:

```bash
./securax cloud login aws
./securax cloud login gcp
./securax cloud login azure
./securax cloud status
```

That proves your three accounts work, with nothing installed and nothing created. **Do not wake any cloud compute while you are
away:** it costs money and adds a public surface that nobody is watching. When you are back, `./securax stages` and `./securax
grow` start from the cheap dormant "seed bank" (storage only, with a monthly budget alarm).

## 5. SecuRAX AI as your daily assistant, with no paid Claude

Get the three free keys (about a minute each; `./securax keys` walks you through them and ends with a live test):

```bash
./securax keys
```

For serious coding add NVIDIA's free hosted Qwen3-Coder, then check what each key can use today:

```bash
./securax providers add nvidia_nim
./securax models --fix
```

| You want | Use |
|---|---|
| Everyday chat and writing | Chat, model `bank-assistant` (Gemini free tier, with your local model as the fallback) |
| Coding in the terminal | `./securax opencode` |
| Coding in a browser, with an agent | `./securax studio` |
| A quick question from the terminal | `./securax ask <agent> "…"` |
| Anything sensitive | Chat, model `bank-assistant-local` (stays on your machine) |

**Two honest points.**

- **Free tiers have terms.** Google's free Gemini tier may use prompts to improve its products and let people read them, so keep
  customer, regulated or employer data out of it. Pick `bank-assistant-local` for that, explicitly; do not rely on a ladder (doc
  24). The estate's gateway also classifies each request and keeps the highest tier of data on local models. Check each
  provider's own terms page; free-tier terms change.
- **The gap is real.** Open and free models handle the large majority of daily work. The hardest multi-file coding is where a
  paid frontier model is still ahead; the answer is to break the task into steps and let `./securax opencode` loop on it, not to
  go back to a subscription.

## 6. Before you leave: the checklist

| Check | Command or action | Good looks like |
|---|---|---|
| The apps open with every machine off | Phone in airplane mode, open the app | It opens |
| Your data is safe off the device | Ops → OneDrive sync on, or **Export backup** kept | A dated file or a synced status |
| The estate is healthy | `./securax selftest` | `every command is wired, loads, and the read-only ones run clean` |
| An off-site backup exists | `./securax backup` then `./securax backup offsite` | A verified copy |
| No machine is a single point of failure | `./securax resilience` | No critical single point of failure that is not accepted |
| The AI answers on free keys | `./securax keys` | A live test names the provider that answered |
| It keeps itself current | `./securax routines` | The update and backup routines are on |

## 7. If something breaks while you are away

Go down this list and stop at the first fix that works.

1. `./securax why` — what stopped, and the plain-English reason.
2. `./securax next` — the one thing to do now.
3. `./securax up --safe` — start only the core when memory is short. `./securax up` brings everything back.
4. `./securax update` — gets the latest safely; it goes back by itself if the new version does not start.
5. Ask the estate itself (this uses your free keys, not a subscription): `./securax ask <agent> "what does this error mean: …"`, or
   open `./securax studio` and let the agent read the repository with you.
6. The apps are hosted, so they stay up whatever happens to a machine. Your phone's app keeps working offline.

## What this deliberately does not do

- It does not bridge a Google or Antigravity consumer login into a Claude-compatible gateway. Those routes are unofficial,
  against the provider's terms, and the projects that do it warn that Google detects and bans such accounts. Use the official
  free API keys above.
- It does not stand up cloud compute on three clouds while nobody is watching.
- It does not put a password vault or any customer data on a public address.
