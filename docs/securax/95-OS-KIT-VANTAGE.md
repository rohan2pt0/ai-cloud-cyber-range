# 95 · One kit, many apps: Vantage, the CISO's operating system

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the OS kit (twelve reusable modules) and Vantage, the CISO's operating system, at /vantage/: next step, leadership rituals, the review rhythm, top risks, decisions, exceptions, tools, stakeholders, team, lessons, KPIs and KRIs, playbooks, progress and the Govern feed; offline, own storage names, estate sync, backup and undo. A new app is one JSON file (./securax os new). Core principles come from one shared file and reach every app at its next build; kit news shows on each app's Today. Reminders, Ask and shared registers wait, with dates. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** reuse the Life OS components to build a personal app that guides a CISO or a similar executive to do the job well. Keep the same principles with new names, and make every module reusable so a new app for another role takes only minor changes.

**The answer:**
- **The OS kit** (`guiding-map/kit/`) holds twelve modules shared by every app.
- **An edition** is one JSON file that names the app, its words and its content.
- **Vantage** is the first edition, served at `http://localhost:8088/vantage/`. *Vantage* means the high ground you see far from: the 40,000-ft view.

## 1. Why a kit and not a copy

Before building, we looked at what the Life OS really is. It has two layers:

| Layer | What it holds | Reusable as is? |
|---|---|---|
| **The engine** | Pillars, wealth stages and risk shield, all computed from a personal profile (income, loans, children) | No. Copied as it stands, it would ask a CISO about home loans. |
| **The practice** | Capture and decide, the one next step, Never-Miss-Twice habits, OKRs, the wheel, the review rhythm, after-action lessons, the antifragility index, offline first, sync to your own estate, undo, backup | Yes. These are the principles. |

So the kit takes **the practice** and leaves the personal-finance engine behind. The Life OS keeps working unchanged. One change was made to it: its sync now leaves the kit apps' keys alone, because the kit apps sync their own.

## 2. The same principles, the CISO's words

| Life OS | Vantage | What it does for a CISO |
|---|---|---|
| Today and the one action | Today: your next step | Picks the single most pressing item from every screen: a late review, an expiring exception, a high risk without a date |
| Daily habits (Never Miss Twice) | Leadership rituals | Six two-minute floors: the threat brief, one risk decision, one stakeholder touch, unblock one person, think and learn, shut down |
| Wheel of Life | Programme wheel | Nine areas scored 1-10 each quarter, from governance to "you: energy and growth"; the lowest area gets the next goal |
| OKRs | Security OKRs | At most three a quarter; starters such as "Prove we can recover from ransomware" |
| Sunday Pulse, Money Date, quarterly review | Rhythm | 19 reviews from weekly to yearly, each with its checklist and the estate command that helps: Monday risk review, tool value check, Board report, drill, policy review |
| Risk shield | Top risks | Likelihood × impact (1-25); the owner is a business role |
| (new) | Decision log, Exceptions, Tools and value, Stakeholders, Team | Registers with their own dates: an exception rises 30 days before expiry, a tool 60 days before renewal, a stakeholder when a touch is due |
| After-Action Review | Lessons | Every incident leaves a lesson, a change and a drill; it feeds the resilience index |
| Scorecard | KPIs and KRIs | 12 numbers; progress counts from your first value, not an example |
| Playbook | Playbooks | The first 90 days, Board reporting, the first hours of an incident, the budget case, tool value, VAPT closure, exceptions, audit readiness, building the team, looking after yourself |
| Antifragility index | Resilience index | It rises only with practice: rhythm kept, numbers on target, lessons turned into changes, top risks owned and dated |
| (new) | Govern feed | The maturity and top gaps from `./securax govern`, shown on Today |

## 3. How a CISO uses it

| When | What | Time |
|---|---|---|
| Every morning | Open Today. Do the next step, tick the rituals, capture anything new. | 5 minutes |
| Monday | The risk and priority review comes due by itself. Tick its checklist. | 30 minutes |
| Month end | Management update and tool value check. `./securax govern board` drafts the page. | 1 hour |
| Quarter end | Board report, drill, goals and wheel reset. | Half a day |

Nothing needs remembering: the app does the remembering, and Today shows what is late.

## 4. Your data

- **On the device:** everything is stored under `osk:vantage:` on the phone or laptop. It works offline, and it is installable as an app.
- **Sync:** it uses the same estate sync as the Life OS. If the Life OS is already paired on this address, Vantage uses that pairing; there is nothing to set up. Each app sends only its own keys, and the sync service merges per key. Your estate keeps a daily snapshot, as it does for the Life OS.
- **Backup:** Settings, then Export, gives one JSON file. Import restores it. A backup from another app is refused.
- **Undo:** the last 30 changes can be undone.
- **No other site:** the page names no external address. Its only optional read is `portal/govern-state.json`, on the same address.

