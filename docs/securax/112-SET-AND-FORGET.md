# Set it once, then forget it: shaping the environment

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: ./securax environment gives a catalogue of set-and-forget changes that reverse eight common struggles (focus, phone overuse, saving, bills, debt, routine, social, reading) into one best change each with one-time device/account steps; four new core principles (best-default, shape-environment, worst-day, aim-at-success) now propagate to every app. The one-tap Life OS screen is queued. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Most life advice is a rule you must remember to follow — "use your phone less", "spend less", "save more". Rules need
willpower, and willpower is exactly what runs out on a hard day. SecuRAX does the opposite: it changes the **setting**, once,
so the good path happens by itself and the harmful one takes effort. This is a core principle of the whole estate
(`governance/principles.json`: **shape-environment**, **best-default**, **worst-day**, **aim-at-success**), not a Life OS
feature only — every app built from the kit carries it.

## The idea

> Don't tell the person what to do. Change the environment so the right thing is the default, the wrong thing is friction,
> and nothing depends on them remembering.

`./securax environment` is the catalogue of these set-and-forget changes. Each one reverses a common struggle into a single
obvious change you make one time:

| The struggle | The one change | Set it once |
|---|---|---|
| Can't focus; the phone pulls you in at night | The phone goes grey and quiet at night, by itself | iPhone Sleep Focus + Color Filters; Android Bedtime mode (grayscale + DND) |
| Doomscrolling | The worst apps are time-boxed and off the home screen | Screen Time / Digital Wellbeing app timers; remove from page 1 |
| Nothing gets saved | Pay yourself first, on salary day, automatically | A standing auto-debit into a separate account the day the salary lands |
| Late fees | Every bill and premium on autopay before its due date | Autopay in each biller app; the Life OS lens alarms you as a backstop |
| Debt that never shrinks | Autopay the minimum everywhere; attack the costliest one | Autopay minimums; point one fixed extra at the highest-interest debt |
| No routine | One keystone habit, anchored to an existing one, with an alarm | The estate schedules and alarms it; you stack it on coffee or brushing teeth |
| Drifting from people | A standing cadence to reach the few who matter | The estate surfaces one person a week and holds their key dates |
| Hard to read or concentrate | The estate reads to you and reads your documents for you | Scan instead of type; turn on Speak Screen / Select to Speak |

## Use it

```
./securax environment                 every change, the one best choice each, with the one-time steps
./securax environment focus money     only the struggles you name (focus, phone, money, bills, debt, routine, social, reading)
./securax environment --json          the catalogue as JSON, for the Life OS one-tap screen
```

Nothing here needs willpower, and nothing leaves your devices — the steps are settings on your own phone and accounts.

## Where this is going

Today the catalogue is delivered in the shell and as JSON. Next it becomes a one-tap screen in the Life OS: you pick the
struggles that are yours, and each change becomes a card with its one-time steps and a "done" tick, so a person who will not
open a terminal still gets the whole benefit. That, and more reversals (a focus mode for work hours, automatic round-up
savings, a spending-account split), are tracked in `governance/queue.json` under `environment-pwa`.
