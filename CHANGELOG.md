# Changelog

All notable changes to SecuRAX are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md)
for the versioning and release policy.

## [Unreleased]
### Added
- **Crown jewels** (doc 84): `./securax jewels` ranks what the estate cannot lose from live checks. Each jewel shows DO NOW / THIS WEEK / WATCH and the one command that fixes it, and the cockpit lights the first one.
- **The crisis and continuity plan** (doc 84): `./securax continuity` lists nine scenarios with their RTO and RPO targets.
  - **Measured:** RPO comes from the real backups and code bundle; RTO comes from timed drills.
  - **Commands:** `show` gives the steps, `drill` runs a safe drill, `mirror` copies the code off GitHub.
- **GitHub-independence:** a nightly verified git bundle of every branch, in the backup and off-site folders, plus pushes to `MIRROR_REMOTES`. A monthly drill proves the code rebuilds without GitHub.
- **Password manager:** `./securax start passwords` runs Vaultwarden 1.37.4 for the Bitwarden apps; `./securax passwords lock` closes sign-ups. It is in every backup.
- **`./securax cloud login aws|gcp|azure`:** the official CLIs in pinned containers, with device-code sign-in; nothing to install.
- **`./securax names`:** professional `https://hub.securax.localhost` addresses in one guided step.
- **Life OS Inbox:**
  - **Capture and decide:** every note becomes an action with a next step and a date, or stays a note.
  - **Reviews:** any ritual (Red-Team Your Life included) runs step by step, and its findings become dated actions.
  - **Google Keep:** `./securax lifeos import keep` brings Keep notes in from Google Takeout.
- **SEO basics on the product site:** canonical address, structured data, `robots.txt` and `sitemap.xml`.
- **One list of features, written everywhere** (doc 65):
  - **Source:** `features.json` holds what SecuRAX can do, in plain words.
  - **Generated surfaces:** `tools/features_sync.py` writes it into the Command Center ("Everything SecuRAX can do"), the website's estate section, the docs home page, the README and `./securax features`.
  - **Facts:** counts on a page (tests, journeys, mapped frameworks) are now generated from the code.
  - **New fitness checks:** `features-current`, and `commands-in-help` (every command is in `./securax help`).
- **`./securax exercise` on its own opens the cyber range** (doc 79): it makes a practice exercise the first time, opens the portal in your browser and says which token to use. It is also a card in the Command Center.
- **The BFSI control matrix works with no file** (doc 66):
  - **Starter library:** built in, public, written in plain words: 67 controls plus the packs', 20 domains, 8 entity kinds.
  - **Your own workbook:** saved in Downloads, it replaces the starter by itself and stays private.
  - **Command Center:** has a BFSI controls card.
- **Build with open models** (doc 83):
  - **Strong chain:** DeepSeek V4 Pro, Kimi K3 and GLM 5.3 on the OpenCode Go key, ending at the local model.
  - **Router:** the `strong` tier, which was `claude`; `autobuild` builds hard work with the strong chain through the same gates.
  - **OpenCode:** `./securax opencode --strong`; it now loads BUILD-CONTRACT.md and LESSONS.md.
  - **Review:** `./securax review`, a second look from the strong chain that refuses vault/ and .env.
  - **`ai share`:** counts work done with the open models.
- **`./securax privacy`:** names that must never appear in this public repository, stored as fingerprints only; the fitness check `private-names` enforces it.
- **`./securax rollback`: go back to a working version at any time** (doc 82):
  - **Known-good record:** every healthy `up` or `update` is recorded (commit, version, newest backup) and pinned in git; the newest 50 are kept.
  - **Safe switch:** unsaved edits are stashed, data is backed up, the version left is pinned, and a version that does not start sends you back automatically.
  - **Options:** `--list`, a number, commit or tag, `--with-data`, `--latest`, `--status`, `--check`; plus `./securax ready`.
  - **Proof:** unit tests, the `rollback_anytime` sandbox journey and a weekly `rollback-check` routine.
- **Exercise range: learning with MITRE ATT&CK, D3FEND and ATLAS** (doc 81):
  - **Tagging:** tasks, red-team attack reports and blue-team incident reports carry framework identifiers. Each is checked against a catalogue built from MITRE's own data and linked to MITRE's page.
  - **Coverage screen:** for each tactic, what was met, detected and defended. The after-action report carries the same table.
  - **Learning paths:** six of them, with practice pointers and the certifications whose published syllabus covers each skill area. No exam content.
  - **Players:** personal tokens, XP only from judged work, levels and badges.
  - **AI-defence task:** a new task tagged with ATLAS.
  - **Market comparison:** how the range compares with commercial ranges and training platforms.
- **Exercise range: rules of engagement, checked every round** (doc 79):
  - **Ping:** every machine gets the HOST check, so blocking ping scores as down.
  - **Green-team account:** it must keep logging in by key with admin rights. A breach costs −5 per host per round until fixed.
  - **Rules screen:** shows the rules and the live rule checks.
- **Exercise range: a timed team plan** with owner, window, done/blocked/overdue state and check-ins.
- **`./securax storage --auto`** and a 6-hourly `storage-guard` routine (doc 80):
  - **Cleans:** folds old exercise data into totals, removes unused old versions of images SecuRAX built, and runs the safe clean-ups when space is tight.
  - **Alerts:** your phone, only when the disk is still short afterwards.
  - **Never touches:** volumes, backups or third-party images.
- **Doc 80:** the storage plan:
  - what bounds every source of growth
  - hot/warm/cold tiers, with SeaweedFS as object storage that scales out
  - indicative cold-tier prices
  - dated next steps
- **AGENTS.md §6:** a standing rule for handling the owner's documents (private, diagnose first, 80/20, nothing broken, growth bounded, recorded).
- **`./securax exercise`: a live-fire cyber defence exercise range** (doc 79), stage 1:
  - **Scenarios:** one JSON scenario serves any team number, and a broken scenario is refused.
  - **Scoring:** a scoring bot checks every service from inside each zone, and simulated staff log in with the passwords the blue team documented.
  - **Red-team bot:** it punishes unchanged default passwords, but only in the attack phase.
  - **The portal** (blue, white and red roles):
    - mission board
    - incident and six-part situation reports
    - judging, which sees the red team's claims
    - scoring log and timeline
    - target checks and per-zone awareness
    - news injects
    - password changes and restores
  - **Score log:** hash-chained, so edits are caught.
  - **Lite range:** isolated Docker networks with one jump-box door on 127.0.0.1:2222.
  - **Verified:** in real Docker and a real browser.
- **`./securax respond`: a crisis response kit** for your estate or another organisation (doc 78):
  - **Permission first:** who authorised the work, and the scope.
  - **The USB kit:** Windows and Unix collectors that follow the order of volatility, write only to the USB and hash everything; a read-me card; a custody form.
  - **Intake:** checks every hash, records the hand-over and stores the evidence read-only.
  - **Chain of custody:** hash-chained, and `verify` catches any edit.
  - **Advisory IOCs:** imported privately with their TLP, reading ranges, defanged domains and wrapped hashes.
  - **Triage, report and requests:** leads from the IOCs and common signs of compromise; a TLP-marked report; and an information-request list fitted to the kind of incident.
- **Docs:**
  - **Doc 78** gives dated targets for every "later" item, the cloud GPU tier with prices, and where a Raspberry Pi helps.
- **FIRST EPSS** (doc 77):
  - **The snapshot:** `./securax offline sync epss` keeps the daily chance that each CVE is exploited in the next 30 days.
  - **In the findings register:** a CVE at 50% or more is at least high, and the EPSS score is shown and kept current.
- **OWASP Agentic Skills Top 10 in `./securax vet`** (docs 31 and 77):
  - **Tags:** every finding is tagged with its AST risk.
  - **New checks:** remote instructions (AST05), unrestricted tool grants (AST03), and read-only claims the code contradicts (AST04).
  - **The mapping:** `./securax vet ast10` shows how all ten are covered.
- **`./securax findings`** (doc 76, after DefectDojo): one register for scan, SARIF and VAPT-workbook findings.
  - **One record per problem:** duplicates are merged.
  - **Fix-by dates:** critical 7 days, high 30, medium 90, low 180. A known-exploited CVE counts as critical.
  - **Re-scans:** they close what is gone and reopen what came back.
  - **Risk acceptance:** time-boxed, at most a year.
  - **Where it shows:** `./securax scan` fills it, and a cockpit reading turns red when something is overdue, which the phone alert sees.
- **`./securax repairs`** (doc 76, after Home Assistant): every red or amber reading, overdue finding, ending acceptance, overdue risk treatment and routine to fix, in one list, each with its command. The Command Center shows the count.
- **`bash install.sh --restore BACKUP`** (doc 76): a new machine is installed and restored in one step. The backup is checked first.
- **Life OS** (doc 76, after Loop):
  - **Home-screen shortcuts:** Move, Mind, Family and Note. They tick, never untick.
  - **Export for Excel (CSV):** one row per day.
- **Fixed:** `./securax backup` did not include `vault/` (controls, risks, findings, setup marks), so a restored machine started blank. Backups now carry it. A restore keeps the vault already there aside, never overwriting it.
- **The Life OS has a new look** (doc 73):
  - **The header:** one quiet line with a ⋯ menu.
  - **Today:** opens with a greeting and a progress ring. The daily three are big keyboard-reachable tiles.
  - **Text and cards:** 15 px body text, softer cards, and gold only for the main action. Contrast passes AA in both themes.
