# Built to last: the briefs

Every gap in [built-to-last.md](built-to-last.md), as one step an open model can finish in 20 minutes. Written
2026-11-16. Queue item `built-to-last` (due 2027-01-31) points here.

**How to use one.** Copy the brief as it stands into `bash lifecycle/delegate_here.sh`. One brief, one pull request.
Write the test first, see it fail, then make it pass. Check the tier first with `python3 lifecycle/route.py "the brief"`.

**The same for every brief:**

- Gates, in this order: `ruff check .`, then the one test file named in the brief, then `git add -A`, then
  `python3 -m lifecycle.fitness`. Do not run the browser audits or the full suite inside the brief; the navigator runs them.
- Paperwork: one line under `[Unreleased]` in `CHANGELOG.md`, then `python3 tools/readme_sync.py`.
- Do not edit `governance/queue.json`. Do not add a dependency or a network call. Use made-up values in fixtures
  (no real names, no digit runs of 13 or more).
- New JSON files are written by hand, compact, one item per line; never load-and-dump an existing one.
- Mark the brief done here (`Done: PR #n`) in the same pull request.

**Ranking.** Score = harm × reach ÷ effort, each from 1 to 5. Harm: how bad if it stays open (5 = permanent or data
loss). Reach: how many people it touches (5 = every user). Effort: 1 = ten minutes, 3 = a full 20-minute slot with
care. Hard gates (security, recovery) go first on a tie.

| Rank | Brief | Harm | Reach | Effort | Score | Tier | Closes |
|---|---|---|---|---|---|---|---|
| 1 | B04 The signing-key register | 5 | 4 | 1 | 20 | local | failure 3, 4 |
| 2 | B05 Update channels as data | 4 | 5 | 1 | 20 | local | failure 2 |
| 3 | B11 The open-core boundary test | 4 | 4 | 1 | 16 | local | section 3 |
| 4 | B02 Rename scan and ratchet | 3 | 5 | 1 | 15 | local | failure 14 |
| 5 | B10 Keep the previous build | 5 | 5 | 2 | 12.5 | opencode | failure 2 |
| 6 | B12 Store facts as data | 3 | 4 | 1 | 12 | local | failure 6 |
| 7 | B08 Offline-first test on the packaged files | 4 | 5 | 2 | 10 | opencode | section 1 |
| 8 | B09 The key restore and rotation drill | 5 | 4 | 2 | 10 | strong (review) | failure 3, 4 |
| 9 | B06 The previous version can read new data | 5 | 5 | 3 | 8.3 | strong (review) | failure 2 |
| 10 | B14 Rate limits on the hosted hub | 4 | 4 | 2 | 8 | strong (review) | failure 9 |
| 11 | B16 The roadmap reaches the app | 2 | 4 | 1 | 8 | local | section 5 |
| 12 | B03 Rename dry-run | 3 | 5 | 2 | 7.5 | opencode | failure 14 |
| 13 | B13 Renewals that warn before they lapse | 3 | 5 | 2 | 7.5 | local | failure 7 |
| 14 | B15 A second person cuts a beta | 5 | 3 | 2 | 7.5 | local | failure 12 |
| 15 | B01 The roadmap file holds its shape | 2 | 3 | 1 | 6 | local | section 5 |
| 16 | B18 The product name in the site comes from the config | 2 | 4 | 2 | 4 | local | section 2 |
| 17 | B07 The desktop project | 3 | 4 | 3 | 4 | opencode | section 1 |
| 18 | B17 Your stage, and one next target | 2 | 4 | 3 | 2.7 | opencode | section 5 |

"strong (review)" means an open model may write it, but a second look (`./securax review`) is required before merge.

**Order to run:** B01 first (it guards a file that already exists), then by rank. B16 needs B01. B03 needs B02.
B17 needs B16. B09 needs B04. B10 before B06. Everything else stands alone.

---

## B04 The signing-key register

- **Why:** a lost updater key ends desktop updates for ever. Nobody can protect a key that is not written down.
- **Test first:** `governance/tests/test_signing_keys.py`. It loads `governance/signing-keys.json` and fails unless
  every key has `id`, `platform`, `held_in`, `second_copy`, `if_lost`, `if_stolen`, `rotate_every_months`,
  `last_drill` (a date or `null`) and `owner_role`; unless the five ids `android-upload`, `apple-distribution`,
  `windows-codesign`, `tauri-updater`, `release-provenance` are present; and if any value looks like key material
  (a line starting `-----BEGIN`, or 40 or more base64 characters in a row).
