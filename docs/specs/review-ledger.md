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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | 20 of 88 reviewed, and parts of `securax` and `DEPLOY.md`; 12 fixed (#313, #325). See slices 1 and 2 |
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
| `install.sh` | skimmed (#313), not line by line | Checksums on the release path, clear failures, no destructive step seen. Read in full in slice 2 |

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

### Slice 2 (2026-11-17, PR #325): the first start, the stop and the update

Nothing in this slice ran against real Docker, a real cluster, a real server or Windows. Each "fixed" is held by a test
that runs the script with stand-ins for `docker`, `kind`, `kubectl`, `helm` and `curl` first on the path
(`local/compose/tests/test_local_scripts.py`, `governance/tests/test_installers.py`).

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#325) | It ran `down -v`, which deletes every data volume (chats, documents, workflows, synced data, models), while the guide called it "stop everything". Now it stops and keeps the data; `--erase` deletes after a typed word and names the backup first |
| `install.sh` | fixed (#325) | Read line by line. `--stable` with no network ended silently with curl's exit code; `--help` stopped mid-sentence. Briefs S1, S2, S3 and L5 remain |
| `local/scripts/bootstrap-laptop.sh` | fixed (#325) | A gateway that never started read as "FAIL - expected 400, got 000", a failed guardrail; the answer file sat at a fixed path in `/tmp`. Downloads are pinned and hash-checked: sound. Brief S4 remains |
| `local/scripts/kind-up.sh` | fixed (#325) | Any refusal of the insecure pod (no cluster, no network) counted as a pass. Now only an admission denial does. Brief S5 remains |
| `local/scripts/daily-driver-up.sh` | reviewed (#325) | Nothing destructive. It shares brief S4 |
| `GETTING-STARTED.md` | reviewed (#325) | Fixed: two pointers to files a person does not have, a placeholder file name, and a device model. Brief S6 remains |
| `local/compose/docker-compose.yml` | reviewed (#325) | Every published port is on loopback unless the person opens it; the gateway, the sync service and the tunnel are read-only with no capabilities. Never rename `name:`: the data volumes carry it. Briefs S7 and S8 remain |
| `securax`: `update` | fixed (#325), this branch only | It blamed "uncommitted local changes" when nothing new was pulled and the estate did not start. Back-up first and rollback are sound. Briefs S9 and S10 remain |
| `securax`: `up` | reviewed (#325), this branch only | Placeholder keys are replaced, the fallbacks are layered, a failed helper never stops the start. Briefs S8, S11 and L7 remain |
| `securax`: `go` | reviewed (#325), this branch only | Checks first, acts only when something is missing. Briefs S12 and L7 remain |
| `securax`: `down` | reviewed (#325), this branch only | One line. Brief S9 remains |
| `securax`: `why` | reviewed (#325), this branch only | Works with Docker off; an unknown log gets no invented reason. Its two messages belong to brief L7 |
| `DEPLOY.md` | reviewed (#325), the Windows rows only | They match the launchers as fixed in #313. Line 18 tells a Windows person to edit a file by hand (`zero-setup`): it joins brief S11. The addresses with ports join brief S6 |

### Briefs from slice 2

**S1. `install.sh --server` switches SSH passwords off when any account has a key.** It counts keys in every home folder.
A key left in another account (a provider's default user) is enough, and a person who signs in as root with a password is
then locked out of SSH. Strong tier. Test first: in `governance/tests/test_installers.py`, with `SECURAX_SERVER_DRYRUN=1`
and a fake home that holds a key for a third account only, expect "SSH still accepts passwords". Step: count the keys of
root and of the person who ran `sudo` (`SUDO_USER`) only.

**S2. `install.sh --server` ignores `--offline` and `--dir` without saying so.** Test first: `--server --offline FILE`
(dry run) exits non-zero and names the flag it cannot honour. Step: one `die` before step 1 of the server path.

**S3. `install.sh --docker` on WSL appends a second `[boot]` section to `/etc/wsl.conf`** when the file already has one
with another key, and its check misses `systemd = true` written with spaces. Test first: a dry run against a fake
`wsl.conf` that already holds `[boot]` prints one edit, not an append. Step: add the key under the section that exists.
confirm: how WSL reads a section named twice (not verified).

**S4. Two start paths, two sets of secrets.** `bootstrap-laptop.sh` and `daily-driver-up.sh` copy `.env.example` and start
the estate with the placeholder gateway key that is public in this repository; `./securax up` replaces it. They also print
addresses with ports, and say "Docker Desktop" to a person who runs Docker Engine in Ubuntu. A decision for the owner,
recommended: both scripts hand the start to `./securax up` (bootstrap keeps its tool installs and its smoke test).
Test first: in `test_local_scripts.py`, run each with a fake `docker` and expect no `docker compose ... up` of their own.
Step: one script per run.

**S5. `kind-up.sh` installs whatever Kyverno chart is newest, and its first line promises Falco, which it never installs.**
Test first: the `helm upgrade --install` line carries `--version`; the header names only what the script installs.
Step: pin the chart; drop the word (the README line says Falco too). confirm: the chart version to pin (not verified here).

**S6. The root guides show addresses with ports** (`GETTING-STARTED.md`: 4 lines; `DEPLOY.md`: 9), the same class as W5.
Step: one file per run; say "`./securax open` prints the right address" once and name the pages, not the ports.
`GETTING-STARTED.md` also teaches the older script path first: after S4, lead with `./securax up` only.

**S7. Two services publish the same port.** Grafana (profile `security`) and Chat (profile `ai`) both take 3000 on this
machine, so the two profiles cannot run together, and `bootstrap-laptop.sh` ends by naming 3000 as Grafana.
Test first: in `local/compose/tests/test_compose_sanity.py`, fail when two services in `docker-compose.yml` publish the
same host port. Step: move Grafana to a free port and update the two lines that name it.

**S8. A database that nothing uses starts on every `up`.** The `postgres` service is on a network no other service joins
(the overlays bring their own), and it starts with the placeholder password unless `setup` was run. It is unreachable, so
the risk is small; the cost is memory and a part to patch. Test first: fail when a service in the default profiles shares
no network with another service. Step: move it to a profile of its own. confirm: that no overlay or script reaches it by
name (`full-stack.yml` and `stage-sprout.yml` define their own).

**S9. `./securax down` says "stopped." while other parts keep running.** It stops the `ai` profile only. Compose leaves
services in other profiles running ([Docker's profiles page](https://docs.docker.com/compose/how-tos/profiles/);
[compose issue 11793](https://github.com/docker/compose/issues/11793)), so the password manager, the online tunnel,
Studio and the `security` profile stay up, and `update` never recreates the ones `up` does not restart. A decision for
the owner, recommended: `down` stops everything and says so; `down --keep passwords` for the person who wants the vault
up. Test first: a `test_cli_friction.py` case with a fake `docker` expects every profile in the call, or a line naming
what was left running. `teardown.sh` has the same gap. Not run against real Docker here.

**S10. A failed update is tried again every night.** After a rollback the checkout is behind main again, so the next
`update --auto` pulls the same version, stops the estate, fails and rolls back. The Go/No-Go poll softens it but does not
know this commit failed here. Test first: in a temp repository, a second `--auto` after a recorded failure of the same
commit exits 0 without `down`. Step: write the failed commit to a small state file; skip it until main moves past it.
The same branch also throws away a person's edit to `litellm-config.yaml` without a word (the L4 finding): say so first.

**S11. `up` asks for a Gemini key on every start, for ever.** A person who pressed Enter (the private local model) is
asked again each time, and one more tip line follows. Pasting a secret is also the open friction `copy-paste-secrets`.
Test first: `test_cli_friction.py` expects the question at most once (a `GEMINI_ASKED` line in `.env`, as `NAMES_ASKED`
does for names). Step: three lines in `up`. The port-clash message in `up` also tells every person to open Windows
PowerShell; say it only on WSL.

**S12. `go` publishes the estate to the person's Tailscale devices by itself** when Tailscale is signed in, under a first
line that says "Nothing you already set up is changed". It also offers to send the one-tap phone link, which carries the
sync token, through the alert topic on a third-party server (asked, default no). Strong tier; a decision for the owner.
Recommended: ask once before the first publish, as `up` does for names. Test first: with a fake `tailscale` that reports
nothing published and no terminal, `go` publishes nothing and prints the one command. Check that
`governance/threat-models.json` covers the link through the alert topic.

**S13. A device model in six more files** (`docs/architecture.md`, docs 00, 05, 10 and 28, `portal/explainer.html`,
`personal-rnd/self_opsec.py`). The repository is public and the model says whose machine it is. Step: "a 16 GB laptop",
one file per run. Slice 2 removed it from the three files it read.

### Next slice (at most 15 files)

The rest of rank 1, largest risk first: `DEPLOY.md` (the whole file), `README.md` (the hand-written parts),
`local/compose/.env.example`, `local/compose/guiding-map.conf`, `local/compose/gen_litellm_config.py`,
`local/compose/model_discovery.py`, `local/compose/full-stack.yml`, `local/compose/stage-sprout.yml`, the TLS overlay
files in `local/compose/`, then the `doctor`, `setup`, `start`, `backup` and `restore` branches of `securax` (count each
branch as one file).