## 5. A new app for any role, in one file

```bash
./securax os                                   # the apps and their modules
./securax os new founder-os --name "Founder OS" --tagline "Build the company, keep your life"
#   edit guiding-map/kit/editions/founder-os.json: words, rituals, reviews, registers, numbers, playbooks
./securax os build founder-os                  # http://localhost:8088/founder-os/
./securax os check                             # every edition valid, every app current (CI runs it)
```

What an edition file holds:

| Key | What it sets |
|---|---|
| `name`, `tagline`, `north_star`, `principles` | Who it is for and why it exists |
| `nav`, `nav_short`, `terms` | Which screens, in what order, and in whose words |
| `modules.rituals / cadence / goals / wheel` | The practice: habits, reviews, goals, areas |
| `modules.registers` | Any number of lists with fields, scores, due dates, expiry and touch cadence |
| `modules.scorecard / playbooks / feeds` | The numbers, the know-how, and what the estate shows |

The builder refuses a broken edition in plain words: a register field that does not exist, a review with no cadence, a feed on another site. It never writes over a folder it did not build. Edition text cannot break out of the page: every `<` is escaped.

Editions that would take little more than a JSON file each:
- A deputy CISO or a SOC manager.
- A data protection officer.
- A founder.
- A family office.
- A doctor running a clinic.
- A school principal.

Doc 96 explains why this is the business model, not only a convenience.

## 6. One change, every app: principles and news

**The principles live in one file:** `governance/principles.json`.
- Every app built from the kit carries the **core** principles (ikigai, antifragility, small wins shown, least effort) automatically. It adds the others it chooses.
- An edition may say a principle in its own words. Vantage says ikigai in a CISO's terms. But it cannot drop a core principle.
- When a principle improves, or a new core one is added:
  - `./securax os check` (and CI) fails until every app is rebuilt with it;
  - `./securax os build --all` carries it into every app.
- A better principle therefore cannot stay in one app by accident.

**What's new reaches people where they look:**

| Where | What it shows | Source |
|---|---|---|
| Each kit app's Today | "New in Vantage" once, until Got it | `guiding-map/kit/whatsnew.json` (all apps, or named ones) |
| Each kit app's Settings | The full list of what's new | the same file |
| The Command Center | A **New** mark on a feature for 30 days, and a "New in the estate" strip | `features.json` `added` |
| The docs home and the README | "New in the estate": the latest five additions | `features.json` `added` |
| `./securax features` | The same list at the top | `features.json` `added` |
| `./securax progress` (and its weekly message) | "New in the estate: try one" | `features.json` `added` |

**The rule for builders:**
- every feature carries its `added` date, and `features_sync` refuses one without it;
- a change to the kit that people would notice gets a line in `whatsnew.json`.

What does not follow automatically yet: the Life OS's own personal-finance engine tags its items with its own principles (Pareto, inversion and others), which predate the shared list. It keeps them until the Life OS is rebuilt on the kit. That has no date yet: it waits until the kit covers the Life OS's money and family screens.

## 7. Proof

- **`tests/kit1.js` (jsdom):** it uses Vantage as a CISO would.
  - The workflow: start, capture and decide, tick a ritual, record a risk, start a goal, see a late review come due, undo.
  - Data safety: back up and restore, and refuse another app's backup.
  - The sync merge rules: newer wins, other apps' keys are ignored, a damaged copy is refused.
  - Security and completeness: no script injection, every screen renders, no page error.
- **`tests/kit_audit.py` (real browser):** it opens every screen in both themes at phone width. It finds 0 page errors, 0 contrast failures and no sideways scroll. The sandbox journey `guiding_map_full_use` runs it.
- **`governance/tests/test_oskit.py`:**
  - Every edition is valid and every built app is current.
  - A new app is one command.
  - Broken editions are refused.
  - A folder the kit did not build is never overwritten.
  - Edition text cannot inject markup.

## 8. What waits

| Item | Why it waits | Target |
|---|---|---|
| Phone reminders for a late review | Needs the push sender that the Life OS already uses, wired per app | 2026-12-01 |
| Ask (the estate's AI) inside the kit | The answer rules are in the gateway; the kit needs a careful-mode screen | 2026-12-15 |
| Share one register with a deputy | Needs a second user on the sync row and a review of who sees what | 2027-01-31 |
| An icon per edition | It works with the Life OS icon today; an edition can ship `<id>-icon-192.png` | when wanted |
