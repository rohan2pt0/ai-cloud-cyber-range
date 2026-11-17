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
| 1 | Launchers and installers | root files (44), `local/` (43), `tools/windows/` (1) | 20 of 88 reviewed; 9 fixed (8 in #313, 1 in #326). Part read: `securax` (5 branches), `DEPLOY.md` (Windows rows). See slices 1 and 2 |
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

### Slice 2 (2026-11-17, PR #326): the first start, on every system

Nothing in this slice was run against a real Docker, a real server or Windows. "Fixed" is held by a test with stand-in
programs; "reviewed" means read line by line, with what was found written as a brief below.

| File | Status | What was found |
|---|---|---|
| `local/scripts/teardown.sh` | fixed (#326) | It erased every Docker volume (chats, private documents, workflows, the password vault, synced Life OS data) while the README and the guide call it "stop everything". It now stops and keeps the data; `--wipe` erases after a typed word |
| `install.sh` | reviewed (#326) | Fixed: `--server` used `sudo` without installing it; `--help` cut the summary short and showed a raw placeholder. Briefs S6, S11 to S14 remain |
| `GETTING-STARTED.md` | reviewed (#326) | Fixed: two pointers to files that exist nowhere. Brief S16 remains (two start paths, ports, an example file nobody has) |
| `DEPLOY.md` | Windows rows only (#326) | Docker Desktop is the only path named; two folder names for one folder; a key typed into a file by hand. Brief S16. The rest goes in a later slice |
| `local/scripts/bootstrap-laptop.sh` | reviewed (#326) | Sound: every download is checked against a pinned hash before it is installed. Brief S15 remains |
| `local/scripts/daily-driver-up.sh` | reviewed (#326) | It starts the estate without the steps `securax up` takes first (the service key stays the public development one). Brief S15 |
| `local/scripts/kind-up.sh` | reviewed (#326) | Says it brings up Falco; nothing installs it. The Kyverno chart has no version. Brief S15 |
| `local/compose/docker-compose.yml` | reviewed (#326) | Sound on the whole: loopback by default, no new privileges everywhere, the database on a closed network, the scanner holds the Docker socket for seconds only. Brief S10 remains |
| `securax`, `up` | reviewed (#326) | Fixed, no test yet: the "show your sync token" hint only worked from the code folder; a closed terminal at the names question ended the start silently. Briefs S8, S9 remain |
| `securax`, `go` | reviewed (#326) | Briefs S1, S2 (what leaves the machine without a clear question) and S8 |
| `securax`, `update` | reviewed (#326) | Careful: backup first, health check, rollback by itself. Briefs S3 to S6 remain |
| `securax`, `down` | reviewed (#326) | One line. Brief S7: it may leave the password manager, the tunnel and Studio running |
| `securax`, `why` | reviewed (#326) | Brief S8 (wrong advice outside Windows) and S9 (asks for raw logs to be pasted) |

### Briefs from slice 2

Ranked by risk to a person. **Strong** marks a brief for the strong tier (secrets, sign-in, update logic).

**S1. The phone link carries the sync token through the alert topic (strong).** `go` offers to send the one-tap phone
link as a notification. The link holds the token that reads and writes all of a person's synced data, and the alert
service is a third party; the default answer is No, but the question says it "is not stored there" and nothing more.
Test first: in `local/compose/tests/`, fail when `securax` passes the output of `synclink.py` to `curl`. Step: send a
pairing code that works once and expires in ten minutes, or show the QR on the laptop screen (`zero-setup`: the pairing
scan). Needs a line in `governance/threat-models.json`.
Verified: an ntfy server keeps messages for 12 hours by default ([ntfy: configuration](https://docs.ntfy.sh/config/)).
confirm: the `Cache: no` header keeps one message out of that store while connected subscribers still get it (read in
a mirror of the ntfy docs, not on the official page); and that on the public server anyone who knows a topic's name
can subscribe to it.

**S2. `go` publishes the app and Chat to the whole tailnet without a question.** It then prints "your devices only".
That holds for a tailnet of one person; on a shared tailnet every member's device can reach it, because a new tailnet
allows all devices to reach each other until its policy says otherwise
([Tailscale: Serve](https://tailscale.com/docs/reference/examples/serve), [policy samples](https://tailscale.com/kb/1192/acl-samples)).
Test first: with a stand-in `tailscale`, `go` asks once (answer kept in `.env`) before `serve --bg`, and the line it
prints says "every device on your tailnet". Step: one question, one changed sentence.

**S3. The stable channel takes a release candidate for the newest release (strong).** `update` picks the highest tag
that matches `v*.*.*`. Checked with git here: `v1.0.0-rc1` sorts above `v1.0.0`, so a stable machine would move to the
candidate and then never to the release. No candidate tag exists today, so nobody is affected yet.
Test first: in `lifecycle/tests/`, a temporary repository with tags `v0.9.0`, `v1.0.0-rc1` and `v1.0.0`; the tag
expression copied from `securax` must print `v1.0.0`. Step: keep only tags of exactly three numbers, and end the
lookup with `|| true` (an empty match must not end `update`).

**S4. `update` throws away a person's edit to `litellm-config.yaml` without a word** (the same as L4). Test first: a
stand-in `git` records calls; expect a copy named `litellm-config.yours.yaml` and one printed line before the
`checkout --`. Step: three lines.

**S5. When neither the new nor the old version starts, `update` says the backup is "intact" and does not name it.**
A rollback returns the code, not data a new version has already changed. Test first: the last message holds the
backup's file name and the words `securax restore`. Step: keep the name `backup` printed, and reuse it in the two
last messages. Drop "your data is untouched" from the rollback line; say "your data is in the backup above".

**S6. A copy installed with `--offline` can never be updated.** `update` says "download the latest ZIP"; `install.sh`
refuses a folder that exists; the keys live in that folder's `.env`. Test first: in `governance/tests/test_installers.py`,
`--offline` onto an existing offline copy checks the checksum, replaces the code and keeps `local/compose/.env` and
`vault/` byte for byte. Step: an `--upgrade` path for offline copies only; `update` names it.

**S7. `down` names one profile.** Compose stops only the profiles it is given, plus services with none
([Docker: profiles](https://docs.docker.com/compose/profiles/)), so the password manager, the online tunnel and Studio
keep running after "stopped." Test first: with a stand-in `docker`, `./securax down` names every profile the compose
file defines and ends with "start again: securax up". Step: read the profiles from the file, not a list.
confirm: on the Compose version the estate ships with, by running it once in the sandbox.

**S8. Advice for Windows shown on every system** (L7, wider). `why` (two messages), the port-clash message in `up`
("open Windows PowerShell") and the Tailscale line in `go` assume Docker Desktop on Windows. Step: the helper L7 adds,
used in these four places too; the test from L7 gains four cases.

**S9. `why` ends with "copy everything above into the chat".** The lines above are raw container logs, which can hold
a key, an address or a prompt. Test first: `governance/why.py` gains `redact()`; a test feeds it a fake low-entropy
key, an address built at run time and a bearer line, and expects none in the output. Step: `securax why` prints the
log through it. The same test covers the key typed at `up`: it is shown on screen as typed today; read it unseen.

**S10. The compose file.** One brief per line, each with a test in `local/compose/tests/test_compose_sanity.py`:
(a) Chat and Grafana both publish port 3000, so the `ai` and `security` profiles cannot run together, and
`bootstrap-laptop.sh` calls 3000 Grafana while every guide calls it Chat: move Grafana, fail on a repeated host port.
(b) Studio mounts the whole repository, so an AI agent inside a third-party editor can read `local/compose/.env`
(every key) and `vault/`: already in the queue as `studio-harden`; add the test that fails while the mount is `../..`.
(c) The comment says Studio is "bound to loopback only"; `BIND_HOST` moves it with the rest. One word.
(d) The password manager starts with sign-ups open and follows `BIND_HOST` too. Test first: `start passwords` on an
opened estate refuses, or closes sign-ups first. confirm: what "sign-ups close after your account" does today.
(e) Four images carry a tag and no digest (`ollama`, `postgres`, `loki`, `trivy`). `digest-pins.json` leaves them
out on purpose: it lists what another device or the internet can reach. The scanner is the exception worth adding: it
is the one third-party image that holds the Docker socket. Step: one entry in `digest-pins.json`, one digest.

**S11. `install.sh --docker` adds a second `[boot]` section to `/etc/wsl.conf`** when one is there already.
Test first: a dry run with `SECURAX_WSL_CONF` pointing at a file that has `[boot]`; expect one section afterwards.
Step: add the key under the section that exists. confirm: how WSL reads a repeated section.

**S12. `--server` turns password sign-in off when any account has a key (strong).** The comment says "this can never
lock you out"; a key the hosting provider put under another account is not a key the person holds for the account
they use. Test first: a dry run where only another account has a key; expect "SSH left as it was" and the
`ssh-copy-id` line. Step: count keys for the account that ran `sudo` (or root), nobody else.

**S13. `--stable` and `--version` take a tag from git with no second check (strong; joins L5).** Only `--offline`
compares a checksum. One brief for both first hops: `install.ps1` and this. `go` and the nightly update follow `main`,
so what runs on a person's machine rests on one code-host account: confirm it is in the register in doc 131.

**S14. The first start may ask for a group password.** When Docker is installed but the person is not in the `docker`
group, `install.sh` runs the start through `sg docker`, which asks for a password nobody has. Test first: stand-in
`sg`, `id` and a failing `docker info`; expect the one line "sudo usermod -aG docker $USER, then open a new terminal"
and no call to `sg`. Step: check membership first.

**S15. The three older scripts.** (a) `bootstrap-laptop.sh` and `kind-up.sh` write to fixed names in `/tmp`: use
`mktemp`. (b) `bootstrap-laptop.sh` waits 60 seconds for the gateway and goes on without a word when it never
answers: say so and name `./securax why`. (c) `kind-up.sh`: give the Kyverno chart a version, as the three tools
beside it have a pinned hash; and either apply `local/k8s/policies/falco-rules.yaml` or drop Falco from the first
line and from the README. (d) `daily-driver-up.sh` should call `./securax up` instead of repeating a part of it.
Test first, one for all four: a static test in `local/compose/tests/` on the script texts.

**S16. Two guides, two ways to start.** `GETTING-STARTED.md` and `DEPLOY.md` give Docker Desktop as the only way on
Windows (the installer's own path is Docker Engine inside Ubuntu), use two names for the folder, show eleven addresses
with a port (`names, not ports`), name an example file nobody has (`my_public_bio.txt`) and tell a Windows person to
type a key into `.env`. Test first: extend the docs recipe test to these two files: no `localhost:` outside a fenced
fallback, one folder name, every file named exists. Step: cut `GETTING-STARTED.md` to one screen (install, start,
the one next step) and link the rest. For the owner, not a model: a laptop's make and model is named in eight files
of a public repository; say "a 16 GB laptop with no graphics card" if that should go.

### Next slice (at most 15 files)

Finish rank 1's most used parts: `DEPLOY.md` (the rest), `README.md` (the hand-written parts), `SECURITY.md`,
`local/compose/.env.example`, `local/compose/guiding-map.conf`, `local/compose/tls.yml` and `tls-internal.yml`, then
the `doctor`, `start`, `open`, `backup`, `restore`, `protect` and `setup` branches of `securax` (count each branch as
one file), and `local/compose/gen_litellm_config.py`. If a file named here does not exist, take the next file in
`git ls-files local/compose` instead and say so.
