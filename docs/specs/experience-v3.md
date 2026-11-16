# Experience v3: priceless to look at, effortless to use

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** A spec, not a build (2026-11-16): the premium look and how the Life OS works for distracted, ADHD, novice and expert minds; it turns amber as the fixes ship. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Status:** proposal, 2026-11-16. **Tokens:** `governance/design-v3.json`. **The work:** [the 20 fixes](experience-fixes.md).
**Builds on:** doc 100 (the design standard), doc 136 (the nature atlas), `governance/design.json`, `guiding-map/shared/lux.css`.

Written by a panel of five: a luxury product designer, a behavioural psychologist, an ADHD coach, an accessibility lead
and a QA lead. Where they disagreed, the rule that protects the person won.

## 1. The promise

A person opens the Life OS tired, distracted, between two other things. In one second they see one calm, beautiful screen
and one thing to do. They do it with one tap. The screen answers at once, and they leave a little better off.

Everything below serves that moment. Beauty earns the first second. Ease earns the first week. Honesty earns the years.

**What v3 changes.** v2 perfected the objects: the rings, the seal, the gold. v3 perfects the behaviour around them.
Measured on 16 November 2026, the app is fast (first paint in about 0.3 s) and free of page errors, and the default Today
is already calm. But a tick moves keyboard focus to nowhere and announces nothing; no sheet closes on Escape; 24 of 26
tabs have no heading; thirty stars twinkle for ever; and the full Today view puts four notices above the first action.
The look is ahead of the manners. v3 closes that gap.

## 2. The look: taken from nature, used like a jeweller

**Restraint is the luxury.** One natural element per surface, chosen for its meaning. The rest is quiet: ivory or
obsidian, a hairline, generous space, one serif title.

### Materials: one meaning each

| Material | Taken from | It means | Where |
|---|---|---|---|
| Gold leaf | polished gold under one light | the one action | the single primary on a screen |
| Jade | polished nephrite | done, kept | a ticked item, a healthy number |
| Moonstone | a soft moving sheen | not yet | an open item, waiting |
| Kintsugi | a gold seam in a mended bowl | a miss you came back from | the seven-day row |
| Amber resin | light through resin | needs attention | a late step, a number to look at |
| Ruby | a cut ruby | real danger | a scam, data loss, a security block. Nothing else |
| Still water | a lake with no wind | paused on purpose | a rest day, a snooze |
| Night sky | stars by magnitude | private, at rest | the lock, the header |

A material never carries a meaning alone. Each has a word or a shape beside it, and a flat fallback for forced colours,
reduced transparency and devices without a GPU. Gold appears once in view. Red never marks a missed habit or a late step.

### Light

One light, from above, the same on every surface: a bright top edge, a soft foot. In dark the screen is a cabin at night:
light comes from the controls, not the page. The time of day changes one thin accent line (dawn, day, dusk, night) and
the greeting. It never changes contrast or layout. After 22:00 the app asks for nothing new; it offers the floor, and rest.

### Motion

Motion confirms what the person just did, then settles. A tick sinks and springs back (under 4% overshoot, settled in
400 ms). A sheet arrives; it does not bounce. Nothing loops while the person reads. Ambient motion (stars, a glint) is
capped at six moving things, rests after 20 seconds without input, and stops when the page is hidden. Under reduced motion
or the in-app still switch, changes cross-fade or cut.

### Sound: off by default

No sound ships switched on. Sound is a rail: a person may turn on one soft tone, under half a second, for the third tick
of the day. Never for a miss, a reminder or an error. Never on first run. Silent mode always wins. Speech happens only when
the person taps Listen.

### Touch and type

Haptics pass through one gate: the haptics switch, reduced motion and the still switch all silence them. A tick is a
light double pulse; nothing vibrates for a reminder. Type carries the brand: the serif for the few words that matter, a
calm sans for the rest, figures that line up. No text under 12 px, body at 15 to 17 px, inputs at 16 px.

## 3. How it works for four kinds of attention

One design serves all four. Building for the distracted mind makes the app better for everyone.

| Person | In the moment | What the app does |
|---|---|---|
| **Distracted** | Arrives mid-task, leaves within a minute | One action in view. The app remembers; they never have to. Coming back lands on the next small step, not where they got lost |
| **ADHD** | Starting is hard; time is vague; shame is close | A two-minute floor that counts. A reward at once. No red, no counters that reset. Rest is a choice, shown with dignity |
| **Novice** | Unsure what any of it means | Works as a guest with example data, clearly marked. Plain words; a term explains itself on one tap. Nothing to read first |
| **Expert** | Wants speed and the whole picture | Everything one tap deeper, never in the way. Keyboard keys for the daily three. Export and off switches in plain sight |

