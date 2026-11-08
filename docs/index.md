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

- **2026-11-06** · [Crisis coordination](securax/125-CRISIS-COORDINATION.md): A regulator or police requisition stops being a multi-week scramble: you see who owns each record and what is overdue, and hand over a complete pack on time instead of facing a show-cause for missing the deadline. `./securax crisis templates`
- **2026-11-06** · [Crisis wargame](securax/126-CRISIS-WARGAME.md): Your team practises the coordination that decides a real crisis — every week, in minutes, alone or together — and each run hands back the exact handoffs that slipped and who must drill them, so the gaps close before a real incident finds them. `./securax wargame list`
- **2026-11-06** · [Threat hunting & post-crisis DFIR](securax/127-THREAT-HUNTING-DFIR.md): After an incident you can collect and triage a suspect host in minutes with no standing infrastructure — in the same pipeline you already run — and the estate hands you a prioritised set of findings and the contain-or-recover actions to approve, instead of a blank screen and a fleet you cannot reach. `./securax hunt packs`
- **2026-11-06** · [Growth map](securax/128-GROWTH-MAP-AMOEBA.md): You never over-build and never hit a ceiling: the estate runs at exactly the size today needs, tells you in one screen what is ready to grow as you scale, and grows the safe steps itself — so one laptop and a thousand-endpoint fleet are the same system at two stages of the same life, not two products. `./securax evolve`
- **2026-10-29** · [Human-in-command tool approvals](securax/124-TOOL-APPROVALS.md): An AI agent can never move your money or act irreversibly without you saying yes to that exact action, once, on the record. `./securax approvals`

Each line names what it does, in plain words, and the one command that opens it. The light is the guide's status (what the lights mean is below).

**Practise and defend**

