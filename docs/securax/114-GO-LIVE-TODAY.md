# Go live today: take control, and let it run itself

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Every piece this go-live runbook uses is built and tested: ./securax go/up/ready/doctor, the Life OS and its phone sync, the open-model build loop (autobuild then ship watch --fix --merge, doc 83) and 26 self-maintenance routines already running (daily backup, offsite mirror, safe nightly self-update with automatic rollback, the autopilot learn/drill/forecast loop). Not yet proven: a full week run by the owner, and one real change shipped end-to-end on the open models with no Claude. Proving those two flips this green. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

This is the day the R&D stops and the life starts. The machine is built. You do not need to understand all of it. You
need to start it, use it for real, and let it look after itself — and you need to know it will keep working the day your
Claude subscription is gone. That is what this page is for. Everything here is a command that already works.

## First, the honest shape of it

SecuRAX runs on **one always-on box** — your laptop, a mini-PC, or a small server at home. That box holds the AI gateway,
your data, the backups and the open-model builders. Your **phone is the remote control and the Life OS**, not the engine:
it shows your life, takes a tap, and lets you watch and nudge the estate from anywhere. A phone on its own cannot run the
builders or the gateway, and this page never pretends it can. The split is the strength: the box does the heavy, always-on
work; the phone keeps you in it with two minutes a day.

"Independent of Claude" means the box **builds and heals itself using open models** on a schedule, and you supervise from
the phone (the GitHub app and the Command Center). The rigor that made Claude trustworthy lives in the **gates**, not in the
model: every change the open models propose must pass the same `pytest`, `ruff`, secret-scan, `Semgrep` and build-drift
checks before it is allowed to land (doc 83, doc 23). You already own that rigor.

## Part 1 — Go live in fifteen minutes

On the box:

1. **Start it.** `./securax go` — brings the estate up and prints the one next step. (`./securax up` starts everything;
   `./securax up --safe` if the box is short on memory.)
2. **Check it answers.** `./securax ready` prints `READY`. `./securax doctor` runs a real chat through the gateway and
   reports health and resources.
3. **Open your life.** `./securax open` opens the Life OS. Do the four-question setup once. This is the only typing the
   system ever forces on you.
4. **Put it on your phone.** `./securax tls on` (names + HTTPS, once), then `./securax sync-link` gives a one-tap link.
   Open it on the phone, add the Life OS to the home screen. It now works offline and syncs back to the box.

That is live. You are using it.

## Part 2 — Cut the cord to Claude (do this once)

So that a paid-Claude limit is never a single point of failure (doc 23, doc 83):

1. **Give it an open-model key.** `./securax providers add opencodego` — the OpenCode Go plan (about $10/month) runs the
   default build ladder and the strong tier. Prefer free or sovereign? `./securax providers add` lists the free cloud tiers,
   and `./securax profile` + `./securax pull coder` set up a local coder that runs on the box for nothing.
2. **Prove it, once.** Pick a tiny real task and let the open models build it with no Claude:
   `./securax autobuild "add a one-line note to the README about going live"`. Watch it edit, run the gates, and commit
   only when green. The first time this goes green is the day you are free of the subscription. (It flips doc 23 green;
   record it with `./securax lessons add "first open-model autobuild landed green on <date>"`.)
3. **Let CI fix itself.** `./securax routines on pr-watch` turns on the unattended pull-request loop: on every PR it opens,
   it watches CI, briefs `autobuild` to fix red (one push a round), and squash-merges when green — the whole
   `./securax ship watch --fix 2 --merge` loop, on the open models, with nobody watching.

For anything genuinely hard (security design, a gnarly bug), `./securax escalate "task"` writes a tight brief you can hand
to any strong model — the open strong tier, or a frontier model if you still have one. The brief, not the subscription, is
the dependency.

## Part 3 — It already heals and maintains itself

Twenty-six routines run on the box with nobody watching (`./securax routines` lists them, times in your clock):

- **Keeps working:** `nightly-update --auto` updates only when main has something new — it backs up first, health-checks,
  and **rolls back by itself** if the new version will not start. `rollback-check` and `storage-guard` watch weekly and
  every six hours.
- **Never loses your data:** `daily-backup`, an off-site `code-mirror`, and restore **drills** that actually open the copy
  as working data (a drill that restores nothing is made to fail, by design).
- **Learns from its own failures (the autopilot):** `autopilot-learn` every hour, `autopilot-drill` nightly,
  `autopilot-forecast` hourly — it turns each failure into a fix, rehearses recovery, and foresees running out of room
  before it happens.
- **Keeps you honest and informed:** `honesty-check`, `resilience-check`, `regwatch` (RBI/SEBI updates), and `progress --send`
  — the Sunday message to your phone that now leads with what the estate had your back on this week.

You do not start these. They are on. `./securax autopilot` shows what it learned, which drills it ran, and what it foresees.

## Part 4 — The daily human loop (two minutes)

The system does the remembering. Your part is small and on the phone:

- **Each day:** open the Life OS, tap your energy, glance at the one open action and the "had your back" card. Two minutes.
- **Each Sunday:** read the progress message; do the 15-minute weekly review when it asks.
- **When you are unsure what to do:** `./securax next` prints exactly one next step in plain words. `./securax finish` shows
  what is left to set up, one step at a time. Never a list to wade through.

## Part 5 — If something breaks

In this order, because the first steps are the estate healing itself:

1. **Wait a beat and look at the phone.** The `andon` routine and the autopilot may have already caught and fixed it; the
   result comes to your phone.
2. `./securax doctor` — what is healthy, what is not. `./securax why <service>` — what stopped and why.
3. `./securax rollback` — go back to the last version that worked on this box; it backs up, pins, health-checks and returns
   you automatically if the older version fails too.
4. `./securax support-packet` — one scrubbed zip (no secrets, no personal data) if you want a second pair of eyes.

## Why this matters

You did not build a machine. You built a system that takes the remembering, the checking and the guarding off your
shoulders, so your attention goes to your work, your people and your purpose. That is the whole point: the estate is for the
human, never the other way round. Today you stop proving it can work and start letting it work. The generations that come
after you will not read this code. They will inherit the calm, the safety and the compounding that it bought you — and that
is the only scoreboard that counts.
