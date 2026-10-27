# SecuRAX — Robust · Adaptive · eXcellence-driven

[![License: FSL-1.1-MIT](https://img.shields.io/badge/License-FSL--1.1--MIT-blue.svg)](LICENSING.md)
[![CI](https://github.com/rohan2pt0/ai-cloud-cyber-range/actions/workflows/devsecops.yml/badge.svg)](https://github.com/rohan2pt0/ai-cloud-cyber-range/actions/workflows/devsecops.yml)
<!-- readme:badge:start -->
[![Version](https://img.shields.io/badge/version-0.3.0-blue)](CHANGELOG.md)
<!-- readme:badge:end -->
![AI red-team defence](https://img.shields.io/badge/red--team%20defence-100%25%2F0%20FP-blue)
![Cost to start](https://img.shields.io/badge/cost%20to%20start-%E2%82%B90-success)
![Frameworks](https://img.shields.io/badge/mapped%20to-NIST%20%7C%20ISO%20%7C%20RBI%20FREE--AI%20%7C%20DPDP-informational)


## ▶ Start here (one step)

```bash
./securax go        # gets everything working and keeps it working; safe to run any time
```

`go` checks Docker, takes the latest code safely (backup first, automatic rollback), starts the estate, installs the schedules
(nightly safe update, backups, alerts, regulator watch), sets up phones over Tailscale when it is on, and ends with one screen:
what works, and the one fix if something does not. On Windows, double-click **`START-HERE-Windows.bat`**.

Your **Guiding Map** (http://localhost:8088, or https://hub.securax.localhost with `./securax tls on`) is the home screen:
tasks, your private AI, money, goals, and one-tap launch of the rest. Install it (Add to Home Screen) to use it like an app,
even offline. Your data stays on your device.

> Something not right: `./securax doctor` · `./securax why` · Which build am I on: `./securax version` · Stop AI at once:
> `./securax ai stop all --reason "..."` · AI allowance: `./securax ai budget` · Stop and free RAM: `./securax down`

<!-- features:start -->
## What you can do

### New in the estate

The latest additions, newest first (the Command Center marks each one New for 30 days):

- **2026-10-27** · [Build it from a browser, on your own models](docs/securax/119-STUDIO.md): Your single biggest dependency - a paid Claude Code subscription and its terminal - is removed: you build and change the estate from a familiar GUI on the open models you already run, so no outside service or plan can gate your day-to-day work. `./securax studio`
- **2026-10-26** · [Prove every command works](docs/securax/117-SELFTEST.md): You can trust that the commands work: the system proves its own command surface on every change, so 'it doesn't even start / that command errors' is caught by a test, not by you at the worst moment. `./securax selftest`
- **2026-10-26** · [One lever a week](docs/securax/112-SET-AND-FORGET.md): Every week the one thing most worth changing about your life is chosen for you and made effortless, so you improve where it actually matters without having to decide what to work on. `./securax improve`
- **2026-10-26** · [One idea a week](docs/securax/115-ONE-IDEA-A-WEEK.md): Every week one timeless, high-leverage idea sharpens how you think, decide and work, tied to a goal you set, so you compound as a professional and a person instead of drowning in a feed you have to wade through. `./securax insight`
- **2026-10-23** · [The one next step](docs/securax/93-PROGRESS-YOU-CAN-SEE.md): You never have to learn 123 commands to be better off: one command always points to the next thing. `./securax next`

**Practise and defend**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Cyber range](docs/securax/79-EXERCISE-RANGE.md) | Practise defending real-looking systems against a live red team, with scoring, judging and MITRE ATT&CK, D3FEND and ATLAS learning paths. | `./securax exercise` |
| 🟡 [Crisis response kit](docs/securax/78-CRISIS-RESPONSE-KIT.md) | Step into an incident: collect evidence properly, find what is wrong, and draft the reports. | `./securax respond` |
| 🟢 [Purple-team loop](docs/securax/30-PURPLE-TEAM-LOOP.md) | Attack your own AI channel, check that the attack was detected, and keep the evidence. | `./securax purple` |
| 🟢 [Adversary ledger](docs/securax/30-PURPLE-TEAM-LOOP.md) | Turn every bounty or red-team finding into a purple probe, a lesson and a drill, and prove it stayed closed. | `./securax adversary` |
| 🟢 [Check software before you trust it](docs/securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) | Look inside a third-party package or file, in a sandbox, and see what a new version can do that the old one could not. | `./securax inspect` |

**Comply and govern**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Readiness for any regulation](docs/securax/106-WHO-SECURAX-IS-FOR.md) | Where your organisation stands on any regulation SecuRAX maps (RBI NBFC directions 2026, SEBI CSCRF, UK CAF, NIST AI 600-1 and more): only your chapter's or category's requirements, each marked with evidence, owner and date; the vital few gaps; VA, PT, IS audit and CISO-to-Board dates; a board pack and an auditor's sheet, kept on your machine. | `./securax readiness demo` |
| 🟢 [BFSI control matrix](docs/securax/66-BFSI-CONTROL-LIBRARY-AND-NAVIGATOR.md) | Every Indian BFSI cyber obligation as one matrix: what applies to you, what is proven, and what to close next. Works with no file from you. | `./securax go` |
| 🟢 [Regulator incident clock](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every applicable regulator's reporting deadline for an incident, counting down, with the drafts ready. | `./securax incident` |
| 🟡 [Regulatory gap maps](docs/securax/35-REGULATORY-GAP-ASSESSMENT.md) | Requirement-by-requirement maps (RBI, SEBI CSCRF, NIST AI 600-1, post-quantum and more) with the evidence for each, checked on every change. | `./securax comply` |
| 🟡 [Risk register](docs/securax/67-RISK-REGISTER-NSCS-CII.md) | Your risks with owners and dates, linked to the controls that treat them, with an overdue lamp. | `./securax risks` |
| 🟢 [Cockpit](docs/securax/37-COCKPIT-STORAGE-PATCHING.md) | One page: what is at risk, what to do next, and the trends. Lamps light only when something needs you. | `./securax cockpit` |
| 🟡 [Govern (for decision makers)](docs/securax/94-GOVERN.md) | Where the organisation stands on governance, people, process and technology; the minimum basic and the highest possible; for each gap the 5W1H and an indicative budget; the team you need; a one-page Board report; and a pack of ready policies, SOPs, registers and an executive deck. | `./securax govern` |
| 🟡 [Vantage (the CISO's operating system)](docs/securax/95-OS-KIT-VANTAGE.md) | A phone-first app for a CISO or security executive: what needs you today, leadership rituals, the review rhythm, top risks, decisions, exceptions, tools and their value, stakeholders, team, KPIs and KRIs, playbooks and visible progress. Built from the same kit as the Life OS; a new app for any role is one file. | `./securax os` |

**Use AI safely**

| | What it does | How to open it |
|---|---|---|
| 🟢 [AI security gateway](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every AI call is checked: personal data masked, prompt injection blocked, data kept in India when it must be, and every call logged. | `./securax doctor` |
| 🟢 [Private chat](docs/securax/53-THE-TWIN.md) | A ChatGPT-style assistant that runs through the gateway, with a private local model when the data must not leave. | `./securax open` |
| 🟡 [Accurate answers without prompt engineering](docs/securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) | Every question reaches the AI with today's date and the rules a careful expert would write: never make things up, say "I don't know", flag what may have changed, show the working. A weak model says so, and a weekly check catches an AI that starts to guess. | `./securax ai honesty` |
| 🟡 [Build with open models](docs/securax/83-BUILD-WITH-OPEN-MODELS.md) | Write and fix code with strong open models through the gateway, so your ability to change the estate need not rest on a single AI subscription. Turn it on by adding its CI key; ./securax ai share shows whether it is carrying real work yet. | `./securax opencode` |
| 🟡 [Ship without Claude Code](docs/securax/98-SHIP-AND-STORE-APPS.md) | The pull-request loop, run by SecuRAX itself: open the PR from the repository's template, watch CI, and when it goes red, gather the failing logs into a brief and let autobuild fix it, one push a round. When everything is green and mergeable, merge and reset the branch. A routine runs it unattended on the always-on machine. | `./securax ship check` |

**Keep it running**

| | What it does | How to open it |
|---|---|---|
| 🟡 [The one next step](docs/securax/93-PROGRESS-YOU-CAN-SEE.md) | Lost or unsure? One command reads where you are and tells you the single next thing to do, in plain words — no list, no jargon. | `./securax next` |
| 🟢 [Prove every command works](docs/securax/117-SELFTEST.md) | One command checks the whole command surface with no side effects: every command is wired (never 'unknown command'), the code behind each one loads (a syntax error, bad import or missing file is caught), and the read-only ones actually run without throwing. It runs on every change in CI, so a command that stops working fails the build before it ever reaches you. | `./securax selftest` |
| 🟡 [Build it from a browser, on your own models](docs/securax/119-STUDIO.md) | VS Code with the Cline AI coding agent, in your browser, pointed at your own gateway - so you can build on the estate from a GUI (edit files, run commands, git, MCP connectors) without a terminal and without a paid Claude subscription. One opt-in command; it is never part of the core start, so it can never affect your running estate. Reached by name at the Command Center's /studio/ path. | `./securax studio` |
| 🟡 [Venture (is it paying its way?)](docs/securax/96-ONE-PLATFORM-MANY-PRODUCTS.md) | Break-even, payback and unit economics for the business built on the estate, counting your time as a cost: log hours, spend and revenue, set your plan, and get a structured prompt that makes an AI stress-test it. | `./securax venture` |
| 🟢 [The estate map](docs/securax/113-THE-ESTATE-MAP.md) | An interactive picture of the whole AI estate, generated from its own declarations: every component is a node coloured by what it is for, every shared platform service is a hub, and an edge joins a component to each service it is built on. Hover, click for detail, filter or search. One self-contained HTML file, online or off. | `./securax map` |
| 🟡 [The suite (built for one, ready for many)](docs/securax/97-BUILT-FOR-ONE-READY-FOR-MANY.md) | Every component is declared with the edition it starts in and the shared platform services it uses, so one person's tool can later serve an organisation of any size. Shows how ready each edition is to sell, what blocks it, and writes an honest datasheet per edition. | `./securax suite` |
| 🟡 [Names, not ports, and links that never break](docs/securax/99-NAMES-NOT-PORTS-AND-LINKS-THAT-NEVER-BREAK.md) | Every part of the estate at a name over HTTPS (hub, chat, docs, flows ...), asked once with a one-click move of the Life OS data; the site and docs on GitHub Pages until your own domain is proven live, then on it with one command; every build fails on a broken link. | `./securax site` |
| 🟢 [Go back to a working version](docs/securax/82-GO-BACK-TO-A-WORKING-VERSION.md) | Something broke? One command takes you back to the last version that worked; your edits and data are kept. | `./securax rollback` |
| 🟡 [Encrypted backups](docs/securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) | Backups that are encrypted, copied off the laptop, and proved to restore every quarter. | `./securax protect` |
| 🟡 [Storage that runs itself](docs/securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) | Every source of growth has a limit; clean-ups run every six hours, and your phone hears only when space is still short. | `./securax storage` |
| 🟢 [What broke, and why](docs/securax/27-INCIDENT-RUNBOOK.md) | Names the service that stopped and the reason, in plain words, with the fix. | `./securax why` |
| 🟡 [Crown jewels and risk](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | What SecuRAX cannot lose, how exposed each one is today, and the one thing to do next, worst first. It re-scores itself every run. | `./securax jewels` |
| 🟢 [Set it once, then forget it](docs/securax/112-SET-AND-FORGET.md) | Instead of telling you what to do, SecuRAX changes the setting once so the good path is the default and the harmful one takes effort: phone grey and quiet at night, autopay on every bill, pay-yourself-first on salary day, the costliest debt attacked first, a daily walk and a keystone habit anchored and alarmed. Twelve struggles mapped to the Wheel of Life, each one obvious change with its one-time steps, an if-then plan and a start-small floor — the elite-sport levers made structural. | `./securax environment` |
| 🟡 [Crisis and continuity plan](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Every crisis written down before it happens: how long it may stop you, how much it may lose, the steps, and safe drills that prove it. | `./securax continuity` |
| 🟢 [Ransomware-proof backups and recovery drills](docs/securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md) | Every backup first checks that your data is still readable. If ransomware got there first, the copy is quarantined, nothing clean is deleted and you are alerted. `restore latest` picks the newest clean copy, a restore twin proves it opens, and tabletop exercises test the plan. | `./securax continuity tabletop ransomware` |
| 🟡 [Many machines, one SecuRAX](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Run it on the laptop, a VPS, a Mac mini or any cloud at once: every machine holds the same data, and any one of them can stop. Each machine is an extra, never a dependency: with every other one off, this one carries on by itself (doc 90). | `./securax nodes` |
| 🟡 [The estate finds its own weak points](docs/securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md) | Every combination of your machines being off is checked: what still works, what slows down, what stops, and the fix for each single point of failure. A new weak point is pushed to your phone. | `./securax resilience` |
| 🟡 [The autopilot](docs/securax/92-THE-AUTOPILOT.md) | The estate learns from its own failures (a postmortem draft and an alert, escalated when one keeps coming back), drills itself every night where it most needs it, and warns days before disk space, backups or the AI allowance run out. | `./securax autopilot` |
| 🟡 [Stable and beta versions](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Keep the version you rely on (stable) while a new one is tried (beta), on its own address; switching is safe and never goes back. | `./securax channel` |

**Your own tools**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Your progress](docs/securax/93-PROGRESS-YOU-CAN-SEE.md) | Is SecuRAX making you better off? Your Life OS rhythm, what made the estate stronger this month, and the one next step, on your phone every Sunday — and a 'had your back' card on the Life OS home that shows, up front, what the estate quietly did for you this week (a safe encrypted copy, a healthy estate, failures turned into fixes), real events only. | `./securax progress` |
| 🟡 [Apps for Android and iOS](docs/securax/98-SHIP-AND-STORE-APPS.md) | Turn any app built from the kit, or the Life OS, into an Android and iOS project in one command: a Capacitor project that works offline from the app's own files, a Trusted Web Activity manifest for the quick Android path, and a store-readiness check. | `./securax os mobile-check vantage` |
| 🟢 [One lever a week](docs/securax/112-SET-AND-FORGET.md) | One calm nudge a week, aimed at the Wheel-of-Life area you rated lowest: the single set-and-forget change that moves it most, with its one-time steps and if-then plan, drawn from the environment catalogue and the behavioural and elite-sport research. One signal a week, where it helps you most; the opposite of a feed. It reads only the wheel you already scored, on your machine, and nothing leaves your box. | `./securax improve` |
| 🟢 [One idea a week](docs/securax/115-ONE-IDEA-A-WEEK.md) | One durable idea a week, aimed at a goal you actually set. Not news and not a feed: a bounded, curated, on-device library of high-leverage ideas (decision-making and leadership, security and AI-risk craft, mental models, money and financial independence), each paraphrased in plain words with its source named and one concrete action. It aims by your OKRs first (the lowest-progress goal whose theme it can match), then your weakest Wheel area, and never repeats an idea until its theme is exhausted. It reads only what is on your machine; nothing leaves your box. | `./securax insight` |
| 🟢 [Guiding Map](docs/securax/14-GUIDING-MAP.md) | Your daily cockpit for life and work: goals, check-ins and plans. Works offline, no AI needed. | `./securax open` |
| 🟡 [Life OS Inbox](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Capture one line; then each note becomes an action with a next step and a date, or stays a note. Reviews turn findings into actions; Google Keep notes come in too. | `./securax open` |
| 🟡 [Life papers, read for you](docs/securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Your life workbooks and private documents (policies, statements, ID scans) are read on your own machine: every open issue becomes a dated Life OS action, the vital fifth first, with calendar alarms; a missing nominee, a lapsing policy or a password left in a sheet is found for you. | `./securax lifeos import workbook` |
| 🟡 [Scan a document with your phone](docs/securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Photograph a policy, bill or letter in the Life OS Inbox; the text is read on your own phone, with no upload and offline after the first scan, and dropped into the capture box to become a dated action or a note. | `./securax open` |
| 🟡 [Understands what it sees, and spots scams](docs/securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Whatever you scan or type is understood on your own device: it is classed (a bill, a policy, an ID, an appointment), its amount and due date are pulled out so the item arrives already dated, and anything that smells like a scam — an OTP request, a 'KYC blocked' message, a UPI collect-request — is flagged in plain words with the reasons. It learns from your taps, on the phone, and nothing you teach it ever leaves it. | `./securax open` |
| 🟢 [Your AI history](docs/securax/51-YOUR-AI-HISTORY.md) | Years of chats from Claude, ChatGPT, DeepSeek or Gemini as one private library you can search. | `./securax knowledge` |
| 🟡 [Password manager](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Your own password vault (Vaultwarden) for the Bitwarden apps on laptop and phone, encrypted on your device before it is stored. | `./securax start passwords` |
| 🟡 [Sign in to AWS, Google Cloud, Azure](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | One command per cloud, nothing to install: open the link on any device, sign in, and start building. | `./securax cloud login aws` |
| 🟡 [SecuRAX on every device](docs/securax/85-USE-SECURAX-ANYWHERE.md) | Your own address on any phone, tablet or computer: sign in with Google and everything is there, synced, with the laptop off. One command sets it up. | `./securax online setup` |

This list is generated from [`features.json`](features.json); the Command Center, the website and the docs home page show the same one.
<!-- features:end -->

<!-- readme:whats-new:start -->
## What's new

**On main, in the next release:**

- [`./securax studio` — build the estate from a browser, on your own models (no Claude, no terminal)](docs/securax/119-STUDIO.md)
- [`./securax insight` — one durable idea a week, aimed at a goal you set](docs/securax/115-ONE-IDEA-A-WEEK.md)
- [`./securax selftest` — prove every command works, before you need it](docs/securax/117-SELFTEST.md)
- ["Choose who you serve" — a new core principle, baked in forever](docs/securax/116-CHOOSE-YOUR-CUSTOMER.md)
- [`./securax improve` — one lever a week, aimed at your weakest Wheel-of-Life area](docs/securax/112-SET-AND-FORGET.md)
- [An SOP for finishing work on the estate with your own open models, not Claude](docs/securax/118-BUILD-WITH-YOUR-MODELS.md)
- Sandbox: the `phone_device` journey retries a transient first-navigation flake once
- Phone alerts: signal, not noise (less alert fatigue)

**Release 0.3.0 - 2026-10-22:**

- [Life papers, read for you](docs/securax/104-LIFE-PAPERS-READ-FOR-YOU.md)
- [Nothing asked is lost](docs/securax/103-NOTHING-ASKED-IS-LOST.md)
- [Releases, small and often](docs/securax/21-VERSIONING-AND-RELEASES.md)
- [Mutation testing of the safety rails](docs/securax/101-A-SANDBOX-THAT-PROVES-MORE.md)
- [Mission control](docs/securax/102-MISSION-CONTROL.md)
- [A sandbox that proves more](docs/securax/101-A-SANDBOX-THAT-PROVES-MORE.md)
- Security round
- Roadmap sweep: dated items done today
- [One look across the estate](docs/securax/100-DESIGN-STANDARD.md)
- [A calm Command Center](docs/securax/100-DESIGN-STANDARD.md)

Everything, with details: [`CHANGELOG.md`](CHANGELOG.md).
<!-- readme:whats-new:end -->

---

> **SecuRAX** is the umbrella: one lifelong, **zero-investment-to-start**, vendor-agnostic,
> antifragile foundation that unifies AI security, AI-for-security (SecOps), a hybrid-AI brain,
> a life-OS, and governance/compliance — starting on one laptop and scaling to an MSSP, never
> rebuilt from scratch. This repository is **Pillar 1 (the AI Security Range)** and the home of
> the shared foundation.
>
> **Start here:** open [`portal/index.html`](portal/index.html) (the self-documenting command
> center — no install, just open it) and read the foundation in [`docs/securax/`](docs/securax/):
> [Overview](docs/securax/00-OVERVIEW.md) · [Principles](docs/securax/01-PRINCIPLES.md) ·
> [Architecture](docs/securax/02-ARCHITECTURE.md) ·
> [Capability Catalog](docs/securax/03-CAPABILITY-CATALOG.md) ·
<!-- readme:site:start -->
> 🌐 **Product site:** [rohan2pt0.github.io/ai-cloud-cyber-range](https://rohan2pt0.github.io/ai-cloud-cyber-range/) · 📘 **Documentation:** [rohan2pt0.github.io/ai-cloud-cyber-range/docs](https://rohan2pt0.github.io/ai-cloud-cyber-range/docs/) (source in `docs/`, built by `mkdocs.yml`). Every page is listed under [All documentation](#all-documentation) below.
<!-- readme:site:end -->
>
> **Deploy it in 3 steps:** [`DEPLOY.md`](DEPLOY.md) (install Docker → `git clone` → one command) · **Start using it:** [`GETTING-STARTED.md`](GETTING-STARTED.md) · **See it visually:** [`portal/explainer.html`](portal/explainer.html) (one-page illustrated walkthrough).

---

# AI Cloud Cyber Range (SecuRAX · Pillar 1)

A multi-cloud, defence-in-depth **AI security cyber range** for hands-on mastery of secure-AI
engineering, **AI-for-security (Agentic SOC)**, adversarial ML / red teaming, AI-SPM
(CNAPP/CSPM/DSPM), guardrail/runtime security, and AI governance — built to show each of these
practices working end to end

Runs on a Powerful laptop by default (Ollama + Docker + kind), and bursts into
**AWS + GCP + Azure** free tiers under a hard **₹2,500/month** ceiling with automated
kill-switches. Everything is code, tested, and mapped to **NIST AI RMF, ISO/IEC 42001, CSA
AICM/MAESTRO, Google SAIF, OWASP LLM & Agentic Top 10, and MITRE ATLAS**.

## What it claims, and what it does not

Every capability SecuRAX claims has a written envelope (the conditions it holds under) and a proof: a test, or a journey that runs the
real estate in CI. `./securax fitness` fails if a proof goes missing ([`governance/claims.json`](governance/claims.json), [doc 55](docs/securax/55-ENGINEERING-STANDARD.md)).

It is a **single-host** estate for one person or a small team. It is not a Slack, not highly available, not multi-region, not
load-tested beyond its measured budgets, and not independently audited. The full "not claimed" list is in the same file.

## Quick start (laptop, zero cost)
```bash
./securax up        # one command: start the whole live estate + print URLs
./securax demo      # red-team scorecard + posture scan (no cloud needed)
# or step-by-step:
./local/scripts/bootstrap-laptop.sh          # gateway + router + db + smoke test
WITH_AI=1 ./local/scripts/bootstrap-laptop.sh # also pull local models + Llama Guard
./local/scripts/kind-up.sh                    # Kubernetes plane (Kyverno + NetPol + Falco)
python3 redteam/run_attacks.py --fail-under 0.9   # adversarial-ML scorecard
./local/scripts/teardown.sh                   # stop everything (costs nothing overnight)
```

## What's inside
| Path | What it is | Why it matters |
|---|---|---|
| `apps/llm-gateway/` | OpenAI-compatible **guardrail gateway** (PEP): India-BFSI PII rails, injection/exfil/secret/canary detection, pluggable Llama Guard / Model Armor / Bedrock / Prompt Shields | secure-AI engineering, guardrails, privacy-by-design |
| `local/` | docker compose AI stack, kind cluster (audit on), **Kyverno + zero-trust NetPol + Falco/ATLAS**, bootstrap scripts | CKS, Kubernetes security, runtime detection |
| `infra/terraform/` | **AWS/GCP/Azure** modules, budget kill-switches, OIDC keyless CI, Model Armor / Content Safety | multi-cloud security architecture, FinOps-as-control |
| `policies/opa/` | conftest/OPA policies that **fail CI** on missing budgets, public buckets, disabled guardrails | policy-as-code, shift-left |
| `redteam/` | self-contained **attack suite**, promptfoo + garak configs, **AI-SPM scanner** (16 controls, CNAPP/CSPM/DSPM), **board-brief generator** | adversarial ML, AI-SPM, board-ready narratives |
| `ai-soc/` | **AI-SOC triage engine** (AI-for-security): correlate gateway+Falco+cloud telemetry → incidents, ATLAS+ATT&CK, guardrail-safe LLM summaries | agentic SecOps, autonomous detection, IR |
| `governance/` | **model registry**: inventory, risk tiers, approval gates, disallowed (shadow) models | model governance, ISO 42001, EU AI Act |
| `notebooks/` | Colab notebook: ASR with rails on/off, evasion, DPDP redaction | NIST AI 100-2, demos |
| `personal-rnd/` | **defensive** OPSEC / self-OSINT / LifeOS / FIRE tools (self-scoped) | privacy engineering, indirect-injection defence |
| `mcp/` | **MCP server** — let an AI assistant operate the estate (9 safe tools) | intelligent, hands-free control |
| `integrations/` | n8n workflows + Claude/Google/Microsoft connectivity | automation, API wiring |
| `docs/` | architecture, traceability, compliance crosswalk, cost controls, demo runbook | governance, the story you tell |
| `.github/workflows/` | DevSecOps: tests + red-team gate + SAST + secrets + SBOM + container/IaC scan | secure MLOps/LLMOps, CI/CD |

## Design principles
Secure-by-design · privacy-by-design · zero-trust · **fail-closed** · everything-as-code ·
**no single point of failure** (see `docs/architecture.md` §5).

## Documentation
- `docs/architecture.md` — reference architecture, control catalogue, resilience, threat model
- `docs/compliance-matrix.md` — NIST AI RMF / ISO 42001 / SAIF / CSA / OWASP / DPDP / RBI crosswalk
- `docs/cost-controls.md` — how it stays under ₹2,500/month
- `docs/demo-runbook.md` — a 15-minute guided walkthrough

<!-- readme:proofs:start -->
> **Proof, not claims:** 49 end-to-end journeys run the real estate (real containers, a real browser) on every merge and every night; pull requests run the ones their change can affect ([doc 68](docs/securax/68-CI-AT-AGENT-SCALE.md)).
<!-- readme:proofs:end -->

<!-- readme:docs:start -->
## All documentation

[SecuRAX — Overview](docs/securax/00-OVERVIEW.md) 🟢 · [SecuRAX — Design Principles](docs/securax/01-PRINCIPLES.md) 🟢 · [SecuRAX — Unified Architecture](docs/securax/02-ARCHITECTURE.md) 🟢 · [SecuRAX — Capability Catalog](docs/securax/03-CAPABILITY-CATALOG.md) 🟡 · [SecuRAX — Compliance & Standards Map](docs/securax/04-COMPLIANCE-MAP.md) 🟡 · [SecuRAX — Roadmap](docs/securax/05-ROADMAP.md) 🟡 · [Extending SecuRAX — how to plug in any future project](docs/securax/06-EXTENDING.md) 🟢 · [SecuRAX — Integrations & Connectivity](docs/securax/07-INTEGRATIONS.md) 🟡 · [SecuRAX — Operating Model](docs/securax/08-OPERATING-MODEL.md) 🟡 · [SecuRAX — Open-Core Model & Tiers](docs/securax/09-OPEN-CORE-TIERS.md) 🔴 · [SecuRAX — Full-Scale Mode (opt-in, turn-off-able)](docs/securax/10-FULL-STACK.md) 🟡 · [SecuRAX — Kaizen & Antifragility (the UPSC lens)](docs/securax/11-KAIZEN.md) 🟡 · [SecuRAX — Intelligent UX (the operator's lens: simple on top, disciplined underneath)](docs/securax/12-INTELLIGENT-UX.md) 🟡 · [SecuRAX — Global Intelligence (decide the community-proven way, before it commoditises)](docs/securax/13-GLOBAL-INTELLIGENCE.md) 🟢 · [SecuRAX — The Guiding Map (the life-OS cockpit)](docs/securax/14-GUIDING-MAP.md) 🟢 · [SecuRAX — Cost, models & never hitting a limit (the FinOps playbook)](docs/securax/15-COST-AND-MODELS.md) 🟢 · [SecuRAX — The agents army (stealth specialist advisors)](docs/securax/16-AGENTS.md) 🟡 · [SecuRAX — Enterprise Architecture alignment (the end-state blueprint)](docs/securax/17-ENTERPRISE-ARCHITECTURE.md) 🟡 · [SecuRAX — Future Financial Planner (sovereign, offline)](docs/securax/18-FINANCIAL-PLANNER.md) 🟢 · [Autonomous web research (the sovereign Manus / Clawbot)](docs/securax/19-AUTONOMOUS-RESEARCH.md) 🟡 · [Claude-subscription parity (the sovereign equivalents)](docs/securax/20-CLAUDE-PARITY.md) 🟡 · [Versioning & release policy](docs/securax/21-VERSIONING-AND-RELEASES.md) 🟡 · [Plugins & AI Providers](docs/securax/22-PLUGINS-AND-PROVIDERS.md) 🟢 · [Build SecuRAX without depending on Claude](docs/securax/23-BUILD-WITHOUT-CLAUDE.md) 🟡 · [Resilience & low-resource operation](docs/securax/24-RESILIENCE-AND-LOW-RESOURCE.md) 🟢 · [Fallbacks & elasticity — what happens when a piece is missing](docs/securax/25-FALLBACKS-AND-ELASTICITY.md) 🟢 · [Coverage check vs. the enterprise reference maps — and the 80/20 gaps](docs/securax/26-COVERAGE-AND-GAPS.md) 🟢 · [Incident runbook — what to do, in order](docs/securax/27-INCIDENT-RUNBOOK.md) 🟢 · [Status & traceability — every ask, what shipped, how it is proven, what is NOT done](docs/securax/28-STATUS-AND-TRACEABILITY.md) 🟢 · [Lifecycle — from a dormant seed to a multi-tenant forest (and back to sleep)](docs/securax/29-LIFECYCLE-SEED-TO-FOREST.md) 🟡 · [The purple-team loop — would anyone *know*?](docs/securax/30-PURPLE-TEAM-LOOP.md) 🟢 · [Supply-chain gate — `./securax vet`](docs/securax/31-SUPPLY-CHAIN-VET.md) 🟢 · [Powerful offline, sharp on a small machine — what we took from the most-starred repos, and what we measured](docs/securax/32-OFFLINE-AND-LOW-RESOURCE.md) 🟢 · [Fitness functions and game days — promises as numbers, resilience as rehearsal](docs/securax/33-FITNESS-AND-GAME-DAYS.md) 🟢 · [CCSP-aligned coverage (step 5)](docs/securax/34-CCSP-COVERAGE.md) 🟢 · [Regulatory gap assessment — RBI NBFC Directions 2026 and SEBI CSCRF](docs/securax/35-REGULATORY-GAP-ASSESSMENT.md) 🟡 · [Identity, incident clock, data residency](docs/securax/36-IDENTITY-INCIDENT-RESIDENCY.md) 🟢 · [Cockpit, storage growth, patching, impact](docs/securax/37-COCKPIT-STORAGE-PATCHING.md) 🟢 · [Engineering practices, research cues, and the friction audit](docs/securax/38-ENGINEERING-PRACTICES-AND-RESEARCH.md) 🟡 · [Growing from one person to many: live sync, team chat, and the scale ladder](docs/securax/39-PEOPLE-SCALE-LIVE-SYNC-CHATOPS.md) 🟡 · [Encryption in transit: HTTPS everywhere, by name, from the browser to the edge](docs/securax/40-ENCRYPTION-IN-TRANSIT.md) 🟢 · [Quantum readiness: what is protected, what is not, and what to do first](docs/securax/41-QUANTUM-READINESS.md) 🟡 · [OpenCode Go and the OpenCode terminal agent](docs/securax/42-OPENCODE-GO-AND-THE-TERMINAL-AGENT.md) 🟢 · [Look inside third-party software before you trust it (REA, sandboxed)](docs/securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) 🟢 · [The admission gate (`forge`) and the self-healing sandbox](docs/securax/44-ADMISSION-GATE-AND-SELF-HEALING-SANDBOX.md) 🟢 · [`./securax autobench`: measure each build model before you trust it](docs/securax/45-AUTOBENCH-MEASURE-YOUR-BUILD-MODELS.md) 🟢 · [Certification path: the hardest offensive and AI certifications, on 30 hours a week and ₹5 lakh a year](docs/securax/46-CERTIFICATION-PATH.md) 🔴 · [Calm mode: less input, more insight (the Guiding Map, reviewed as a user)](docs/securax/47-CALM-MODE-LESS-INPUT-MORE-INSIGHT.md) 🟢 · [The Guiding Map, freeze-ready: a quarterly system you will actually run](docs/securax/48-GUIDING-MAP-FREEZE-READY.md) 🟢 · [Career compass: choose the next job without betting the house](docs/securax/49-CAREER-COMPASS.md) 🟢 · [Reasoning budget: think less where it does not pay](docs/securax/50-REASONING-BUDGET.md) 🟡 · [Your AI history: years of chats as one library you own](docs/securax/51-YOUR-AI-HISTORY.md) 🟢 · [Automation that works on day one, and the SuperApp plan](docs/securax/52-AUTOMATION-PACK-AND-SUPERAPP-PLAN.md) 🟡 · [The Twin: a Claude-like assistant you own](docs/securax/53-THE-TWIN.md) 🟢 · [SecuRAX technical gist (for another engineer or AI assistant)](docs/securax/54-TECHNICAL-GIST.md) 🟢 · [The engineering standard: no claim without proof](docs/securax/55-ENGINEERING-STANDARD.md) 🟢 · [Pool your machines: what we took from RAMDeck, and what we did not](docs/securax/56-POOL-YOUR-MACHINES.md) 🟡 · [Compute, memory and storage: the smart way round the limits (global and Indian options)](docs/securax/57-COMPUTE-STRATEGY.md) 🟡 · [Phones over Tailscale, and a shell on the laptop from your phone](docs/securax/58-PHONES-AND-REMOTE-SHELL.md) 🟡 · [The end state, and how SecuRAX gets there](docs/securax/59-END-STATE-ARCHITECTURE.md) 🟡 · [Ship it on cyberbaba.org, and build SecuRAX with SecuRAX](docs/securax/60-SHIP-IT-AND-BUILD-WITH-SECURAX.md) 🟡 · [Run SecuRAX as a business, with a low profile](docs/securax/61-RUN-IT-AS-A-BUSINESS.md) 🟡 · [Strategy: what Cyera and the AI unicorns teach, and where SecuRAX can win](docs/securax/62-STRATEGY-LESSONS-FROM-CYERA-AND-AI-UNICORNS.md) 🟡 · [Engineering resilience audit: the backend fundamentals, checked against SecuRAX](docs/securax/63-ENGINEERING-RESILIENCE-AUDIT.md) 🟢 · [Success mantras: what the best organisations do, and where SecuRAX does it too](docs/securax/64-SUCCESS-MANTRAS.md) 🟢 · [Configuration, not code: nothing specific is hardwired](docs/securax/65-CONFIGURATION-NOT-CODE.md) 🟢 · [The BFSI control library, the navigator, and a dark cockpit](docs/securax/66-BFSI-CONTROL-LIBRARY-AND-NAVIGATOR.md) 🟢 · [Risk register, the NSCS audit baseline and national CII guidance, all linked](docs/securax/67-RISK-REGISTER-NSCS-CII.md) 🟡 · [CI at agent scale: prove what changed, not everything, every time](docs/securax/68-CI-AT-AGENT-SCALE.md) 🟡 · [Human-in-command for AI, and what the October 2026 fintech signals mean for SecuRAX](docs/securax/69-HUMAN-IN-COMMAND-AND-FINTECH-SIGNALS.md) 🟢 · [What national strategies teach a personal estate (80/20)](docs/securax/70-LESSONS-FROM-NATIONAL-STRATEGIES.md) 🟢 · [What 26 national strategies agree on, and what SecuRAX does about it](docs/securax/71-WHAT-26-NATIONAL-STRATEGIES-AGREE-ON.md) 🟡 · [Sync and backup without the laptop](docs/securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) 🟡 · [Finish setting up, and publish the site](docs/securax/73-FINISH-SETTING-UP-AND-PUBLISH-THE-SITE.md) 🟡 · [Pattern interrupt: in a heavy week, the Life OS subtracts](docs/securax/74-PATTERN-INTERRUPT.md) 🟢 · [Distribute, install, feedback: how SecuRAX reaches people and gets better](docs/securax/75-DISTRIBUTE-INSTALL-FEEDBACK.md) 🟡 · [Findings, repairs, restore, shortcuts: the best of four mature tools](docs/securax/76-FINDINGS-REPAIRS-RESTORE-SHORTCUTS.md) 🟢 · [OWASP and other global projects: what SecuRAX uses, what it adds now, what waits](docs/securax/77-OWASP-AND-GLOBAL-PROJECTS.md) 🟢 · [Crisis response kit: step in, collect properly, find what is wrong, report](docs/securax/78-CRISIS-RESPONSE-KIT.md) 🟡 · [Exercise range: live-fire cyber defence exercises](docs/securax/79-EXERCISE-RANGE.md) 🟡 · [Storage that grows with you: bounded by design, tiered, and run by itself](docs/securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) 🟡 · [The range against the market, and how it teaches: MITRE frameworks, learning paths, players and badges](docs/securax/81-RANGE-VS-THE-MARKET-AND-LEARNING.md) 🟡 · [Go back to a working version, at any time: first restore, then diagnose](docs/securax/82-GO-BACK-TO-A-WORKING-VERSION.md) 🟢 · [Build with open models: leave the Claude Code subscription without losing the rigour](docs/securax/83-BUILD-WITH-OPEN-MODELS.md) 🟡 · [Crown jewels, the crisis plan, and the foundation for scale](docs/securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) 🟡 · [Use SecuRAX from any device, like a SaaS app](docs/securax/85-USE-SECURAX-ANYWHERE.md) 🟡 · [Many machines, one SecuRAX, and the road to a lakh users](docs/securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) 🟡 · [Security review before the freeze](docs/securax/87-SECURITY-REVIEW-BEFORE-FREEZE.md) 🟡 · [Ransomware and disaster recovery, proven before shipping](docs/securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md) 🟢 · [Accurate answers without prompt engineering](docs/securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) 🟡 · [It works on whatever machine is on](docs/securax/90-WORKS-ON-WHATEVER-IS-ON.md) 🟢 · [Any machine can carry the estate, and the estate finds its own weak points](docs/securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md) 🟡 · [The autopilot: the estate learns, drills and looks ahead by itself](docs/securax/92-THE-AUTOPILOT.md) 🟡 · [Progress you can see: the point of all of it](docs/securax/93-PROGRESS-YOU-CAN-SEE.md) 🟡 · [Govern: for decision makers](docs/securax/94-GOVERN.md) 🟡 · [One kit, many apps: Vantage, the CISO's operating system](docs/securax/95-OS-KIT-VANTAGE.md) 🟡 · [One platform, many products: how the estate pays its way](docs/securax/96-ONE-PLATFORM-MANY-PRODUCTS.md) 🟡 · [Built for one, ready for many: the suite](docs/securax/97-BUILT-FOR-ONE-READY-FOR-MANY.md) 🟡 · [Leave Claude Code for good, and put the apps in the stores](docs/securax/98-SHIP-AND-STORE-APPS.md) 🟡 · [Names, not ports, and links that never break](docs/securax/99-NAMES-NOT-PORTS-AND-LINKS-THAT-NEVER-BREAK.md) 🟡

🟢 built · 🟡 partly built · 🔴 not built yet ([what the lights mean](docs/index.md#the-status-lights))
<!-- readme:docs:end -->