- **The one step:** write `governance/signing-keys.json` with those five entries, taken from the table in section 1
  of the spec. `held_in` and `second_copy` name a kind of place ("hardware token", "sealed envelope, second
  location"), never a path, an account or a person.
- **Files:** the JSON, the test. Nothing else.

## B05 Update channels as data

- **Why:** staged rollout and rollback must mean the same thing on five platforms.
- **Test first:** `governance/tests/test_channels.py`. It fails unless `governance/channels.json` has exactly
  `nightly`, `beta`, `stable`; each names its target on `web`, `android`, `ios`, `windows`, `linux`; `stable` has
  `stages` of `[5, 20, 100]`, `min_days_on_beta` of 3 and a `rollback` line for every platform.
- **The one step:** write `governance/channels.json` from the channel table and the four rules in section 1.
- **Files:** the JSON, the test.

## B11 The open-core boundary test

- **Why:** one closed file committed here is public for ever, and one public file that needs a closed part breaks
  the promise that the core runs alone.
- **Test first:** `governance/tests/test_open_core.py`. With a temp folder as the repository it fails when a tracked
  path matches a `closed_paths` pattern, and when a public `.py`, `.js` or `.html` file contains a `closed_markers`
  string. It then runs the same check on the real repository and expects no finding.
- **The one step:** write `governance/open-core.json`: `open` (what stays public, in words), `closed_paths`
  (`editions/private/**`, `hosted/**`, `agents/private/**`), `closed_markers` (`@closed-overlay`), and the three
  rules from section 3. Put the checking function in the test file's helper `governance/open_core.py` (standard
  library; `git ls-files` for the list).
- **Files:** the JSON, `governance/open_core.py`, the test.

## B02 Rename scan and ratchet

- **Why:** the product name is hard-coded in 314 files and nothing stops the count from growing.
- **Test first:** `governance/tests/test_rename.py`. On a temp repository with three fixture files it checks that
  `scan()` sorts each hit into `display`, `frozen`, `legal` or `history`. On the real repository it fails when the
  count of `display` hits in code files (not docs, not markdown) is above the number in `governance/rename.json`.
- **The one step:** add `governance/rename.py` (standard library) with `scan(root)` and a `scan` command that
  prints counts by kind. Read the names from `governance/config.py` `load()`, never as literals. Write
  `governance/rename.json` with `frozen` patterns (the CLI file name, the environment-variable prefix, `.localhost`
  names, container paths, image names, storage keys, calendar UIDs), `legal` (`LICENSE`), `history`
  (`CHANGELOG.md`) and today's `display_in_code` count as the ceiling.
- **Files:** `governance/rename.py`, `governance/rename.json`, the test. Do not add a `securax` command yet.

## B10 Keep the previous build

- **Why:** rollback of the hosted app is "republish the old one", and today the old one is gone.
- **Test first:** in `governance/tests/test_pwa_publish.py`, a new test: publish build A into a temp folder, then
  build B into the same folder; `previous/` must hold A's files and A's build label, and the top level must hold B's.
  A third publish must leave exactly one `previous/`.
- **The one step:** in `tools/pwa_publish.py`, before writing a new build, move the current app files into
  `previous/` (replace what was there). Skip when there is no current build.
- **Files:** `tools/pwa_publish.py`, the test. Do not touch the service worker or any file under `guiding-map/`.

## B12 Store facts as data

- **Why:** a store listing answered from memory drifts from what the app does, and a wrong privacy answer gets an
  app removed.
- **Test first:** `governance/tests/test_store_facts.py`. It fails unless `governance/store.json` has `android` and
  `ios`, each with `package_id_from` equal to `SITE_DOMAIN`, `account_type`, `data_collected` (an empty list for the
  free core), `data_leaves_device` (`false` unless the person turns on their own sync), `min_os`, `review_notes`
  and `verified`; and unless `android.min_os` matches the Capacitor pin in `governance/oskit.py`.
- **The one step:** write `governance/store.json` from section 1 (Android 7 / API 24, iOS 15) and the app's real
  behaviour: no account, no tracking, data on the device.
- **Files:** the JSON, the test.

## B08 Offline-first test on the packaged files

