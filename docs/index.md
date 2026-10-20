---
hide: [navigation, toc]
---

# SecuRAX documentation

**Your own AI estate, on your own machine.** It brings chat, a digital twin, a life cockpit, private documents and
automation behind one guarded gateway. Private data stays local, cloud models are optional, and every claim is backed
by a test.

<!-- features:start -->
## Everything SecuRAX can do

Each line names what it does, in plain words, and the one command that opens it. The light is the guide's status (what the lights mean is below).

**Practise and defend**

| | What it does | How to open it |
|---|---|---|
| 🟡 [Cyber range](securax/79-EXERCISE-RANGE.md) | Practise defending real-looking systems against a live red team, with scoring, judging and MITRE ATT&CK, D3FEND and ATLAS learning paths. | `./securax exercise` |
| 🟡 [Crisis response kit](securax/78-CRISIS-RESPONSE-KIT.md) | Step into an incident: collect evidence properly, find what is wrong, and draft the reports. | `./securax respond` |
| 🟢 [Purple-team loop](securax/30-PURPLE-TEAM-LOOP.md) | Attack your own AI channel, check that the attack was detected, and keep the evidence. | `./securax purple` |
| 🟢 [Check software before you trust it](securax/43-INSPECT-THIRD-PARTY-SOFTWARE.md) | Look inside a third-party package or file, in a sandbox, and see what a new version can do that the old one could not. | `./securax inspect` |

**Comply and govern**

| | What it does | How to open it |
|---|---|---|
| 🟢 [BFSI control matrix](securax/66-BFSI-CONTROL-LIBRARY-AND-NAVIGATOR.md) | Every Indian BFSI cyber obligation as one matrix: what applies to you, what is proven, and what to close next. Works with no file from you. | `./securax go` |
| 🟢 [Regulator incident clock](securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every applicable regulator's reporting deadline for an incident, counting down, with the drafts ready. | `./securax incident` |
| 🟡 [Regulatory gap maps](securax/35-REGULATORY-GAP-ASSESSMENT.md) | Requirement-by-requirement maps (RBI, SEBI CSCRF, NIST AI 600-1, post-quantum and more) with the evidence for each, checked on every change. | `./securax comply` |
| 🟡 [Risk register](securax/67-RISK-REGISTER-NSCS-CII.md) | Your risks with owners and dates, linked to the controls that treat them, with an overdue lamp. | `./securax risks` |
| 🟢 [Cockpit](securax/37-COCKPIT-STORAGE-PATCHING.md) | One page: what is at risk, what to do next, and the trends. Lamps light only when something needs you. | `./securax cockpit` |

**Use AI safely**

| | What it does | How to open it |
|---|---|---|
| 🟢 [AI security gateway](securax/36-IDENTITY-INCIDENT-RESIDENCY.md) | Every AI call is checked: personal data masked, prompt injection blocked, data kept in India when it must be, and every call logged. | `./securax doctor` |
| 🟢 [Private chat](securax/53-THE-TWIN.md) | A ChatGPT-style assistant that runs through the gateway, with a private local model when the data must not leave. | `./securax open` |
| 🟡 [Build with open models](securax/83-BUILD-WITH-OPEN-MODELS.md) | Write and fix code with strong open models through the gateway, so no single AI subscription or its limits can stop the work. | `./securax opencode` |

**Keep it running**

| | What it does | How to open it |
|---|---|---|
| 🟢 [Go back to a working version](securax/82-GO-BACK-TO-A-WORKING-VERSION.md) | Something broke? One command takes you back to the last version that worked; your edits and data are kept. | `./securax rollback` |
| 🟡 [Encrypted backups](securax/72-SYNC-AND-BACKUP-WITHOUT-THE-LAPTOP.md) | Backups that are encrypted, copied off the laptop, and proved to restore every quarter. | `./securax protect` |
| 🟡 [Storage that runs itself](securax/80-STORAGE-THAT-GROWS-WITH-YOU.md) | Every source of growth has a limit; clean-ups run every six hours, and your phone hears only when space is still short. | `./securax storage` |
| 🟢 [What broke, and why](securax/27-INCIDENT-RUNBOOK.md) | Names the service that stopped and the reason, in plain words, with the fix. | `./securax why` |
| 🟡 [Crown jewels and risk](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | What SecuRAX cannot lose, how exposed each one is today, and the one thing to do next, worst first. It re-scores itself every run. | `./securax jewels` |
| 🟡 [Crisis and continuity plan](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Every crisis written down before it happens: how long it may stop you, how much it may lose, the steps, and safe drills that prove it. | `./securax continuity` |

**Your own tools**

| | What it does | How to open it |
|---|---|---|
| 🟢 [Guiding Map](securax/14-GUIDING-MAP.md) | Your daily cockpit for life and work: goals, check-ins and plans. Works offline, no AI needed. | `./securax open` |
| 🟡 [Life OS Inbox](securax/84-CROWN-JEWELS-CONTINUITY-AND-FOUNDATION.md) | Capture one line; then each note becomes an action with a next step and a date, or stays a note. Reviews turn findings into actions; Google Keep notes come in too. | `./securax open` |
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
