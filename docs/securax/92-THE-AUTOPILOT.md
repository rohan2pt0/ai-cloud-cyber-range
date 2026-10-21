# 92 · The autopilot: the estate learns, drills and looks ahead by itself

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: hourly, a newly failing routine gets a postmortem draft and an alert, a recurring one is escalated with the fix command, a recovery is announced; nightly, the 2 drills that most need it run and a slower recovery is flagged; hourly, disk, backup headroom, the AI allowance and latency are forecast with a robust trend and warned 7 days ahead; CI opens an issue when the nightly sandbox is red. The forecasts start after 2 days of readings on your machine. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** make the estate more intelligent, so it stops depending on its owner to notice what is wrong. Do what is best.

**The answer in one line:** three closed loops that run by themselves. One learns from every failure, one drills the estate every night, and one sees trouble days before it arrives. A person still approves every fix.

## 1. Why loops, not a bigger model

What made the estate fragile was never a lack of model intelligence. It was that nothing joined the dots:
- a routine failed, and no one learned from it;
- a drill was written once and never run again;
- the disk filled slowly, and the alarm came when it was full.

Each loop below closes one of those gaps with the parts the estate already had (routines, drills, postmortems, notifications). It needs no new dependency and no cloud spend.

## 2. The three loops

| Loop | When | What it does | How it decides |
|---|---|---|---|
| **Learn** (`autopilot learn`) | hourly | A routine that newly fails gets a **postmortem draft** in `vault/postmortems`, naming the routine and its last words, plus an alert. One that fails 3 times in 7 days is **escalated** with the command that starts a fix you approve (`./securax autobuild "…"`). A recovery is announced once | Reports (which are meant to find things), reminders and the autopilot itself are left out, so it never loops on its own noise |
| **Drill** (`autopilot drill`) | 3:40 am nightly | Runs the 2 drills that most need it: from the continuity plan (restore twin, rollback check, code bundle, models, disk, accounts), plus the resilience and honesty checks. A failure, or a recovery much slower than usual, reaches your phone | score = days since last run (never = 100) × 2 if critical × 3 if it failed last time. Over a few weeks every drill runs; the risky ones run most. "Much slower" means over 1.5 times its usual median time, and at least 2 minutes more |
| **Forecast** (`autopilot forecast`) | hourly | Records free disk space, backup headroom (whether the copies that retention keeps still fit), the AI allowance used this month, and answer latency. Warns when a trend will cross its limit **within 7 days**, at most once a day per warning | The Theil–Sen slope (the median of all pairwise slopes), so one odd reading cannot fool it. It needs 6 readings over 2 days first, and until then says it is still learning |

```bash
./securax autopilot            # one screen: failures being learned from, drills (next first), forecasts
```

**CI does the same for the code.** When the nightly run of every journey on `main` goes red, an issue opens by itself, naming the run. A later red night comments on the same issue, and the next green night closes it.

## 3. What it will not do

- **It changes no data, keys or code.** It drafts, measures, drills and tells you.
- **A fix is a command you run.** Autobuild then proposes the change, and the forge gate and the tests decide whether it can land.
- **It never sends your data anywhere.** Alerts carry routine names, counts and dates, and go through your own notify channel.
- **Everything it keeps is bounded:**
  - 5,000 readings;
  - 2,000 drill results;
  - one record per routine;
  - postmortem drafts in your vault, which you close.

## 4. Proof

- **`test_autopilot.py`:**
  - a new failure gets one draft and one alert;
  - a repeat failure is escalated with a fix command;
  - a recovery is announced;
  - reports, reminders and the autopilot itself are ignored;
  - drills that never ran or failed come first;
  - a much slower recovery is flagged, and noise is not;
  - one wild reading does not move the trend;
  - a disk filling up is warned days ahead;
  - a warning is sent once a day at most;
  - readings are bounded;
  - the nightly drill records each result and alerts on a failure.
- **Fitness `continuity-declared`:** the autopilot declares how it behaves with a machine off. Each machine runs its own.
- **The workflow parse test:** the nightly-red issue job is valid YAML.

## 5. Next, with dates

| By | Step |
|---|---|
| 2026-11-15 | Careful mode for important questions (doc 89) |
| 2026-11-30 | Routing each question to the model that has proved best for that kind of task, learned from the honesty, benchmark and failure records the autopilot keeps |
| 2026-12-15 | Per-caller baselines in the gateway audit, so a stolen key is spotted by how it behaves |
