# 102 · Mission control: the estate's management operating system, run by AI agents

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the twelve management disciplines mapped onto the estate, every role an AI agent (RACI, three lines, maker-checker) with the owner's decisions named; ten flight rules acted on hourly by the autopilot within its intent; a Go/No-Go poll the nightly update must pass; the double nightly backup removed. A cost view (./securax mission costs), a weekly after-action review (./securax mission aar, Sundays) and the mission line on the Command Center are built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** run the estate on a real management operating system: the twelve disciplines and the cycle every well-run department, company or country uses. Every role a person would hold is filled by an AI agent until scope or revenue needs a person. Check that what the estate already does happens in the right order and wastes nothing. Add an autopilot that borrows what space and military missions do well.

## 1. The cycle, and who runs it

**Set direction → allocate resources → execute with controls → measure and verify → correct and improve**, then repeat.

| Step | Run by | Where you see it |
|---|---|---|
| Set direction | The owner (the Life OS wheel and OKRs); the commander's intent below for the agents | Life OS, `governance/mission.json` |
| Allocate resources | The AI allowance per caller, storage rules, the provider chain | cockpit, `./securax storage` |
| Execute with controls | Operations and Builder agents, inside the flight rules; maker-checker before anything merges | routines, `./securax ship` |
| Measure and verify | Risk officer and Assurance agents: KPIs, KRIs, fitness, journeys, drills, proof gaps | cockpit, `./securax proofs` |
| Correct and improve | Flight director: postmortems, lessons, the next fix brief | `LESSONS.md`, the autopilot (doc 92) |

## 2. The crew: every role an AI agent

`./securax mission crew` prints it. The three lines of the Three Lines Model are kept apart: operations does the work, risk and compliance watch it, and assurance checks independently that what is claimed is true.

| Role | Line | Agent | RACI |
|---|---|---|---|
| Flight director | 1 | the autopilot and mission control | A |
| Operations | 1 | watchdog, backup, update, storage | R |
| Builder | 1 | autobuild on the open models | R |
| Checker (maker-checker) | 1 | review, CI and the forge gate | C |
| Risk officer | 2 | cockpit, risks, crown jewels, continuity | C |
| Compliance | 2 | comply, regwatch, Govern | C |
| Assurance (internal audit) | 3 | fitness, proofs, game days and drills, honesty checks, the sandbox | R/A for assurance |
| Intelligence | 1 | regwatch, threat data | I |
| Communications | 1 | notify (andon), progress | I |

**Kept for you:**
- spending money;
- opening or closing an outside account;
- anything that cannot be undone: deleting data, rotating the backup key, publishing;
- accepting the risk of a red security finding.

**When people join:** Govern's job descriptions and the people-scale planner (doc 39) are ready. A role moves to a person when its trigger is met, for example a paying customer whose contract needs a named human. Until then it stays an agent.

## 3. What we took from space and military missions

| Practice | Where it comes from | In the estate |
|---|---|---|
| **Flight rules** | NASA mission control: the response to each known situation is agreed before it happens | `./securax mission rules`: ten rules, each with its trigger, its action, and whether an agent may act alone. The hourly `mission-rules` routine acts on the agent's rules (a missed backup is retaken, a red disk is cleaned, a core service healed) and only reports the owner's |
| **Go/No-Go poll** | Launch control: every console reports before a risky step; one NO-GO holds | `./securax mission poll update`: ransomware alarm, a clean backup from the last day, disk, a reporting clock, and main's nightly sandbox. The nightly update now runs only on GO, and tells you once why it held |
| **Commander's intent** | Military mission command: agents act alone inside a stated intent and limits | "Keep the owner's data safe and the estate useful every day, at the lowest cost in money, machine and attention; when unsure, protect the data and wait" |
| **OODA loop** | Observe, orient, decide, act | `./securax mission`: one screen, ending in the one thing that needs you, or "nothing needs you" |
| **Two-person rule** | Nuclear and launch safety | nothing irreversible without a second check (CI and review) or the owner |
| **Fault detection, isolation and recovery, and game days** | Spacecraft, Google DiRT | the watchdog, chaos experiments on the everyday estate (doc 101), restore drills (doc 88) |
| **After-action review** | Army | `./securax mission aar` every Sunday: intended, what happened, what differed and why, keep, change. It never calls a week quiet when nothing ran |

## 4. The order of events, checked, and the waste removed

The 27 routines were read in the order they run.

- **Two backups every update night.** The 02:30 backup was followed at 03:15 by the update taking another full one. The update now uses a clean backup from the last 2 hours as its safety copy.
- **The laptop updated even after a red nightly build.** The nightly sandbox on main runs at 02:00 IST; the 03:15 update did not ask how it went. It now asks, through the Go/No-Go poll. If GitHub cannot be reached, that console alone does not hold the update.
- **The watchdog healed only the gateway** (found by the chaos work, doc 101). It now heals the Command Center and sync too, and unfreezes a frozen container.

What already ran in the right order: storage clean-up before the nightly backup, backup before update, the mirror after the backup, the autopilot drill after the update.

## 5. The twelve disciplines, mapped

`governance/mission.json` holds this table; a test fails if one goes missing.

| # | Discipline | In the estate | State |
|---|---|---|---|
| 1 | Strategy and direction | Life OS wheel and OKRs, principles, the north star | built |
| 2 | Performance management | cockpit KPIs and KRIs, `progress` | built |
| 3 | Risk and resilience | risk register, crown jewels, continuity, backups, chaos | built |
| 4 | Governance and accountability | the crew (RACI, three lines, maker-checker), roles, the kill switch | built |
| 5 | Operations and process excellence | routines as SOPs, watchdog, safe update, postmortems | built |
| 6 | Finance and resource allocation | AI allowance, Govern's yearly cost, storage forecast, `./securax mission costs` | built; money only from your own list |
| 7 | People and organisation | AI agents today; job descriptions and the planner ready | built for agents |
| 8 | Programme and project execution | dated roadmap rows, `proofs`, `ship` | built |
| 9 | Data and intelligence | the cockpit snapshot as the single source of truth, regwatch, threat data | built |
| 10 | Change and transformation | channels, rollback, dated migrations | built |
| 11 | Assurance and compliance | compliance maps with evidence, fitness, journeys, drills, weekly mutation testing of the rails | built |
| 12 | Learning and improvement | lessons, postmortems, honesty history | built |

## 6. Next, with dates

| Step | By |
|---|---|
| ~~One cost view of the estate~~ done 2026-10-22: `./securax mission costs` (money from your own private list, machine and model tokens measured) | ~~2026-11-15~~ |
| ~~A written weekly after-action review~~ done 2026-10-22: `./securax mission aar`, every Sunday at 18:30 into `vault/mission/` (private) | ~~2026-11-15~~ |
| ~~The mission board on the Command Center~~ done 2026-10-22: one folded line, "GO for the nightly update" or why not, the rules firing, and what needs you | ~~2026-11-30~~ |
