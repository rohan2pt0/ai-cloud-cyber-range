# 79 · Exercise range: live-fire cyber defence exercises

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Stage 1 built and tested: scenario format, scoring engine with hash-chained log, the portal (mission board, reports, judging, timeline, target checks, awareness, injects, password changes), the isolated lite range with scoring bot, simulated staff and a red-team bot, verified in real Docker and a real browser. Stages 2-4 (realism, blue-team kit, full cloud range and multi-team control) have target dates in the doc. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The aim:** run the kind of live-fire exercise national cyber-defence events run, inside SecuRAX:

- A blue team defends an organisation's network while a red team attacks it.
- Scoring bots check that the required services stay up, and simulated staff keep logging in.
- The team files incident and situation reports for judges, and works through a mission board of tasks.

It serves your own team's practice first. Running exercises for other teams comes later (stage 4).

The design follows the screens and rules of commercial exercise platforms (an "integrated scoring and situational awareness" portal). It is built from scratch, with open-source parts, and holds no other exercise's content.

## The easy way: one command

```bash
./securax exercise
```

- **The first time:** it makes a practice exercise from the built-in sample scenario.
- **Every time:** it opens the portal in your browser (http://127.0.0.1:8097/) and prints the sign-in tokens to use:
  - **white:** you, running the exercise
  - **blue:** the defenders
- **Without Docker** it still works: tasks, reports, judging and the MITRE learning paths need no containers.
- **The live machines to defend:** `./securax exercise lite up` adds them.
- **Where else to find it:** the Command Center lists it under **Practise and defend**, with a live dot while the portal runs.

## Step by step, when you want control

```bash
./securax exercise plan                      # check the scenario and see what the lite range runs on this machine
./securax exercise new --name practice       # create an exercise; prints the white, red and blue sign-in tokens ONCE
./securax exercise lite up                   # isolated containers, the scoring bot, simulated staff, the red-team bot
./securax exercise serve                     # the portal on http://127.0.0.1:8097/ ; sign in with a token
ssh -p 2222 rangeadmin@127.0.0.1             # the blue team's jump box (the scenario's admin password; change it first)
```

Then:

- **Exercise control** presses **Start the clock** (or runs `./securax exercise start`).
- **When you finish:** `./securax exercise report` writes the after-action report. `./securax exercise lite down` removes the range; the scores and reports stay.

## What each screen does

| Screen (portal) | Who | What it does |
|---|---|---|
| Overview | all | The phase, the minute, and the team's points by category |
| Rules | all (red: the rules only) | The scenario's rules of engagement, the green-team account, and this round's rule checks |
| Team plan | blue, white | **Plan:** the timed plan, item by item, with owner, window, and done / blocked / overdue / now.<br>**Check-ins:** the next check-in, plus a warning when a situation report is due. |
| Scoring log, Team timeline | blue, white | Every scoring event; cumulative points per category over time |
| Target checks status | all (red: names only) | Every host and service, green, red or "compromised", from the latest scoring round |
| Team awareness | blue, white | Per zone: % good, compromised, not available |
| News injects | all | Scenario events released on the minute (a journalist calls, a threat warning) |
| Mission board | blue, white | Tasks by phase:<br>• **Open:** tasks locked until their minute.<br>• **Answer:** answers go to judging.<br>• **Hint:** costs 20% of the task's points.<br>• **Abandon:** costs 50% and closes the task. |
| Incident report | blue | Target, compromised or not, chronology, impact, source, action plan, additional information |
| Situation report | blue | I. Event overview · II. Adversary assessment · III. Impact on operations · IV. Actions taken · V. Status · VI. Any other business |
| Judging | white | **Queues:** incident reports, situation reports and task answers.<br>**Beside each incident report:** the red team's own claims on that target.<br>**Grades:** the points are capped at the scenario's maximum. |
| Staff password changes | blue, white | The blue team documents every change to a staff account, per system or "all". The simulated staff use it |
| Restore from backup | blue | Records a revert. `./securax exercise revert HOST` rebuilds a lite host and costs the penalty |
| Report an attack, Attack reports | red, white | One report per objective achieved, with evidence. Each costs the blue team points |
| Exercise control | white | **Start the clock** and **special adjustments**, each with a reason.<br>**Score-log check:** confirms the log was not edited. |

## The scoring model

The categories are the ones the exercise timeline showed. Every value comes from the scenario file:

| Category | Sample value | Comes from |
|---|---|---|
| Availability | +1 per service up per round, +1 per staff login that works | The scoring bot, every 60 s, after the clock starts |
| Solve task | Up to the task's points | Judges |
| Use hint / Abandon task | −20% / −50% of the task | Blue team's choice |
| Attack reports | −40 each | Red team (human or bot), only in a phase with `attacks_allowed` |
| Incident reports | Up to +20 | Judges, who see the red team's claims beside the report |
| Situation reports | Grade 0–5 × 4 | Judges |
| Restore from backup | −25 | Blue team (revert) |
| Rule breaches | −5 per broken rule per round | The scoring bot's rule checks, until the breach is fixed |
| Special | Any, with a reason | Exercise control |

A host stays "compromised" for 60 minutes after a red-team success. An accepted incident report filed after the attack clears it sooner. Every scoring event is hash-chained: `./securax exercise verify` finds an edited, deleted or reordered event.

## Rules of engagement, checked by the range

Exercise rules usually say what the blue team must not break. The range checks what a machine can prove, every round:

- **Ping stays allowed.** Every machine has a **HOST** check (one ICMP echo), as exercise portals show it. A machine that drops ping scores as down.
- **The green-team account stays intact.** Every game makes its own key pair. The `greenteam` account is an administrator on every lite host and logs in by key only. Each round the scoring bot logs in with that key and confirms the account is still an administrator. Removing the key, the account or its rights is a **rule breach**: −5 per host per round until it is fixed.
  - **Verified on the real range:** deleting the key on one host and removing the admin right on another both show as broken, with the reason.
- **Staff accounts keep working.** The simulated staff logins already enforce this (an undocumented password change fails).
- **Addresses and names do not change.** Every check runs against the scenario's address, so a changed address fails its checks.

**Not checked automatically (exercise control judges these):**
- workstation software staying installed
- outgoing traffic from workstations
- IPv6 parity: the lite range has no IPv6 yet; the full range will check both families

## The lite range (on the laptop) and what it leaves out

- **What runs:** every scenario host marked `"lite": "gamebox"` is a small Alpine container running the services its checks name: SSH, web, DNS (dnsmasq) and mail (OpenSMTPD). Each comes with the scenario's staff accounts and admin account. Inside a host, `svc start|stop|status` controls the services.
- **Isolation:** every zone is a Docker network with `internal: true`, so the range cannot reach the internet or your LAN. The only door is the jump box on `127.0.0.1:2222`.
- **Subnet safety:** `lite up` refuses to start if a zone's subnet overlaps a network your machine already uses, such as a VPN.
- **Bot addresses:** the scoring bot works from address .252 in every zone, as exercise scoring bots do. The red-team bot sits at .251, on the public zones and guest Wi-Fi only.
- **What the bot containers mount:** only the `exercise` code, never the rest of SecuRAX or your vault.
- **The red-team bot is a baseline adversary.** In the attack phase it tries the scenario's *original* passwords. It leaves a harmless marker in `/tmp` and files an attack report. Human red teamers do everything else.
- **Simulated staff:** they log in over SSH every round with the password the blue team last documented for that machine. An undocumented change makes their logins fail, as in the real exercise.
- **Left out of the lite range:**
  - **Windows:** domain controllers, Exchange, SQL Server and desktops. The sample's `dc1` is marked `goad`, to come from the existing AD lab (`./securax range`, doc 32). The rest show as "not deployed".
  - **Network gear:** routers and the firewall exist only in the full range.

## Scenarios

**One JSON file describes an exercise for any team number.** `{X}` is the team number, and simple arithmetic is allowed (`10.188.33.{X*4-2}`). Anything else in a template is refused, never run.

**A scenario names:**
- zones, and hosts with their scored services
- staff accounts and the admin account
- phases, with `attacks_allowed`
- tasks and news injects
- the scoring values

**A broken scenario is refused before anything runs**, with every problem listed at once:
- an address outside its zone
- a duplicate host
- an unknown check type
- an address at .250 or above, which is kept for the bots

The repository ships a fictional sample: Example Corp, `ex{X}.range.test`, made-up staff. Real exercise scenarios hold private detail and belong in `vault/exercise/scenarios/`; run them with `--scenario`.

## What was verified, and how

- **Unit tests** (`exercise/tests/`):
  - **Scenarios:** templates, and refusal of a broken scenario.
  - **Service checks:** each against a real local server, including a defaced page and a DNS name with no answer.
  - **Game rules:** every scoring rule, judging limits, phase rules, the tamper check, per-system password changes, rule breaches, the team plan, and compaction.
  - **Portal:** run over real HTTP; it covers each role's limits and the security headers, and refuses token guessing.
  - **Lite range:** its isolation rules.
- **Browser audit** (`exercise/tests/ui_audit.py`):
  - **Coverage:** every screen, as each role, in both themes, at desktop and phone width.
  - **Pass criteria:** no page error, no raw object text, no text below WCAG AA contrast, and no sideways scrolling.
- **Sandbox journey** `exercise_lite_range`, a whole game in real Docker:
  1. Every service is up and every staff login works.
  2. The bot gets in only in the attack phase.
  3. The blue team changes the admin password through the jump box, and the bot is shut out.
  4. A rebuild costs the penalty, the log verifies, the report is written, and the range is removed.
- **A real run found and fixed a design flaw.** A documented staff password change had been applied to every machine. In the lite range, accounts are per machine (unlike a Windows domain), so a change now applies to the named system, or to all systems when it says "all".

## Lessons from the earlier exercise material, built in

- **Hardening must not break scored services.** The earlier hardening scripts and SOPs contained changes that would take required services down:
  - disabling NetBIOS on domain controllers
  - "deny all inbound except SSH" on servers that must serve DNS, mail and web
  - a 5-attempt lockout that lets the red team lock out the simulated staff

  The blue-team kit (stage 3) checks every change against the host's scored services first.
- **Remote-execution and credential handling must actually work and stay safe.** The earlier scripts had three problems:
  - **Broken connection test:** `BatchMode=yes` disables password logins, so the test always failed.
  - **Wrong tool:** `winrs` does not exist on Linux.
  - **Leaked passwords:** they sat on the command line and in plain-text files, and scripts were served over plain HTTP.

  Here, passwords go through the environment and never appear in `ps` output; the kit will use Ansible with vault-held secrets.
- **Captures must rotate.** The earlier 24-hour timetable wrote every packet to one capture file without a limit, which is how a disk fills in the middle of an exercise. Rotate them (`tcpdump -C 100 -W 20` keeps at most 2 GB); doc 80 covers storage.
- **Scoring should follow the real model, not a guess.** The 40/30/20/10 weights in the SOP do not match what the exercise timeline showed. The engine uses that timeline's categories instead.

## Cues taken from your material (the ledger)

Each document you share is read for what SecuRAX lacks. The best of it is applied 80/20 and recorded here, so nothing is lost and nothing is applied twice. The documents stay private: only the cue, in our own words, is recorded.

| Material | Cue | Where it went | State |
|---|---|---|---|
| Exercise portal screenshots | Scoring categories, mission board, incident and situation report structure, judging, target checks, per-zone awareness, news injects | The portal (this doc) | Done |
| Exercise network diagram and system list | One template for any team number; zones; scored services per host; scoring bot at .252 | The scenario format | Done |
| Staff accounts page | Staff accounts must keep working; password changes documented per system | Simulated staff + Staff password changes | Done |
| Earlier blue-team scripts | The broken SSH test, `winrs` on Linux, `Set-LocalUser` on DCs, NetBIOS off on DCs, unquoted-path fix breaking services, passwords on command lines | Lessons above; the stage 3 blue-team kit | Lessons recorded; kit due 2026-11-25 |
| SOPs and strategy | Roles, the first 15 minutes, check-ins, playbooks; scoring weights that were guesses; risky hardening advice | The Team plan (sample playbook) and lessons above | Done |
| Rules of engagement | Required services stay up; no address changes; ping allowed; green-team account untouched; staff accounts and software keep working; revert is for recovery only | Rule checks, Rules screen, scoring | Machine-checkable rules done; the rest are judged |
| Ask: beat the commercial ranges; teach MITRE ATT&CK, D3FEND and ATLAS; certification-ready skills; gamify | Framework tags on everything, a coverage screen, learning paths, players, XP, badges; a market comparison | Doc 81 | Done; AI zone and commercial readiness dated |
| 24-hour timetable | Unbounded packet capture; containers built from `:latest` | Capture rule (lessons above); pinned images and storage guard (doc 80) | Done |

## Next stages (target dates, each needs your merge)

| Stage | What | Target | Needs |
|---|---|---|---|
| 2. Realism | **Simulated staff:** web browsing, mail sending, file edits (GHOSTS-style). **Automated red campaigns:** MITRE Caldera or Atomic Red Team, vetted first. **ICS zone:** an OpenPLC controller with a web HMI. **Security zone:** traffic capture and log search through the Wazuh and Suricata organs | 2026-11-10 | — |
| 3. Blue-team kit | **Hardening:** a dry-run-first Ansible playbook that refuses any change that would break a scored service. **Report drafts:** incident and situation reports drafted from `respond`/`incident` evidence, a person approves. **Team dashboard.** The timed checklist is already done (the Team plan) | 2026-11-25 | — |
| 4. Full range and exercise control | **Full range:** the Windows estate and network gear in the cloud (Terraform, started only for an exercise), or on Proxmox. **Exercise control:** several teams at once. **Access:** a VM console (Guacamole) and team chat (the Mattermost organ) | 2026-12-20 | A cloud account with Mumbai quota, or a Proxmox host; Windows evaluation images |

The Windows evaluation images and the cloud running cost will be checked and priced when stage 4 starts.

## What it does not do

- **It does not judge reports by itself.** People grade them; the engine only enforces the limits.
- **It is not exposed to a network.** It binds to `127.0.0.1` unless you choose otherwise, and the tokens are the only protection. For a multi-team event, put it behind the TLS edge (doc 48) and the gateway's identity layer.
- **It is not a substitute for an exercise's rules of engagement.** Write those for every event, and make sure everyone has read them.
