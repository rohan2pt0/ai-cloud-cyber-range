# 72 · Sync and backup without the laptop

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Sync, backups and the restore drill are built and tested; hosting the app on Cloudflare Pages needs your 15-minute setup (steps in this doc). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The problem:** the Life OS (Guiding Map PWA) synced between devices through the laptop's estate. When the laptop was off, or Docker was not running, the phone and the laptop drifted apart. That made the laptop a single point of failure.

**The fix:** each device now syncs directly with your own OneDrive, over the internet, using the Microsoft 365 connection you already set up through your Azure app. No SecuRAX server needs to be running. Everything is end-to-end encrypted before it leaves the device, so Microsoft stores only ciphertext.

The laptop sync still works. The two transports share one merge, so whichever runs, the result is the same.

## How it works

| Part | What it does |
|---|---|
| Where | One file in the app's own OneDrive folder: `Apps/<your Azure app>/sync/state.enc.json`. The `Files.ReadWrite.AppFolder` permission confines the app to that folder, so it cannot read the rest of your OneDrive. |
| Encryption | AES-256-GCM. The key comes from your passphrase through PBKDF2-SHA256 with 310,000 rounds (the OWASP 2023 figure). The random salt is stored in the file; the passphrase never leaves the device. |
| Merge | Per-key, last writer wins, using each key's change time. Edits made on two devices at once are both kept when they touch different keys. The anomaly guard still refuses a remote copy that would wipe most of your data. |
| Conflicts | Every write uses the file's ETag (`If-Match`). If another device wrote first, the write is rejected (412), the device re-reads, merges and tries again, up to 3 times. |
| When | 4 seconds after any change, every 60 seconds while the app is open, when the app comes back to the foreground, and when the device comes back online. |
| Offline | Changes stay on the device and go up on the next sync. |

## Set it up (once per device)

1. **Azure app.** Add every address the app is opened from as a **Single-page application** redirect URI, for example `https://hub.securax.localhost/guiding-map/`, the same with `index.html` on the end (the installed app opens there), and the hosted address if you host one. Sign-in fails on an address that is not listed.
2. **In the app:** go to Ops → Microsoft 365, choose **Connect**, then **Turn on OneDrive sync**. Choose a passphrase of 12 or more characters.
3. **On every other device:** connect, then enter **the same passphrase**. A wrong passphrase is refused and receives no data.

Keep the passphrase in your password manager. Without it, the OneDrive copy cannot be read, by Microsoft or by you.

## Backups

**Life OS.**
- **Daily:** once a day, when connected, the app saves a dated, encrypted backup to the same app folder and keeps the newest copies.
- **Restore:** Ops → Microsoft 365 → **Restore newest backup**.
- **What is left out:** exports and backups exclude the sync key itself.

**Estate** (`./securax backup`).
- **Off-site copy:**
  1. Run `./securax backup offsite` once. It lists the OneDrive folders on the machine (Windows and WSL); pick one, and later encrypted backups are copied to `SecuRAX-backups` inside it.
  2. The OneDrive client then uploads that folder.
  3. Each copy is verified byte for byte, and the newest 12 are kept.
- **Encrypted only:** only encrypted backups (`SECURAX_BACKUP_KEYFILE`) leave the machine. An unencrypted backup stays local, with a warning.
- **Quarterly restore drill:**
  - `./securax backup drill` decrypts the newest off-site copy, unpacks it and checks every file against its `SHA256SUMS`.
  - It runs automatically at 10:05 on the first day of each quarter (routine `offsite-restore-drill`).
  - It writes the result to `~/.securax/drills.log`.

## Host the app off the laptop (Cloudflare Pages behind Cloudflare Access)

An installed PWA opens from its own cache with no network, but a first install and updates need somewhere to load it from. Today that is the laptop. A static host removes that last dependency. The host only ever serves the app's code, which is already public in this repo; your data stays on your devices and, encrypted, in your OneDrive.

**Why Cloudflare.**
- **The service worker is ready:** it already recognises a Cloudflare Access sign-in redirect.
- **Your domain's DNS is already there** (doc 60).
- **Access limits who can load the app:** an allow-list of one email address.

**Steps, about 15 minutes, once.**
1. **Pages project.**
   - In the Cloudflare dashboard: Workers & Pages → Create → Pages → Connect to Git → this repository.
   - Settings:

     | Setting | Value |
     |---|---|
     | Production branch | `main` |
     | Framework preset | None |
     | Build command | leave empty |
     | Build output directory | `guiding-map` |

   - Every merge to `main` then redeploys the app.
2. **Your own address.** In the project, Custom domains → add a subdomain such as `life.<your-domain>`.
3. **Lock it to you.**
   - In Zero Trust → Access → Applications → Add → Self-hosted, add that subdomain.
   - Add a policy that allows your email address only, with sign-in by one-time PIN or your Microsoft account.
   - In the Pages project settings, also turn on the Access policy for preview deployments, so `*.pages.dev` previews are not open.
4. **Azure.** Add both `https://life.<your-domain>/` and `https://life.<your-domain>/index.html` as Single-page application redirect URIs in your Azure app. The installed app opens at `index.html`, and sign-in returns to exactly the page it started from.
5. **Each device.**
   - Open the new address and install it (Add to Home Screen).
   - Connect Microsoft 365, then turn on OneDrive sync with the same passphrase.

**Cost.**
- **Pages:** the free plan allows 500 builds a month ([limits](https://developers.cloudflare.com/pages/platform/limits)), and this app needs no build step.
- **Access:** the free Zero Trust plan covers up to 50 users ([Cloudflare](https://blog.cloudflare.com/teams-plans)).
- These figures were checked on 19 Oct 2026; confirm on Cloudflare's pricing page.

**What stays.** The laptop estate keeps serving the app at its local address, and both copies sync through the same OneDrive file. If Cloudflare is ever unavailable, the installed app keeps working from its cache.

## What is still a single point of failure

- **Microsoft 365.** If your Microsoft account is unavailable, devices keep working offline and catch up later. The JSON export (Ops → Export) remains the provider-independent copy.

## Proof

- **Life OS sync:** `guiding-map/tests/test22.js` runs two simulated devices against a fake Microsoft Graph that enforces ETags. It checks that:
  - shared state reaches the other device
  - only ciphertext is stored
  - simultaneous edits on both devices are both kept
  - a wrong passphrase is refused and receives no data
  - the key never appears in an export
- **Estate backup:** the off-site copy and the drill were tested end to end on a scratch folder.