- **Report a problem** (Life OS, ⋯ menu): the details a helper needs, with nothing personal in them. You copy them, and a link opens the prefilled bug form. The repository comes from `brand.env` through `build.json`.
- **`./securax support-packet`** (doc 75): a Mattermost-style zip in `vault/support/`. It holds the versions, health, containers and routine runs, the setting names but no values, and the recent log. E-mails, keys, long numbers and home paths are scrubbed out.
- **Installers** (doc 75):
  - `install.sh` for Linux, macOS and WSL: rolling, `--stable`, `--version`, and `--offline` with a checksum check.
  - `install.ps1` for Windows: it checks WSL and Ubuntu, then runs `install.sh` inside.
  - Both never use sudo and never change an existing folder.
- **Release assets:** source `.tar.gz` and `.zip`, the rendered installers, `SHA256SUMS` and a signed build provenance, beside the SBOM.
  - **New action:** `actions/attest-build-provenance`, GitHub's own. It lets anyone verify where a download came from.
- **`./securax routines prune`** (doc 20): every routine has to earn its place.
  - **The record:** each run is kept locally with whether it found anything.
  - **The findings:** failing routines, reports that flagged nothing in 4 weeks, duplicates, and routines that never ran. Each comes with the command to act.
  - **Never pruned:** guards (backups, updates, alerts), because silence is their success.
  - **Switching off:** `./securax routines off ID` and `on ID` keep the choice on this machine. The cockpit lights a lamp when there is something to decide.
- **Fixed:** `./securax routines` dropped every argument after the first.
- **Pattern interrupt in the Life OS** (doc 74):
  - **The trigger:** 3 heavy-week signs in 7 days, counted on the device. The signs are your own words in notes or questions to the AI, and low-energy days.
  - **What Today shows:** one card with one question, one small action, a 3-hour rest block for your calendar, and a 7-day pause. It offers no plan.
  - **In recovery mode:** new goals and the quarterly check-in wait. The AI is told not to plan, and code replaces any answer that still offers a framework, KPI or checklist.
  - **Repeat questions:** the AI answer now says when you have asked the same thing before, with the dates.
- **Claude for the hard fifth only** (doc 23):
  - **`./securax route "task"`:** names the builder (local, OpenCode or Claude) and why. Its rules are data in `lifecycle/route.json`.
  - **autobuild asks it first:** a task routed to Claude gets its brief at once. A green diff that touches a sensitive part asks for a Claude review.
  - **`AGENTS.md` and `LESSONS.md`:** how the repo works, and what went wrong before. Every builder reads both, and Claude Code reads them through `CLAUDE.md`. autobuild adds a lesson when a red attempt turns green.
  - **`./securax ai share`:** Claude's share of the month's commits. The cockpit lamp lights above 20%; the baseline was 98%.
- **`./securax finish`** (doc 73): all 10 optional parts in one list, each with what it gives you, whether it is done, and the exact steps.
  - **Ticks:** items the estate can check tick themselves; the rest are ticked once with `./securax finish done ITEM`.
  - **Where it shows:** a "Finish setting up" banner on the Command Center and a card on the cockpit.
- **Product site, ready to publish on GitHub Pages:**
  - **Workflow:** builds the site and `/docs` and publishes them once `SITE_PAGES=true`.
  - **Domain:** comes from `brand.env` or a repository variable, so moving to another domain or host is one value.
  - **Page changes:** a phone menu with no script, a nav that never wraps, and a "Deploy your way" section.
- **Life OS on a phone:**
  - four fixed bottom tabs (Today, Goals, Ask, Ops) and More; no tab is hidden off-screen
  - Today shows the Daily Three and your one open action first, with the rest under "More today"
  - the vitals sit at the top of Today
  - the header shrinks to one line once you scroll
- **Life OS goals, the way national strategies run them** (docs 70 and 71):
  - **Key results "from X to Y by a date":** type today's number and the score, progress bar and days left fill themselves. Free-text key results still work with the slider.
  - **No drift:** a goal with no movement for 6 weeks asks for a decision: recommit, re-scope or drop. A drop keeps its lesson on record under "Dropped on purpose".
  - **Strengths first:** name your 3 strengths before the first objective, and each objective says which one it builds on.
- **"Who touched my data"** (Ops): every time Life OS data leaves a device or comes back (a sync, a backup, a restore, an export, a question to AI), one line records when, which device, what and where. Every device's log is shown, and repeats within the hour are not logged again.
- **Host the Life OS off the laptop** (doc 72): steps for Cloudflare Pages behind Cloudflare Access, about 15 minutes once. Free-plan limits checked 19 Oct 2026.
- **Sync without the laptop** (doc 72): the Life OS syncs each device directly with your OneDrive, end-to-end encrypted.
  - **No server:** the laptop and Docker no longer need to be on.
  - **Encryption:** AES-256-GCM, with the key derived from your passphrase through PBKDF2 (310,000 rounds).
  - **Conflicts:** writes are checked against the file's ETag, and simultaneous edits on two devices are both kept.
- **Daily encrypted Life OS backup to OneDrive,** with one-click restore of the newest copy.
- **Estate off-site backup and quarterly restore drill:**
  - `./securax backup offsite` picks a OneDrive folder once; every encrypted backup is then copied there, verified byte for byte, and the newest 12 kept.
  - `./securax backup drill` decrypts, unpacks and checks the newest copy, and runs automatically every quarter.
- **Which tier gets the task** (doc 23): a one-table rule for sending work to a local or cheap model, OpenCode, or Claude with a brief, so Claude handles about a fifth of the work. Prices checked 19 Oct 2026.
- **Control navigator you can read without the workbook:**
  - **Grid:** every box shows its full control ID, and clicking it opens a panel that says, in plain words, its status, what it asks, the evidence expected, how to test and fix it, and every citation.
  - **Maturity chart:** explained in one sentence, with a table beside it.
  - **Risk heat map:** fills itself. SecuRAX estimates each control's likelihood from its evidence and its impact from its tier, your own workbook scores replace the estimate, and open risks from your register are plotted too.
