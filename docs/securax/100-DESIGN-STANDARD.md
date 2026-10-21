# 100 · The design standard: calm by default, no manual needed

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the Command Center opens on one honest status line and at most three things to do, with everything else folded and searchable; two core principles (calm by default, no manual needed) reach every kit app; governance/design.json holds the shared tokens and rules and a test holds each page on the standard. The cockpit, the ready reckoner and the control navigator take one shared style from governance/design.py (83 pages measured, 0 contrast failures); the Life OS and kit apps keep their brand colours with the same basics. Role-aware views are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** the Command Center had become a catalogue of about 60 equal cards. The owner asked for three things:
- a cockpit that is quiet when all is well and shows only what needs attention;
- the craft of the best designed products;
- design principles in the estate's core values, applied everywhere, without making anything harder to use.

## 1. The rule every screen answers to

**Show what matters. Say why. Make the right action obvious. Fold everything else away until it is wanted.**

Every screen answers three questions, in this order:
1. What needs me?
2. Why does it matter?
3. What do I do next?

Two new **core principles** carry this into every app, through `governance/principles.json` (doc 95 §6):
- **Calm by default:** when all is well the screen is quiet. Only what needs you lights up, with why it matters and the one thing to do. Everything else waits one tap away.
- **No manual needed:** anyone can use it the first time, on a phone or a laptop, by keyboard or screen reader, in light or dark. If it needs explaining, it is not finished.

## 2. What we took, and from whom

| Source | What it teaches | How SecuRAX applies it |
|---|---|---|
| Apple Human Interface Guidelines | Hierarchy, harmony and consistency: the most important thing is clear at a glance, and what you learn in one place works in another | One large status line; the same card, button and fold patterns on every page |
| Nielsen Norman Group heuristics | Recognition rather than recall; progressive disclosure | Buttons that say what they do ("Copy: ./securax backup"); details folded, never deleted |
| WCAG 2.2 (W3C) | AA contrast; targets at least 24 px (2.5.8); visible focus | Contrast measured in both themes; 44 px targets; a 3 px focus ring |
| Microsoft Fluent and IBM Carbon | Enterprise consistency, keyboard first, accessible tokens | Shared colour tokens in `governance/design.json`; everything works by keyboard |
| Samsung One UI and Material | Reachable controls and adaptive layouts on a phone | One column at 390 px, nothing wider than the screen, safe-area padding for notches |
| Security operations tools (SOC consoles, observability) | Triage first, then drill down | At most three actions, then the cockpit for evidence, then the logs |

These are sources of principles, not visual identities to copy. SecuRAX keeps its own restrained look.

## 3. Three levels, one tap apart

| Level | What it shows | Where |
|---|---|---|
| **Glance** | One status line, and at most three things to do | The top of the Command Center |
| **Decide** | Why each matters, the evidence, the command | Each action card, and "Why and how" |
| **Investigate** | Every vital sign, every capability, history and settings | The folded panels, the cockpit, the ready reckoner |

## 4. The Command Center, rebuilt

**The status line is never falsely reassuring.** It says one of five things:

| It says | When |
|---|---|
| **N things need you** | Something is red. The most important one comes first, as an action ("Take a backup now", not "KRI backup: red"). |
| **Nothing urgent** | Only items to watch. |
| **All clear** | Only when the last health check is fresh and nothing measured is wrong, with the time it was checked. |
| **Status may be out of date** | The last check is more than a day old. |
| **Status unknown** | No health check has run. Unknown is never shown as green. |

**What needs you:**
- **At most three.** The first has the one primary button; the rest are counted ("2 more in the cockpit"), not listed.
- **Where they come from:** cockpit vital signs that are red or urgent, a core app that stopped answering, the first repair, and the next setup step when nothing else is waiting.
- **Each one carries** the action, the reason and the evidence, and copies its command in one press.

**Open:** the three apps you came for (Guiding Map, Chat, Cockpit), with live status dots.

**Folded:**
- System health, as one line: "4 fine · 5 to watch · 2 need you".
- Add-ons.
- **Explore everything SecuRAX can do:** the full library, with search as you type and New marks.
- Phone setup, AI providers, and handy commands.

**What did not change:** every link, the name-based addresses, the Tailscale handling, the live re-check every 5 seconds, the version badge and the model list. The existing tests prove it.

## 5. The standard is checked, not hoped for

`governance/design.json` holds the shared tokens and the rules, and `governance/design.py` turns them into the CSS every generated page uses. `governance/tests/test_design_standard.py` checks every page and generator on the standard for:
- the tokens in both themes;
- `lang`, viewport and safe-area settings;
- a visible focus, and reduced motion;
- 44 px targets, three actions at most, and the folds closed by default.

The Command Center is also checked:
- **`guiding-map/tests/test32.js`:**
  - unknown is never all clear, and red leads;
  - at most three items, one primary button, and no repeats;
  - stale data is said out loud;
  - search narrows the library.
- **`ui_audit` contrast check:** 0 contrast failures and no horizontal scroll at 390 px, in both themes.

## 6. Where the standard reaches

**Every page the estate generates, from one place.** `governance/design.py` turns `design.json` into one block of CSS:
the tokens in both themes, safe-area padding, a visible focus, reduced motion and 44 px targets. These pages take it:
- the Command Center;
- the cockpit;
- the 78 ready-reckoner pages;
- the control navigator, about 25 pages (it was dark only; it now follows the device's light or dark setting).

Change a colour in `design.json`, and every one of them follows on its next build.

**Fixed on the way:**
- **Heat map:** in light mode, the numbers on the navigator's heat-map cells were dark text on dark colour. They are white now, in both themes.
- **N/A cells:** grey on grey, a contrast failure that was there before this change.
- **The cockpit's "posture by area" table:** too wide for a phone. It now scrolls inside its own box.

All 83 pages were measured in both themes, at laptop and phone width: no contrast failure, no page error, no sideways scroll.

**Apps with their own brand keep it.** The Life OS (navy and gold) and the kit apps such as Vantage keep their colours, which are part of their identity. They meet the same basics:
- a visible keyboard focus on every control;
- calm motion;
- notch-safe edges;
- 44 px buttons and fields in the kit.

Their contrast is measured by `ui_audit.py` and `kit_audit.py`.

| Still to do | By |
|---|---|
| Role-aware views (CISO, analyst, engineer), reusing the same pages and the existing roles service (doc 97) | 2027-03-31 |

A generator joins `generators_on_the_standard` in `design.json` when it moves; the test then holds it there.

## 7. What we deliberately did not do

- **No framework migration.** The pages stay plain HTML that works offline and on any phone (doc 98).
- **No invented scores.** Every item shows its real value and its reason. The order comes from the cockpit's own urgency and importance (doc 37), which you can read on each item.
- **No AI in the way.** Nothing needs a chat to work, and AI suggestions are never shown as facts.

## Sources

- [What's new in WCAG 2.2 (W3C)](https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/)
- [WCAG 2.2 updates (Deque)](https://dequeuniversity.com/resources/wcag-2.2)
- [Liquid Glass: hierarchy, harmony and consistency (Create with Swift)](https://www.createwithswift.com/liquid-glass-redefining-design-through-hierarchy-harmony-and-consistency/)
- [10 usability heuristics (Nielsen Norman Group)](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [Progressive disclosure (Nielsen Norman Group)](https://www.nngroup.com/articles/progressive-disclosure/)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Recognition rather than recall (The Decision Lab)](https://thedecisionlab.com/reference-guide/design/recognition-rather-than-recall)
