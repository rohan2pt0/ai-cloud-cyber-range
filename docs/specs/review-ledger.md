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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | Slice 1: 14 of 88 reviewed, 8 fixed (#313). Slice 4 adds 11 more, 5 fixed (#321; `securax` counts one per branch). Slices 2 and 3 wait in open PRs #316 and #319 and carry their own counts |
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

### Slices 2 and 3 (open PRs #316 and #319, not on main yet)

The installer and the laptop scripts (#316), then `up`, `go`, `down`, `update`, `why` and the main compose file (#319).
Their tables and briefs (M1 to M10, N1 to N13) are in those PRs. Slice 4 below was started from main and does not
repeat them; when all three merge, keep every table.

### Slice 4 (2026-11-16, PR #321): stop one part, back up, restore, first set-up

Nothing in this slice was run against real Docker, a real backup or a real restore. The fixes are held by
`lifecycle/tests/test_cli_restore_and_stop.py`, which runs a copy of the CLI in a scratch folder with a pretend
`docker`; the rest is read from the text. Each branch of `securax` counts as one file.

| File | Status | What was found |
|---|---|---|
| `securax`, `stop` | fixed (#321) | **`./securax stop docs` stopped nothing and said "stopped".** It always named a TLS sidecar; without internal TLS no file defines one, compose then refuses the whole line, and the error was thrown away. It now names a sidecar only when one exists, says when the stop failed (and keeps the add-on remembered), and a good stop says the data is kept and how to start it again. Brief P11 remains |
| `securax`, `start` | fixed (#321), one line | With internal TLS on, `start passwords` named a sidecar the password manager does not have, so it could not start. Fixed with the same check. Sign-ups stay open until a second command is run: brief P6 |
| `securax`, `restore` | fixed (#321), in part | Checks first, changes later, keeps the old `.env` and the old vault aside: good. But it **emptied each volume while a part outside the `ai` profile could still be running on it**; it took volume names from file names inside the backup and put them into a shell line; and a backup could write anywhere in the code folder, then be run. It now stops whoever holds a volume before it empties it, and refuses odd names and anything outside `vault/` before anything is changed. No way back for the volumes, and no proof of who made an unencrypted backup: briefs P1 to P3 |
| `securax`, `backup` | fixed (#321), in part | Careful: verified, refuses to write plain when encryption was asked for, suspect copies kept apart, only encrypted copies leave the machine. The file with the keys was readable by other accounts until the closing `chmod` (now private from the first byte), and the last line printed `restore <file>` (now `restore latest`). Briefs P4 and P10 |
| `securax`, `setup` | fixed (#321), one line | With no `openssl`, the sync token and three passwords were made from the clock, which can be guessed; they now come from the system's random source, as `up` already did. The wizard itself is the older path: brief P5 |
| `securax`, `doctor` | reviewed (#321) | The real chat test and the true error are the best part of it. With Docker unreachable it says so, then prints eight more lines that all read "down" and waits up to four minutes on the chat test. Brief P7 |
| `local/compose/.env.example` | reviewed (#321) | No real secret in it. The header still says "copy and fill in"; three lines carry a comment after the `=`; India is the default for everyone. Brief P8 |
| `local/compose/tls.yml` | reviewed (#321) | Sound: one HTTPS port, the phone ports on the loopback address only, the CA key never enters a container, the edge image pinned by digest |
| `local/compose/tls-internal.yml` | reviewed (#321) | Sound in design (every listener on loopback, trust files hold the public CAs too). The sidecar image has no digest; the password manager has no sidecar. Brief P9 |
| `local/compose/tls-move.yml` | reviewed (#321) | Five lines, right as it is: the old address answers on this machine only |
| `local/compose/full-stack.yml` | reviewed (#321) | Opt-in, loopback only, passwords have no default. Two images with no digest, one of them old. Brief P9 |

### Briefs from slice 4

**P1. A restore that fails half way has no way back (strong tier: recovery).** Each volume is emptied, then refilled. If
the second one fails (a full disk, Docker stopping), the first holds the backup's data, the rest hold today's, the old
`.env` is still in place, and the estate is down. Test first: with a pretend `docker` whose `run` fails on the second
volume, expect the last line to name a safety copy taken before anything was emptied and the one command that puts it
back. Step: take `./securax backup` into a file marked `pre-restore` first, as `update` does before it changes anything;
if that backup fails, stop there unless `--no-safety-copy` is given.

**P2. Nothing proves who made an unencrypted backup (strong tier: supply chain).** The checksums travel inside the same
file, so they show damage, not tampering. Slice 4 closed the worst door (a file outside `vault/`). Still open: the
`.env` in the backup replaces the live one (it can point the estate at another server), and the secrets and records
archives unpack into `~/.securax` with no list of what may be in them. Test first: a pretend backup whose
`sprout-secrets.tgz` holds a file outside `sprout/`; expect a refusal before anything is changed. Step: the same member
check for `sprout-secrets.tgz` (only `sprout/`), `records.tgz` (only the three record files) and `tls-ca.tgz`; then say
plainly, before the question, when the file is not encrypted and was not taken on this machine.
confirm: GNU tar refuses a member that writes through a link placed earlier in the same archive (it is the default; no test here holds it).

**P3. Replacing everything takes one "y" (`friction-by-consequence`).** The question does not say which backup (its
date), how old it is, or what goes: everything written since. Test first: the question names the backup's date and
asks for a typed word, and anything else leaves everything as it is. Step: read the date from `MANIFEST`; ask for the
word `RESTORE`; `--yes` stays for the routines.

**P4. Databases are copied as files while they run** (confirm). A Postgres folder copied under writes may not open
again; the drill opens the copy, but nobody has checked that it opens the Postgres ones. Test first: a sandbox journey
that backs up while a writer runs, restores, and reads the last committed row. Step: for a Postgres volume, a dump from
inside the container rides along and the restore prefers it.

**P5. A decision for the owner: `./securax setup` is from before `./securax go`** (the same family as M6 and N12). It
asks for a key to be pasted and shows it (brief N4), opens every published port to the whole Wi-Fi on one "y" over
plain HTTP, prints an address with a placeholder and a port, tells the person to install a third-party app, and says to
paste the sync token into the app (`zero-setup`: the pairing scan does this). `up` suggests it and `DEPLOY.md` leads
with it. Test first: no line `setup` prints holds `<`, a port, or the word "paste". Step: `setup` becomes a pointer to
`./securax go` and `./securax phones`; the phone question moves behind the HTTPS switch.

**P6. The password manager takes new accounts until a second command is run (strong tier: sign-in).** `start passwords`
ends on "create your account, then run `passwords lock`". Until then anyone who can reach the page can make an account.
Test first: after the first account exists, a second sign-up is refused without any command. Step: the estate closes
sign-ups by itself once one account exists, and says so. Small, same branch: `start all` does not start it although the
usage line reads as if it did, and `stop passwords` leaves `PASSWORDS_ENABLED=1` (confirm: what reads it).

**P7. `doctor` with Docker down.** It should stop after the first finding with the one next step (`one-open-action`),
not print "down" for each part and run a chat test that cannot pass. The Windows advice names Docker Desktop only (L7).
Test first: with a pretend `docker` whose `info` fails, expect at most five lines, no "Testing", and exit 1.

**P8. `.env.example`.** (a) The header and the sync lines tell a person to copy the file, fill it in and make tokens by
hand; `go` does all three. Step: the header says "you never need to edit this". (b) `XAI_API_KEY`, `PERPLEXITYAI_API_KEY`
and `AZURE_API_BASE` carry a comment after the `=`; the CLI's own reader returns that comment as the value. confirm:
whether any reader then treats the provider as set. Test first: no line in the file has text after `=` that starts with
spaces and `#`. (c) `ANSWER_CONTEXT`, the clock offset, the rupee cap and the cloud region are India for everyone
(`global-ready`). Step: `go` sets them from the region; the file's defaults assume no country. (d) confirm: `up` replaces
the public default of `LITELLM_MASTER_KEY` and the canary on first start, as it does the passwords.

**P9. Images with no digest in the overlays (do it with N9).** The internal-TLS sidecar (`nginx:1.31-alpine`), and in
`full-stack.yml` the database and the team chat; the team chat's version line is old (confirm: still supported).
`./securax full up` prints an address with a port. Test first: the pin test that covers the main compose file also
reads every overlay.

**P10. Small ones in `backup`.** `backup offsite` with a letter instead of a number ends on a shell error; a failed
checksum write is ignored and only shows at restore; the ransomware alert sends the machine's name to the webhook; a
restore unpacks the whole backup under `/tmp`, which may be memory on some machines. One test each, first.

**P11. Nothing proves the stop on real Docker.** Test first: a sandbox journey that runs `start flows`, then
`stop flows`, and reads from Docker that the container is no longer running; then the same with internal TLS on.

### Next slice (at most 15 files)

After slices 2 to 4, rank 1 still holds: the `status`, `open`, `protect`, `passwords`, `phones`, `tls`, `full` and
`studio` branches of `securax` (each counts as one file; `protect` and `passwords` hold secrets, so read those first),
`local/compose/stage-sprout.yml`, `design.yml` and `local/compose/litellm-config.yaml`.
