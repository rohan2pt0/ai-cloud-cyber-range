# Set it once, then forget it: shaping the environment

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: ./securax environment gives a catalogue of set-and-forget changes mapped to the Wheel of Life (twelve struggles across health, finances, career, relationships, environment, recovery and personal growth), each reversed into one best change with its one-time device/account steps, an if-then implementation-intention plan and a start-small floor — the elite-sport levers made structural; filter by struggle or by a weak Wheel spoke. Four core principles (best-default, shape-environment, worst-day, aim-at-success) propagate to every app. The one-tap Life OS screen, process-based scoring and the marginal-gains view are queued. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Most life advice is a rule you must remember to follow — "use your phone less", "spend less", "save more". Rules need
willpower, and willpower is exactly what runs out on a hard day. SecuRAX does the opposite: it changes the **setting**, once,
so the good path happens by itself and the harmful one takes effort. This is a core principle of the whole estate
(`governance/principles.json`: **shape-environment**, **best-default**, **worst-day**, **aim-at-success**), not a Life OS
feature only — every app built from the kit carries it.

## The idea

> Don't tell the person what to do. Change the environment so the right thing is the default, the wrong thing is friction,
> and nothing depends on them remembering.

`./securax environment` is the catalogue of these set-and-forget changes, mapped to the **Wheel of Life** so a weak spoke
points straight at its fix. Each reverses a common struggle into a single obvious change you make one time:

| Life area | The struggle | The one change | Set it once |
|---|---|---|---|
| Health · sleep | Can't focus; the phone pulls you in at night | Phone goes grey and quiet at night, by itself | iPhone Sleep Focus + Color Filters; Android Bedtime mode; a fixed wake alarm + morning light |
| Health · body | Sedentary; the gym never happens | A daily walk, anchored to an existing cue | The estate schedules + alarms it; 'after lunch, I walk'; park far, take stairs |
| Health | No routine; habits never stick | One keystone habit, anchored, with an alarm | Two-minute floor, stacked on coffee or brushing teeth |
| Finances | Nothing gets saved | Pay yourself first, on salary day, automatically | A standing auto-debit into a separate account the day the salary lands |
| Finances | Late fees | Every bill/premium on autopay before its due date | Autopay in each biller app; the Life OS lens alarms you as a backstop |
| Finances | Debt that never shrinks | Autopay the minimum; attack the costliest | Autopay minimums; one fixed extra at the highest-interest debt (avalanche) |
| Career | Sunday dread; no visible wins | A protected weekly block: one skill, one reach-out, one win | A recurring 'busy' calendar hour the estate protects and alarms |
| Relationships | Drifting from people | A standing cadence to reach the few who matter | The estate surfaces one person a week and holds their key dates |
| Environment | Clutter; the place feels out of control | A 10-minute daily reset, anchored to a cue | 'While the kettle boils, I clear one surface'; two-minute floor |
| Fun & recovery | Burnout; rest never gets scheduled | Protected recovery blocks — recovery is training | A weekly 'busy' rest block; a lighter 'deload' week every 4–6 weeks |
| Personal growth | Doomscrolling instead of learning | Time-box the worst apps; put a learning app in their place | Screen Time / Digital Wellbeing timers; swap the home-screen cue |
| Personal growth | Hard to read or concentrate | The estate reads to you and reads your documents | Scan instead of type; turn on Speak Screen / Select to Speak |

## The Olympic levers, made structural

The same science that trains elite athletes is built into every entry, so success is engineered, not exhorted:

- **If-then plans (implementation intentions).** Every entry carries an `if <cue>, then <one action>` — the single
  best-evidenced behaviour lever (Gollwitzer: an if-then plan roughly doubles follow-through over a bare goal). The estate
  stores the plan, not a vague wish.
- **Start small, grow at the edge (deliberate practice).** Habit entries begin at a two-minute floor and ratchet up only
  once automatic — the athlete's progressive overload, so a bad day still counts and nothing is ever too big to start.
- **Process, not outcome.** You are scored on the rep you control (the walk taken, the message sent), never the result —
  the mindset Olympic champions share, and the estate's `control-inputs` principle made into how streaks count.
- **Recovery is training (periodization).** Rest is scheduled and protected, and a missed habit in a planned light week is
  rest, not failure — gains happen during recovery.
- **Aggregation of marginal gains.** No single heroic change: a stack of 1% environment tweaks that compound, shown in
  `./securax progress`.

## Use it

```
./securax environment                 every change, the one best choice each, with its if-then plan and one-time steps
./securax environment focus money     by struggle (focus, phone, money, bills, debt, routine, social, reading, move, career, space, rest)
./securax environment finances        or by Wheel-of-Life area — a weak spoke returns every change that fixes it
./securax environment --json          the catalogue as JSON, for the Life OS one-tap screen
```

Nothing here needs willpower, and nothing leaves your devices — the steps are settings on your own phone and accounts.

## Where this is going

Today the catalogue is delivered in the shell and as JSON. Next it becomes a one-tap screen in the Life OS: you pick the
struggles that are yours (or tap a weak spoke on the wheel), and each change becomes a card with its if-then plan, its
one-time steps and a "done" tick, so a person who will not open a terminal still gets the whole benefit. That, process-based
scoring (count the reps you control) and the marginal-gains compounding view in `./securax progress` are tracked in
`governance/queue.json` under `environment-pwa`.
