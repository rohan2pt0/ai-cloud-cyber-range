# 98 · Leave Claude Code for good, and put the apps in the stores

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: ./securax ship opens the pull request, watches CI, briefs autobuild on red (one push a round, at most two rounds), merges when green and mergeable, and resets the branch; the pr-watch routine runs it unattended. ./securax os mobile makes a Capacitor (Android and iOS) project and a Trusted Web Activity manifest from any kit app or the Life OS; mobile-check names what a reviewer would stop on; the estate sync answers store apps' origins. Not yet proven on a real store submission; the native abilities Apple's rule 4.2 needs are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:**
- Building SecuRAX still needs Claude Code. Make SecuRAX able to build itself.
- Build everything so it can become an Android or iOS app without friction.

## 1. Why Claude Code was still needed

Doc 83 moved the coding itself to OpenCode and the open models. Its own table named what was left:

| Claude Code did | Before this | Now |
|---|---|---|
| Opened the pull request | `gh pr create` by hand | `./securax ship pr` (fills the repository's template) |
| Watched CI and fixed a red check by itself | you read CI on GitHub and pasted the failure into OpenCode | `./securax ship watch N --fix 2` writes the failure brief and lets autobuild fix it |
| Merged when green and reset the branch | by hand | `./securax ship watch N --merge` |
| Kept going while you were away | it ran in the cloud | the `pr-watch` routine runs the loop every 15 minutes on your always-on machine (doc 79) |

On your own machine, `./securax ship check` names whatever is still missing, each with its fix. Typically that is:
- the GitHub token;
- OpenCode;
- the OpenCode Go key.

## 2. The ship loop

```bash
./securax ship check                     # what this machine still needs
./securax ship login                     # a GitHub fine-grained token, kept in vault/github-token (0600)
./securax ship pr                        # push this branch, open its pull request
./securax ship watch 123 --fix 2 --merge # wait; fix red (at most 2 rounds); merge when green
./securax routines on pr-watch           # the same, unattended, every 15 minutes
```

**The token:** a fine-grained token for this one repository, with these permissions:
- Contents: read and write;
- Pull requests: read and write;
- Actions: read;
- Checks: read.

**What a round does:**
1. Fetches the failing jobs' logs.
2. Writes a private brief in `vault/ship/`. The brief holds the telling lines, the recent lessons and the rule: never skip, disable or weaken a test.
3. Runs `./securax autobuild` with the brief on the pull request's branch.
4. Pushes only if autobuild's own gate (verify, diffcheck) went green.

**The rules it keeps:**
- One push a round, because each push restarts the 40-minute sandbox.
- It merges only when every check passed and GitHub calls the pull request mergeable.
- It waits on people (a "blocked" pull request) without pushing.
- It never rewrites history, except resetting its own branch after a merge.
- After two rounds it stops and hands the brief to a person, or to `./securax opencode --strong`.
- It tells your phone when it merges or needs you (`./securax notify`).

## 3. A day without Claude Code

1. Pick the tier: `./securax route "the task"`.
2. Do the work:
   - most tasks: `./securax opencode`;
   - hard ones: `./securax opencode --strong`;
   - unattended: `./securax autobuild "..."`.
3. Get a second look: `./securax review`.
4. Ship it: `./securax ship pr`, then leave it to `pr-watch`, or run `ship watch --fix 2 --merge`.
5. Each month, check who did the work: `./securax ai share`.

What still needs a person: product decisions, and a red check that two rounds of autobuild could not fix. The brief is then waiting in `vault/ship/`.

## 4. Store apps: two ways

| | Trusted Web Activity (Android only) | Capacitor (Android and iOS) |
|---|---|---|
| What it is | The Play Store app opens your own https address full screen | The app's own files ship inside the app, and it works offline |
| Needs | the app served over https on your domain (doc 78), and `/.well-known/assetlinks.json` | Node; Android Studio for Android; a Mac with Xcode for iOS |
| Make it | `./securax os mobile vantage --host https://your.domain` gives `twa-manifest.json` for Bubblewrap | `./securax os mobile vantage` gives the Capacitor project |
| Updates | every estate update reaches the app at once | a new store build per release |

```bash
./securax os mobile vantage --host https://your.domain   # build/mobile/vantage/ with README.md, the exact steps
./securax os mobile-check vantage                        # what a reviewer would stop on
./securax os assetlinks vantage --fingerprint AB:CD:...   # the Android link file, from your signing key
./securax os mobile lifeos                               # the Life OS too
```

The package id comes from your own domain in `brand.env`, for example `org.example.vantage`. Capacitor is pinned to version 8.0.0 ([upgrade notes](https://capawesome.io/blog/how-to-upgrade-your-capacitor-app-to-capacitor-8)). Raise it on purpose, never by accident.

**Sync on a phone:**
- A store app runs from its own origin: `capacitor://localhost` on iOS, `https://localhost` on Android.
- The estate's sync now answers those origins, and only for the state and snapshot calls. It sends no cookies, and the device token is still required.
- In the app's Settings, pair it with your estate's full address ending in `/sync`, your user name and a device key.
- Your Cloudflare sign-in cookie does not reach a store app. A device key, over Tailscale or your own address, does.

## 5. Store-ready by design

Every app built from the kit already has what reviewers check:
- It is one self-contained page, and nothing loads from another site. Apple's reviewers try apps in airplane mode, and an app that shows a browser error there is flagged as a web wrapper ([guideline 4.2](https://www.technetexperts.com/guideline-4-2-minimum-functionality/)).
- Its data stays on the device under its own names, with backup and export.
- It has both icon sizes, opens full screen, keeps clear of the notch (`viewport-fit=cover`, safe-area padding), has tap targets of at least 40 pixels, and passes contrast checks in both themes.

`./securax os mobile-check` proves this for each app. A test fails CI if any app built from the kit ever stops being store-ready.

## 6. What waits, and the costs

**Apple's 4.2 rule:** a wrapped web app needs at least one thing a home-screen web app cannot do. Before an App Store submission, add one native ability:

| Native ability | Target |
|---|---|
| Local notifications for a review that comes due, with the Capacitor plugin (the same date as the reminders in doc 95) | 2026-12-01 |
| Face ID or fingerprint unlock | 2027-01-31 |
| The share sheet, for the Board pack and backups | 2027-01-31 |

Android through Play has no such rule for the Trusted Web Activity path.

**Costs** (check them on the day; neither page was confirmed for 2026):
- **Google Play:** a one-time developer registration fee, quoted at US$25 in [older guides](https://vaadin.com/blog/submitting-a-pwa-to-google-play-store-using-bubblewrap).
- **Apple:** the Developer Program, US$99 a year to our knowledge.
- **A Mac:** iOS builds need one, or a cloud Mac build service.

**Store listing:** each store asks for screenshots and a privacy form (Play's Data safety, Apple's privacy labels).
- The screenshots come from `guiding-map/tests/kit_audit.py`, which already captures every app in both themes.
- The privacy answers are short, because data stays on the device and syncs only to your own estate.
- For India, the DPDP Act notice still applies to any personal data you hold for others (doc 96).

## 7. Proof

- **`lifecycle/tests/test_ship.py`:**
  - red, pending and green are told apart, and no checks at all is never green;
  - the brief is private and carries the rule;
  - green and mergeable merges; blocked, red or conflicted does not;
  - fix rounds stop at their limit;
  - the body follows the template without its instructions;
  - a missing token is a clear setup step.
- **`apps/estate-sync/tests/test_app_origins.py`:**
  - the app origins may ask and read;
  - the token is still required;
  - other origins and other paths get nothing.
- **`governance/tests/test_oskit.py`:**
  - a store project is one command, with pinned versions;
  - a page that loads from another site fails the readiness check;
  - the Android link file needs a real fingerprint;
  - every kit app stays store-ready.

## Sources

- [Bubblewrap and Trusted Web Activities](https://web.dev/using-a-pwa-in-your-android-app)
- [Digital Asset Links for TWAs](https://developer.chrome.com/docs/android/trusted-web-activity/android-for-web-devs)
- [Capacitor 8 upgrade guide](https://capawesome.io/blog/how-to-upgrade-your-capacitor-app-to-capacitor-8)
- [Capacitor support policy](https://capacitorjs.com/docs/v7/main/reference/support-policy)
- [Apple guideline 4.2 explained](https://www.technetexperts.com/guideline-4-2-minimum-functionality/)
