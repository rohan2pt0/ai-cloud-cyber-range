# 100 · The design standard: calm by default, no manual needed

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the Command Center opens on one honest status line and one thing to do (chosen by risk, the rest under Later), with everything else folded and searchable; two core principles (calm by default, no manual needed) reach every kit app; governance/design.json holds the shared tokens and rules and a test holds each page on the standard. The cockpit, the ready reckoner and the control navigator take one shared style from governance/design.py (83 pages measured, 0 contrast failures); the Life OS and kit apps keep their brand colours with the same basics. The product site joined on 2026-11-08: one generated stylesheet with a dark theme, 16 page views audited in a real browser, 0 failures. Role-aware views are dated. [What the lights mean](../index.md#the-status-lights)
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
| Security operations tools (SOC consoles, observability) | Triage first, then drill down | One open action, the rest under Later, then the cockpit for evidence, then the logs |

These are sources of principles, not visual identities to copy. SecuRAX keeps its own restrained look.

## 3. Three levels, one tap apart

| Level | What it shows | Where |
|---|---|---|
| **Glance** | One status line, and one thing to do (the rest under Later) | The top of the Command Center |
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
- 44 px targets, one open action (the rest under Later), and the folds closed by default.

The Command Center is also checked:
- **`guiding-map/tests/test32.js`:**
  - unknown is never all clear, and red leads;
  - one open item with the one primary button, the rest folded under Later (n), and no repeats;
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

The product site (`website/`: home, assess, NBFC, personal) keeps its navy and gold too. Its one stylesheet, `website/site.css`, is generated by `tools/site_css.py` from the same basics, with a dark theme; `python3 website/tests/ui_audit.py` holds all four pages at 0 page errors, 0 contrast failures and no sideways scrolling, in both themes, on a laptop and a 390 px phone.

Their contrast is measured by `ui_audit.py` and `kit_audit.py`.

| Still to do | By |
|---|---|
| Role-aware views (CISO, analyst, engineer), reusing the same pages and the existing roles service (doc 97) | 2027-03-31 |

A generator joins `generators_on_the_standard` in `design.json` when it moves; the test then holds it there.

## 6b. The premium language (2026-11-09)

The product should read as private-bank grade: calm, exact, a little precious. The language lives once, in
`governance/design.json` under `premium`, and `governance/design.py` turns it into CSS (`premium_css()`), so no page keeps a palette of its own.

- **Colour: obsidian and ivory.** Warm ivory surfaces in light; dark grey, never pure black, in dark, with surfaces that rise in lighter greys
  rather than shadows. One gold accent, used like leaf: the action rim, a mark, a link. Status colours are muted. Every text pair is at least
  4.5:1 in both themes, and a test measures each one.
- **Type.** A display serif (Instrument Serif, self-hosted under the SIL Open Font License, no font service) for the few words that matter, a
  quiet system sans for the rest, one scale (13, 15, 17, 21, 28, 36, 48 px), tabular figures on numbers only.
- **Space and material.** One spacing scale: 4, 8, 16, 24, 32. Hairline borders, soft depth in light, 20 px cards.
- **Motion and touch.** 150 to 250 ms with one easing curve, on a change of state only, and off under reduced motion. Presses scale a little, so
  they feel physical. Haptics are hooks: an element with `data-haptic` asks for a short pulse, never under reduced motion.
- **Finishes.** Six lit "pebbles" (Gold Leaf, Rose Gold, Obsidian Mirror; and the limited Jade, Midnight Blue, Amethyst), each a base, a
  highlight and a rim, drawn by one CSS layer with no images. They are accents only: editions, milestones, the owner's chosen tint. Text and
  data stay on the neutrals.
- **Glass, sparingly.** Frosted glass only on layers that float over scrolling content (sticky bars, the tab bar, sheets,
  dialogs), never on cards or whole pages: on a flat page it is just grey. It stays 92% opaque so text reads even where a
  phone does not draw the blur, and turns solid when the person asks for less transparency.
- **Buttons.** Three kinds and no more: a solid primary with a gold rim (one per screen), an outlined secondary whose edge
  is at least 3:1 against every surface, and an underlined text link. Every button shows pressed, working, done and disabled.
  Haptics only on the moments that matter (a daily-three tick, marking done, a confirmation), never on every tap.
- **AI that can be overruled.** A suggestion is labelled "Suggested", says why under "Why?", is never the main button and never
  acts by itself; one switch turns suggestions off (safety warnings stay).
- **Access by default.** A skip link, more contrast when the phone asks, Windows high-contrast mode, an in-app motion switch,
  and squircle corners where the browser can draw them (plain rounded corners elsewhere).
- **Alerts, said once and calmly.** Four kinds (note, attention, danger, success): a tinted card, a thin edge in its colour,
  an icon, a short sentence-case title, ink text and at most one action. Red only for real danger (a scam, data loss, a
  security block); a missed habit is attention. One alert per cause, never one per item. An error says what happened, why
  and the next step.
- **Copy.** Short, warm and certain, like a concierge. No exclamation marks.

**Rollout, done 2026-11-10.** Every page is on the language: the Command Center (the hosted door and the node's page), the
Life OS, the product site, the generated pages (cockpit, ready reckoner, control navigator), the kit apps, the exercise portal
and the docs. The three hero screens went first, each with before and after pictures for the owner's yes; then `premium`
replaced the older `tokens`, so there is one source.

**The rules the owner collected,** held mechanically where a browser can measure them (queue `ui-rules-lint`): body line height 1.4 to 1.6 and
45 to 75 characters a line; one primary action per view; labels that stay; buttons that say what happens; the 4/8/16/24/32 scale; one accent;
never colour alone; underlined links; 44 px targets and the main action near the thumb; 16 px inputs with the right keyboard; no hover-only
actions; bottom sheets, not centred dialogs; dark grey, never black; dashboards that lead with one number, with a period and a change,
bars from zero, sorted bars instead of pies, figures right-aligned.

## 6c. Design for the human mind (principles `human-first` and `whole-view`, 2026-11-10)

Everything here is built for people, so their psychology is a design input, not an afterthought. A person judges in two
stages: **first by the look** (a study flashed web pages for 50 ms and the verdicts matched those given after longer viewing;
that first feeling then colours how usable and trustworthy the rest seems), **then by the use** (speed, few steps, nothing to
learn, nothing that nags). The look earns the second visit; the use earns the hundredth. The vital few levers, with where the
estate already uses them:

| Stage | Lever (the effect behind it) | In the estate |
|---|---|---|
| First seconds | Beauty reads as quality (aesthetic-usability) | the premium language (section 6b) |
| First seconds | Fewer choices, faster decisions (Hick's law) | one action per screen, chosen by risk; the rest under Later (`one-open-action`) |
| First seconds | Under about 0.4 s feels instant | offline-first pages; the one-second target in the premium review |
| First week | People keep the default (default effect) | guest first; best defaults; the one-tap capture |
| First week | A started task gets finished (endowed progress) | example numbers they correct, not a blank form |
| First week | What you shaped, you value (IKEA effect) | "Make them mine"; their own goals in three taps |
| Every day | Behaviour = motivation × ability × a prompt (Fogg) | the floor version of each habit; one gentle reminder |
| Every day | Visits are remembered by their peak and their end (peak-end) | end on a small win; the daily three ring |
| Every day | Visible progress keeps people going (small wins) | `./securax progress`, streaks, the vitals |
| Always | Pressure makes people push back (reactance, the root of "reverse psychology") | invite, never command: "the floor is enough", not "mandatory" |
| Always | Losses weigh about twice as much as gains (loss aversion) | used only for real risk (a scam, a lapsed policy), never to guilt |

**Guardrails.** No dark patterns: no fake scarcity or urgency, no guilt, no confirm-shaming, no hidden costs, no hard-to-find
off switch. Every nudge passes the test of showing the person exactly how and why it nudges them.

**The 360 review** (AGENTS.md section 0) is how `whole-view` is applied, in the spirit of the great generalists. Leonardo
studied the whole subject before drawing a part. Jobs started from the experience and worked back to the technology, and
finished the unseen side of the box. Musk's sequence is: question the requirement, delete the part, simplify, then speed up,
then automate. Before building, answer six questions in the PR:
1. the person;
2. first principles;
3. the whole system;
4. craft, including the unseen;
5. proof;
6. ethics.

Sources, cited by reference: Lindgaard and others, *Behaviour & Information Technology* (2006), on 50 ms first impressions
(their participants had no task, so use still decides whether people stay); Brehm (1966) on reactance; Kahneman's peak-end
findings; Fogg's behaviour model; Thaler and Sunstein on defaults.

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
