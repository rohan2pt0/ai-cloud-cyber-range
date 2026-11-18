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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | 19 of 88 reviewed, 3 more in part (`securax`, `DEPLOY.md`, `docker-compose.yml`); 8 fixed (#313), 5 fixed (#327). See slices 1 and 2 |
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
| `install.sh` | skimmed (#313); read line by line in slice 2 | See slice 2. One line here was wrong: only `--offline` checks a checksum; `--stable` and `--version` do not |

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

**L5. `install.ps1` runs `install.sh` from `main` with no checksum (strong tier: supply chain).** Only the `--offline`
path inside `install.sh` checks a checksum (corrected in slice 2); the first hop does not, and nor do `--stable` and
`--version` (brief I1). Test first: `governance/tests/test_installers.py` expects
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

### Slice 2 (2026-11-17, PR #327): the first start on Linux, macOS and inside Ubuntu

Nothing in this slice was run against Docker, kind, a real server or Windows. `teardown.sh` was run against a fake
`docker` that records its arguments; `install.sh` was run with a fake `curl`; the rest is held by static tests
(`local/compose/tests/test_local_scripts.py`, four new tests in `governance/tests/test_installers.py`).

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#327) | **It deleted every data volume** (`down -v`) while three pages called it "stop everything, costs nothing overnight". Now it stops and keeps the data; `--erase` says what is lost, offers the backup first and needs the typed word ERASE at a terminal |
| `install.sh` | fixed (#327), briefs I1 to I4 remain | `--stable` ended silently when the newest release could not be found (a failed command inside `$(…)` under `set -e`); a failed download had no plain reason; `--server --restore` found a mistyped backup only after it had changed the machine; `--help` left out `--yes` and `--no-start` |
| `local/scripts/kind-up.sh` | fixed (#327) | The admission test read ANY failure (no cluster, a timeout) as "PASS, admission denied". It now passes only when the error says denied. It wrote to a fixed name in `/tmp` |
| `local/scripts/bootstrap-laptop.sh` | fixed (#327), brief S1 and S2 remain | Said it checks terraform (it does not); a gateway that never answered was reported as "expected 400, got 000"; a fixed name in `/tmp`; named one laptop model |
| `GETTING-STARTED.md` | fixed (#327), brief G1 remains | Sent a person to two "uploaded" files nobody else has; showed an address with a port; named one laptop model; said Docker Desktop is the only way |
| `local/scripts/daily-driver-up.sh` | reviewed (#327) | Sound as a script, but it is the older path. Brief S1 |
| `securax`: `update` | reviewed (#327), one line fixed | **Its WSL DNS advice overwrote `/etc/wsl.conf`**, the file `install.sh --docker` writes "start Docker by itself" into. Now it appends (`tee -a`), in doc 121 too, and a test fails on any overwrite. Briefs U1 and U2 remain |
| `securax`: `up` | reviewed (#327) | No defect found in the start-up ladder; the `|| true` guards the lessons ask for are there. Briefs P1 and P2 |
| `securax`: `go` | reviewed (#327) | Brief T1 (strong tier) |
| `securax`: `down` | reviewed (#327) | Brief D1 |
| `securax`: `why` | reviewed (#327) | Brief Y1; its Docker Desktop wording is brief L7 |
| `DEPLOY.md` | Windows rows only (#327) | Told Windows users to edit `.env` by hand though `securax.cmd setup` works; one row said Docker Desktop is the only Docker. Both fixed. The rest is not reviewed |
| `local/compose/docker-compose.yml` | surveyed (#327), not line by line | Read in full: the service list, every published port, every secret default, and the `trivy`, `vaultwarden`, `cloudflared` and `studio` services. Every port binds to this machine only by default and every service sets `no-new-privileges`. Briefs C1 to C4. It goes back in the next slice |

### Briefs from slice 2

**I1. `--stable` and `--version` trust the tag as fetched (strong tier: supply chain; do it with L5).** Test first:
`test_installers.py` expects the stable path to compare the release archive with its published `SHA256SUMS` (the check
`--offline` already has) before any file is used. Step: download the archive and the sums, reuse the offline branch.
confirm: whether releases are signed; if they are, verify the signature, and say "matches the published checksum", since
a checksum next to the file proves the download is whole, not who made it.

**I2. The server path starts the estate twice.** `--server` runs the installer again as the `securax` user; since
2026-11-11 that inner run also turns HTTPS on, starts and opens, and then the outer run starts it again. Test first:
with `SECURAX_SERVER_DRYRUN=1` the "would run" line names `--no-start`. Step: pass `--no-start` to the inner run.
confirm (owner): a server is reached through the tunnel, so the inner "HTTPS on" should not be needed there.

**I3. A half-unpacked offline install blocks the next try.** A full disk mid-`tar` leaves the folder, and the next run
says "already exists, run update". Test first: an archive cut short leaves no folder behind. Step: unpack to a
temporary folder beside it, then rename.

**I4. Two smaller ones in `install.sh`.** (a) `--docker` appends `[boot] systemd=true` to `/etc/wsl.conf` even when the
file already has a `[boot]` section or says `systemd=false`; confirm how WSL reads a repeated section, then edit the
section in place. (b) `--server` sets the clock to India when `SECURAX_TZ` is not given (`global-ready`): keep the
machine's own zone unless one is asked for, and say which zone the schedules will use.

**S1. Two start scripts skip what `./securax up` does for safety (owner decision; recommended: make them call it).**
`bootstrap-laptop.sh` and `daily-driver-up.sh` copy `.env.example` and start Compose themselves, so the estate runs
with the placeholder gateway key that is printed in this public repository, placeholder database and dashboard
passwords, and no sync token. `./securax up` replaces each of these on first start. Every port is local, so the risk is
other programs on the same machine. Test first: a static test fails when a script under `local/scripts/` runs
`docker compose ... up` without going through `securax`. Step: `daily-driver-up.sh` becomes `exec ./securax up "$@"`;
`bootstrap-laptop.sh` keeps its tool installs and smoke test and calls `./securax up` for the start.

**S2. Pinned tools in `bootstrap-laptop.sh` are past support.** kubectl 1.31.3: Kubernetes 1.31 reached end of life on
2025-11-11 (kubernetes.io/releases). Test first: fail when the pinned kubectl is older than the three newest minor
releases named in a small data file the update routine refreshes. Step: bump kind, kubectl and helm with their hashes.
confirm: the three pinned hashes were not re-checked in this session (no download was made). Also: a failed `tar` in
`install_helm` is silent, so the first sign is "helm: command not found" one script later; one `|| return 1`.

**G1. `GETTING-STARTED.md` sections 1 to 3 describe the older "pillars" path** (three scripts, a table of addresses
with ports, a key pasted into `.env`). Owner decision; recommended: keep the one-step start, replace sections 1 to 3
with the same commands through `./securax` (`up`, `open`, `setup`, `down`), and move the range demo to
`docs/demo-runbook.md`. Test first: the `no-raw-addresses` check reads this file but still lets its old
addresses through; expect none in it. confirm: how the check lets them through (a baseline count or a marker). `README.md` line 211 and `docs/securax/05-ROADMAP.md` name the same scripts.

**U1. A failed update is tried again every night.** After a rollback the nightly `update --auto` sees the same new
version and repeats: stop, start, fail, roll back, and a phone message, each night until the code moves. Test first:
in `governance/tests/`, a second `--auto` run for a target recorded as failed exits early and says "held: this
version failed on DATE". Step: write the failed commit to a small file on rollback; skip while it is still the target.

**U2. `update` discards a person's edit to `litellm-config.yaml` without saying so** (the same as L4, in the CLI).
Test first: a temp repository with that file edited; expect a line that names the file and where the copy went.
Step: copy it to `litellm-config.yaml.yours` first, and say so.

**P1. `up` asks for an AI key to be pasted, and shows it on screen as it is typed.** `zero-setup` says no pasted
secrets; until the one-door path replaces it, the prompt should at least not echo. Test first: the prompt line uses
`read -rs`. Step: that, and record the friction in `governance/frictions.json`. The same branch tells a person to
print their sync token with `grep`; point to `./securax sync-link` instead.

**P2. The "port is already used" advice is for Windows only.** On Linux and macOS it still says "open Windows
PowerShell". Test first: with a fake `uname`, expect `ss -ltnp` (Linux) or `lsof -i` (macOS) in the message. Step: one
helper, used here and by brief L7's messages.

**T1. `go` publishes the Life OS and Chat on Tailscale without asking (strong tier; needs a threat model first).**
When Tailscale is installed and signed in, `go` runs `tailscale serve` for both and prints "your devices only". That
is true on a personal tailnet and false on a shared one (a family's, or an employer's): everyone the tailnet's rules
allow can open them. Test first: with a fake `tailscale` on the path, `go` asks once (default no when the answer
cannot be read) before the first `serve`, and remembers the answer. Step: the question, a stored answer, and the
wording "everyone on your Tailscale network". confirm: no model for this flow was found in
`governance/threat-models.json`; add one (spoofing and information disclosure are the two that matter).

**D1. `./securax down` and STOP-Windows.bat leave some services running.** `down` names only the `ai` profile, and
Compose stops only the services of the profiles it is given (docs.docker.com/compose/profiles). So the password
manager, the editor and, the one that matters, the online tunnel stay up after "stop". Test first: with a fake
`docker`, expect `down` to name every profile in the compose file (read them from the file, not a list). Step: that one
line. Then check `update`, which calls `down` then `up`: `up` brings back passwords and online; Studio and the
`security` profile must be restarted too, or left out on purpose with a line that says so.

**Y1. `why` ends with "copy everything above into the chat".** The lines above are raw service logs. Test first: feed
`why`'s output a log line that holds a key-shaped value and an e-mail address; expect both masked. Step: pass the log
through the redaction the gateway already has before printing. confirm: which module holds it.

**C1. Two services want the same port.** Grafana (`security`) and Chat (`ai`) both publish 3000, so the two profiles
cannot run together, and `bootstrap-laptop.sh` prints 3000 for Grafana. Test first: `test_compose_sanity.py` fails on
a host port used twice. Step: move Grafana.

**C2. One switch opens nine doors (strong tier).** `BIND_HOST` is shared by the gateway, Chat, Private Docs,
Automation, the password manager, the Command Center and Studio. A person who sets it to reach Chat from a phone
opens all of them to the same network. Studio mounts the whole folder, `.env` and `vault/` included, and its password
defaults to empty. Test first: `test_container_hardening.py` expects Studio and the password manager to bind to this
machine whatever `BIND_HOST` says. Step: give those their own variable. confirm: what code-server does with an empty
`PASSWORD`, and whether `./securax studio` always sets one.

**C3. Four images are pinned by tag only** (`ollama`, `postgres`, `loki`, `trivy`); nine have a digest. Test first:
fail on a third-party image without `@sha256:`. Step: add the digests. confirm: an existing test may allow these on
purpose.

**C4. Thin hardening outside the gateway.** 2 of 15 services have a health check, 3 run read-only, 3 drop
capabilities. Test first: a ratchet in `test_container_hardening.py` (the three counts may only rise). Step: one
service per run, the ones that hold data first.

### Next slice (at most 15 files)

`local/compose/docker-compose.yml` (line by line), `local/compose/.env.example`, `DEPLOY.md` (the rest), `README.md`
(the quick start), then the branches of `securax` a person meets next (count each as one file): `doctor`, `start`,
`open`, `setup`, `backup`, `restore`, `protect`, `status`, `shortcut`, and the helpers `preflight` and `autosize`.
