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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | 19 of 88 reviewed; 13 fixed (#313, #322). `securax` (5 of its branches), `DEPLOY.md` and the compose file are part-read. See slices 1 and 2 |
| 2 | The Life OS | `guiding-map/` (196) | not reviewed |
| 3 | The gateway and security | `apps/` (47), `governance/` (230), `policies/` (1), `redteam/` (11), `ai-soc/` (6), `mcp/` (3), `agents/` (12), `intel/` (9) | 1 of 319 reviewed (#313, encoding only) |
| 4 | Sync and backup | inside `apps/` and `governance/` (review them first within rank 3), `routines/` (10), `sandbox/` (4) | not reviewed |
| 5 | The website | `website/` (24), `portal/` (3) | brand and colour check only (#313, section 1); not reviewed line by line |
| 6 | Docs | `docs/` (165), `design/` (6), `templates/` (16), `knowledge/` (2), `learning/` (8) | brand check only (#313, section 1); one line of doc 121 fixed (#322) |
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
| `install.sh` | skimmed (#313); read line by line in slice 2 | See slice 2 |

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

### Slice 2 (2026-11-16, PR #322): the installer, the local scripts, five branches of `securax`

Nothing here was run against Docker, a cluster, WSL or a real server. Each "fixed" is held by
`lifecycle/tests/test_review_slice2.py`, which runs the scripts against stand-ins, or reads their text.

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#322) | **Data loss.** The README and Getting Started called it "stop everything", and it ran `down -v`: chat history, private documents, workflows, the sync copy and the database were deleted with no question. Now it stops and keeps the data; `--erase` says what is lost, names the backup first, and needs the typed word |
| `securax`, `up` | fixed (#322), part | **Weak key.** Without python3 the gateway key was written as the three characters `sk-` and reported as "strong", and the sync token as empty. One helper now falls back to openssl, then the kernel, and a short key is never written. Also: a pasted AI key was shown on the screen; the port-clash advice was Windows-only on every system; a printed `grep` worked only from the code folder. Briefs S1, S9, S10, S13 remain |
| `securax`, `update` | fixed (#322), part | Its WSL DNS advice overwrote `/etc/wsl.conf`, which also removed the line the installer writes so that Docker starts by itself. It now adds to the file (doc 121 said the same; fixed). Briefs S4, S10 remain |
| `securax`, `go` | reviewed (#322) | Sound: every step checks first. Briefs L7 and S2 remain |
| `securax`, `why` | reviewed (#322) | Brief S3 remains |
| `securax`, `down` | reviewed (#322) | One line. Brief S1 remains |
| `install.sh` | fixed (#322) | `--server` checked a backup, a key file and its own file only after it had changed the machine; a second `[boot]` section could be written to the WSL file, and a person's own `systemd=` choice was ignored; it said "your Command Center is open" when nothing had opened; `--help` cut its own text in half. Briefs L5, S4, S5, S6 remain |
| `local/scripts/kind-up.sh` | fixed (#322) | **A test that could not fail.** The "insecure pod must be rejected" check passed on any error at all (no cluster, no network). It now passes only on a denial by the admission policy. The header claimed Falco is installed; it is not. A fixed file name in `/tmp`. Brief S8 remains |
| `local/scripts/bootstrap-laptop.sh` | fixed (#322) | When the gateway never came up, the smoke test ran anyway and failed with a missing file; a fixed file name in `/tmp`; it said it checks terraform and does not. Briefs S8, S11 remain |
| `local/scripts/daily-driver-up.sh` | reviewed (#322) | Starts the estate without the key step of `up`. Brief S11 remains |
| `GETTING-STARTED.md` | reviewed (#322) | Pointed to two files that are not in the repository; now points to `./securax why` and `./securax profile`. The rest is the older path. Brief S12 remains |
| `README.md` (one line) | fixed (#322) | The same "stop everything" line for `teardown.sh` |
| `DEPLOY.md` | Windows rows only (#322) | In step with `securax.cmd` after #313. Its address table shows ports (W5's rule); it goes in the next slice for a full read |
| `local/compose/docker-compose.yml` | security lines only (#322) | Every published port is on the loopback address by default; the Docker socket is held only for the seconds a scan takes. Briefs S7, S8, S11 remain; a line-by-line read is in the next slice |

### Briefs from slice 2

Ranked by risk. **Strong** means security: a strong model writes it and a second look reviews it.

**S11. The database password is the public example value (strong).** `local/compose/.env.example` ships a database
password and `up` replaces the gateway key and the sync token but never this one, so every install runs the same
published password. The database has no host port and sits on an internal network, which is why this is not rank one.
Test first: in `local/compose/tests/`, run the key step of `up` on a copy of the example file and expect the password
changed and at least 32 characters. Step: make it once for a NEW install only (no data volume yet), with `rand_hex`.
confirm: an existing volume keeps its old password, so a changed value in `.env` would lock the estate out; that path
needs `ALTER USER` and its own brief. The two older scripts (`bootstrap-laptop.sh`, `daily-driver-up.sh`) copy the
example file and start with the placeholder gateway key as well: make both call the same key step.

**S2. `go` sends the phone's set-up link through the alert service (strong).** The comment beside it says the sync
token "is never sent to a server"; the link goes out as a notification's tap address, so the relay sees it.
Test first: `governance/tests/` expects the message to carry no part of the sync token. Step: send a one-time pairing
code that the laptop exchanges, or show the QR on the laptop only. It needs a line in `governance/threat-models.json`.
confirm: what the link from `governance/synclink.py --print-only phone` holds today.

**S4. A release is not checked for its origin (strong; joins L5).** `--stable` and `--version` clone a tag over HTTPS
and check nothing more; `update` on the stable channel moves to the newest tag the same way; `--offline` compares the
archive with a `SHA256SUMS` file that sits next to it, which catches a damaged download and not a replaced one.
Slice 1 said the release path checks a checksum: only `--offline` does. Test first: `governance/tests/test_installers.py`
expects a signature check on the sums file before the archive is opened, and a plain refusal when it fails.
Step: verify the signature the release workflow already makes. confirm: that the workflow signs, and with what.

**S1. `./securax down` says "stopped." while parts keep running.** It stops one profile. The password manager, the
online tunnel and Studio belong to others, so the tunnel can stay up, pointing at nothing. Test first: a unit test with a
stand-in `docker` expects every profile the person switched on (`SECURAX_OPTIONAL`) in the `down` call, and expects the
last line to name anything left running. Step: one line. confirm: on a real machine that `update` (which calls `down`,
then `up`) brings each part back.

**S3. `why` prints raw log lines and says "copy everything above into the chat".** A log can hold a key or a token.
Test first: feed `why` a log line with a plainly fake key and expect it masked. Step: mask anything shaped like a key before a line is printed.
confirm: whether `governance/why.py` already masks, and whether the gateway has a mask to reuse.

**S5. `--server` turns password sign-in off when any account has a key.** If the only key belongs to an account that
cannot use `sudo`, root is then reachable only through the provider's console. Test first: the dry run with a stand-in
key file for a non-admin account expects SSH left as it is, with the reason. Step: count keys for root and for members
of the `sudo` group only.

**S6. `--server --restore` on a server that already has SecuRAX restores nothing, starts nothing, and says "running".**
Test first: the dry run with an existing folder and `--restore` expects a refusal that names `./securax restore`.
Step: one check before step 1.

**S7. Two parts want the same port.** Grafana (the `security` profile) and Chat (the `ai` profile) both publish host
port 3000, so the two profiles cannot run together, and `bootstrap-laptop.sh` prints that port for Grafana.
Test first: `local/compose/tests/test_compose_sanity.py` fails when two services publish one host port. Step: move Grafana.

**S8. Pins that have aged or are missing.** `bootstrap-laptop.sh` pins kind, kubectl and helm by version and hash;
the versions are two years old. `kind-up.sh` installs the Kyverno chart with no version. In the compose file the
database, the local-model server, Loki and Trivy carry a tag and no digest. Test first: extend the pin test
(`local/compose/digest-pins.json`) to every image, and a static test that `helm upgrade --install` carries `--version`.
confirm: the three hashes were not re-checked against their publishers in this session; whether those tool versions
are still supported; whether the four images are left without a digest on purpose.

**S9. `up` asks a person to paste a key into a terminal.** `zero-setup` says a secret is never copied by hand. It is
now hidden as it is pasted, which is the cheap half. Step: none for a model; it belongs to the queue item that replaces
`.env` keys with the one-door sign-in. confirm: that item's id in `governance/queue.json`, and an entry in
`governance/frictions.json`.

**S10. Two silent removals.** `update` runs `git checkout --` on `litellm-config.yaml` without a word (the same as
L4), and `up` runs `rm -rf` on the generated config when it is a folder; when Docker made that folder as root, the
removal fails and `up` ends with a bare permission error. Test first: expect a line that says what was put back and
where a copy is; expect a plain next step when the removal fails. Step: two messages and one copy.

**S12. `GETTING-STARTED.md` is the older path.** It shows ports, three scripts that `./securax up` replaced, and a
command that names a file the person does not have. A decision for the owner; recommended: keep its first section
(one step) and replace the rest with links to `DEPLOY.md` and `WINDOWS-QUICKSTART.md`.

**S13. A device model is named in seven more files** (`docs/architecture.md`, docs 00, 05, 10 and 28,
`personal-rnd/self_opsec.py`, `portal/explainer.html`). It hints at the owner's own machine in a public repository.
Three places were made general in this slice. Test first: `lifecycle/tests/` fails on the model's name anywhere,
read from a fingerprint, never written in the test. Step: one file per run.

**L7 still stands**, and is wider than slice 1 found: `go`, `why` and `preflight` all send a person with Docker Engine
inside Ubuntu to Docker Desktop.

### Next slice (at most 15 files)

`local/compose/docker-compose.yml` (line by line), `tls.yml`, `tls-internal.yml`, `tls-move.yml`, `full-stack.yml`,
`.env.example`, `gen_litellm_config.py`, `guiding-map.conf`, `DEPLOY.md` (in full), `CONTRIBUTING.md`, then the
`doctor`, `open`, `backup`, `restore` and `setup` branches of `securax` (count each branch as one file).
