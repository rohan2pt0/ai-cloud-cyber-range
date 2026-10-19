# 72 · Sync and backup without the laptop

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** OneDrive end-to-end encrypted sync, daily encrypted backup, estate off-site copy and quarterly restore drill are built and tested; hosting the app off the laptop is the remaining step. [What the lights mean](../index.md#the-status-lights)
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

1. **Azure app.** Add every address the app is opened from as a **Single-page application** redirect URI, for example `https://hub.securax.localhost/guiding-map/` and the hosted address, if you host one. Sign-in fails on an address that is not listed.
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

## What is still a single point of failure

- **Hosting the app itself.**
  - An installed PWA opens from its own cache with no network, but a first install and updates need somewhere to load it from.
  - Today that is the laptop's estate.
  - Hosting the static files on a free static host (Cloudflare Pages behind Cloudflare Access, which the service worker already supports, or GitHub Pages) removes it. Add that address as a redirect URI.
- **Microsoft 365.** If your Microsoft account is unavailable, devices keep working offline and catch up later. The JSON export (Ops → Export) remains the provider-independent copy.

## Proof

- **Life OS sync:** `guiding-map/tests/test22.js` runs two simulated devices against a fake Microsoft Graph that enforces ETags. It checks that:
  - shared state reaches the other device
  - only ciphertext is stored
  - simultaneous edits on both devices are both kept
  - a wrong passphrase is refused and receives no data
  - the key never appears in an export
- **Estate backup:** the off-site copy and the drill were tested end to end on a scratch folder.
