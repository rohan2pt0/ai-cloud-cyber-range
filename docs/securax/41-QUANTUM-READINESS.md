# 41 · Quantum readiness: what is protected, what is not, and what to do first

*Written 14 Oct 2026. Everything below is read from the estate by `./securax crypto`; nothing is asserted without a check.*

## The threat, in three lines
A large quantum computer breaks the public-key maths behind today's TLS key exchange, certificates, JWT signatures and VPN handshakes (Shor). It does **not** break well-sized symmetric encryption (AES-256) or SHA-2 (Grover only halves their strength). Traffic recorded today can be decrypted later ("harvest now, decrypt later"), so **key exchange is the urgent part**; signatures and certificates matter only at the moment they are checked, so they can follow.

## What changed
| Where | Before | Now |
|---|---|---|
| Browser / phone ⇄ HTTPS edge | classical X25519 / P-256 | **hybrid X25519 + ML-KEM-768** offered first (FIPS 203); classical fallback for clients without it. Needs OpenSSL 3.5, so the edge and sidecars moved from nginx 1.27 (OpenSSL 3.3, which would have refused to start with this setting) to **nginx 1.30**. |
| Backups | plain `tar.gz`, owner-only | **AES-256 encrypted** when you set a key file or use a passphrase; wrong key and tampered file are refused before anything is touched |
| Knowing where you stand | nothing | `./securax crypto` (ranked inventory), `--cbom` (CycloneDX 1.6 Cryptography Bill of Materials), `--strict` (exit 1 for cron/CI) |
| Regulatory view | none | `./securax comply pqc` (17 items; entity obligations kept separate) |

Proven by the sandbox against the real stack: the `tls_edge` journey negotiates `X25519MLKEM768` with an OpenSSL 3.5 client and shows a classical-only client still connects; `backup_encrypted` takes an encrypted backup, shows it is not a readable archive, refuses a wrong key and a tampered copy, restores the account with the right key, and checks no decrypted copy is left in `/tmp`.

## Check where you stand (30 seconds, no jargon)
```
./securax crypto
```
It answers four questions in plain words: what needs you **now**, what is **already protected**, what **can wait**, and what is **outside SecuRAX** (your side). The full technical table (the CBOM an auditor asks for) is `./securax crypto --full`; `--cbom` writes it as a CycloneDX file. The Cockpit shows the same two things as traffic lights ("Backups locked", "Quantum-resistant connections").

## Protect your backups (2 minutes, one command)
```
./securax protect          # Windows: double-click PROTECT-BACKUPS-Windows.bat
```
It makes the key, asks you ONE question (where to keep a second copy: type a USB drive letter, or press Enter and it shows you the key to save in your password manager), switches encryption on, takes your first encrypted backup and proves it opens with your key. After that every backup, including the one `./securax update` takes first, is encrypted without you doing anything. Lose the key and the backups cannot be opened by anyone, so the safe copy matters more than anything else here.

Why there is no "Protect" button in the browser: a page that could run commands on your computer would be a door for any malicious website to push through. The Windows double-click and the Cockpit's status lights give you the ease without that door.

Restore on a new machine: `./securax restore FILE --keyfile /path/to/key` (or type the passphrase if you used `./securax backup --passphrase`).

**Why a symmetric key and not a public/private key pair:** a key pair would reintroduce RSA/ECC, the very thing a quantum computer breaks. Strength here is the strength of your key file or passphrase (OpenPGP symmetric, AES-256, iterated and salted key derivation, modification detection). `gpg` is required (`sudo apt install gnupg`; it is normally already there).

## What `./securax crypto` found about this estate (do these in this order)
1. **Backups** (ours, harvest-now exposure) - fixed above once you set a key file.
2. **Remote access (Tailscale / WireGuard)** (third-party, harvest-now exposure) - WireGuard has no standard post-quantum handshake yet; a pre-shared key is the interim mitigation. Keep sensitive traffic on the local network.
3. **Estate CA** - valid 10 years, i.e. past 2035, the date NIST's *draft* IR 8547 proposes for disallowing P-256. It is private, so the reissue date is yours; reissue as ML-DSA/hybrid once tooling supports it.
4. **Gateway token signatures** - RS256 (RSA) and HS256 only; no ES256/EdDSA/ML-DSA path. HS256 with a 256-bit secret is the quantum-safe choice for service tokens meanwhile.
5. **Calls to cloud AI providers** - the router image offers hybrid key exchange (probed), but the provider decides what is accepted. Sensitive classes stay local by the data-tier router.
6. Release signing (Sigstore, ECDSA) - third party; not retroactively forgeable.

## What this does NOT do
- It does not make the entity "quantum-safe": inventory of the entity's wider estate, vendor roadmaps, HSM/KMS custody, a migration plan, an owner and Board reporting are the entity's (marked 🏛 in the map).
- Post-quantum **certificates** (ML-DSA) are not issued: browsers and CA tooling do not accept them yet. This is the largest remaining gap and is safe to defer because a signature cannot be forged retroactively.
- Nothing here is an RBI requirement. The RBI formed the **Q-SAFE committee on 25 May 2026** (terms of reference include a cryptography inventory / CBOM, crypto-agility, most-exposed systems, vendor tool maturity and a roadmap; the report is due about six months after its first meeting). Re-read `comply pqc` when it publishes.
- NIST IR 8547 (deprecate 112-bit RSA/ECC after 2030, disallow 128-bit after 2035) and FIPS 206 (FN-DSA) are **drafts** as far as secondary sources show; the Indian Express article's DST dates (2027/28/29) and EU dates are unverified claims. FIPS 203/204/205 (13 Aug 2024) and the March 2025 HQC selection are NIST's own.

## Sources
- RBI press release on the Q-SAFE committee, 25 May 2026: <https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62803> (and MediaNama's report)
- NIST post-quantum project: <https://csrc.nist.gov/projects/post-quantum-cryptography>
- NGINX on post-quantum support (OpenSSL 3.5, `ssl_ecdh_curve X25519MLKEM768`): <https://blog.nginx.org/blog/pqc-nginx>
