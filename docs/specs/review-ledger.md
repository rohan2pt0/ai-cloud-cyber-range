# Review ledger

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Every directory ranked by risk with its review state; reviewed one slice per session. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Every file in the repository gets a senior review, a slice at a time, over several sessions. Each session takes the next
unreviewed slice (at most 15 files), fixes what is cheap, and writes the rest as briefs: one step each, test first, small
enough for an open model to finish in 20 minutes. Nothing here is "done" because it was read: a row is **fixed** only when
a test holds it.

How to read a brief: **Test first** is the check to write and see fail; **Step** is the one change that turns it green;
**confirm** marks something nobody has verified yet.

## 1. Website and docs in step (checked 2026-11-16)

The generators ran clean: `tools/features_sync.py`, `tools/readme_sync.py` and `docs/sync_status.py` all reported
"already current", and `./securax config check` passed. The mismatches below are ones those checks do not look for.
No app code was changed; each is a brief.

| # | Mismatch | Where | Size |
|---|---|---|---|
| W1 | Brand name, domain, e-mail or repository written out instead of a `brand.env` placeholder | `docs/` and `mkdocs.yml` | 12 files, 40 lines |
| W2 | The product name written out; the placeholder is used twice | `website/*.html` (5 pages) | 58 places |
| W3 | Colours written inline that are not in `governance/design.json` | 4 website pages, `website/site.css`, `docs/stylesheets/premium.css` | 21 to 23 values a page; 6; 2 |
| W4 | A version in prose that the code has moved past (the chat app is pinned two releases on) | `docs/securax/54-TECHNICAL-GIST.md` | 1 line, likely more |
| W5 | An address with a port shown to a person (`names, not ports`) | `WINDOWS-QUICKSTART.md`, "Use it" | 1 line |

### Briefs

**W1a. Docs: no brand value outside `brand.env`.**
Test first: in `lifecycle/tests/test_brand_in_docs.py`, read `SITE_DOMAIN`, `CONTACT_EMAIL`, `REPO_SLUG` and `BRAND_NAME`
from `brand.env` at run time (never write them in the test) and fail on any line under `docs/get-started/` that holds one.
Step: replace the two clone lines in `docs/get-started/quickstart.md` and the eight lines in
`docs/get-started/laptop-runbook.md` with the placeholders the docs build already fills.
confirm: the docs hook fills a repository placeholder as it fills the site one (it is not used in `docs/` today).

**W1b. The same for `docs/securax/`.** Extend the W1a test to `docs/securax/` and `mkdocs.yml`. Step: one doc per run,
largest first: 60 (8 lines), 61 (6), 85 (3), 75 (3), 130 (2), 00 (2), then 29, 137, 131 (1 each). Doc 131 names the
hosting origin as a risk on purpose: keep the sentence, use the placeholder.

**W2. Website: the product name through the placeholder.**
Test first: in `website/tests/`, fail when a page's visible text holds the `PRODUCT_NAME` value from `brand.env` and
not its placeholder (skip `alt`, `title` and the generated blocks). Step: one page per run, `index.html` first.
confirm: `website/build.sh` renders the product placeholder in page text as it does the brand one.