- **Why:** a packaged app that reaches for the network at start shows a blank screen on a plane.
- **Test first:** in `governance/tests/test_oskit.py`, a new test: build the mobile project for the default edition
  into a temp folder, then fail on any `http://` or `https://` address in a `src=`, `href=`, `@import`, `url(` or a
  top-level `fetch(` of the packaged `www` files that is not on a short allow-list (links a person taps, the
  person's own sync address).
- **The one step:** add `offline_problems(www)` to `governance/oskit.py`, call it from `mobile_problems`, and print
  each finding as: the file, the address, and "bundle it or load it after first paint".
- **Files:** `governance/oskit.py`, the test. If the test finds a real address in the app, do not fix the app:
  list it in the pull request for the navigator.

## B09 The key restore and rotation drill

- **Why:** a second copy that was never opened is a hope, not a copy.
- **Test first:** `governance/tests/test_signing_keys.py`, a new test with an injected "today": `drills_due(today)`
  returns every key whose `last_drill` is `null` or older than its `rotate_every_months`; a key drilled yesterday
  is not returned.
- **The one step:** add `governance/signing_keys.py` with `drills_due(today)` and a `due` command, and a short
  section "The key drill" in `docs/securax/21-VERSIONING-AND-RELEASES.md`: restore from the second copy on a clean
  machine, sign a throwaway file, verify it, write the date into the register. No real key is read by the code.
- **Files:** `governance/signing_keys.py`, the test, the doc section. Needs B04.

## B06 The previous version can read new data

- **Why:** rollback is only safe if the older app can open what the newer one saved.
- **Test first:** `guiding-map/tests/test_back_compat.js` (jsdom): load the storage fixture
  `guiding-map/tests/fixtures/next-version.json`, which holds one unknown key and one known key with an unknown
  extra field; boot the app; assert no page error, the known screens render, and after a save both unknown parts
  are still in storage, unchanged.
- **The one step:** write the fixture and the test, and add the test to `npm test` in `guiding-map/package.json`.
  If it fails, stop and report which reader drops the unknown part: the fix is a separate, strong-tier brief.
- **Files:** the fixture, the test, `package.json`. No change to `ops.js` or `index.html` in this brief.

## B14 Rate limits on the hosted hub

- **Why:** a launch-day flood, or one broken client in a loop, must not take the hub down for everyone.
- **Test first:** `apps/estate-sync/tests/test_rate_limit.py`: 30 writes from one device id inside a second get at
  least one `429` with a `Retry-After` header; a second device id is still served; reads of the health path are
  never limited.
- **The one step:** a small in-memory token bucket per device id in `apps/estate-sync/syncsvc/`, off unless
  `SYNC_RATE_PER_MIN` is set, taking a lock around the bucket (see the audit-chain lesson). The client already
  retries with backoff; do not change it.
- **Files:** one new module, its wiring in `main.py`, the test. Run the test in a venv from the pinned requirements.

## B16 The roadmap reaches the app

- **Why:** the stages help nobody while they sit in a file the app never reads.
- **Test first:** `guiding-map/tests/test_roadmap.js` (jsdom): after boot, `window.GM_ROADMAP.stages.length` is 4
  and `window.GM_ROADMAP.targets.length` matches the file.
- **The one step:** in `guiding-map/build.js`, load `levers/roadmap.json` exactly as `council.json` is loaded two
  lines above, and expose it as `window.GM_ROADMAP`. Run `node build.js`. Add the test to `npm test`.
- **Files:** `build.js`, the test, `package.json`, the rebuilt output. No new screen. Needs B01.

## B03 Rename dry-run

- **Why:** a rename nobody has rehearsed will be done by hand, under pressure, and will break installed copies.
- **Test first:** in `governance/tests/test_rename.py`: on a temp repository, `plan(root, to="Newname", domain=
  "new.example")` lists every display hit with its file and new text, lists frozen hits as kept, stops on a legal
  file with a plain message, and writes nothing (file hashes unchanged).
- **The one step:** add `plan()` and a `--dry-run` command to `governance/rename.py`; add the `rename` branch to the
  `securax` CLI with a usage comment and a line in `./securax help`. Without `--dry-run` it prints "apply is not
  built yet" and exits 2.
- **Files:** `governance/rename.py`, `securax`, the test. Needs B02.

## B13 Renewals that warn before they lapse

- **Why:** a domain, a certificate or a developer account that lapses takes the product down on a date known a
  year ahead.
- **Test first:** `governance/tests/test_renewals.py` with an injected "today": an item 30 days from `expires` is
  returned by `due(today, within_days=45)`; one 90 days away is not; an item with no date is returned as "date
  not set". No test may depend on the real date.
- **The one step:** write `governance/renewals.json` (the domain, the Apple membership, the code-signing
  certificate, each with `expires: null` for the owner to fill) and `governance/renewals.py` with `due()`; show the
  due ones in `./securax backlog` as one more source beside `queue_items` in `build()` of `governance/backlog.py`.
- **Files:** the JSON, the module, one source entry in `backlog.py`, the test.

## B15 A second person cuts a beta

- **Why:** today one person can release. A runbook that only its author has followed is not a runbook.
- **Test first:** `lifecycle/tests/test_doc_recipes.py` already checks every command in a doc. Add the new page to
  the list it walks, and a check that each numbered step has exactly one command and one "you should see" line.
- **The one step:** write `docs/get-started/cut-a-beta.md`: at most 10 numbered steps from a clean clone to a
  published beta and back (rollback), using only commands that exist. Add it to `mkdocs.yml` nav and
  `docs/status.yml` (red), then `python3 docs/sync_status.py`.
- **Files:** the page, the nav line, the status line, the test list.

## B01 The roadmap file holds its shape

- **Why:** a levers file with a missing cell or a stale date shows a person a wrong target.
- **Test first and only step:** `governance/tests/test_roadmap.py`. It fails unless
  `guiding-map/levers/roadmap.json` has `verified` and `review` dates with `review` later; four stages in order;
  five areas; at least one target for every area and stage; unique ids; every target with a non-empty `confirm`, a
  `where` list drawn from `IN` and `GLOBAL`, and exactly one of `atLeast`, `atMost`, `is`. Match the error text in
  each negative case (a copy of the data with one field removed).
- **Files:** the test. Do not change the JSON; if the test finds a fault in it, report it.

## B18 The product name in the site comes from the config

- **Why:** the site already takes the domain from `brand.env`; the product name is still typed into 5 site files.
- **Test first:** in `governance/tests/test_config.py`: rendering a fixture page that holds `{{PRODUCT_NAME}}` with
  a changed `PRODUCT_NAME` gives the new name; and no file under `website/` holds the literal product name outside
  a `{{…}}` placeholder.
- **The one step:** replace the literal in `website/*.html` with `{{PRODUCT_NAME}}`. Build the site in a temp copy
  to check it (the build writes into tracked files: see the lesson of 2026-10-23), then lower the ceiling in
  `governance/rename.json`.
- **Files:** the site pages, the test, the ceiling.

## B07 The desktop project

- **Why:** Windows and Linux have no build at all.
- **Test first:** in `governance/tests/test_oskit.py`: `desktop("vantage", out=tmp)` writes `www/` with the same
  files as the mobile project, and `src-tauri/tauri.conf.json` whose `identifier` equals the mobile package id,
  whose updater has `endpoints` from `governance/channels.json` and a `pubkey` read from the environment (the build
  refuses with a plain message when it is unset), and whose content security policy allows no remote script.
- **The one step:** add `desktop()` to `governance/oskit.py` beside `mobile()`, reusing `mobile_source()`, and a
  `desktop` sub-command. Pin the Tauri version in one constant, as `CAPACITOR` is. Generate files only: build and
  sign nothing.
- **Files:** `governance/oskit.py`, the test, one `./securax help` line. Needs B05.

## B17 Your stage, and one next target

- **Why:** a person should see where they stand and the one next step, without filling in anything new.
- **Test first:** `guiding-map/tests/test_stage.js` (jsdom): with a fixture of one month of buffer and nothing
  else, `gmStage()` returns `survive` for money and overall, and `gmNextTarget()` returns exactly one target; with
  no data it returns `null` and the screen shows the invitation, not a zero.
- **The one step:** add `gmStage()` and `gmNextTarget()` to `guiding-map/ops.js` (grep for both names first), reading
  only facts the app already stores; targets whose measure the app does not hold are skipped, never asked for. No
  new screen in this brief: the card is the next one.
- **Files:** `ops.js`, the test, `package.json`, the rebuilt output. Needs B16. The navigator runs the browser audits.

---

## Not briefs: only the owner can do these

Each costs money, binds the owner, or touches an account. They are listed so they are not lost.

| Step | Why it cannot wait long | Suggested by |
|---|---|---|
| Choose the Play account type (personal: 12 testers for 14 days; organisation: a D-U-N-S number) | it sets the earliest possible Android launch date | 2026-12-15 |
| Decide who holds the licence and the mark (a company), with a lawyer and a chartered accountant | every store account, certificate and trademark filing is made in that name | 2026-12-31 |
| Clear the product name, then file the trademark | a forced rename after launch is the costliest kind | 2027-01-15 |
| Make the updater key, seal two copies in two places, name a second keyholder | failure 3 is permanent | before the first desktop beta |
| Buy the Windows code-signing certificate (confirm which service accepts an Indian publisher) | unsigned installers are blocked or warned on | before the first desktop beta |
| Harden the code account and turn on the mirror (gate `repository-hardened`) | failure 5 | 2026-12-15 |
