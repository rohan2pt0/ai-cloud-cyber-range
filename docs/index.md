---
hide: [navigation, toc]
---

# SecuRAX documentation

**Your own AI estate, on your own machine.** It brings chat, a digital twin, a life cockpit, private documents and
automation behind one guarded gateway. Private data stays local, cloud models are optional, and every claim is backed
by a test.

<!-- features:start -->
## Everything SecuRAX can do

### New in the estate

The latest additions, newest first (the Command Center marks each one New for 30 days):

- **2026-10-23** · [The one next step](securax/93-PROGRESS-YOU-CAN-SEE.md): You never have to learn 123 commands to be better off: one command always points to the next thing. `./securax next`
- **2026-10-23** · [The estate map](securax/113-THE-ESTATE-MAP.md): You see the whole estate and how it hangs together at a glance, instead of reading a list of 43 things. `./securax map`
- **2026-10-23** · [Adversary ledger](securax/30-PURPLE-TEAM-LOOP.md): A bug-bounty finding becomes the last of its kind: the estate gets stronger from every attacker, not just safer on paper. `./securax adversary`
- **2026-10-23** · [Set it once, then forget it](securax/112-SET-AND-FORGET.md): The right thing happens without willpower, because your phone and accounts are set up to make it the default — nothing to remember. `./securax environment`
- **2026-10-22** · [Readiness for any regulation](securax/106-WHO-SECURAX-IS-FOR.md): A Board-ready answer to "where do we stand on the Directions?", with proof, instead of a consultant's spreadsheet that dates in a week. `./securax readiness demo`

Each line names what it does, in plain words, and the one command that opens it. The light is the guide's status (what the lights mean is below).

**Practise and defend**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Cyber range](securax/79-EXERCISE-RANGE.md) | Practise defending real-looking systems against a live red team, with scoring, judging and MITRE ATT&CK, D3FEND and ATLAS learning paths. | `./securax exercise` |
| 🟡 [Crisis response kit](securax/78-CRISIS-RESPONSE-KIT.md) | Step into an incident: collect evidence properly, find what is wrong, and draft the reports. | `./securax respond` |
| 🟢 [Purple-team loop](securax/30-PURPLE-TEAM-LOOP.md) | Attack your own AI channel, check that the attack was detected, and keep the evidence. | `./securax purple` |
| 🟢 [Adversary ledger](securax/30-PURPLE-TEAM-LOOP.md) | Turn every bounty or red-team finding into a purple probe, a lesson and a drill, and prove it stayed closed. | `./securax adversary` |
| 🟢 [Check software before you trust it](securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) | Look inside a third-party package or file, in a sandbox, and see what a new version can do that the old one could not. | `./securax inspect` |

