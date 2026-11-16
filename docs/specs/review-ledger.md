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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | 19 of 88 reviewed; 8 fixed (#313), 5 fixed (#PRNUM). See slices 1 and 2 |
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

**L5. `install.ps1` runs `install.sh` from `main` with no checksum (strong tier: supply chain).** Only `--offline`
inside `install.sh` checks a checksum (slice 2 corrected this: `--stable` clones a tag and checks nothing, see M2); the first hop does not. Test first: `governance/tests/test_installers.py` expects
`-Stable` to fetch from the release and compare a published hash. Step: do that for `-Stable` and `-Version`; leave the
rolling channel as it is, and say so in the script's first lines. Needs a threat-model line (`governance/threat-models.json`).

**L6. `free-c-drive.ps1`, step 6 moves the Ubuntu disk on a single "y".** That is the one step here that can lose data if
it is interrupted (`friction-by-consequence`). Test first: a static test expects a typed word, not "y", before
`wsl --manage ... --move`, and a line that names a backup first. Step: one `Read-Host` and one message.

**L7. `securax` itself tells Docker-Engine-in-Ubuntu users to start Docker Desktop** (four messages in `up`, `go`,
`doctor` and `start`, and slice 2 found two more in `why`; `go` says it on macOS and Linux too). Test first: a sandbox-free unit test that runs each branch with a fake `docker` that fails and a
fake `dockerd` on the path, and expects "sudo service docker start". Step: one shared helper, used by the four places.

**L8. A batch file fetched "raw" from GitHub arrives with LF endings** (the stored copy is LF; only a checkout converts).
Test first: fail when any doc tells a person to download a `.bat` or `.cmd` by a raw address. Step: none today (no doc
does). confirm: that GitHub's "Download ZIP" applies the CRLF rule; if it does not, store the batch files as CRLF
(`-text`) and update the two tests that name the current rule.

### Slice 2 (2026-11-16, PR #PRNUM): the installer, the laptop scripts and the daily commands

Nothing in this slice was run against Docker, a kind cluster, WSL or macOS. `teardown.sh` is held by a test that runs it
with stand-in tools; every other "fixed" is held by a static test (`local/compose/tests/test_laptop_scripts.py`).

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#PRNUM) | It deleted every data volume, every time, with no question, while three docs called it "stop everything". Now it stops and keeps the data; `--erase` says what is lost, offers the backup first and needs a typed word |
| `install.sh` | fixed (#PRNUM) | With no network, `--stable` ended with no message (a failed lookup under `pipefail`); `--help` cut the header mid-sentence. Briefs M1 to M4 remain |
| `securax`, `up` | fixed (#PRNUM) | A pasted AI key was shown on the screen and stayed in the scrollback (also in `setup`). Briefs M5, M6 remain |
| `securax`, `update` | fixed (#PRNUM) | Its DNS advice replaced `/etc/wsl.conf`, wiping the line `install.sh --docker` writes to start Docker (doc 121 said the same). Briefs M7, M8 remain |
| `securax`, `go` | fixed (#PRNUM) | Said "the app just opened" when nothing had opened it (macOS has no `xdg-open`). L7 covers its Docker message |
| `local/scripts/kind-up.sh` | fixed (#PRNUM) | The admission check passed on ANY refusal (no cluster, no namespace), a false green; a fixed name in `/tmp`. Brief M9 remains |
| `local/scripts/bootstrap-laptop.sh` | reviewed (#PRNUM) | Fixed: a gateway that never came up read as "expected 400, got 000"; a fixed name in `/tmp`; "install Docker Desktop" as the only path. Hashes are pinned and checked before install: sound. Briefs M9, M10 remain |
| `local/scripts/daily-driver-up.sh` | reviewed (#PRNUM) | Starts compose directly, so it skips what `./securax up` does (strong keys, HTTPS names, fallbacks) and prints four port addresses. Brief M10 |
| `GETTING-STARTED.md` | reviewed (#PRNUM) | Fixed: two pointers to a file that was never in the repository; a device model. Brief M11 remains |
| `DEPLOY.md` (Windows rows) | reviewed (#PRNUM) | Nothing changed. Brief M11 |
| `securax`, `why` | reviewed (#PRNUM) | Sound: read-only, bounded output. Brief M12; L7 covers its Docker messages |
| `securax`, `down` | reviewed (#PRNUM) | One line, one profile. Brief M13 |
| `local/compose/docker-compose.yml` | reviewed (#PRNUM): ports, pins, limits, volumes, mounts | Every port is on loopback by default; hardening flags are on. The environment blocks are not read line by line: they go in the next slice. Briefs M14 to M16 |

### Briefs from slice 2

**M1. `install.sh --server` can lock the owner out of SSH (strong tier: sign-in).** It turns password login off when
ANY account on the server holds a key, not when the person running it does. Test first: in
`governance/tests/test_installers.py`, a dry run with a key only under another account's home must print "SSH left as
it was". Step: count keys only for root and `$SUDO_USER`. confirm: which account a provider's image puts its key under.

**M2. `--stable` and the stable update channel trust a tag with no check (strong tier: supply chain).** Both
`install.sh` and `securax update` check out the newest `v*` tag as fetched; a moved or forged tag is run as it is.
Test first: expect a refusal when the tag's commit is not the one the release's published `SHA256SUMS` names.
Step: one shared check, used by both. Needs a line in `governance/threat-models.json`. Do it with L5.

**M3. `--server --restore` leaves the backup and its key file side by side** in the service account's home, for good.
Test first: a dry run must print a step that removes both copies after the restore. Step: two `rm` lines and one `say`.

**M4. `--server --restore` on a server that already has SecuRAX does nothing and still says "ready".** Test first: a dry
run with the folder present and `--restore` must stop with one next step (`./securax restore FILE`). Step: one `die`.

**M5. A port clash tells Linux and macOS users to open Windows PowerShell.** Test first: with a stand-in `docker` that
prints "port is already allocated", `up` outside WSL must not print "PowerShell". Step: pick the hint by system
(`ss -ltnp` on Linux, `lsof -i` on macOS). Do it with L7: one helper for "which system is this".

**M6. `up` still asks a person to paste a key** (`zero-setup`). Not a model's task: add it to
`governance/frictions.json` as open, with the one-tap consent path as the fix.

**M7. `update` throws away a hand edit to `litellm-config.yaml` without a word** (the same finding as L4, in a second
place). Test first: a temp repository with that file edited; `update` must say it set the edit aside and where.
Step: copy it to `litellm-config.yaml.yours` before the checkout, and say so.

**M8. "Your data is untouched" is not proven when an update moves an image forward.** A newer chat or database image
can change its stored data on start; the code then rolls back but the data does not. Test first: `update` without
`--auto` must stop, not continue, when the safety backup fails on a running estate. Step: replace "continuing" with
one next step. confirm: which pinned images change their data on a version step (the chat app does, by its notes).

**M9. The Kubernetes tools are two years old and one is not pinned.** `bootstrap-laptop.sh` pins kind, kubectl and helm
at late-2024 builds; `kind-up.sh` installs the admission controller's chart at whatever is newest. Test first: fail when
`kind-up.sh` has a `helm upgrade --install` with no `--version`. Step: pin the chart; raise the three tools and their
hashes together. confirm: the known flaws fixed since in helm (look them up; do not write them from memory).

**M10. Two ways to start, and the older one is the unsafe one.** `bootstrap-laptop.sh` and `daily-driver-up.sh` start
compose themselves and print port addresses that a default install (HTTPS names on) no longer serves. Test first: fail
when a script under `local/scripts/` prints `localhost:` followed by a port. Step: make `daily-driver-up.sh` three
lines that call `./securax up` and `./securax open`; keep `bootstrap-laptop.sh` for the range demo and have it print
`./securax status` for addresses. On macOS it would install Linux tools: stop there with a plain line instead.

**M11. The two root guides give addresses a fresh install no longer answers on.** `install.sh` now turns the HTTPS
names on, yet `GETTING-STARTED.md` (4 places) and `DEPLOY.md` (about 12) say `localhost` and a port, name Docker
Desktop as the only way, call the folder by the repository's name where the installer uses `~/securax`, and tell a
Windows person to edit `.env` by hand. Test first: extend the fitness check `no-raw-addresses` to the root `.md`
files. Step: one guide per run; say "run `./securax open`" and let it print the address. Finish W5 with it.

**M12. `why` prints raw logs and invites a paste into a chat.** A log line can hold a key or a person's text.
Test first: feed `why` a stand-in log holding a plainly fake key (low entropy) and expect it masked. Step: pass the
lines through the masking the gateway's audit already uses. confirm: that a shared masking helper exists to reuse.

**M13. `down` may leave the password manager, the online tunnel and the studio running.** It names one profile; those
three are in others. Test first: a static test expects `down` to cover every profile `up` and `start` can start.
Step: `--profile "*"`. confirm: on the pinned compose version, whether `down` with one profile stops the others.

**M14. The monitoring profile cannot start beside Chat: both publish port 3000.** Test first: in
`test_compose_sanity.py`, fail when two services publish the same host port. Step: give the dashboard its own port.

**M15. Five services have no memory limit** (the router, the database, the log store, the dashboard, the scanner), so
one of them can take the laptop down with it. Test first: `test_container_hardening.py` expects a limit on every
service. Step: add one each, sized from `docker stats` on a running estate (a person runs that once).

**M16. The scanner is handed Docker's control socket** (read-only on a socket does not limit what can be asked of it),
and four images are pinned by tag only (the local model, the database, the log store, the scanner). Strong tier.
Test first: fitness `threat-modelled` expects a model that names the socket. Step: write the model; accept with a
review date or put a socket proxy in front. Pin the four by digest in the same change.

**M17. A device model is named in eight more files** (`docs/architecture.md`, docs 00, 05, 10 and 28,
`portal/explainer.html`, `personal-rnd/self_opsec.py`). The three in this slice now say "a 16 GB laptop".
Test first: fail on the model's name anywhere tracked (keep the name out of the test: hash it, as the privacy list does).
Step: one file per run.

### Next slice (at most 15 files)

The environment blocks of `local/compose/docker-compose.yml`, `local/compose/.env.example`, `tls-internal.yml`,
`tls-move.yml`, `guiding-map.conf`, `gen_litellm_config.py`, `litellm-config.yaml`, `model_discovery.py`, then the
`doctor`, `start`, `setup`, `backup`, `restore` and `protect` branches of `securax` (count each branch as one file),
and `README.md`.
