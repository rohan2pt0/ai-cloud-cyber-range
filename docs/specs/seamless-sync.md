# Spec: seamless-sync — sign in once, every device has the same Life OS

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** Spec and threat-model outline only: sign in once, sync with no key to paste. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Queue item `seamless-sync` · owner 2026-11-18 · strong tier (sync, keys, sign-in): built by hand, threat model first.

## The ask, in the owner's words

"The Life OS asks to sync all devices (mobile, iPad, laptop): the biggest friction. It must be seamless, like ChatGPT or
Claude: they don't ask me to sync after I log in. And I need to copy-paste one more key: the real friction I see every day."

## What is wrong today (diagnosed 2026-11-18)

- Two sync paths, both ask for a secret on each device: the estate hub (`gm_sync_cfg`: address, user, a pasted key) and
  OneDrive (Microsoft sign-in plus the same passphrase typed on each device, `gm_sync_odk`).
- To verify on the owner's devices: does the Microsoft token (`gm_ms_tok`, about an hour) fall back to an interactive
  sign-in instead of a silent refresh? Is the Life OS opened from the home-screen app on iPhone and iPad? (In Safari as a tab,
  storage the site has not touched for 7 days can be cleared; an installed web app is exempt.)

## The outcome

Open the Life OS on any device, sign in once with the account you already have (Microsoft or Google), confirm with Face ID or
a fingerprint, and your data is there and stays in step. No address, no key, no passphrase, no "sync" button.

## Design (the 20% that removes 80% of the friction)

1. **Transport: the person's own drive app folder** (OneDrive `approot`, Google Drive `appDataFolder`), the narrowest scope.
   Sync runs by itself on open, on change (debounced) and on return to the app; there is no sync button, only a quiet
   "Up to date · 2 min ago" line.
2. **Key: from a synced passkey** (WebAuthn `prf` extension). The passkey lives in iCloud Keychain or Google Password
   Manager, which already copy it to the person's devices; the same passkey gives the same key on each device, so data stays
   end-to-end encrypted (the drive provider cannot read it) and nothing is ever typed or pasted.
3. **Fallback where PRF is missing:** a device already in shows a QR; the new one scans it once (a one-time, short-lived,
   key-wrapping code, `zero-setup`). Never a pasted key.
4. **Tokens:** silent refresh (MSAL-style refresh with PKCE, no client secret); an interactive sign-in only when the
   account itself asks for it.
5. **Migration:** an existing passphrase or hub key re-wraps the data key once under the passkey, then is forgotten.
6. **The estate hub stays** as an optional second copy (no single point of failure), paired by the same QR, not a key.

## Threat model (fill `governance/threat-models.json` BEFORE any code)

Parts: the PWA on each device; the drive app folder; the passkey provider; the QR hand-over. Trust boundaries: device ↔
drive, device ↔ device (QR). STRIDE to answer, with evidence: a stolen drive token (data is sealed, key not in the drive);
a phished QR (short-lived, shown only after the device's own unlock, confirms the new device's name); a lost phone
(revoke its passkey; re-wrap the key); tampering with the sealed file (AES-GCM, versioned); replay of an old file
(monotonic version per device); the provider reading data (cannot without the passkey).

## Tests that prove it

- jsdom: a second device with the same fake PRF output reads the first device's sealed data with no prompt and no input.
- jsdom: no screen in the sync path contains an input for a key, passphrase or address (`one-door`, `zero-setup`).
- Real browser: two contexts, one sign-in each, a change on one appears on the other within 10 s.
- Robustness: a damaged sealed file is quarantined, never applied.

## Rail (amoeba to enterprise)

One person, their own drive → a family (each member's passkey wraps the same household key) → an organisation (the
key wrapped by the tenant's KMS through the one door). Declare the path in `governance/evolution.json`.