| | What it does | How to open it |
|---|---|---|
| 🟢 [Incident playbooks](securax/123-INCIDENT-PLAYBOOKS.md) | Run an incident-response playbook as a live, ticked checklist. Pick a scenario (ransomware, data exfiltration, an exploited zero-day), start a run, and work the ordered steps through the NIST phases — triage, contain, eradicate, recover, report, learn — each step pointing at the estate's own command that does the work (the forensic kit, the regulator clock, the fix-by register, restore). It records who did what and when, will not let you close while a critical step is open, and ends by writing a blameless postmortem seeded with the run's timeline. A starting library for a BFSI SOC; add your own scenarios as data. | `./securax playbook list` |
| 🟢 [Crisis coordination](securax/125-CRISIS-COORDINATION.md) | Coordinate a multi-agency cyber crisis and hit every agency deadline. When a regulator, a sectoral CERT or the police send a requisition — each with a short deadline and each item needing a specific record from a specific team — open it from a ready template, and every item is already assigned to its owning team. Track what is done, pending and overdue against the clock, generate the response pack (a register plus a filled cover letter) to hand over, and keep the ready documents for the moments that stall a real response: a forensic-tool policy-exception form, a chain-of-custody form, a forensic-collection SOP and a duty roster. The templates are generic data — add your own agencies, items and documents. It takes the tedious coordination off you: one command stands the whole crisis up, another names the single most urgent action, the estate auto-prepares every item it can source itself and chases the owning teams for the rest from one node (no duplicate nudges, no single point of failure), and ready crisis-communication drafts keep every channel on the same message. AI drafts; anything that leaves the building stays behind a human approval. Pairs with the regulator clock (incident) and the response checklist (playbook). | `./securax crisis templates` |
| 🟢 [Crisis wargame](securax/126-CRISIS-WARGAME.md) | Rehearse the coordination of a cyber crisis as a timed tabletop, and score it. The hard part of a real crisis is not the attack but the coordination — the right action reaching the right team in time while deadlines collide, a key person is on leave and a second hit lands mid-response — and you cannot practise that from a document. A scenario is a timeline of injects (a thing that happens, owned by a team, with an expected action and an SLA); the clock starts, each inject fires on time, you respond in free text, and the estate scores whether the right action reached the right owner in time. It then writes an after-action report: the per-inject scores, the coordination gaps (what went unanswered, what was late, what was incomplete), and a specific, owned improvement action for each — which you can turn into standing lessons in one line. Worst-cases are built in by design: colliding agency deadlines, the one person who knows the system unreachable, a node that holds the clock going down. Scoring is deterministic (a keyword rubric against each inject's expected action plus timeliness against its SLA), so it runs the same offline and in CI; when a gateway is configured it also asks a model to grade the free text and to play the inject's sender under pressure, inheriting the gateway's rails and audit trail. The scenarios are generic data — add your own. Pairs with the real coordination (crisis) and the technical tabletop (continuity). | `./securax wargame list` |
| 🟢 [Threat hunting & post-crisis DFIR](securax/127-THREAT-HUNTING-DFIR.md) | After a cyber crisis the question is where the foothold is, how far it spread, and what was left to get back in. This drives Velociraptor — the Apache-2.0 endpoint engine — to collect and hunt, in two modes from the same packs: a single self-contained OFFLINE COLLECTOR with no server, the minimal mode that fits a DevSecOps pipeline or one suspect host; and a fleet of server + clients at mass scale for many teams. It ships NO proprietary forensic binary: the manifest declares each tool (Velociraptor, System Informer, and — gated behind a recorded EULA acceptance — KAPE, FTK Imager, Autoruns, Resource Hacker) with its licence, whether it may be redistributed, its official source and a pinned hash, and fetches it on use or from your internal mirror; KAPE-style triage uses Velociraptor's open Windows.KapeFiles.Targets, so there is no Kroll licensing exposure. A hunt pack (data, one per scenario — ransomware aftermath, payment-fraud persistence, lateral-movement / data-breach sweep, service outage, insider misuse, supply-chain compromise, quick triage) names the artifacts to collect, deterministic rules that score the collected output into prioritised findings, and turns those findings into an ordered, approve-gated remediation plan (only the actions whose findings fired, most-supported first; an AI agent drafts the narrative order through the gateway when one is up), which hunt report captures to feed the crisis pack and the lessons. The estate auto-prepares the matching hunt when a crisis is open (from one node, no duplicate nudges, no single point of failure), an AI agent drafts a second-opinion triage through the governed gateway when one is up, and every action that TOUCHES an endpoint — isolate a host, capture memory, rotate credentials, remove persistence — stays behind ./securax approve: a single-use, time-boxed, audited human yes. Pairs with crisis (coordination), incident (the clock) and respond (the evidence kit). | `./securax hunt packs` |
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
| 🟢 [Human-in-command tool approvals](securax/124-TOOL-APPROVALS.md) | When an AI agent asks to take a consequential action — move money, send a wire, email out — the gateway does not just block it: it holds the exact call for a human. `./securax approvals` lists what is waiting; `./securax approve <id>` grants a single-use, ten-minute approval scoped to that exact tool and arguments, and only then does the agent's next identical call go through. A different argument, a second attempt, or an expired grant is blocked again, and three blocked calls in a row stop the agent and ask for a person. Every grant is written to the tamper-evident audit chain. The dangerous tools (shell, delete, drop) stay denied outright. | `./securax approvals` |
| 🟢 [Saved prompts](securax/122-CATCHUP-AND-PROMPTS.md) | Reusable, parametrised prompts you can call by name — a daily stand-up, a decision aid, a board-ready threat brief, a plain-English rewrite — with {date}, {owner} and the words you type filled in automatically. Ask any advisor with one: `./securax ask <agent> --prompt NAME`. Kept generic and private (no personal or employer data in the repository); add your own. | `./securax ask productivity --prompt standup` |
| 🟢 [AI security gateway](securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every AI call is checked: personal data masked, prompt injection blocked, data kept in India when it must be, and every call logged. | `./securax doctor` |
| 🟢 [Private chat](securax/53-THE-TWIN.md) | A ChatGPT-style assistant that runs through the gateway, with a private local model when the data must not leave. | `./securax open` |
| 🟡 [Accurate answers without prompt engineering](securax/89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) | Every question reaches the AI with today's date and the rules a careful expert would write: never make things up, say "I don't know", flag what may have changed, show the working. A weak model says so, and a weekly check catches an AI that starts to guess. | `./securax ai honesty` |
| 🟡 [Build with open models](securax/83-BUILD-WITH-OPEN-MODELS.md) | Write and fix code with strong open models through the gateway, so your ability to change the estate need not rest on a single AI subscription. Turn it on by adding its CI key; ./securax ai share shows whether it is carrying real work yet. | `./securax opencode` |
| 🟡 [Ship without Claude Code](securax/98-SHIP-AND-STORE-APPS.md) | The pull-request loop, run by SecuRAX itself: open the PR from the repository's template, watch CI, and when it goes red, gather the failing logs into a brief and let autobuild fix it, one push a round. When everything is green and mergeable, merge and reset the branch. A routine runs it unattended on the always-on machine. | `./securax ship check` |

**Keep it running**

| | What it does | How to open it |
|---|---|---|
| 🟢 [Growth map](securax/128-GROWTH-MAP-AMOEBA.md) | The estate is built to start as an amoeba — the simplest living thing that helps today, one person, no server, offline — and carry the DNA to become an enterprise organism, with the dormant rail already built into each capability so it can grow when conditions call for it. This is where you see and steer that growth. It reads the estate's own conditions locally (how many nodes are live, whether a model gateway, a fleet server, an internal tool mirror or more than one team is present, and stress signals like load or a lost node) and, for each capability, shows the stage it is in, whether conditions now favour the next stage, and the exact rail to pull — ransomware hunting that is an offline collector today and a governed fleet when there are endpoints and teams; a crisis that is one responder today and per-team owners with SLA timers when there are teams and nodes; a gateway that is a local model today and a metered multi-tenant service when the organisation scales. The safe, in-box steps the estate can grow by itself; anything that provisions infrastructure, costs money or touches endpoints is proposed for your approval, never done silently. Nature is the architect: the organism grows only as conditions warrant, and falls back to the amoeba form under stress so no scaled-up part is ever a single point of failure. The growth map is data (governance/evolution.json); fitness evolution-declared makes every enterprise-capable feature ship its rail. | `./securax evolve` |
| 🟡 [The one next step](securax/93-PROGRESS-YOU-CAN-SEE.md) | Lost or unsure? One command reads where you are and tells you the single next thing to do, in plain words — no list, no jargon. | `./securax next` |
| 🟢 [Prove every command works](securax/117-SELFTEST.md) | One command checks the whole command surface with no side effects: every command is wired (never 'unknown command'), the code behind each one loads (a syntax error, bad import or missing file is caught), and the read-only ones actually run without throwing. It runs on every change in CI, so a command that stops working fails the build before it ever reaches you. | `./securax selftest` |
| 🟡 [Build it from a browser, on your own models](securax/119-STUDIO.md) | VS Code with the Cline AI coding agent, in your browser, pointed at your own gateway - so you can build on the estate from a GUI (edit files, run commands, git, MCP connectors) without a terminal and without a paid Claude subscription. One opt-in command; it is never part of the core start, so it can never affect your running estate. Reached by name at the Command Center's /studio/ path. | `./securax studio` |
| 🟡 [Venture (is it paying its way?)](securax/96-ONE-PLATFORM-MANY-PRODUCTS.md) | Break-even, payback and unit economics for the business built on the estate, counting your time as a cost: log hours, spend and revenue, set your plan, and get a structured prompt that makes an AI stress-test it. | `./securax venture` |
| 🟢 [The estate map](securax/113-THE-ESTATE-MAP.md) | An interactive picture of the whole AI estate, generated from its own declarations: every component is a node coloured by what it is for, every shared platform service is a hub, and an edge joins a component to each service it is built on. Hover, click for detail, filter or search. One self-contained HTML file, online or off. | `./securax map` |
| 🟡 [The suite (built for one, ready for many)](securax/97-BUILT-FOR-ONE-READY-FOR-MANY.md) | Every component is declared with the edition it starts in and the shared platform services it uses, so one person's tool can later serve an organisation of any size. Shows how ready each edition is to sell, what blocks it, and writes an honest datasheet per edition. | `./securax suite` |
| 🟡 [Names, not ports, and links that never break](securax/99-NAMES-NOT-PORTS-AND-LINKS-THAT-NEVER-BREAK.md) | Every part of the estate at a name over HTTPS (hub, chat, docs, flows ...), asked once with a one-click move of the Life OS data; the site and docs on GitHub Pages until your own domain is proven live, then on it with one command; every build fails on a broken link. | `./securax site` |
| 🟢 [Go back to a working version](securax/82-GO-BACK-TO-A-WORKING-VERSION.md) | Something broke? One command takes you back to the last version that worked; your edits and data are kept. | `./securax rollback` |
| 🟡 [Encrypted backups](securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) | Backups that are encrypted, copied off the laptop, and proved to restore every quarter. | `./securax protect` |
| 🟡 [Storage that runs itself](securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) | Every source of growth has a limit; clean-ups run every six hours, and your phone hears only when space is still short. | `./securax storage` |
| 🟢 [What broke, and why](securax/27-INCIDENT-RUNBOOK.md) | Names the service that stopped and the reason, in plain words, with the fix. | `./securax why` |
| 🟡 [Crown jewels and risk](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | What SecuRAX cannot lose, how exposed each one is today, and the one thing to do next, worst first. It re-scores itself every run. | `./securax jewels` |
| 🟢 [Set it once, then forget it](securax/112-SET-AND-FORGET.md) | Instead of telling you what to do, SecuRAX changes the setting once so the good path is the default and the harmful one takes effort: phone grey and quiet at night, autopay on every bill, pay-yourself-first on salary day, the costliest debt attacked first, a daily walk and a keystone habit anchored and alarmed. Twelve struggles mapped to the Wheel of Life, each one obvious change with its one-time steps, an if-then plan and a start-small floor — the elite-sport levers made structural. | `./securax environment` |
| 🟡 [Crisis and continuity plan](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Every crisis written down before it happens: how long it may stop you, how much it may lose, the steps, and safe drills that prove it. | `./securax continuity` |
| 🟢 [Ransomware-proof backups and recovery drills](securax/88-RANSOMWARE-AND-DISASTER-RECOVERY-PROVEN.md) | Every backup first checks that your data is still readable. If ransomware got there first, the copy is quarantined, nothing clean is deleted and you are alerted. `restore latest` picks the newest clean copy, a restore twin proves it opens, and tabletop exercises test the plan. | `./securax continuity tabletop ransomware` |
| 🟡 [Many machines, one SecuRAX](securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Run it on the laptop, a VPS, a Mac mini or any cloud at once: every machine holds the same data, and any one of them can stop. Each machine is an extra, never a dependency: with every other one off, this one carries on by itself (doc 90). | `./securax nodes` |
| 🟡 [The estate finds its own weak points](securax/91-ANY-MACHINE-CAN-CARRY-THE-ESTATE.md) | Every combination of your machines being off is checked: what still works, what slows down, what stops, and the fix for each single point of failure. A new weak point is pushed to your phone. | `./securax resilience` |
| 🟡 [The autopilot](securax/92-THE-AUTOPILOT.md) | The estate learns from its own failures (a postmortem draft and an alert, escalated when one keeps coming back), drills itself every night where it most needs it, and warns days before disk space, backups or the AI allowance run out. | `./securax autopilot` |
| 🟡 [Stable and beta versions](securax/86-MANY-NODES-AND-THE-ROAD-TO-SCALE.md) | Keep the version you rely on (stable) while a new one is tried (beta), on its own address; switching is safe and never goes back. | `./securax channel` |

**Your own tools**

| | What it does | How to open it |
|---|---|---|
| 🟢 [Catch me up](securax/122-CATCHUP-AND-PROMPTS.md) | One short brief of what needs YOU right now, from your own estate: the things to act on today (an overdue finding, an overdue risk treatment, a failing routine, a red cockpit reading), your one next step, and your Life OS rhythm. A model summarises it through the gateway when one is up (so it inherits the rails, the allowance and the audit trail); with no gateway it shows the same facts plainly. The 'act today' list is the ground truth and is always shown, so a summary can never hide a real overdue item. | `./securax catchup` |
| 🟡 [Your progress](securax/93-PROGRESS-YOU-CAN-SEE.md) | Is SecuRAX making you better off? Your Life OS rhythm, what made the estate stronger this month, and the one next step, on your phone every Sunday — and a 'had your back' card on the Life OS home that shows, up front, what the estate quietly did for you this week (a safe encrypted copy, a healthy estate, failures turned into fixes), real events only. | `./securax progress` |
| 🟡 [Apps for Android and iOS](securax/98-SHIP-AND-STORE-APPS.md) | Turn any app built from the kit, or the Life OS, into an Android and iOS project in one command: a Capacitor project that works offline from the app's own files, a Trusted Web Activity manifest for the quick Android path, and a store-readiness check. | `./securax os mobile-check vantage` |
| 🟢 [One lever a week](securax/112-SET-AND-FORGET.md) | One calm nudge a week, aimed at the Wheel-of-Life area you rated lowest: the single set-and-forget change that moves it most, with its one-time steps and if-then plan, drawn from the environment catalogue and the behavioural and elite-sport research. One signal a week, where it helps you most; the opposite of a feed. It reads only the wheel you already scored, on your machine, and nothing leaves your box. | `./securax improve` |
| 🟢 [One idea a week](securax/115-ONE-IDEA-A-WEEK.md) | One durable idea a week, aimed at a goal you actually set. Not news and not a feed: a bounded, curated, on-device library of high-leverage ideas (decision-making and leadership, security and AI-risk craft, mental models, money and financial independence), each paraphrased in plain words with its source named and one concrete action. It aims by your OKRs first (the lowest-progress goal whose theme it can match), then your weakest Wheel area, and never repeats an idea until its theme is exhausted. It reads only what is on your machine; nothing leaves your box. | `./securax insight` |
| 🟢 [Guiding Map](securax/14-GUIDING-MAP.md) | Your daily cockpit for life and work: goals, check-ins and plans. Works offline, no AI needed. It is also published with the product site, so it opens and installs on every device even with all your own machines off (doc 130). A hosted Command Center door finds whichever of your machines is up and opens it, so the front door needs no machine either (doc 131). | `./securax open` |
| 🟡 [Life OS Inbox](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Capture one line; then each note becomes an action with a next step and a date, or stays a note. Reviews turn findings into actions; Google Keep notes come in too. | `./securax open` |
| 🟡 [Life papers, read for you](securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Your life workbooks and private documents (policies, statements, ID scans) are read on your own machine: every open issue becomes a dated Life OS action, the vital fifth first, with calendar alarms; a missing nominee, a lapsing policy or a password left in a sheet is found for you. | `./securax lifeos import workbook` |
| 🟡 [Scan a document with your phone](securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Photograph a policy, bill or letter in the Life OS Inbox; the text is read on your own phone, with no upload and offline after the first scan, and dropped into the capture box to become a dated action or a note. | `./securax open` |
| 🟡 [Understands what it sees, and spots scams](securax/104-LIFE-PAPERS-READ-FOR-YOU.md) | Whatever you scan or type is understood on your own device: it is classed (a bill, a policy, an ID, an appointment), its amount and due date are pulled out so the item arrives already dated, and anything that smells like a scam — an OTP request, a 'KYC blocked' message, a UPI collect-request — is flagged in plain words with the reasons. It learns from your taps, on the phone, and nothing you teach it ever leaves it. | `./securax open` |
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