**Comply and govern**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Readiness for any regulation](securax/106-WHO-SECURAX-IS-FOR.md) | Where your organisation stands on any regulation SecuRAX maps (RBI NBFC directions 2026, SEBI CSCRF, UK CAF, NIST AI 600-1 and more): only your chapter's or category's requirements, each marked with evidence, owner and date; the vital few gaps; VA, PT, IS audit and CISO-to-Board dates; a board pack and an auditor's sheet, kept on your machine. | `./securax readiness demo` |
| 🟢 [BFSI control matrix](securax/66-BFSI-CONTROL-LIBRARY-AND-NAVIGATOR.md) | Every Indian BFSI cyber obligation as one matrix: what applies to you, what is proven, and what to close next. Works with no file from you. | `./securax go` |
| 🟢 [Regulator incident clock](securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every applicable regulator's reporting deadline for an incident, counting down, with the drafts ready. | `./securax incident` |
| 🟡 [Regulatory gap maps](securax/35-REGULATORY-GAP-ASSESSMENT.md) | Requirement-by-requirement maps (RBI, SEBI CSCRF, NIST AI 600-1, post-quantum and more) with the evidence for each, checked on every change. | `./securax comply` |
| 🟡 [Risk register](securax/67-RISK-REGISTER-NSCS-CII.md) | Your risks with owners and dates, linked to the controls that treat them, with an overdue lamp. | `./securax risks` |
| 🟢 [Cockpit](securax/37-COCKPIT-STORAGE-PATCHING.md) | One page: what is at risk, what to do next, and the trends. Lamps light only when something needs you. | `./securax cockpit` |
| 🟡 [Govern (for decision makers)](securax/94-GOVERN.md) | Where the organisation stands on governance, people, process and technology; the minimum basic and the highest possible; for each gap the 5W1H and an indicative budget; the team you need; a one-page Board report; and a pack of ready policies, SOPs, registers and an executive deck. | `./securax govern` |
| 🟡 [Vantage (the CISO's operating system)](securax/95-OS-KIT-VANTAGE.md) | A phone-first app for a CISO or security executive: what needs you today, leadership rituals, the review rhythm, top risks, decisions, exceptions, tools and their value, stakeholders, team, KPIs and KRIs, playbooks and visible progress. Built from the same kit as the Life OS; a new app for any role is one file. | `./securax os` |

**Use AI safely**

| | What it does | How to open it |
|---|---|---|
| 🟢 [AI security gateway](securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every AI call is checked: personal data masked, prompt injection blocked, data kept in India when it must be, and every call logged. | `./securax doctor` |
| 🟢 [Private chat](securax/53-THE-TWIN.md) | A ChatGPT-style assistant that runs through the gateway, with a private local model when the data must not leave. | `./securax open` |
| 🟡 [Accurate answers without prompt engineering](securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) | Every question reaches the AI with today's date and the rules a careful expert would write: never make things up, say "I don't know", flag what may have changed, show the working. A weak model says so, and a weekly check catches an AI that starts to guess. | `./securax ai honesty` |
| 🟡 [Build with open models](securax/83-BUILD-WITH-OPEN-MODELS.md) | Write and fix code with strong open models through the gateway, so your ability to change the estate need not rest on a single AI subscription. Turn it on by adding its CI key; ./securax ai share shows whether it is carrying real work yet. | `./securax opencode` |
| 🟡 [Ship without Claude Code](securax/98-SHIP-AND-STORE-APPS.md) | The pull-request loop, run by SecuRAX itself: open the PR from the repository's template, watch CI, and when it goes red, gather the failing logs into a brief and let autobuild fix it, one push a round. When everything is green and mergeable, merge and reset the branch. A routine runs it unattended on the always-on machine. | `./securax ship check` |

**Keep it running**

| | What it does | How to open it |
|---|---|---|
| 🟡 [The one next step](securax/93-PROGRESS-YOU-CAN-SEE.md) | Lost or unsure? One command reads where you are and tells you the single next thing to do, in plain words — no list, no jargon. | `./securax next` |
| 🟡 [Venture (is it paying its way?)](securax/96-ONE-PLATFORM-MANY-PRODUCTS.md) | Break-even, payback and unit economics for the business built on the estate, counting your time as a cost: log hours, spend and revenue, set your plan, and get a structured prompt that makes an AI stress-test it. | `./securax venture` |
| 🟢 [The estate map](securax/113-THE-ESTATE-MAP.md) | An interactive picture of the whole AI estate, generated from its own declarations: every component is a node coloured by what it is for, every shared platform service is a hub, and an edge joins a component to each service it is built on. Hover, click for detail, filter or search. One self-contained HTML file, online or off. | `./securax map` |
| 🟡 [The suite (built for one, ready for many)](securax/97-BUILT-FOR-ONE-READY-FOR-MANY.md) | Every component is declared with the edition it starts in and the shared platform services it uses, so one person's tool can later serve an organisation of any size. Shows how ready each edition is to sell, what blocks it, and writes an honest datasheet per edition. | `./securax suite` |
| 🟡 [Names, not ports, and links that never break](securax/99-NAMES-NOT-PORTS-AND-LINKS-THAT-NEVER-BREAK.md) | Every part of the estate at a name over HTTPS (hub, chat, docs, flows ...), asked once with a one-click move of the Life OS data; the site and docs on GitHub Pages until your own domain is proven live, then on it with one command; every build fails on a broken link. | `./securax site` |
| 🟢 [Go back to a working version](securax/82-GO-BACK-TO-A-WORKING-VERSION.md) | Something broke? One command takes you back to the last version that worked; your edits and data are kept. | `./securax rollback` |
| 🟡 [Encrypted backups](securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) | Backups that are encrypted, copied off the laptop, and proved to restore every quarter. | `./securax protect` |
| 🟡 [Storage that runs itself](securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) | Every source of growth has a limit; clean-ups run every six hours, and your phone hears only when space is still short. | `./securax storage` |
| 🟢 [What broke, and why](securax/27-INCIDENT-RUNBOOK.md) | Names the service that stopped and the reason, in plain words, with the fix. | `./securax why` |
| 🟡 [Crown jewels and risk](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | What SecuRAX cannot lose, how exposed each one is today, and the one thing to do next, worst first. It re-scores itself every run. | `./securax jewels` |
| 🟢 [Set it once, then forget it](securax/112-SET-AND-FORGET.md) | Instead of telling you what to do, SecuRAX changes the setting once so the good path is the default and the harmful one takes effort: phone grey and quiet at night, autopay on every bill, pay-yourself-first on salary day, the costliest debt attacked first, a keystone habit anchored and alarmed. Each struggle becomes one obvious change with its one-time steps. | `./securax environment` |
| 🟡 [Crisis and continuity plan](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Every crisis written down before it happens: how long it may stop you, how much it may lose, the steps, and safe drills that prove it. | `./securax continuity` |
| 🟢 [Ransomware-proof backups and recovery drills](securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md) | Every backup first checks that your data is still readable. If ransomware got there first, the copy is quarantined, nothing clean is deleted and you are alerted. `restore latest` picks the newest clean copy, a restore twin proves it opens, and tabletop exercises test the plan. | `./securax continuity tabletop ransomware` |
| 🟡 [Many machines, one SecuRAX](securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Run it on the laptop, a VPS, a Mac mini or any cloud at once: every machine holds the same data, and any one of them can stop. Each machine is an extra, never a dependency: with every other one off, this one carries on by itself (doc 90). | `./securax nodes` |
| 🟡 [The estate finds its own weak points](securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md) | Every combination of your machines being off is checked: what still works, what slows down, what stops, and the fix for each single point of failure. A new weak point is pushed to your phone. | `./securax resilience` |
| 🟡 [The autopilot](securax/92-THE-AUTOPILOT.md) | The estate learns from its own failures (a postmortem draft and an alert, escalated when one keeps coming back), drills itself every night where it most needs it, and warns days before disk space, backups or the AI allowance run out. | `./securax autopilot` |
| 🟡 [Stable and beta versions](securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Keep the version you rely on (stable) while a new one is tried (beta), on its own address; switching is safe and never goes back. | `./securax channel` |

**Your own tools**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Your progress](securax/93-PROGRESS-YOU-CAN-SEE.md) | Is SecuRAX making you better off? Your Life OS rhythm, what made the estate stronger this month, and the one next step, on your phone every Sunday. | `./securax progress` |
| 🟡 [Apps for Android and iOS](securax/98-SHIP-AND-STORE-APPS.md) | Turn any app built from the kit, or the Life OS, into an Android and iOS project in one command: a Capacitor project that works offline from the app's own files, a Trusted Web Activity manifest for the quick Android path, and a store-readiness check. | `./securax os mobile-check vantage` |
| 🟢 [Guiding Map](securax/14-GUIDING-MAP.md) | Your daily cockpit for life and work: goals, check-ins and plans. Works offline, no AI needed. | `./securax open` |
| 🟡 [Life OS Inbox](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Capture one line; then each note becomes an action with a next step and a date, or stays a note. Reviews turn findings into actions; Google Keep notes come in too. | `./securax open` |
| 🟡 [Life papers, read for you](securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Your life workbooks and private documents (policies, statements, ID scans) are read on your own machine: every open issue becomes a dated Life OS action, the vital fifth first, with calendar alarms; a missing nominee, a lapsing policy or a password left in a sheet is found for you. | `./securax lifeos import workbook` |
| 🟢 [Your AI history](securax/51-YOUR-AI-HISTORY.md) | Years of chats from Claude, ChatGPT, DeepSeek or Gemini as one private library you can search. | `./securax knowledge` |
| 🟡 [Password manager](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Your own password vault (Vaultwarden) for the Bitwarden apps on laptop and phone, encrypted on your device before it is stored. | `./securax start passwords` |
| 🟡 [Sign in to AWS, Google Cloud, Azure](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | One command per cloud, nothing to install: open the link on any device, sign in, and start building. | `./securax cloud login aws` |
| 🟡 [SecuRAX on every device](securax/85-USE-SECURAX-ANYWHERE.md) | Your own address on any phone, tablet or computer: sign in with Google and everything is there, synced, with the laptop off. One command sets it up. | `./securax online setup` |
<!-- features:end -->

<div class="grid cards" markdown>

-   :material-rocket-launch: **Get started**

    ---

    Install, start, and get a real chat answer in about 30 minutes on Windows (WSL), macOS or Linux.

    [:octicons-arrow-right-24: Quickstart](get-started/quickstart.md)

-   :material-cellphone-link: **Phones and tablets**

    ---

    One private address for the app, Ask, sync and Chat over Tailscale, plus a secure shell from your phone.

    [:octicons-arrow-right-24: Phones and remote shell](securax/58-PHONES-AND-REMOTE-SHELL.md)

-   :material-robot-happy: **The Twin**

    ---

    A Claude-like assistant that remembers you, searches the web and reads your handbooks, with a private mode
    that stays local.

    [:octicons-arrow-right-24: The Twin](securax/53-THE-TWIN.md)

-   :material-map-marker-path: **Where it is going**

    ---

    The enterprise end state, with a light on every box and the build order from easy to hard.

    [:octicons-arrow-right-24: End-state map](securax/59-END-STATE-ARCHITECTURE.md)

-   :material-shield-lock: **Security and compliance**

    ---

    Guardrails, data residency (India), encryption, supply-chain vetting, and maps to RBI, SEBI CSCRF and NIST AI 600-1.

    [:octicons-arrow-right-24: Capability catalog](securax/03-CAPABILITY-CATALOG.md)

-   :material-console: **Command reference**

    ---

    Every `./securax` command, generated from the CLI itself, so it never drifts.

    [:octicons-arrow-right-24: Commands](reference/cli.md)

-   :material-lifebuoy: **Troubleshooting**

    ---

    Symptom, cause, fix. Built from real installs.

    [:octicons-arrow-right-24: Troubleshooting](troubleshooting.md)

</div>

## The status lights

Every page starts with a light, so you always know whether you are reading about something real:

| Light | Means | Proof |
|---|---|---|
| 🟢 **Built** | works today | an automated test or a sandbox journey that runs the real estate in CI |
| 🟡 **Partly built** | some of it works, or it works but is not yet proven end to end | the page says which part |
| 🔴 **Not built yet** | a design, a plan, or a deliberate non-goal | – |

The lights come from one file, `docs/status.yml`, and CI fails if a page and that file disagree. The
[end-state map](securax/59-END-STATE-ARCHITECTURE.md) gives a light to every box of the enterprise architecture SecuRAX
is heading for, with the order to build them in, from easy to hard.

## How the docs are organised

| Section | Use it when you want to… |
|---|---|
| **Get started** | install and use SecuRAX day to day |
| **How-to guides** | do one task: add a provider, import your AI history, set up alerts |
| **Apps** | learn the Guiding Map, financial planner, career compass and cockpit |
| **Concepts** | understand why it is built this way: architecture, cost, resilience, the engineering standard |
| **Security and compliance** | review controls, evidence and regulatory mappings |
| **Reference** | look up commands, the technical gist, status, roadmap and changelog |

!!! note "What SecuRAX does not claim"
    No high availability, no multi-region, no independent audit or certification yet. See the
    [engineering standard](securax/55-ENGINEERING-STANDARD.md#4-what-securax-does-not-claim).