### One action

Every screen has exactly one primary action, chosen for the person by risk: the lowest unfinished layer first. The rest
folds under **Later (n)**. The budget before that action, at 390 by 844:

- at most **one** notice above it;
- at most **40 words** before it;
- at most **three** choices offered at once;
- its top edge within the first **420 px**.

The person never has to choose what to do next. They may always choose something else.

### Defaults

The right choice is already made, and it is the small, safe one. Every default says it is a default and changes in one
tap. Nothing is ever pre-set that spends money, shares data or sends a message. A fact is asked once, in one place.
First run asks nothing before giving value: target zero questions before the first useful screen.

### Streaks without guilt

- **Measure strength, not a chain.** Habit strength is a weighted average over about twenty days. One bad day barely
  moves it. No counter ever resets to zero.
- **A miss is quiet.** One miss is an empty ring, nothing more. Two in a row offers the two-minute floor.
- **Coming back is honoured.** A day you returned from is mended in gold and stays in the story.
- **Rest is a choice.** One tap marks a rest day. It is drawn as still water and is never a miss.
- **Words.** Never *broke, failed, behind, you missed, streak at risk*. Instead *kept, mended, rested, the floor counts,
  welcome back*.

### An honest use of loss aversion

People feel a loss about twice as strongly as an equal gain. That power is used only under four conditions, all of them:

1. the loss is **real** and already happening;
2. the number comes from the **person's own data**, never from example data;
3. it is said **once** per cause, with the **one step** that stops it;
4. the person can **dismiss** it for at least 30 days.

Allowed: "Twelve days of changes live only on this phone. Save a copy." Not allowed: a countdown that is not a real
deadline, a loss invented to bring someone back, or any shame for a thing not done.

### No dark patterns

The test for every nudge: *would we be proud to show the person exactly how and why it works?* So, never:
confirmshaming; fake urgency or scarcity; a pre-ticked box that shares or spends; a smaller or hidden "no"; asking again
within 30 days of a no; making leaving, exporting or erasing harder than joining; guilt in a notification; an endless
feed; a reward made random on purpose. Notifications are off until asked for, at most one a day, quiet from 21:00 to
08:00, and always an invitation with one action.

## 4. Manners: what the app does after every tap

- **It answers in under 100 ms**, in at most three channels: sight, one polite announcement, one haptic if on.
- **Focus stays** on the thing the person just used, after any redraw.
- **Errors speak plainly**: what happened, why, the one next step. In the page, never in a browser alert.
- **Undo for 30 minutes** on anything that changes data. Anything irreversible needs a typed word and offers the safe
  step first.
- **Every dialog** has a name, takes focus, closes on Escape and gives focus back.
- **Every view** has one main landmark, one heading and a skip link. Every control has a name and is a real button or link.
- **It honours the device**: reduced motion, more contrast, less transparency, forced colours, the theme, 200% text,
  320 px wide with no sideways scroll.

## 5. The test plan

**Scope.** The Life OS (`guiding-map/`), then every kit app through the shared look. **Baseline:** the measurements in
`governance/design-v3.json` under `measured_2026_11_16`.

**Entry.** A fix lands with its own failing-then-passing test. **Exit, per fix:** its test, the full `npm test` and
`python3 -m pytest -q` are green, and no audit below got worse. **Exit, for v3:** every row below passes on two
consecutive runs, and the owner has used it on a real phone for a week.

### Automated, on every pull request

