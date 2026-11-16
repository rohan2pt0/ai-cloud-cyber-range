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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | 22 of 88 reviewed (`securax`: 5 of its branches); 15 fixed (#313, #316, #319). See slices 1 to 3 |
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
| `install.sh` | skimmed (#313); read line by line in slice 2 | Checksums on the release path, clear failures, no destructive step seen. It goes back in the next slice for a full read |

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

### Slice 2 (2026-11-16, PR #316): the installer and the laptop scripts

Nothing in this slice was run against real Docker, a real server or a real install. The fixes are held by
`lifecycle/tests/test_laptop_scripts.py`, which runs `teardown.sh` with a pretend `docker` and `kind`.

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#316) | **It deleted every volume** (`down -v`): chats, documents, automations, the synced Life OS state, the password vault and the database, while the README and the getting-started page called it "stop everything". It now keeps the data; `--erase` says what is lost, offers the backup first and needs the typed word |
| `install.sh` | fixed (#316), read line by line | `--help` stopped three lines early; an offline unpack that failed left a folder that blocked the second try with "already exists"; the last line said the Command Center was open when it had not opened. Briefs M1 to M3, M7 to M9 remain |
| `local/scripts/bootstrap-laptop.sh` | fixed (#316) | A gateway that never came up was reported as "expected 400, got 000"; the answer went to a fixed name in the shared temp folder; the header named one make of laptop. Briefs M4 and M5 remain |
| `GETTING-STARTED.md` | fixed (#316) | Sent a newcomer to an "uploaded" file that is not in the repository, twice; named one make of laptop. Briefs M4 and M6 remain |
| `local/scripts/daily-driver-up.sh` | reviewed (#316) | Works as written. Shows four addresses with ports; an empty container id gives a cryptic error. Brief M4 |
| `local/scripts/kind-up.sh` | reviewed (#316) | Works as written. The Kyverno chart has no version; a missing tool gives "command not found". Briefs M4 and M5 |

### Briefs from slice 2

**M1. `install.sh --server` can lock the owner out of SSH (strong tier: sign-in).** It switches passwords off when *any*
account holds a key. A person who signs in as root with a password, on an image where another account holds a key, is
then shut out, and the comment says this "can never" happen. Test first: in `governance/tests/test_installers.py`, a
dry run with a pretend home folder where only another account holds a key expects "SSH left as it was". Step: count
keys only for the account that ran it (`SUDO_USER`, else root).

**M2. `--server` says "SecuRAX is running" when it is not.** With `--restore`, the inner installer leaves quietly when
Docker is not up, and a second run skips both the restore and the start because the folder exists; the last line is the
same either way. Test first: a dry-run test expects the closing line to differ when a restore was asked for and did not
happen. Step: check `securax status` (or the restore's exit code) before the closing line.

**M3. `--stable` and `--version` check nothing (strong tier: supply chain; do it with L5).** L5 said the release path
checks a checksum. Only `--offline` does: the other two clone a tag, and a tag can be moved. Test first: expect
`--stable` to compare the cloned commit with one the release publishes. Step: publish the tag's commit in `SHA256SUMS`
(or sign the tag) and compare after the clone. confirm: which of the two the release workflow can do today.

**M4. The older scripts show ports and name Docker Desktop only.** `daily-driver-up.sh` (4 lines), `bootstrap-laptop.sh`
(1) and `GETTING-STARTED.md` (5) show an address with a port; `bootstrap-laptop.sh` and `kind-up.sh` do not say which
tool is missing. Test first: extend `test_laptop_scripts.py` to fail on a port shown to a person in these three files.
Step: one file per run; use `web_url`, and the two Docker messages from L7.

**M5. Pins two years old, and one missing.** `kind` v0.25.0, `kubectl` v1.31.3 and `helm` v3.16.3 are pinned with
hashes (good) but old; the Kyverno chart in `kind-up.sh` has no version at all. Test first: `test_burrow_pinning.py`
expects `--version` on every `helm upgrade --install`. Step: pin Kyverno; then one tool per run, version and hash
together. confirm: the current versions and their published hashes (needs the network).

**M6. A decision for the owner: sections 1 to 3 of `GETTING-STARTED.md` are the path from before `./securax`.**
Recommended: keep the one-step start, fold the rest under one line that points to the docs, and change the same five
lines in the README's quick start. Also `--footprint-file my_public_bio.txt` names a file the person does not have:
give the command a fallback or an example file. Test first: the page holds no command that names a missing file.

**M7. A second `[boot]` section in `/etc/wsl.conf`.** `--docker` appends `[boot]` and `systemd=true` even when the
file already has a `[boot]` section. confirm: how WSL reads a repeated section. Test first: a dry run with a pretend
`wsl.conf` that already has `[boot]` expects one section afterwards.

**M8. `--server` assumes India's clock** (`global-ready`). Low. Step: keep the machine's zone unless `SECURAX_TZ` is
set or the person's region is known; say which was used.

**M9. Small ones in `install.sh`.** `--help` in a copy taken from git prints the unfilled repository placeholder in the
first command; `--stable` without `curl` ends with the shell's own words. Test first: `--help` output holds no `{{`.

**M10. Nothing proves the stop on real Docker.** Test first: a sandbox journey that starts the core, writes one row,
runs `teardown.sh`, starts again and finds the row. Step: the journey only.

### Slice 3 (2026-11-16, PR #319): start, stop, update and the compose file

Nothing in this slice was run against real Docker, a real update or Windows. The fixes are held by
`lifecycle/tests/test_cli_stop_and_go.py`, which runs `./securax down` with a pretend `docker`; the rest is read from
the text. Each branch of `securax` counts as one file.

| File | Status | What was found |
|---|---|---|
| `securax`, `down` | fixed (#319) | No `-v` anywhere: a stop keeps the data (and no branch of the CLI removes a volume with compose; a test now holds that). But it stopped the `ai` profile only, so **the password manager and the online tunnel kept running after "stop"**; a failure ended with Docker's words alone; "stopped." did not say the data is kept. It now stops all three, says the data is kept and the next step, and fails in plain words. Brief N8 remains |
| `securax`, `go` | fixed (#319) | Said "your previous version is running again" for every failed update, also when nothing was running; said "the app just opened" when no opener worked, and a Mac had no opener at all. Both now say what happened. Briefs N6, N7 and N13 remain |
| `securax`, `up` | reviewed (#319) | Sound: four fallbacks, keys made by itself, never left with nothing running. The port-clash help is for Windows only; a pasted key shows on screen. Briefs N4 and N5 |
| `securax`, `update` | reviewed (#319) | Careful: backup first, health check, goes back by itself, exit 3 for a rollback. Runs new code with no signature check; carries on when the backup failed; drops a person's edit to one file without a word. Briefs N1 to N3 |
| `securax`, `why` | reviewed (#319) | Works as written. Names Docker Desktop only (brief N6) |
| `local/compose/docker-compose.yml` | fixed (#319), header only | Every published port is on the loopback address by default, the database network has no way out, required passwords have no default. The header named one make of laptop (fixed). Briefs N9 to N11 remain |
| `DEPLOY.md` (the Windows rows, "Stop, update, back up") | fixed (#319) | Gave `git pull` as the way to update, which leaves the old code running and takes no backup; it now names the safe update. Brief N12 remains |
| `README.md`, "Quick start" | reviewed (#319) | True since #316 (the stop keeps the data). The older step-by-step path is brief M6 |

### Briefs from slice 3

**N1. An update runs new code that nobody checked the signature of (strong tier: supply chain; do it with L5 and M3).**
The beta channel pulls `main`; the stable channel takes the newest `v*.*.*` tag, and a tag can be moved. `go` starts an
update by itself whenever it is behind. Test first: in `governance/tests/`, a temp repository with an unsigned newer tag
expects "release not verified, nothing changed" on the stable channel. Step: verify the tag (or compare its commit with
the one the release publishes) before `git checkout`. confirm: which of the two the release workflow can do today.

**N2. "Your data is untouched" is not always true after a rollback.** When the backup fails, `update` carries on. A newer
image of a service that keeps data (chat, the database, automation, the password manager, private documents) can change
its stored data on first start, and the older image may not open it after the rollback. Test first: with a pretend `git`
and a failed backup, an update whose compose file moves the image of a data-keeping service is held with `--auto` and
asks first without it. Step: compare the image lines of those services between the two commits before `down`.
confirm: which of the five really migrate on start, and whether each can go back.

**N3. `update` discards a person's edit to `litellm-config.yaml` without saying so** (the same habit as L4). Test first: a
temp repository with that file edited expects the edit saved beside it and one line that says so. Step: copy, then
restore. `DEPLOY.md` tells people to run the same `git checkout --` by hand: change that line with it.

**N4. `up` asks for a key in the terminal, and it shows as it is pasted** (`zero-setup`: secrets are never pasted). A
decision for the owner first: hide the typing (`read -s`, which looks frozen to a novice), or move the ask to the
Command Center, where the key panel already is. Recommended: the second; it is part of the open friction
`copy-paste-secrets` in `governance/frictions.json`. Test first: `test_one_command_setup.py` expects no `read` of a key in `up` without `-s`.

**N5. The port-clash help in `up` is for Windows only.** A person on a Mac or Linux is told to open Windows PowerShell
and run `netstat`. It also names the default domain, not `SECURAX_DOMAIN`. Test first: run the branch with a pretend
`docker` that prints "port is already allocated" and a pretend `uname` that says Darwin; expect `lsof`, not PowerShell.
Step: one helper that picks the line by system (`/proc/version` holds "microsoft" on WSL).

**N6. `why` belongs in L7.** It too says "start Docker Desktop" when Docker Engine runs inside Ubuntu, and `go` says
"not reachable from Ubuntu" on every system. L7 names four places; there are six. Step: the same shared helper.

**N7. `go` can send the phone link through the alert topic (strong tier: secrets).** The link holds the sync token. The
comment above it says the token "is never sent to a server"; this path sends it through one, after a yes (default no),
and trusts that server to honour "do not store". Test first: `governance/tests/` expects a `threat-models.json` entry
for this flow, or expects the offer gone. Recommended: remove the offer once the pairing scan covers phones
(`zero-setup`, "Secrets too"); until then add the threat-model line and correct the comment.

**N8. What `down` still leaves, and no proof on real Docker.** Studio and the `security` profile (the log store, the
dashboards) keep running after a stop. A decision for the owner: Studio has its own stop and says "your estate is
untouched", so the recommended answer is to say "Studio is still running" in the closing line rather than stop it.
Test first: add to the M10 journey that after `down` no container of the password manager or the tunnel is left.
confirm: every supported Docker Compose accepts several `--profile` flags on `down`.

**N9. Two versions of one scanner, and four images with no digest.** The compose file runs Trivy 0.76.2; `./securax
scan` runs 0.58.1. Ollama, Postgres, Loki and Trivy carry a tag only, and the Postgres tag moves with every minor
release. Test first: `local/compose/tests/test_container_hardening.py` expects a digest on every `image:` line that is
not built here, and one Trivy version across the repository. Step: one image per run. confirm: the digests (needs the
network), and that the newer Trivy reads the current ignore file.

**N10. Chat and the dashboards both publish port 3000.** Starting the `ai` and `security` profiles together fails with
a port clash. The comment block at the top still describes profiles as they were ("Llama Guard", "SIEM-lite"). Test
first: `test_compose_sanity.py` fails when two services publish one host port. Step: move the dashboards to a free
port, through `web_url`, and rewrite the three comment lines.

**N11. The scanner container is given the Docker socket (strong tier).** `:ro` on a socket does not make Docker's API
read-only: a process that can reach it can start a container with the whole disk. It is in the `security` profile only
and runs when asked. Test first: `governance/tests/` expects a threat-model entry that names this and its review date.
Step: write the entry (accepted with a reason and a date), or scan saved images instead of the socket.

**N12. `DEPLOY.md` sections 1 to 5 are from before `./securax go`.** The Windows step in the first box says to edit
`.env` although the first start asks; ten lines show an address with a port (with W5 and M4); "your data lives in the
browser" is from before sync and backup; "pin a version" gives `git checkout` where `./securax channel stable` and
`./securax rollback` exist. Decide it with M6. Test first: `lifecycle/tests/test_doc_recipes.py` fails on `git pull` or
`git checkout` given as the way to update or pin in a root page. confirm: on Windows, does the first double-click
reach the key question (is it a real terminal there)?

**N13. Small ones in `go`.** A first regulator-watch fetch that fails says nothing (neither done nor to fix), and the
line names two Indian regulators for everyone (`global-ready`: a `where`). Test first: with a pretend `regwatch` that
fails, expect one line under "Needs one action each".

### Next slice (at most 15 files)

Still in rank 1: the `doctor`, `start`, `stop`, `setup`, `backup` and `restore` branches of `securax` (each counts as
one file; `restore` empties a volume before it refills it, so read that one first), `local/compose/.env.example`,
and the other compose files (`tls.yml`, `tls-internal.yml`, `tls-move.yml`, `full-stack.yml`).