- **UK NCSC Cyber Assessment Framework 4.0 map** (`./securax comply caf`, doc 71): all 41 contributing outcomes scored against what SecuRAX proves, with CI-verified evidence. 15 are supported, 18 partial, 2 gaps and 6 belong to the organisation.
- **Tamper-evident gateway audit** (CAF C1.b, Estonia's signed and logged exchange): every audit event carries the hash of the one before it. `./securax audit verify` names an edited, deleted, inserted or reordered event.
- **What 26 national strategies agree on** (doc 71): eight patterns that several governments arrived at independently, what SecuRAX does for each, and eight ranked next steps.
- **README that keeps itself current:** the version badge, "What's new" and the full documentation index are generated from `VERSION`, `CHANGELOG.md` and the docs (`tools/readme_sync.py`). The `readme-current` fitness check fails CI when the README falls behind. "Start here" now leads with `./securax go`.
- **RBI MRM draft, checked paragraph by paragraph:** the pack cites the draft's paragraphs and gains ET-104 to ET-106 (third-party models, change management, continuity).
  - **Para 21:** `./securax ai inventory` flags models the gateway serves that are not in the inventory.
  - **Para 42:** it flags models changed since validation.
  - **Para 22:** it flags a missing intended use or owner.
- **RBI Payments Vision 2028 pack:** Cyber KRI framework (3.9), governed AI access to payments data (3.11), switch on/off for every digital mode (3.1) and beneficiary-side mule detection (3.5).
- **Lessons from national strategies** (doc 70): six patterns from Saudi Vision 2030, Vision India@2047 and the 2025 US National Security Strategy, what SecuRAX already does, the three proposed Life OS changes, and which documents to add next.
- **Human-in-command for AI** (doc 69, following RBI's June 2026 draft model-risk guidance):
  - **Kill switch:** `./securax ai stop all|MODEL --reason "..."` and `resume`. The gateway refuses on the next request with no restart, tells the caller who stopped it and why, and lights a cockpit lamp. The switch is a read-only file, not an API, and a malformed file stops all AI.
  - **Model inventory:** `./securax ai inventory` checks owner, third-party source, explainability, validation and yearly re-validation for high-risk models, and keeps decommissioned models' records for 10 years.
  - **Disclosure:** every answer carries `X-AI-Generated: true`.
  - **Control library:** the pack `rbi-mrm-draft-2026` adds controls ET-101 to ET-103.
- **AI allowance per caller** (doc 69, on by default): 2M tokens a day and 20M a month on cloud models, about US$15 a month on a Flash-class model.
  - **Limits:** a warning at 80%; at 100% the gateway refuses with 429 and says which limit, when it resets, and how to extend it.
  - **`./securax ai budget`** shows each caller's use. `./securax ai budget extend --day|--month --tokens N --reason "..."` adds tokens for the current day or month only, and every extension is logged.
  - **Local model:** not counted, so it still answers when the cloud allowance runs out.
  - **Visibility:** remaining allowance in the response headers, a cockpit lamp, and spend that survives a gateway restart.

### Fixed
- **The TLS CA key was in no backup.** Backups now carry it, and `restore` brings it back.
- **Backups ran weekly.** They now run nightly (`daily-backup`), so a lost laptop costs at most a day.
- **`update` blamed "local changes" when GitHub was unreachable.** It now says so and points to the GitHub-down steps.
- **No decorative emoji in the Command Center or the Life OS tab bar:** line icons and plain words instead.
- **A confidential agency's name is gone from the repository.** The CII pack, doc 67 and every mention use neutral wording, and the importer maps a workbook's column title to the neutral name. Old commits still contain it (doc 65).
- **Hand-kept counts that had drifted:**
  - **Website:** "736 tests, 41 journeys"; now generated.
  - **Docs 28, 54, 68 and the explainer:** their counts are generated too.
  - **Doc 79:** "30 checks in the sample"; it now gives no fixed count.
- **The help text** now lists every command (it missed `exercise`, `respond`, `findings`, `repairs`, `ai`, `ready` and others), and separates the AD lab (`range`) from the cyber range (`exercise`).
- **Doc 15** pointed IDE agents at LiteLLM directly (port 4000), around the gateway's guardrails; it now points at the gateway.
- **The local model's context window:** OpenCode assumed 32K. Ollama's context length is now set (16K by default), and OpenCode reads the same number.
- **Trivy:** the range gamebox image now has a health check; its by-design root user is an accepted finding scoped to that one file (`.trivyignore.yaml`, read through `trivy.yaml`).
- **`./securax restore` no longer leaves a secrets file that git would pick up.** It keeps the previous `.env` as `local/compose/.env.pre-restore`, which is now git-ignored. Before, the checkout stayed dirty, so `update` could not roll back safely, and the file could have been committed.
- **Sandbox:** the CCSP and RBI-map tamper journeys put back the files they edit, so later journeys no longer start from a dirty checkout.
- **`./securax controls import FILE.xlsx` crashed with a traceback** when typed as shown in the cockpit hint.
  - **Import:** no path, a wrong path, a folder or the wrong workbook now finds the right workbook.
  - **`./securax go`:** imports a workbook saved in Downloads by itself.
  - **Risk import:** follows the same rule.
- **Backup hints** now point to the guided `./securax protect` instead of "make a key, then edit .env".
- **Phone-sync step on the Command Center:** it no longer asks you to copy a token out of `.env`.
- **Cockpit crashed when the gateway reported allowance callers:** a loop variable shadowed the page's configuration. Caught by the `cockpit_page` journey on a real estate, now covered by a regression test.

## [0.2.0] - 2026-10-17
### Added
- **CI at agent scale** (doc 68):
  - **Pull requests** run only the end-to-end journeys that guard what they touch, picked by the impact map (`impact.py --journeys`). A docs-only PR runs none, a Life OS change runs 4, and the sandbox, the map, the workflow or an unmapped file run all.
  - **Main and nightly (02:00 IST)** run all 40 journeys, so anything narrowed away is caught within one merge.
  - **Superseded runs:** a newer push cancels the older run of the same PR.
- **Nightly safe update:** a new routine (3:15 am) runs `./securax update --auto`. It does something only when main has new commits, the checkout is on main and there are no local edits. It backs up, updates, health-checks and rolls back by itself if needed, never opens a browser, and tells your phone the outcome. Nothing new means no restart.

### Fixed
- **"v0.1.0 never updates":** the Life OS badge, the Command Center, `/version` and `./securax version` now show the build, e.g. `v0.1.0+74 · 21006c7`. It is written by every `./securax up` from git (`governance/buildinfo.py`), so each push is visible without bumping anything by hand. The release number still changes only when a release is cut.
  - **Offline cache:** the Life OS service worker is registered per build and names its cache after it. The hand-bumped cache version (`v14.11.0`, last changed long ago) is gone, so a new build replaces the old cache and reloads once by itself.
  - **`doctor`** warns when the running estate is an older build than the code on disk.
  - **Test:** two commits in a scratch repository must change the label without touching `VERSION`. The old check only proved that the badge matched `VERSION`.
- **A busy port 80/443 no longer leaves you with nothing running** (seen on Windows: `ports are not available: exposing port TCP 0.0.0.0:80`):
  - `./securax tls on` checks the ports first, changes nothing when another program holds them, and says how to find it.
  - `up` and `go` switch back to `http://localhost:8088` by themselves when the HTTPS edge cannot get its ports.
  - Any other busy port is named with the one fix, instead of the misleading "the model router rejected its config" and its log.
- **Risk registers with a one-row header lost their first risk:** a one-row header now wins over a two-row reading when both match equally.

### Added
- **No paths to type:** `./securax controls import` and `./securax risks import` with no file find the workbooks in Downloads, Documents and Desktop (the Windows ones too, on WSL), list them and ask once.
- **Risk register, interlinked** (doc 67): `./securax risks import | list | overdue | cii`.
  - **Import:** reads V/T/R registers (risk-wise, asset-wise, observations) and risk assessment + treatment plan workbooks by column name (two-row headers included). Treatment-plan rows are joined to their risks by reference.
  - **Private:** the register stays in `vault/risks/`.
  - **Links:** each risk is linked to the library controls that treat it. The navigator's heat map plots open risks when controls are unscored, and the vital few rank controls by your highest open risk.
  - **Overdue treatments** light a lamp in the navigator and, only when there are any, in the cockpit.
  - **`cii`:** the four the national CII agency impact tests, recorded as a self-check.
- **NSCS Audit Baseline pack:** all 68 markers (csm/pro/det/res/rec/imp) are linked to library controls, with the three risk profiles recorded. `pro.19` becomes control AS-101 (change control).
- **national CII pack:** the evaluation framework's five phases and the identification guidelines are linked to library controls. Both packs carry references only, never the documents' text.
- **Professional names with phones:** the HTTPS edge gets two loopback-only device ports (9443 app with same-origin `/v1`, `/sync`; 9444 Chat) for `tailscale serve`. `go` and `phones` use them, so `https://hub.securax.localhost` on the laptop and the ts.net names on phones work at the same time; `go` no longer asks you to switch the edge off.
- **BFSI control library and navigator** (doc 66), `./securax controls import | profile | dominance | navigator | gaps`:
  - **Import:** the gap-assessment workbook (202 controls, 20 domains, 22 regulated-entity classes, RBI/SEBI/IRDAI/IFSCA/NPCI/CII/CERT-In/DPDP citations) is read with a standard-library .xlsx reader into a private `vault/controls/library.json`. Your yellow-cell scores come with it; author metadata is never read.
  - **Ceiling profile:** the strictest requirement per control across every class, so meeting it meets them all. `dominance` shows that SCB/PSB alone misses AUD-002/AUD-006 for NBFC-UL, AIFI, IFSC IBU, MII and brokers, and AUD-003 for insurers.
  - **Packs** in `governance/controls/packs/` add new regulations or citations without code.
  - **SecuRAX map:** `governance/controls/securax-map.json` covers 53 controls, each proven or partly proven with real evidence files (CI checks they exist).
  - **Navigator** (one page per profile): master-caution lamps, the vital few, a MITRE-style 20 × 202 grid, a domain radar, a 5 × 5 heat map, regulator coverage bars and the SCB/PSB exceptions. No script, no external request.
- **Dark cockpit:** only abnormal vital signs are lit. A master-caution panel shows warnings, cautions, the nominal count and a Controls lamp; nominal and not-measured readings are folded away, and the planning views sit in one "Mission planning" section.
- **Configuration, not code** (doc 65): nothing brand- or vendor-specific is hardwired any more.
  - **`brand.env`** holds the brand name, product name, domain, contact address, repository and image registry; an environment variable with the same name wins. Every value is optional.
  - **`integrations.txt`** switches the optional parts on or off, one per line, like `requirements.txt` (tailscale, ntfy, webhook, cron, regwatch, backup, cloudflare-pages, github, tls). `./securax go` and `doctor` only act on what it lists; no file means everything is on.
  - The product site uses `{{SITE_DOMAIN}}`, `{{CONTACT_EMAIL}}` and `{{BRAND_NAME}}`, filled by `website/build.sh`. `mkdocs.yml`, `tools/publish-clean.sh` and the regulator watch read the same values.
  - `./securax config show | check | enabled | render`. A new **`config-clean`** fitness check fails CI when a brand value or a registrar/host vendor appears in code, or when either file is malformed.
### Added
- **`./securax go`: one command that gets everything working and keeps it working.** It updates safely or starts, installs the schedules, publishes to your phones over Tailscale, starts the regulator watch, takes a first backup, opens the app with sync set up, and can send the one-tap phone link through your ntfy alerts. Every step checks first and only acts when something is missing. It ends with one status screen: ✔ for what works, and one ✗ line with the single fix for what does not. `START-HERE-Windows.bat` now runs it, and it heads `./securax help`.
- **Resilience fundamentals in the gateway and alerts** (doc 63, a 35-concept audit):
  - **p95 / p99 latency:** a Prometheus histogram and `GET /v1/latency` (p50/p95/p99 of the last 1,000 calls), instead of an average only.
  - **Connection pooling:** one keep-alive HTTP client instead of a new connection per model call.
  - **Backpressure:** at most `MAX_INFLIGHT` (8) model calls at once; past `QUEUE_WAIT_S` (20 s) a fast 503 with `Retry-After`, counted as `shed_overload`.
  - **Circuit breaker** per detector: after 3 failures it is skipped for 30 s, then one trial. Verdicts are unchanged; only the waiting is gone.
  - `Retry-After` on 429. Phone alerts retry with exponential backoff and jitter, and a failed alert goes to a dead-letter file and is re-sent first next time.
- **Practices from the best engineering organisations** (doc 64: one success mantra per organisation, the 80/20 seven, each with its proof):
  - **Idempotency keys** (Stripe): send `Idempotency-Key` on `/v1/chat/completions`; a retry gets the first answer, never a second model or tool call. Same key with a different body is a 422; same key while the first call runs is a 409.
  - **SLOs and error budgets** (Google SRE): `GET /v1/slo`, availability 99 % (only our own failures count) and latency 95 % under 30 s, each with the budget left.
  - **Blameless postmortems** (Amazon Correction of Error): `./securax postmortem new "title"` writes a five-whys template to `vault/postmortems/`; `actions` lists the open fix-it actions and fails when one is overdue or has no owner.
### Changed
- The app no longer asks anything when a sync link matches the setup it already has (so `go` can open it on every run).
### Fixed
- **Command Center over Tailscale:** opened at `https://<laptop>.<tailnet>.ts.net`, its cards linked to `https://chat.securax.localhost/` and similar names that only exist on the laptop. They now use the Tailscale name (Chat on `:10000`), hide Private Docs and Automation (not published over Tailscale), and read the gateway status from the same address (`/version` added to the app's proxy).
- **`./securax sync-link` prints a laptop link and a phone link** (the Tailscale name, found automatically). Both use the app's own address for sync (`/sync`), so one tap per device restores your data after any update, new browser or new phone, with no forms. Previously the link pointed at port 8089, which phones cannot reach.
### Added
- **Laptop runbook** (`docs/get-started/laptop-runbook.md`): one page for one-time setup, the daily commands, sync, which address to use where (and the NordVPN caveat), what Chat keeps across updates, the website on cyberbaba.org, the build loop, and the business steps.
### Security
- **`./securax up` now replaces an empty or placeholder sync token** (`change-me…` from older `.env` templates) with a strong random one. A known placeholder would have let anyone who can reach the sync service read and write your data; before, it also blocked setting up cross-device sync.
### Added
- **Time to first block, measured on every build:** new fitness checks `time-to-first-block` (a cold gateway refusing its first prompt attack: 0.68 s locally, budget 5 s) and `block-latency-p95` (60 blocked attacks: p50 3.8 ms, p95 6.5 ms, budget 50 ms). The number is on the Shield page.
- **Agent and tool-call guard** (OWASP LLM06 / ASI02): when a model returns `tool_calls`, the gateway checks each tool and its arguments before the agent runs it.
  - Built-in policy: shell, exec, eval and delete tools are denied; transfer, payment, refund and e-mail tools need a human approval; `TOOL_POLICY_FILE` (JSON with `allow`, `deny`, `require_approval` glob lists) overrides it, and a broken file fails closed.
  - Destructive arguments (`rm -rf`, `DROP TABLE`, pipe-to-shell, fork bombs) and secrets or canaries in arguments are blocking; personal data in arguments is redacted.
  - In enforce mode a blocked call is withheld with `finish_reason: content_filter` and the rule names; counted as `blocked_tool_call`. 14 new tests.
- **Regulator watch** (`./securax regwatch fetch|list|digest|sources`): RBI notifications and press releases and SEBI circulars from their official RSS feeds, filtered (market operations and recovery proceedings out), de-duplicated into `vault/regwatch.json`.
  - The first fetch is a silent baseline; later fetches push only new titles to your phone. The monthly digest is Markdown with titles, dates and links only, and links CERT-In for a manual check because it publishes no feed.
  - Links that do not point to the regulator's own site are dropped; DTD and entity declarations are refused. Daily and monthly routines added. 7 tests.
### Fixed
- **A real detection gap the new probe found:** "SYSTEM OVERRIDE: forget prior guidance…" was not blocked, because "guidance" was missing from the override rule (PI-001). The rule now also covers directions, constraints, safeguards and policies. Regression and benign tests were added; the red-team scorecard stays at 100 % defence with 0 false positives.
- **Free AI-risk check** (`website/assess/`), the site's front door:
  - Ten questions mapped to RBI, SEBI CSCRF, DPDP, CERT-In, NIST AI 600-1 and OWASP, with an instant score and the gaps, each showing Shield's real status light.
  - It runs only in the browser and sends nothing anywhere. It is linked from the Shield banner, hero and nav.
- **Doc 62, strategy:**
  - Cyera's model: wedge to platform, speed-to-value proof, education and free assessments as distribution.
  - The 2025 consolidation of standalone prompt firewalls into platforms, and the patterns shared by the unicorns.
  - The category for SecuRAX to own: the **sovereign, regulator-native, proof-native AI firewall**, with its build order.
- **Shield page:** the eyebrow now reads "The sovereign AI firewall", the closing reads "Use any AI. Prove you stayed in control."
- **SecuRAX Shield** is the home page (`website/index.html`): *"Let your people use AI. Keep your data out of it."*, the AI firewall for regulated companies.
  - Real blocked and redacted examples in the hero, a "one control point" flow diagram, and capabilities with honest lights (the admin console and GDPR maps are 🔴).
  - The audiences are NBFCs, brokers, AMCs, fintechs and DPDP firms. The offer is a five-place design-partner programme.
  - The consumer page moved to `/personal/` (SecuRAX Personal).
- **Low-profile publishing:** `tools/publish-clean.sh <org>` makes a fresh, history-free copy under a brand organisation, rewrites links and code owners, leaves itself out, and refuses to publish while personal identifiers remain. The sweep removed a personal e-mail from a Terraform example, owner tags, a sample user name and the laptop name.
- **Doc 61:** run SecuRAX as a business. It covers identity layers, conflicts to avoid, the entity choice (OPC/LLP), GST and LUT, Razorpay for India, a merchant of record for global sales, and the first 90 days.
- **Product site for cyberbaba.org** (`website/`), written for anyone with something worth protecting:
  - The promise: *"Your private superintelligence"*, for the 1% who own their AI, with the 1% club hook (1.01^365 ≈ 37.8).
  - Who it is for, person-agnostic: individuals and families, founders, creators and public figures, professionals, organisations, governments. Then three pillars (Private, Guarded, Provable).
  - A **real guardrail demo**: the actual output of SecuRAX's rails blocking a prompt injection (OWASP LLM01, MITRE ATLAS) and redacting PAN, card and mobile.
  - A product tour with real screenshots (Today on a phone, the Money Map, the status-light roadmap), three-step setup, who it is for, proof numbers, compliance stated as "mapped, not certified", Community / Professional / Enterprise pricing, and an executive FAQ.
  - Static and responsive (no horizontal scroll at 390 px), WebP screenshots of 58–77 KB, and security headers in `website/_headers`.
  - `website/build.sh` builds the site with the docs at `/docs/` for Cloudflare Pages.
- **Doc 60:** how to go live on cyberbaba.org with Cloudflare Pages (custom domain, Full (strict) TLS, free Email Routing for hello@), and how to move all development to the SecuRAX build agent (`autobuild` / `opencode` with free models, the same gates, main protected by CI), with the next builds queued as ready tasks.
### Fixed
- The docs footer said Apache-2.0; the licence is **MIT**.
- **Status lights on every documentation page** (🟢 built and proven · 🟡 partly built or not yet proven · 🔴 not built yet):
  - One source of truth, `docs/status.yml`; `docs/sync_status.py` writes each light into a banner under the page title, so it shows on GitHub and on the docs site.
  - A test fails if a page and the file disagree, or if a site page has no light. The legend is on the docs home page.
- **Doc 59, the end state and the build order:**
  - The two enterprise reference-architecture diagrams as the destination.
  - Every box rated with a light, the SecuRAX component that does the job, and the next step.
  - A totals table that is checked by CI, and a six-level wiring order from easy (use what is built) to hard (a second machine, then a product).
  - Linked from the home page, docs 00, 02 and 17, and the README.
- **Documentation site** (MkDocs Material, Microsoft-Learn-style):
  - Home, Get started (new **Quickstart**), How-to guides, Apps, Concepts, Security and compliance, Reference (a **command reference generated from `./securax help`** on every build, plus the changelog) and a new **Troubleshooting** page built from real installs.
  - Light and dark themes, search, and a copy button on every code block.
  - The `docs` workflow builds strictly on every PR. It publishes to GitHub Pages from `main` once Pages is enabled and the repository variable `DOCS_PAGES=true` is set.
### Changed
- **No more pasting during setup** (friction seen on a real install: pasted fences left the shell waiting, a `sudo` prompt swallowed the next pasted lines, a cron line pointed at an old folder, a phone subscribed to a mistyped topic):
  - `./securax notify setup [--new]`: random topic saved, shown, tested.
  - `./securax routines install`: exactly one schedule line for this folder, stale ones removed, cron started (enabled at boot with systemd).
  - `./securax phones [--apply]`: checks the HTTPS edge, the app port and Tailscale, then prints the steps with your own `*.ts.net` address (or runs the two `serve` commands).
  - `doctor` now reports Docker reachability first (with the WSL-integration fix), and adds `phone alerts` and `schedule` lines.
  - `why` names the WSL-integration fix too.
- **Phones over Tailscale on one address** (doc 58): the app's web server forwards the AI gateway (`/v1`, `/healthz`) and sync (`/sync`, WebSocket included), so Ask and sync work on phones from `https://<laptop>.<tailnet>.ts.net` with no cross-origin permission and nothing else published; on a `*.ts.net` address the app defaults Ask and the sync URL to that address and Chat links to port 10000 (PWA cache v14.10.0).
- **Strong router key**: `./securax up` replaces the shipped placeholder `LITELLM_MASTER_KEY` (`sk-range-change-me`) once with a random 48-hex key.
- **No false "wrong provider" warning** for providers that reuse another's key (`openrouter_pro`, `groq_qwen` carry the same `key_prefix`; providers reading the same key variable count as one, so a real mix-up such as an OpenRouter key under ElevenLabs is still caught).
- **Consent fields** (`…_OK`, e.g. `OPENROUTER_PRO_OK`) now ask you to type `yes`, visibly, instead of "paste".
- **Ask panel (Guiding Map)**: advisor chips are styled and show which one is selected; switching advisor no longer wipes a half-typed question; answers render as readable Markdown (bold, lists, headings, code), HTML-escaped first so model output cannot inject markup, with "Answered as: <advisor>" above the answer (test21; PWA cache v14.9.0).
- **Cockpit, oldest running software**: names the image. The age is the vendor's build date of the pinned version, so `update` cannot lower it until a release raises that pin; stop an unused organ instead (n8n 1.74.1 today: `./securax stop flows`).
- Image pins refreshed: Ollama 0.5.7 → 0.40.4, Open WebUI 0.5.20 → 0.12.2 (both were the oldest running images, Jan/Mar 2025, which the cockpit flagged as red). Open WebUI's 0.12.x breaking items (Valkey, MinerU, SCIM) do not apply: the estate uses LanceDB and none of those features. n8n (1.74.1) is deliberately NOT changed here: 2.x is a major upgrade that needs a planned migration.
### Added
- **Compute strategy** (doc 57): Ollama keeps the conversation cache in 8-bit (`OLLAMA_KV_CACHE_TYPE=q8_0` + flash attention; about half the context memory; `f16` switches back); **`e2e-in`**, an opt-in Indian cloud rung (E2E Networks TIR, OpenAI-compatible, INR) in no chain and treated as zone `global` until the owner confirms its region and maps it; ranked guidance on home machines, notebooks (Kaggle/Colab for Green-tier batch jobs only), pay-per-use GPUs, Indian clouds and why IndiaAI subsidies and crowd-sourced GPUs do not fit.
- **`home` rung: lend the estate a stronger machine you own** (doc 56): `REMOTE_OLLAMA_BASE` + `HOME_MODEL` (was a recipe that meant hand-editing the catalog); joins every chain just before this laptop's model; counts as local for residency, so it is enabled only for loopback, private-LAN, Tailscale or `*.ts.net` addresses (tested with public and look-alike addresses). The heavy-compute recipe no longer says `curl | sh` or `0.0.0.0`. Idea from RAMDeck; its model-splitting (llama.cpp RPC) is deliberately not built (doc 56).
- **Engineering standard** (doc 55): `governance/claims.json` lists every product claim with its envelope and proof (test or real-stack journey) plus what SecuRAX does NOT claim; fitness `claims-proven` fails if a proof goes missing.
- **Coding providers** (docs 23, 42, 54): build chain is now OpenCode Go → GLM → **Groq** (free; `openai/gpt-oss-120b` plus a second family `groq_qwen`, `qwen/qwen3.8-27b`, each on its own daily quota) → **NVIDIA NIM** (free; its terms allow development use, so build chain only, never Chat) → DeepSeek → Gemini → OpenRouter → local coder → local. **Cerebras** is an evaluation-only provider (trial credit, 5 requests/min) in NO chain: add it yourself with `./securax providers chain builder add cerebras [--before ID]` (kept in `.env` as `CHAIN_BUILDER`; Chat chains cannot be edited this way; local always stays last). The **local coder** is picked from catalog tiers by the memory Docker sees and stepped down when it would not fit beside the estate (qwen3-coder:30b / gpt-oss:20b / qwen2.5-coder:7b; a 16 GB laptop gets qwen2.5-coder:7b); `./securax pull coder` asks before the large download. **OpenCode** now gets the build chain only (no Chat chain), and `./securax opencode --check` says so. **Cockpit** has a "Coding providers" line (one model-list GET per enabled provider, cached 5 minutes, remaining quota when the provider sends it).  Gemini's free tier stays in Chat and build chains as a Green-tier rung (gateway redaction before any cloud call; `residency enable` keeps Red-tier local).
- **Technical gist** (doc 54): one file to hand another engineer or AI assistant (architecture, request path, ladders, CLI, gates, known gaps, how to ask for a change), with a verdict on the "free Claude Code" plan: routing Claude Code to non-Claude models is not supported by Anthropic and would bypass the gateway, so OpenCode stays the open agent; most of the rest already exists.
- **The Twin** (doc 53): Chat (Open WebUI 0.12.2) gets web search (DuckDuckGo, off per chat until clicked), memory, notes, folders as projects and the in-browser code runner, all from `.env` so they survive restarts; a `twin` model whose ladder starts with an opt-in PAID strong open model (`./securax providers add openrouter_pro`, GLM-5.2 by default, capped by the router budget) and then the free ladder; DeepSeek kept out of Chat. Hardening from the Open WebUI scaling/hardening guide: a fixed sign-in key created by `up` (before, every update signed you out and broke tool tokens), 7-day sessions, no external avatar fetching, Chat memory cap 1.5 GB so document search cannot kill it. Journey `open_webui_chat` proves you stay signed in after the container is recreated.
- **Automation pack and andon** (doc 52): `./securax notify` pushes to your phone through **ntfy** (`SECURAX_NOTIFY_NTFY`, optional token), `notify send` for any script, `digest --changed` (only when the picture changes, including back to green). Routines: `andon` (every 15 min, silent unless something changed), `weekly-backup`, `monthly-review`, `quarterly-checkin`. Doc 52 also has the SuperApp plan (Twin, brain options with dated prices, Jarvis voice, family Android app, fly rails). Fixed on the way: notify read its settings only from the process environment, so a webhook put in `.env` as documented was never used.
- **`./securax knowledge`** (doc 51): imports the official exports of Claude (chats and projects), ChatGPT, DeepSeek and Gemini (Takeout) into one markdown file per conversation plus a dated index, for Private Docs. Read in memory (never extracted), credentials and Aadhaar/card/PAN redacted with the gateway's rules, your own flag terms route a conversation to `flagged/` for review, re-runs skip what has not changed; daily routine `knowledge-inbox` imports whatever you drop into `vault/knowledge/inbox` (git-ignored). The export request itself stays manual on purpose (no API; a browser robot would hold four live sessions).
- **Reasoning budget** (doc 50): the gateway meters thinking tokens (`guardrail_tokens_total{kind="reasoning"}`); optional per-provider cap `<ID>_REASONING=<level>` (Gemini 3, Groq gpt-oss, Claude 5), applied only when the current model matches and the level is listed, off by default. A global switch was rejected: LiteLLM 1.105 maps a 'low' effort to thinking ON on Ollama/DeepSeek and to 'high' on Mistral. Verdict on Hybrid Reasoning Agents (arXiv 2610.18861): not adoptable on this estate yet (custom CUDA engine, no OpenAI-compatible server); one catalog line when it is.
- **Career compass** (doc 49, Guiding Map → Career): one screen for a job decision. Floor (today's real value: net + employer-paid rent and perks + retirement; plus your own cover), honest CTC and the +30% target, FI need (corpus, SIP, in-hand), each offer's in-hand under the FY 2026-27 new regime (salary or fee; 44ADA only when ticked), break-even CTC per offer structure, must-have gates (any ✗ rejects, any ? = not decidable) then weighted good-to-haves, worst cases against the emergency fund, the BFSI security ladder worked backwards with proof per rung, and a dated plan (notice period → month 30) that shows in Due now. Personal numbers only via the screen or your own career file; nothing personal ships.
- **Guiding Map freeze-ready** (doc 48): quarterly check-in in about 5 minutes of taps (grade last quarter, 8-area wheel, up to 3 goals suggested from the lowest scores); "Add the rhythm to my calendar" (.ics, 5 repeating events with reminders); the After-Action Review is a monthly ritual; Kids: add in place, this quarter's three actions and the education SIP; Ops reorganised (advanced tools folded). Fixed: Undo kept a 10-day-old snapshot that would have wiped days of entries (now 30 min, dismissable); pausing asks first; integrations claimed auto-fill (now honest copy-in boxes with Indian/Android sources); 439 WCAG contrast failures across both themes (now 0); runway read 274219.5 months when a lakh field was typed in rupees. New journey `guiding_map_full_use` audits every tab in a real browser.
- **Guiding Map Calm mode** (doc 47, default; "Show everything" restores the full app): Today is one screen (1,603 px, was 3,675; first tap at 220 px, was ~700) with tap check-in plus optional energy, the one open action, due-now lines, a week insight computed on the device and an optional review by your estate AI (ID numbers never sent), and "From your estate" lines. Setup is 4 questions written once into both data models, and example people and loans are removed after it. 5 tabs plus More. **`./securax lifefeed`** feeds it from the cockpit, the certification planner and backups.
- **`./securax certs`** (doc 46): certification path planner for OSCP+/OSWE/OSEP/OSED/OSAI, CPTS/COAE, CRTP/CRTE/CRTM, CRTO and BSCP, ordered by shared skills and dated and costed against your hours and yearly rupee budget (retake reserve, carry-over, OffSec per-course vs Learn Unlimited compared). Prices are a dated snapshot with sources.
- **`./securax autobench`** (doc 45): measures each build model inside the autobuild loop on ten hidden-graded tasks (cheating detected, 95% interval, plain vs contract prompt, asks before a large paid run; `selftest` proves the benchmark with no model). Found and fixed on the way: the forge mutation gate could leave stale bytecode of a mutant behind (regression test added). The e2e workflow now installs pytest.
- **Less friction**: `./securax why [service]` (what stopped and why, in plain words; Windows: double-click `WHATS-WRONG-Windows.bat`), `./securax shortcut` (type `securax <command>` from any folder; installed by the WSL setup; undo with `shortcut off`), `UPDATE-Windows.bat`. Found and fixed on the way: `why` would have exited silently on a fully healthy estate.
- **Admission gate + self-healing sandbox** (doc 44): `./securax forge gate` (fail-to-pass, mutation check on the changed lines, complexity budget) now runs inside `autobuild`; failures are fed back as a short typed brief, and infrastructure-only reds (Docker/network) are re-run instead of "repaired". The sandbox re-runs a journey once when every failure is infrastructure, and records it.
- **REA (Reverse Engineer Anything) in a sandbox** (doc 43): `./securax inspect` reads third-party software (npm package, tarball, folder, file) and says in plain words what it can do and what is worth a look; `--diff` and a weekly `--watch` (your crontab, or the `supply-chain-watch` workflow) catch **capability drift**: a new version that can do what the old one could not (new install script, network, program launching, hard-coded address, native code); `./securax opencode --rea` gives the agent REA over MCP. REA 6.5.0 is pinned by lockfile with integrity hashes and no install scripts, and runs only in a container with no network, a read-only disk, no privileges and the target mounted read-only (`--selftest` proves it). Static only: running the target is never offered. Proven with the real REA on real packages and by journey `inspect_sandbox`; the real OpenCode 1.19.0 connected to it over MCP.
- **OpenCode Go and the OpenCode terminal agent** (doc 42): `./securax providers add opencodego` turns on flat-rate open models (DeepSeek V4.1 Flash, GLM Flash; US/EU hosted, zero retention) as the first rungs of the **build** ladder only (never Chat), with the provider's required user agent and a per-install session id; the router generator now supports any OpenAI-compatible `api_base` and fixed headers per provider; `./securax opencode` starts the OpenCode terminal UI with every model call routed through the SecuRAX gateway (its other providers off, asks before edits/commands, no auto-update, no public sharing; verified with the real OpenCode 1.19.0); journey `provider_opencode_go`.
- **Simpler protection** (doc 41): `./securax crypto` is now a plain-English check (needs you now / already protected / can wait / outside SecuRAX; `--full` keeps the technical CBOM); `./securax protect` (Windows: double-click `PROTECT-BACKUPS-Windows.bat`) does everything to encrypt backups with one question; the Cockpit shows "Backups locked" and "Quantum-resistant connections"; `./securax start|stop docs|flows|all` is remembered, so `up` and `update` no longer silently drop the add-ons.
- **Quantum readiness** (doc 41): the HTTPS edge now offers a **hybrid post-quantum key exchange (X25519 + ML-KEM-768)** first, with classical fallback (edge and sidecars move to nginx 1.30 / OpenSSL 3.5; proven against the real edge); `./securax crypto` - a ranked cryptography inventory read from the estate (`--cbom` CycloneDX 1.6, `--strict` for cron/CI, `keygen` for a backup key file); **encrypted backups** (OpenPGP symmetric AES-256, key file kept off the machine or a typed passphrase; wrong key and tampered files refused; restore verified in the journey `backup_encrypted`); `./securax comply pqc` (17 items, entity obligations separate). `restore` also no longer leaves the unpacked backup (it contains your keys) in /tmp when it restarts the estate.
- **`./securax start docs|flows|all`** starts the optional Private Docs / Automation add-ons that lite mode skips (with their TLS sidecars when internal TLS is on) and waits until they answer by name.
- **Encryption in transit, phase 2** (doc 40): `./securax tls internal on|off` - a per-service TLS sidecar (own certificate from the private authority, service listens on loopback only) for gateway, LiteLLM, Ollama, Open WebUI, n8n and the sync service; the edge verifies every upstream; plain HTTP between containers is refused; real-stack journey `tls_internal`. Known exceptions (AnythingLLM, Sprout stage, n8n env assumption) are listed in doc 40.
- **Ops without chores** (doc 39): the sync service keeps a daily snapshot of each user's merged state (30 days; list/restore endpoints) and the Guiding Map shows "Backed up automatically" with a restore-a-day control instead of nagging for a manual export; `./securax sync-link` prints a one-tap setup link for a phone or second computer (token after `#`, destination shown before saving, existing setup never replaced without a second confirmation).
- **Encryption in transit, phase 1** (doc 40): `./securax tls on|trust|status|renew|off` - a private, name-constrained certificate authority and ONE HTTPS edge (TLS 1.2/1.3, forward-secret ciphers) on port 443 that routes by NAME - `https://hub.securax.localhost`, `chat.`, `docs.`, `flows.`, `sync.`, `api.` (no port numbers; `--domain` for your own domain with one wildcard DNS record, so an IP change touches one record) - in front of the Command Center, Chat, Private Docs, n8n, the sync service (incl. wss) and the gateway; the plain web ports are no longer published while it is on; hub/PWA links follow the page and domain; **the cockpit's maturity chart is now readable**: plain-English area names, a how-to-read guide, a posture summary, and a weakest-first table with each area's next step; cockpit indicator; RBI 118/21(9) and CSCRF PR.DS.S1-S3 updated honestly. **Fixed**: the gateway (8080) and Grafana (3000) were published on every network interface; they now follow `BIND_HOST` (default: this machine only). Internal container-to-container hops are not encrypted yet and are listed by `tls status`.
- **Live sync, team chat, people-scale ladder** (doc 39): `estate-sync` WebSocket push (`/sync/ws`, signal-only, first-message auth) with Guiding Map client and polling fallback; Mattermost as a dormant pinned organ (`./securax organ mattermost up`); `./securax notify` (webhook digest to any chat, https-only off-LAN, secret-safe); `./securax capacity --people N [--bench]` (1 → 100,000 tier ladder with an enforced honest-gaps list); OpenSSF Scorecard workflow and SLSA build-provenance for released images.
- **Cockpit, storage, safe update, impact** (docs 37, 38): `./securax cockpit` (one self-contained page: vital signs, Eisenhower, 80/20, NIST CSF maturity radar, AI-risk coverage, trends; no script/port; linked from the Command Center), `./securax storage` (sizes, growth forecast, safe tidy; `SECURAX_BACKUP_DIR`), `./securax update` now backs up, health-checks and **rolls back** a release that does not start, `./securax impact` + a fitness rule (blast-radius map), `./securax regulated on` (one switch), W3C trace context through the gateway, `comply mit-ai-risk|nist-ai-600-1`, grouped `./securax help`, Dependabot for compose-pinned images and Terraform, Guiding Map gateway-key field for sign-in estates.
- **Identity-aware gateway, incident clock, data residency** (doc 36): `./securax gateway-auth` (OIDC/JWT from any provider + hashed service keys, roles, MFA for privileged roles, lock-out, authenticated audit; no new dependency), `./securax incident` (one detection starts RBI/SEBI/CERT-In… clocks; regulators are data; hash-chained case log; drafts; quarterly roll-up), `./securax residency` (classification-aware routing to allowed zones, cloud-region allow-list + attestation; jurisdiction is a file). The AI-SOC raises `auth-bruteforce`. Detectors now see redacted text only.
- **Regulatory gap assessment** (doc 35): `./securax comply` maps the RBI NBFC Cybersecurity/Technology Directions 2026 and SEBI CSCRF requirement by requirement (supported / partial / gap / entity / n/a), with verifiable evidence, a prioritised backlog and category filter; ships in `./securax evidence`, `verify` and `fitness`. Found: no caller authentication on the gateway, no incident-reporting clock, no data-localisation guard.
- **CCSP-aligned coverage** (doc 34): `./securax ccsp` maps the estate to ISC2's six CCSP domains / 38 sub-topics with verifiable evidence (stale references and unproven 'covered' fail the gate); included in `./securax evidence`, `verify` and `fitness`. A practice map, not exam content.
- **Fitness functions + game days** (doc 33): `./securax fitness` (rails latency over adversarial inputs = ReDoS guard, memory, cold start, dependency count, plus ratchets: no new critical supply-chain findings, no undocumented commands) and `./securax gameday list|run|all` (node loss, control-plane restart and an etcd snapshot-RESTORE disaster drill on the burrow twin, each with an SLO; twin left as found). `burrow.twin_restore` rewinds the control plane to a snapshot. Journey `gameday`; wake-time budgets in `lifecycle_burrow`.
- **Offline power-ups** (doc 32): `./securax offline sync|status` + `./securax kev` (CISA KEV and MITRE ATT&CK snapshots, streamed and slimmed, work with no network; the AI-SOC names ATT&CK techniques and `scan` flags known-exploited CVEs from them) and `./securax bench` (measures your installed local models for RAM fit / accuracy / tokens-per-second and recommends one). Verified repo ledger: llama.cpp, BitNet, whisper.cpp, llamafile, Atomic Red Team, Sigma, osv-scanner, sqlite-vec. Journey `offline_power`.
- **Behavioural rules + `./securax diffcheck`** (docs 31): the four rules popularised by Karpathy's LLM-coding observations, in our own words, in `BUILD-CONTRACT.md`; `diffcheck` enforces the contract's mechanical hard rules on the diff and gates `autobuild` (journey `diffcheck_gate`). Adoption ledger for agent-skills, ECC (vet: BLOCK, ideas only), karpathy-skills, freellmapi, context-mode.
### Fixed
- **Cockpit files could be left mixed** when two refreshes overlapped (the background refresh after `up`, the andon, a manual run): a plain write truncates first, so a short write over a long one left the old tail ("Extra data", seen in the sandbox `cockpit_page` journey). The cockpit page, its JSON, its caches and the Guiding Map feed now write to a unique temp file and rename it into place; a contention test (3 writers, 2 readers) gets 0 broken reads where the old write got 2,266.
- **Sync could lose concurrent saves**: read → merge → write ran without a lock, so with a second worker or container 175 of 200 keys were lost in the new 8-writer test (today's single worker hid it); now one immediate write lock. **Sync merge depended on arrival order** on same-millisecond ties, and the phone kept its own value on a tie while the server kept the other, so two devices could disagree for ever; now one deterministic rule on both (larger value by Unicode code point). **A non-numeric timestamp crashed a save** (500); now a clear 400. Property tests (stdlib only) and `guiding-map/tests/test20.js` keep it that way.
- `./securax backup` no longer fails on a running estate when a service writes while its volume is copied (GNU tar exit 1 "file changed as we read it", seen with Open WebUI 0.12): the archive is verified and kept; real read errors still abort.
- **A fixed Command Center looked unchanged after an update**: the web server sent no cache headers, so browsers kept an old `hub.html` for hours; the pages now always revalidate (and the service worker no longer trusts the browser's cache). The Windows launcher, the first-run script and the quick-start still pointed at `http://localhost:8088`, which is not published once HTTPS is on; they now open the right address.
- **Command Center behind the HTTPS edge**: the Guiding Map and Cockpit cards still pointed at `:8088` (refused: that port is no longer published); status dots showed a stopped service as running (a cross-origin fetch cannot read a 502) - the edge now answers a same-origin `/_up/<name>` probe; a stopped optional service shows a plain-English page with the exact start command instead of a bare nginx 502. Proven by `guiding-map/tests/test16.js` and the `tls_edge` / `tls_internal` journeys (which now also start an optional service).
- **No more `curl | sh` in our own installers** (doc 31): helm, kind, kubectl, Tailscale and k3s are now version-pinned and SHA-256-checked before they run; the WSL quick-start saves the script before running it. `vet` also catches `curl … | VAR=x sh`. The fitness ratchet tightened from 9 to 6 accepted findings.
- The gateway's output rails raised on a malformed URL in a model reply (`http://[abc`); it is now treated as an untrusted host and removed. `vet` no longer crashes on files that break its scanner.
- **Supply-chain gate** (`./securax vet`, doc 31): pin + licence + executable-surface + guardrail-engine text scan of third-party agent skills/plugins/MCP servers; BLOCK can't be pinned; vendored copies must be byte-identical to upstream and are hash-verified (part of `./securax verify`); `escalate` attaches vetted skills only while they verify. First use: agent-skills (2 skills vendored). The purple loop gained a `skill-poisoning` attack (13 attacks). Sandbox journey `vet_gate`.
- **Purple-team loop** (`./securax purple`, doc 30): attacks through the real gateway → captured audit log → real AI-SOC → prevented / logged / alerted report with a detection backlog. Found and fixed: only 3/12 attacks alerted (new SOC rules `injection-probe`, `agentic-tool-coercion`, `output-exfil-channel`, `pii-harvesting`) and PII redaction audited as `allow` (now `sanitise`). CI gate in `devsecops.yml`; sandbox journey `purple_loop`.
- **Range** (`./securax range soil|plan|fetch|install|wake|hibernate|snapshot|reset|status|prune`): a dormant Active Directory practice lab for OSCP-style training, wrapped around GOAD pinned to a verified commit. Says which lab fits this machine (real RAM numbers, re-derived from upstream in CI), refuses cloud providers without explicit cost consent, same lifecycle verbs as the rest. Sandbox journey `lifecycle_range` (28 checks). Never run against a hypervisor here.
- **Burrow (stage 2a, own hardware)**: `./securax grow|hibernate|prune burrow`, `burrow power`, `spore server|agent`. A Docker twin of real k3s (1 server + 2 agents) rehearses your future machines from the same `lifecycle/burrow.json`; spore writes the bash/cloud-init installer (optional GPU label, NUT power reflex, Argo CD hand-over). Sandbox journey `lifecycle_burrow` (27 checks).
- **Lifecycle: the whole ladder as dormant, wake-on-demand code** (doc 29). `./securax stages|soil|grow|hibernate|prune|scale|rhythm|tenant|organ`.
  - **Phase 1 sprout** (`local/compose/stage-sprout.yml`, profile `sprout`, never started by `up`): Keycloak, OpenBao (auto-unsealed on wake), SeaweedFS S3, Prometheus + Alertmanager; optional upstream organs Wazuh / MISP / TheHive fetched at pinned commits (`lifecycle/organs.json`) with ports pinned to localhost. Backups now include the sprout secrets.
  - **Phases 2-4 Terraform** (`infra/terraform/lifecycle/{aws,gcp,azure}`): `awake=false` plans only the seed bank (vault with object lock, KMS key, data disk, budget); `awake=true` germinates one k3s VM (tree), a managed cluster (EKS Auto Mode / GKE Autopilot / AKS) or a multi-tenant forest with per-tenant key + bucket. `prove.py` proves the dormancy logic and security invariants with offline plans (mutation-checked).
  - **GitOps genome** (`gitops/`): Argo CD app-of-apps, platform (cert-manager, KEDA, Kyverno, Falco, Prometheus, Velero), shared router, a tenant chart stamped per `gitops/tenants/*.yaml`, per-tenant metering rules + dashboard. Gateway now exports token and latency metrics.
  - CI job `lifecycle-genome`; `./securax verify --full` runs the Terraform proofs; sandbox journeys `lifecycle_sprout`, `lifecycle_organs`, `lifecycle_cloud_is_safe`.
### Fixed
- The legacy `infra/terraform/environments/lab` could not `terraform init` (a module with its own provider used `count`); fixed and now validated in CI.
- **Self-correcting provider model names** (`local/compose/model_discovery.py`, `./securax models [--fix]`): providers retire
  models every few months (Oct 2026: Groq `llama-3.3-70b-versatile`, older Gemini/Grok names) which silently killed ladder
  rungs. `keys` and a daily `up` now ask each provider which models your key can use and switch `<ID>_MODEL` to a live one;
  rejected keys are named; offline changes nothing. Shipped defaults refreshed (Groq → `openai/gpt-oss-120b`,
  Anthropic → `claude-haiku-5-5`, Grok → `grok-4.3`, Gemini → `gemini-3.5-flash-lite`) — treat as starting points.
- **`./securax autobuild`** — unattended build loop gated by `verify` (retry with feedback, commit only when green, rollback + escalation brief).
- **`./securax evidence`** (auditor pack, no prompts/keys) and **`./securax scan`** (Trivy over running images).
- `./securax backup|restore|watch`; `docs/securax/26` (coverage vs reference maps), `27` (incident runbook), `28` (status & traceability).
- Sandbox: journeys for model self-correction, autobuild, backup/restore, watchdog; more providers (Mistral, Grok, Perplexity).
- **`WINDOWS-QUICKSTART.md` + `local/scripts/wsl-setup.sh`** — blind-followable Windows install: WSL memory config, Docker WSL
  integration, one paste to install into WSL's fast disk (keeps your `.env` keys and model volumes). `securax.cmd` prefers it.
- **`./securax keys`** — guided free-key setup (Gemini → Groq → OpenRouter) ending in a live test (who answered, how fast).
- **Elastic resources**: every `up` sizes the local model, Ollama RAM cap and lite mode to what Docker can really use
  (`./securax size` to preview). **Preflight** names port conflicts / low disk / Docker-not-reachable; **layered start**
  retries without rebuild, then core-only. See `docs/securax/25-FALLBACKS-AND-ELASTICITY.md`.
- Sandbox: 5 new journeys (keys wizard, elastic sizing, explained blockers, self-healing after killing components, update
  from a dirty checkout).
- **`securax.cmd` — Windows launcher.** `.\securax.cmd up|update|doctor|providers add|…` from PowerShell runs the
  bash CLI in WSL, checking WSL/Docker/Docker-WSL-integration first and printing the exact fix. START/STOP
  `.bat` files now use it (they previously skipped router-config generation and the readiness wait).
- **`./securax verify [--full]`** — one definition of done (lint, unit tests, router-config baseline, compose
  validity; `--full` adds the sandbox). `./securax build` now uses it as its auto-test command.
- `.gitattributes` keeps `securax`/scripts LF so a Windows checkout can't break them.
- **User-perspective sandbox (`sandbox/`, `python3 sandbox/run.py`, CI `e2e-sandbox`)** — runs the real product from a fresh
  clone (no `.env`) with a real browser, real Ollama model and faked cloud providers; 8 journeys / 88 checks. It found and
  drove fixes for: readiness race, no config regeneration on `up`, one-shot Command Center status, gateway `stream:true`
  500s, and the router phoning huggingface.co.
- **`./securax update`** — `git pull --ff-only` then recreate the containers, so fixes actually run (a
  plain pull leaves the old containers running). `./securax doctor` now warns when you're behind `main`.
- **`./securax guard [status|on|off]`** for the optional Llama Guard detector; **`./securax up` auto-heals**
  the broken state (Llama Guard on but never installed → every request blocked) by switching it off, loudly
  and reversibly. The built-in rails enforce either way.
- The provider wizard now takes keys **silently** (a visible key ends up in screenshots/chat pastes), warns
  when a key looks like a *different* provider's (e.g. an OpenRouter `sk-or-` key under ElevenLabs) and
  refuses to store it unless you confirm, and rejects a typed command in the provider-id prompt.
- **Degradation ladders** — `bank-assistant` (Gemini → Groq → OpenRouter → local) and `builder`
  (DeepSeek → free tiers → local coder → local). Missing keys skip rungs; every chain ends in the
  always-on local model, so there is an answer even with zero keys and zero internet. Cloud rungs
  fail over in 40 s and cool down after repeated failures. New Groq plugin. `./securax build` now
  defaults to the `builder` ladder.
- **`./securax profile`** — detects RAM/CPU and right-sizes the local model, Ollama caps and lite mode
  (with WSL2 `.wslconfig` guidance); **`./securax up --lite`** runs only the core path.
  `./securax doctor` now probes the real ladder and reports which rung answered.
- Ollama tuned for CPU-only machines (warm model, single request/model at a time).
- `docs/securax/24-RESILIENCE-AND-LOW-RESOURCE.md`.
- **`./securax pull`** — pull the local model in the foreground so you can be sure it's ready (the
  free/offline `bank-assistant-local`), instead of relying on the background pull.
- **`./securax doctor` now runs a REAL end-to-end chat test** through the gateway and prints the
  *actual* upstream error (not a chat UI's generic "Oops"), plus whether the local model is pulled.
- **Build SecuRAX with its own models** (reduce the Claude dependency). `./securax build "task"`
  drives [Aider](https://aider.chat) against the SecuRAX gateway with a cheap/local model (default
  `deepseek`, or the new sovereign `coder` = local Qwen2.5-Coder), loads the new **BUILD-CONTRACT.md**
  as always-on context, and runs `ruff + pytest` after every edit until green — rigor from the test
  loop, not just the model. `./securax escalate "task"` writes a tight brief (task + diff + rules) for
  the hard 10% that still needs a frontier model. New `coder` plugin + `ENABLE_LOCAL_CODER`/`BUILD_MODEL`/
  `CODER_MODEL` knobs. Full strategy: `docs/securax/23-BUILD-WITHOUT-CLAUDE.md`.
- **AI provider plugins** (Mattermost-style). A catalog (`plugins/catalog.json`) drives a generator
  that builds the LiteLLM router config from whichever providers you enable, so adding
  **OpenAI, Anthropic, DeepSeek, Mistral, Grok (xAI), Perplexity, Azure AI Foundry, AWS Bedrock,
  OpenRouter** is one command — `./securax providers add` — and the model appears in Chat, still
  routed through the security gateway. The gateway `/v1/models` now mirrors the live router models.
  Model IDs are overridable per provider (`<ID>_MODEL`). Voice via ElevenLabs (`./securax say`),
  plus a heavy-compute (Colab / cloud GPU) recipe. See `docs/securax/22-PLUGINS-AND-PROVIDERS.md`.
- **Command Center** (`hub.html`, reachable at `/hub.html`, `/hub`, or the Guiding Map's **◆ All
  Apps** header button) — one front door with a clickable card + live status for every app, so you
  never type `:3000/:3001/:5678` again. `./securax up` opens it. It is served from the same mount as
  the PWA (no second mount/alias), so a restart can't 404 it; the old `/portal/hub.html` path
  redirects for existing bookmarks.
- **`./securax setup`** — a 30-second wizard that writes `.env` (Gemini key, multi-device access,
  a generated sync token, strong service passwords) so you never hand-edit `.env`.
- Gateway **`GET /v1/models`** so Open WebUI / AnythingLLM can list and select a model.
- **`BIND_HOST`** to expose the UIs to your phone/iPad over Wi-Fi or Tailscale; `DEPLOY.md` gains a
  multi-device + sync section.

### Changed
- CPU-only default chat model is now qwen2.5:1.5b on 16 GB laptops (was 3b — about twice as slow for little gain).
- **Free/sovereign by default.** Chat (Open WebUI) now defaults new conversations to `bank-assistant`
  (free Gemini tier → local fallback), so you never accidentally land on a paid provider that errors
  with "Oops" when its key has no credits. Pick any other model from the dropdown any time.
- **`./securax up` is now true one-step setup:** if no Gemini key is set and you're in a terminal, it
  asks for a free key inline (Enter to skip) — no more hunting for `.env`.
- **Command Center is honest about scope:** Chat + Guiding Map are shown as "works out of the box";
  Private Docs (RAG) and Automation (n8n) are grouped as optional add-ons that need their own setup.
  The gateway is shown as a friendly security status ("every AI call is guarded"), not raw JSON.

### Fixed
- **`git pull` conflicted after every `up`** (found on a real Windows laptop): `up` rewrote the tracked
  `litellm-config.yaml`. The router now mounts a git-ignored `litellm-config.generated.yaml`; the tracked file is a
  baseline `up` never touches. Config generation failing is now reported, not swallowed. Sandbox asserts `up` leaves
  the checkout clean.
- **"400: Request blocked by AI security policy" on harmless prompts.** `.env.example` once shipped
  `LLAMA_GUARD_URL` enabled; existing `.env` files keep it (git pull never rewrites `.env`), and with the
  model not installed the fail-closed gateway blocked everything. The gateway now says a *detector is
  offline* (machine-readable `reason: detector_unavailable`) instead of implying the prompt was malicious,
  and the Guiding Map no longer calls it "an attack pattern".
- Open WebUI: the random "Arena Model" is off and the stack's config is authoritative
  (`ENABLE_PERSISTENT_CONFIG=false`), so `DEFAULT_MODELS=bank-assistant` now applies to existing installs.
- **The Guiding Map showed "v13.0.2".** That badge was a hardcoded legacy string (not stale cache —
  a fresh load showed it too) while the product is `VERSION` 0.1.0. `guiding-map/build.js` now stamps
  it from `VERSION`, and a CI test fails if it ever drifts or a hardcoded version returns.
- **Provider keys never reached the router.** The LiteLLM container was only given the Gemini/Azure
  keys, so OpenAI/Anthropic/DeepSeek/xAI/Mistral/Perplexity/OpenRouter always failed with an auth error
  (it looked like "no credits"). All provider keys are now passed through, and a CI test fails if the
  generated config ever references an env var compose doesn't wire in.
- **`bank-assistant` was randomly load-balanced** between Gemini and the slow local model (two
  deployments under one name + `simple-shuffle`). Every alias is now a single deployment; local is a
  fallback, never a coin-flip.
- AWS Bedrock now authenticates with the AWS key pair + region (it was sent the access-key id as an
  `api_key`); `LOCAL_MODEL` is now honoured by the router (bare tags get the `ollama/` prefix).
- **The PWA self-updates now.** After a redeploy/`git pull`, the Guiding Map auto-reloads once when
  the new service worker takes control, so you never get stuck on a stale old version in the cache.
- **Clear WSL vs Windows guidance.** `START-HERE-Windows.bat` typed inside WSL gives "command not
  found"; docs + the Command Center now say to use `./securax up` in a terminal and only double-click
  the `.bat` in File Explorer. Added troubleshooting for "models won't list / old version after pull"
  (the containers need `./securax down && ./securax up` to recreate — a pull alone doesn't).
- **Models now work out of the box.** The `modelplane` network was `internal: true`, so Ollama
  couldn't pull models and LiteLLM couldn't reach cloud models — breaking every answer. Given egress
  (models still publish no host ports). LiteLLM now defaults to **fast cloud Gemini with a local
  fallback**, so answers are instant with a free key and private-local otherwise.
- **No more false "Blocked by the guardrail".** Llama Guard was enabled by default but its model
  wasn't pulled, so the fail-closed detector blocked *every* request. It's now opt-in; the fast
  deterministic rails (100% red-team defence) run by default. The PWA also stops mislabeling a
  model-unavailable error as a guardrail block.
- `fin_freedom.py` argparse crash from a literal `%` in help text (Python 3.14).
- The optional kind/k8s plane used host port 8080, clashing with the gateway; moved to 8081.


## [0.1.0] - 2026-10-11
First versioned public release. SecuRAX is a sovereign, local-first AI-security + life-OS estate.

### Added
- **AI Guardrail Gateway** — fail-closed Policy Enforcement Point for LLM traffic (prompt-injection,
  PII redaction, secret/exfil output rails, Red/Yellow/Green data classification), with pluggable
  detectors (Llama Guard / Model Armor / Bedrock / Prompt Shields) and a `/version` endpoint.
- **MCP control plane** — zero-dependency stdlib JSON-RPC server exposing 19 estate capabilities.
- **LiteLLM multi-model router** — OpenAI-compatible, local-first (Ollama) with capped free/cloud fallback.
- **Guiding Map PWA** — offline life-OS cockpit (8 pillars, cadence engine, wealth engine, inline help).
- **Sovereign cross-device sync** (`estate-sync`) — SQLite + server-side per-key merge, fail-closed Bearer auth.
- **Autonomous web-research agent** — read-only, allowlist + SSRF-gated, injection-safe, HITL; optional
  Playwright render engine and approved-action executor (write path, audited, per-action approval).
- **Advisor army** — 26 stealth specialist agents (first-draft opinions, anti-hallucination contract).
- **Global Intelligence** — community-consensus decision engine (replicate/edge, capability-fit, timing).
- **Financial planner** — sovereign retirement-corpus projection (India/BFSI defaults).
- **Routines** — sovereign scheduled estate tasks (the local "Claude Routines").
- **Local image generation** — sovereign text-to-image (opt-in `design` profile).
- **DevSecOps CI** — pytest + jsdom suites, gitleaks, Semgrep, Trivy (IaC + image), CycloneDX SBOM,
  OPA/Conftest, compose sanity + build-drift poka-yoke gates, AI red-team scorecard + AI-SPM posture.
- **Documentation set** — `docs/securax/` (vision, principles, architecture, capability catalog,
  compliance map, roadmap, cost/models, end-state enterprise architecture, Claude-parity, more).
- **One-step deployment guide** (`DEPLOY.md`) — install Docker, run one command, done.
- **Product scaffolding** — SemVer `VERSION`, `CHANGELOG`, `SECURITY`, `CODE_OF_CONDUCT`,
  `GOVERNANCE`, `MAINTAINERS`, `SUPPORT`, `CODEOWNERS`, issue/PR templates, Dependabot, ruff lint
  gate + pre-commit, and a tag-driven release workflow.

### Security
- Fail-closed everywhere; no secrets in the repo (pattern-based PII/secret CI gate); SSRF + DNS-rebind
  defenses on the web agent; append-only audit trail for approved actions.

[Unreleased]: https://github.com/rohan2pt0/ai-cloud-cyber-range/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/rohan2pt0/ai-cloud-cyber-range/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rohan2pt0/ai-cloud-cyber-range/releases/tag/v0.1.0