| # | What is proven | How | Pass |
|---|---|---|---|
| A1 | Nothing breaks | `npm test` (jsdom), `python3 -m pytest -q` | exit 0 |
| A2 | Contrast and page errors, both themes, every tab | `guiding-map/tests/ui_audit.py` | 0 errors, 0 failures |
| A3 | Every device keeps its form | `guiding-map/tests/device_audit.py` (9 profiles) | 0 issues; screenshots looked at |
| A4 | Damaged storage never locks a person out | `guiding-map/tests/robustness_audit.py` | pass |
| A5 | One action | one primary per view; notices above it ≤ 1; first action top ≤ 420 px at 390 × 844 | every tab |
| A6 | A tick has manners | focus stays on the tile; the live region says item and count | Today, both views |
| A7 | Dialogs | name, focus in, Escape closes, focus back | every sheet and overlay |
| A8 | Structure and names | one main, one h1 per view; 0 unnamed controls or fields; 0 click targets that are not buttons or links | every tab |
| A9 | Type floor | 0 visible text nodes under 12 px | every tab |
| A10 | Motion rests | reduced motion: 0 running animations; otherwise ≤ 6, and 0 after 20 s idle or when hidden | Today, lock |
| A11 | Sound | no audio object exists until the setting is on | a fresh profile |
| A12 | Words | none of the banned streak words, no exclamation mark, in any catalog string | source scan |
| A13 | Honest loss | with example data, no loss-framed line renders | Today, Money |
| A14 | No browser dialogs | 0 calls to `alert` or `confirm` | source scan |
| A15 | Speed | first useful paint ≤ 1 s, tap to paint ≤ 100 ms, offline reload works | throttled mid-range phone profile |

A5 to A15 are new. Each arrives with the fix that needs it, as one real-browser file (`guiding-map/tests/manners_audit.py`)
that reads its thresholds from `governance/design-v3.json`, so a number is changed in one place.

### By hand, before v3 is called done

| # | Check | Who | Pass |
|---|---|---|---|
| M1 | Screen reader, whole daily loop: open, tick three, hear the count, close (VoiceOver on iPhone, TalkBack on Android) | accessibility lead | done without sight, no dead end |
| M2 | Keyboard only, laptop: the same loop, plus open and close every sheet | accessibility lead | no mouse, focus always visible |
| M3 | Text at 200%, and 320 px wide | QA | nothing cut off, no sideways scroll |
| M4 | Five-second test, five people new to the app: "what is this, what would you do?" | designer | four of five name the one action |
| M5 | First-win test, the same five: count taps and seconds to the first tick | psychologist | one tap, under 30 seconds, no question asked |
| M6 | Interrupted-task test: leave mid-task for an hour, come back | ADHD coach | lands on the next small step; nothing lost |
| M7 | The two-miss day: skip two days, open the app | ADHD coach | no red, no shame word, the floor offered once |
| M8 | Dark-pattern review: every nudge, notice and notification read aloud against section 3 | psychologist | each one we would show the person |
| M9 | Real devices: a small Android, a large iPhone, an iPad both ways, a laptop, in daylight and at night | designer and QA | stunning, not merely shrunk |
| M10 | Battery: Today open for ten minutes, untouched | QA | no ambient CPU after 20 s |

### Measures that say it worked for a person

Counted on the device, shown in `./securax progress`, never sent anywhere: first-week return (days opened of the first
seven); taps to the first tick; share of days closed on the floor or better; returns after two misses; rest days chosen.
The target is that people **come back after a miss**, not that they never miss.

### Risks, and what holds them

- **Beauty costs speed or battery.** A10 and A15 fail the build.
- **A fix for one group hurts another.** Every fix runs A1 to A4 and the persona audit.
- **Nudges drift towards pressure.** A12, A13 and M8, with the banned lists kept in `design-v3.json`.
- **jsdom passes, a real phone fails.** The manners audit runs in a real browser; M9 is not optional.

### Sign-off

| Role | Signs when |
|---|---|
| QA lead | A1 to A15 green twice in a row; M3 and M10 pass |
| Accessibility lead | A6 to A9 green; M1 and M2 pass |
| Behavioural psychologist | A12 and A13 green; M5 and M8 pass |
| ADHD coach | M6 and M7 pass |
| Luxury product designer | M4 and M9 pass, screenshots reviewed in both themes |
| Owner | one week of real use on a real phone |

## 6. What v3 deliberately does not do

- No sound by default, no mascot, no confetti, no points, no leaderboards.
- No new material without a meaning. No second gold element in view.
- No streak counter that can reach zero.
- No new sign-in, server or dependency: all of v3 runs offline, on the device.
- No rebuild: the 20 fixes change manners, not the product.

## Open decision for the owner

First run opens on "Make it yours": five questions and eleven buttons before any value. v3's target is zero questions
before the first useful screen, with the same sheet offered as an invitation on Today. That changes a flow tuned on
15 November (`test106`, the persona audit), so it is not among the 20 fixes. It waits for a yes or a no.