**W3a. Website: inline colours to tokens.**
Test first: extend `governance/tests/test_design_standard.py` (or the site's own test) to collect every hex colour in
`website/**/*.html` and fail on one that `governance/design.json` does not hold. Step: move the inline `<style>` values
of `website/index.html` to the variables `tools/site_css.py` already writes; then one page per run.
The off-token values seen: status tints (greens, reds, ambers), four near-ivory greys that differ by one step, and two
golds one step apart. Most are near-duplicates of a token, so the fix is a merge, not a new token.

**W3b. `site.css` and the docs stylesheet.** Same test, pointed at `website/site.css` (6 values) and
`docs/stylesheets/premium.css` (2). Step: change the source in `tools/site_css.py`, never the generated file.

**W4. Versions in prose become facts.** Test first: fail when a doc names an image version that differs from the pin in
`local/compose/docker-compose.yml`. Step: turn the table in doc 54 into `<!-- fact:NAME -->` markers the generator
fills, as counts already are.

**W5. The quickstart shows a port.** Step: say "run `./securax open`: it prints the right address" and drop the literal
address. The root `.md` files are read on GitHub as they are, so they cannot use placeholders; the repository address in
them is accepted for that reason and is not a mismatch.

## 2. The ledger

Ranked by risk to a person using SecuRAX: what they touch first, and what hurts most when it is wrong, comes first.
Counts are tracked files (`git ls-files`) on 2026-11-16. Status is one of: **not reviewed**, **reviewed (PR)**,
**fixed (PR)**. A directory is "reviewed" only when every file in it has been; until then the row says how many.

| Rank | Area | Directories (tracked files) | Status |
|---|---|---|---|
| 1 | Launchers and installers | root files (44), `local/` (44), `tools/windows/` (1) | 20 of 89 reviewed; 8 fixed (#313), 1 fixed (#324). `securax`: 5 branches read; `DEPLOY.md`: Windows rows only. See slices 1 and 2 |
| 2 | The Life OS | `guiding-map/` (196) | not reviewed |
| 3 | The gateway and security | `apps/` (47), `governance/` (230), `policies/` (1), `redteam/` (11), `ai-soc/` (6), `mcp/` (3), `agents/` (12), `intel/` (9) | 1 of 319 reviewed (#313, encoding only) |
| 4 | Sync and backup | inside `apps/` and `governance/` (review them first within rank 3), `routines/` (10), `sandbox/` (4) | not reviewed |
| 5 | The website | `website/` (24), `portal/` (3) | brand and colour check only (#313, section 1); not reviewed line by line |
| 6 | Docs | `docs/` (165), `design/` (6), `templates/` (16), `knowledge/` (2), `learning/` (8) | brand check only (#313, section 1) |
| 7 | Tools and the build | `tools/` (15 more), `lifecycle/` (69), `.github/` (22), `.claude/` (2), `.opencode/` (5) | not reviewed |
| 8 | The rest | `exercise/` (25), `gitops/` (26), `infra/` (31), `integrations/` (8), `assistant/` (3), `finance/` (3), `notebooks/` (1), `personal-rnd/` (5), `plugins/` (1), `vendor/` (7) | not reviewed |

### Slice 1 (2026-11-16, PR #313): the Windows path

Nothing in this slice was run on Windows. Every "fixed" below is held by a static test only.

| File | Status | What was found |
|---|---|---|
| `securax.cmd` | fixed (#313) | Read `wsl -l` (UTF-16 on older Windows); used an undocumented `--cd ~/securax`; refused `why` when Docker was down; wrong advice for Docker Engine inside Ubuntu; no log |
| `START-HERE-Windows.bat` | fixed (#313) | No plain reason when opened from a ZIP or copied to the Desktop; no log |
| `STOP-Windows.bat` | fixed (#313) | The same |
| `UPDATE-Windows.bat` | fixed (#313) | The same, and a failure was never checked |
| `PROTECT-BACKUPS-Windows.bat` | fixed (#313) | The same, and a failure was never checked |
| `WHATS-WRONG-Windows.bat` | fixed (#313) | The same; and it could not run when Docker was down, the moment it is needed |
| `install.ps1` | fixed (#313) | Took an error sentence for a distribution name; a failure closed the window; no log. Brief L5 remains |
| `.editorconfig` | fixed (#313) | Said LF for every file, so an editor could save a batch file wrongly |
| `.gitattributes` | reviewed (#313) | Right as it is: batch files CRLF, the rest LF |
| `local/scripts/wsl-setup.sh` | reviewed (#313) | Fixed: it told a person to delete their SecuRAX folder (keys and data) when an update failed. Brief L4 remains |
| `WINDOWS-QUICKSTART.md` | reviewed (#313) | Now names the log and the shortcut rule. Brief W5 remains |
| `tools/windows/free-c-drive.ps1` | reviewed (#313) | Sound and careful (report first, asks before each step). Brief L6 remains |
| `governance/respond_kit/collect.ps1` | reviewed (#313), encoding only | Two strings held a non-ASCII dot that prints as noise in Windows PowerShell 5.1; fixed. Its logic is not reviewed |
| `install.sh` | skimmed (#313), not line by line | Checksums on the release path, clear failures, no destructive step seen. It goes back in the next slice for a full read |

### Briefs from slice 1

**L1. The owner's check on a real PC (a person, not a model).** In a folder whose path has a space: double-click each of
the five launchers; then quit Docker and double-click `WHATS-WRONG-Windows.bat`; then copy `STOP-Windows.bat` alone to
the Desktop and double-click it. Paste `%LOCALAPPDATA%\SecuRAX\last-run.log` into the chat if any step surprises.

**L2. Run the failure path on real Windows in CI.**
Test first: a `windows-latest` job in `.github/workflows/` that copies the launchers into a folder named with a space,
runs `cmd /c "START-HERE-Windows.bat" < nul`, and asserts: exit code 1, the words "Next step" in the output, and
`last-run.log` exists. Step: add the job; nothing else. This proves cmd.exe parses every line, which no static test can.
confirm: what a hosted runner has for WSL (the expected path is "no distribution", step 1).

**L3. The log holds the launcher's steps, not the command's own output.** A decision for the owner, not a model: piping
the output through a logger would also change how prompts and colours behave in the window. Recommended: keep it, and
have a failed run append `securax why` to the log. Test first: `test_windows_launchers.py` expects a `why` line after a
non-zero exit. Step: three lines in `securax.cmd` after `:ran`.

**L4. `wsl-setup.sh` belongs to the older Docker Desktop path.** It stops with "start Docker Desktop" even when Docker
Engine is inside Ubuntu, and it silently throws away a person's edit to `litellm-config.yaml` before updating.
Test first: in `local/compose/tests/`, assert the script says which set-up it found and never runs `git checkout --` on
a changed file without saying so. Step: reuse the two messages `securax.cmd` now prints.

**L5. `install.ps1` runs `install.sh` from `main` with no checksum (strong tier: supply chain).** The release path
inside `install.sh` checks a checksum; the first hop does not. Test first: `governance/tests/test_installers.py` expects
`-Stable` to fetch from the release and compare a published hash. Step: do that for `-Stable` and `-Version`; leave the
rolling channel as it is, and say so in the script's first lines. Needs a threat-model line (`governance/threat-models.json`).

**L6. `free-c-drive.ps1`, step 6 moves the Ubuntu disk on a single "y".** That is the one step here that can lose data if
it is interrupted (`friction-by-consequence`). Test first: a static test expects a typed word, not "y", before
`wsl --manage ... --move`, and a line that names a backup first. Step: one `Read-Host` and one message.

**L7. `securax` itself tells Docker-Engine-in-Ubuntu users to start Docker Desktop** (four messages in `up`, `go`,
`doctor` and `start`). Test first: a sandbox-free unit test that runs each branch with a fake `docker` that fails and a
fake `dockerd` on the path, and expects "sudo service docker start". Step: one shared helper, used by the four places.

**L8. A batch file fetched "raw" from GitHub arrives with LF endings** (the stored copy is LF; only a checkout converts).
Test first: fail when any doc tells a person to download a `.bat` or `.cmd` by a raw address. Step: none today (no doc
does). confirm: that GitHub's "Download ZIP" applies the CRLF rule; if it does not, store the batch files as CRLF
(`-text`) and update the two tests that name the current rule.

### Slice 2 (2026-11-17, PR #324): the first start on Linux, Mac and a server

Nothing in this slice was run against Docker, a real server or WSL: this session had none. Every "fixed" below is held
by `local/compose/tests/test_laptop_scripts.py`, which runs a copy of the script with a fake `docker`, or reads the text.

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#324) | **Data loss.** The guide and the README print it as "stop everything", and it deleted every volume (chats, documents, workflows, the database) with no question. It now keeps them; `--erase-data` names what is lost, offers a backup first and needs a typed word |
| `install.sh` | reviewed (#324), line by line | Fixed: `--server` changed the whole machine before it noticed a mistyped `--restore` or `--keyfile`, and quietly ignored `--offline`; `--help` cut off `--no-start`, `--yes` and the `--server` note. Briefs I1 to I6 remain. Slice 1 said the release path checks a checksum: only `--offline` does (brief I3) |
| `GETTING-STARTED.md` | reviewed (#324) | Fixed: it sent a person to two "uploaded" files that were never in the repository, and named one particular laptop. Brief S4 remains |
| `local/scripts/bootstrap-laptop.sh` | reviewed (#324) | Fixed: the laptop model. Sound where it matters: every download is pinned and hash-checked before it is installed. Briefs S1, S2 remain |
| `local/scripts/daily-driver-up.sh` | reviewed (#324) | Briefs S1, S2, S3 |
| `local/scripts/kind-up.sh` | reviewed (#324) | Brief S5 |
| `local/compose/docker-compose.yml` | reviewed (#324) | Fixed: the laptop model. Sound: every published port is on 127.0.0.1 unless the person opens it, the database and dashboard passwords have no default, the gateway and sync are read-only with no capabilities. Briefs C1 to C5 remain |
| `securax`: `up` | reviewed (#324), this branch only | Layered fall-backs are careful and each says what it did. Briefs U1 to U4 |
| `securax`: `go` | reviewed (#324), this branch only | Briefs G1, G2 (and L7 from slice 1) |
| `securax`: `update` | reviewed (#324), this branch only | Fixed: its DNS advice for WSL overwrote `/etc/wsl.conf`, which undoes the line `install.sh --docker` writes there so Docker starts by itself; it now appends. Backup first, health check and rollback read right. Briefs P1 to P3 |
| `securax`: `why` | reviewed (#324), this branch only | Sound. Its two "Docker is not running" lines are part of L7 |
| `securax`: `down` | reviewed (#324), this branch only | Brief D1 |
| `DEPLOY.md` | Windows rows only (#324) | Brief D2. The rest goes in the next slice |

### Briefs from slice 2

Ranked by risk x reach / effort. The first four can lock a person out, lose their data or leak a key: do them first.

**I1. `--server` can lock a person out of their own server (strong tier: do not hand to a small model).** The firewall
step allows SSH by its named profile, which is port 22. A server whose SSH listens on another port loses its only door
when the firewall is switched on. Test first: in `governance/tests/test_installers.py`, run the dry run with a fake
`sshd -T` that reports another port and expect that port in the "would run" firewall line. Step: read the port
(`sshd -T`, else the fourth field of `SSH_CONNECTION`, else 22) and limit that port. The keys-only step has a cousin:
it counts a key in ANY home folder, then stops root passwords; require a key for root or for a user who can `sudo`.

**C1. The password manager lets anyone who reaches it make an account.** `PASSWORDS_SIGNUPS` is on by default, and
`BIND_HOST` opens every published port at once. Test first: `test_compose_sanity.py` expects the default to be off.
Step: default off; `./securax start passwords` turns it on for the first account only, then off again.
confirm: what `start passwords` does today, and whether the online tunnel ever carries this service.

**S1. Two scripts start the estate with the public development key.** `bootstrap-laptop.sh` and `daily-driver-up.sh`
copy `.env.example` and call `docker compose` themselves, so they skip the step in `./securax up` that replaces the
placeholder gateway key and makes the sync token and the chat sign-in key. Test first: `test_laptop_scripts.py`
expects neither script to call `docker compose ... up` itself. Step: both call `./securax up` (bootstrap keeps its
smoke test). This also removes their four printed ports (S3).

**G1. The one-tap phone link carries the sync token through a public relay (strong tier).** `go` asks first and the
default is no, which is right. Test first: `governance/tests/` expects a threat-model entry for it in
`governance/threat-models.json` (information disclosure: anyone who knows the topic name reads the link).
Step: write the entry; mitigation to weigh: a link that works once and for ten minutes.
confirm: whether the sync service can issue a one-time pairing code today (the pairing scan may already do it).

**P1. An update runs whatever the code host serves (strong tier; belongs with the updater threat model, autopilot
task 7).** The nightly run is held by the Go/No-Go poll, takes a backup and rolls back, but nothing checks who signed
the code. Test first: on the stable channel, expect `git verify-tag` before the checkout and a plain refusal when it
fails. confirm: that release tags are signed today (`.github/workflows/release.yml`); if not, that is step one.

**I2. `--server` sets the clock to India for everyone (`global-ready`).** Test first: the dry run with no
`SECURAX_TZ` prints no time-zone change. Step: change the zone only when `SECURAX_TZ` is set, and say in one line how
to set it. An owner decision if the India default should stay for the Local edition.

**I3. Only `--offline` checks a checksum; `--stable` and `--version` trust the code host.** Same shape as L5: say so in
the script's first lines now, and verify a signed tag once P1 lands. Also: a file missing from `SHA256SUMS` says
"checksum mismatch"; say "not listed in SHA256SUMS" (it fails safely today on both `sha256sum` and `shasum`, checked here).

**I4. A failed `--offline` unpack leaves a half-filled folder,** and the next run says "already exists, run update".
Test first: a truncated archive leaves no folder behind. Step: remove the folder the installer itself made, then stop.

**I5. `--docker` appends a second `[boot]` section to `/etc/wsl.conf` when one exists.** Test first: a fake file that
already holds `[boot]` ends with one section. Step: add the key under the existing section.
confirm: how WSL reads a repeated section. `docs/securax/121-DRIVE-HOME.md` (line 74) still overwrites the file: append there too.

**I6. Run from a pipe, the installer reads `brand.env` from whatever folder the person is in.** Low risk (the release
copy has the name written in). Step: read it only when the script's own path is a real file.

**U1. A flag `up` does not know is ignored without a word.** `./securax up --lit` starts the full estate; `--lite` is
read only as the second word. Test first: `test_cli_friction.py` expects exit 2 and the list of flags. Step: one loop.

**U2. The "port is taken" help assumes Windows** ("open Windows PowerShell, not this Ubuntu window") on Linux and Mac.
Test first: outside WSL the message names `ss -ltnp` or `lsof -i`. Step: branch on `/proc/version`, as `update` does.

**U3. A printed command works from one folder only** (`grep '^SYNC_TOKENS=' local/compose/.env`). Step: print the
full path, or better, never show the token: the pairing scan hands it over (`zero-setup`).

**U4. The key prompt in `up` asks a person to paste a secret, in clear text.** Already an open friction
(`zero-setup`); until it goes, read it with `read -rs`. Also: Ctrl-D at the names question ends `up` silently
(`read` under `set -e`); end it with `|| _nm=""`.

**G2. "Your devices only" is true on a one-person tailnet.** confirm: what a shared tailnet member can reach after
`tailscale serve`; if they can, say "everyone on your tailnet".

**P2. `update` discards a person's edit to `litellm-config.yaml` without saying so** (the same finding as L4). Test
first: a changed file is copied to `.bak` and named in one line before the checkout.

**P3. On the stable channel a manual update with no network says "skipped" and exits 0.** Step: for a person at the
keyboard say "no network, nothing changed" and exit 1; keep 0 for `--auto`.

**D1. `./securax down` says "stopped" but names one profile.** confirm: that `docker compose --profile ai down` leaves
the password manager, the online tunnel and Studio running (they sit in other profiles). If it does: stop every profile
the person started, and print what was stopped. Test first: a fake `docker` sees every started profile.

**C2. One switch opens everything.** `BIND_HOST` publishes the gateway, chat, documents, automation, passwords and
Studio together. Test first: a doc test expects the warning next to every place `BIND_HOST` is taught. Step (later):
one switch per service. confirm: that Studio never starts with an empty `STUDIO_PASSWORD`.

**C3. Chat and the dashboard both claim host port 3000** (profiles `ai` and `security`). Test first:
`test_compose_sanity.py` fails on two services with one host port. Step: move the dashboard.

**C4. The scanner mounts the Docker socket.** Read-only on a socket does not limit what it can ask Docker to do.
Accept with a reason and a review date in `governance/threat-models.json`, or scan saved images instead.

**C5. Four images carry a version and no digest in the file** (the model server, the database, the log store, the
scanner). confirm: that `local/compose/digest-pins.json` covers them; if it does, this is closed.

**S2. Both scripts say "Install Docker Desktop" and stop,** even with Docker Engine inside Ubuntu (L7's helper fits).
**S3. They print four addresses with ports** (`names, not ports`); S1 removes them.
**S4. `GETTING-STARTED.md` still shows ports, two example files a person does not have (`my_public_bio.txt`) and
sample money figures.** Step: use `./securax open`, a sample file that ships, and plainly round figures.
confirm: that the sample figures are invented.
**S5. `kind-up.sh` installs the admission controller at whatever version is newest** and writes to a fixed file in
`/tmp`. Step: pin the chart version; use `mktemp`.

**D2. `DEPLOY.md` and the installer disagree on the folder name** (the guide keeps the repository's name, the
installer makes `~/securax`), and step 3 tells a Windows person to edit `.env` by hand (`zero-setup`).

### Next slice (at most 15 files)

`DEPLOY.md` (the rest), `README.md` (the install and run sections), `CONTRIBUTING.md`, `local/compose/.env.example`,
`tls.yml`, `tls-internal.yml`, `tls-move.yml`, `full-stack.yml`, `guiding-map.conf`, then the `doctor`, `start`,
`open`, `backup`, `restore` and `protect` branches of `securax` (count each branch as one file).
