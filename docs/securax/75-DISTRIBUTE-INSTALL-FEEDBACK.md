# 75 · Distribute, install, feedback: how SecuRAX reaches people and gets better

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the installers (online, stable, offline with checksums), the release assets with signed provenance, the support packet and Report a problem. The Play Store build waits on a public site, a signing key and a Play account. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The question.** How do mature open-source tools reach people? Mattermost is the model here, with Rocket.Chat beside it. How do they keep installing simple, and turn bug reports into fixes? This page records what they do, what SecuRAX now does the same way, and what waits for later.

## What the mature tools do

| | Mattermost | What SecuRAX does now |
|---|---|---|
| **Server install** | A signed package repository on Ubuntu; a tarball for other Linux and for air-gapped sites; a Kubernetes operator for production; Docker for trying it out | `install.sh` on Linux and macOS, `install.ps1` on Windows (through WSL), an offline archive with checksums; Docker Compose runs the estate; the k3s cluster and Argo CD for more than one machine (docs 10 and 29) |
| **Desktop and phone apps** | A store app or installer on each platform (Microsoft Store, MSI, App Store, DMG, AppImage, deb, rpm, Flatpak); phone apps in both stores | The Life OS is a web app you install from the browser (⋯ → Install as an app) on Android, iOS, Windows, macOS and Linux. A Play Store build is planned (below) |
| **Release rhythm** | A monthly feature release. An Extended Support Release every 9 months, supported for 12 | The rolling channel (main, which the nightly update follows) and numbered releases (doc 21). An ESR-like long-term line comes when there are outside users |
| **Proof of what you got** | Signed packages and published checksums | Every release carries SHA256SUMS, a CycloneDX SBOM and a signed build provenance (`gh attestation verify`) |
| **Bug reports** | A public issue tracker with templates; a support packet from the admin console or `mmctl` | GitHub Issues with bug and feature forms; **Report a problem** in the Life OS; `./securax support-packet` |

## Install: one command per platform

**Linux, macOS or WSL:**

```bash
curl -fsSLO https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/install.sh
less install.sh          # read it first: it is short
bash install.sh          # or: bash install.sh --stable   (the newest release)
```

**Windows 10 or 11 (PowerShell):**

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File install.ps1
```

**What the installer does:**

1. It checks for Python 3.10 or newer, Git and Docker, and gives the exact install line for anything missing.
2. It puts the code in `~/securax`, or in `--dir PATH`.
3. It adds the `securax` shortcut and prints the next command, `./securax up`.

**What it never does:** it never uses sudo, never starts anything and never changes a folder that already exists. On Windows it only checks for WSL and Ubuntu, then runs `install.sh` inside Ubuntu.

**No network (an air-gapped site, a bank's lab):**

1. Download `securax-X.Y.Z.tar.gz` and `SHA256SUMS` from the same release.
2. Copy both across, then run `bash install.sh --offline securax-X.Y.Z.tar.gz`.

The installer refuses an archive whose checksum does not match. You can also check where the file came from with `gh attestation verify securax-X.Y.Z.tar.gz --repo rohan2pt0/ai-cloud-cyber-range`.

## The channels

- **Rolling (the default):** the main branch. `./securax update` and the nightly routine follow it, with a backup first and an automatic rollback.
- **Stable:** a release tag, installed with `bash install.sh --stable` or `--version vX.Y.Z`. You cut a release by pushing the tag (doc 21). Each release now publishes the source as `.tar.gz` and `.zip`, the two installers, `SHA256SUMS`, the SBOM and the provenance.
- **Long-term (later):** an ESR-like line, once other people run SecuRAX. It means fixes backported to one release for about a year. Until then it would be ceremony, not value.

## Feedback: from "something is off" to a fix

1. **In the Life OS:** ⋯ → **Report a problem or idea** shows the details a helper needs:
   - the build, the device and the screen size
   - the theme and the tab
   - the last five script errors

   Nothing personal goes in: no name, no numbers and no notes. You copy the details yourself, and **Open a bug report** opens the bug form with the version filled in. Security problems never go in a public report; use the private advisory form instead.
2. **For the estate:** `./securax support-packet` writes one zip to `vault/support/` (private, never in git). It holds:
   - the versions and the health check
   - the running containers
   - your setting **names**, with values shown only as `<set>` or `<empty>`
   - the routine runs and the last 200 log lines

   Before the zip is written, e-mails, keys and tokens, long numbers and your home folder's path are scrubbed out. Look inside with `python3 -m zipfile -l FILE`, then attach it to the report.
3. **Triage:** each report gets a label (bug, idea, security), one owner and a target release. Fixes ride the normal path: the change, the tests, a CHANGELOG line, then the release.
4. **The loop closes when** the fix ships and the report links the release.

Why GitHub Issues and not a separate bug tracker such as Bugzilla, Redmine or GitLab? Issues needs no server to run, it already holds the forms and the security advisories, and each fix links to its code. A self-hosted tracker becomes worth it only when reports must stay off GitHub. Then the same forms move into the estate's own Mattermost or TheHive cases (docs 10 and 39).

## Later, with what each step needs

| Step | Needs | Cost (checked October 2026) |
|---|---|---|
| **Android app in the Play Store** (a wrapper around the web app, built with Bubblewrap) | The Life OS on a public HTTPS address (doc 73's Cloudflare step); a signing key kept in the vault; a link file proving the site and the app belong together; a Play developer account | Google: US $25, once. A new personal account must also run a closed test with 12 testers for 14 days before going public. Confirm the fee on Google's sign-up page before paying |
| **iPhone app in the App Store** | A Mac, an Apple developer account, a native wrapper | Apple: US $99 a year (reported as ₹8,700 in India) |
| **Package repositories** (apt, rpm, Homebrew) | A signing key and a hosted repository | Free on GitHub Pages; the work is upkeep |
| **A Windows or Mac installer for the CLI** | Code-signing certificates | Paid each year; not worth it while WSL works |
| **A Docker image of the whole estate** | Already partly done: the gateway image is published (doc 21) | Free |

**The order that pays off first:** the Play Store build, once the site is live, because most people will use the Life OS on a phone. The rest waits for outside users.

## Sources

- Mattermost: [Deploy](https://mattermost.com/deploy/) · [Server on Linux](https://docs.mattermost.com/deployment-guide/server/deploy-linux) · [Kubernetes](https://docs.mattermost.com/deployment-guide/server/deploy-kubernetes.html) · [Desktop app](https://docs.mattermost.com/end-user-guide/access/install-desktop-app) · [Release policy](https://docs.mattermost.com/product-overview/release-policy) · [Extended Support Release](https://docs.mattermost.com/upgrade/extended-support-release.html) · [Support packet](https://docs.mattermost.com/administration-guide/manage/admin/generating-support-packet)
- Android from a web app: [Bubblewrap](https://npmjs.com/package/@bubblewrap/cli) · [web.dev: a PWA in an Android app](https://web.dev/using-a-pwa-in-your-android-app) · [Play testing requirement](https://support.google.com/googleplay/android-developer/answer/14151465)
- Fees as reported in October 2026: [Play account cost](https://magora-systems.com/google-play-developer-account-cost/) · [Apple developer fee](https://magora-systems.com/apple-developer-fee/) · [Apple forum: India price](https://developer.apple.com/forums/thread/835350)
- The tests: `governance/tests/test_installers.py`, `governance/tests/test_support_packet.py`, `governance/tests/test_buildinfo.py`, `guiding-map/tests/test26.js`.
