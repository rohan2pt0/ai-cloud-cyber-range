# 93 · Progress you can see: the point of all of it

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the north star is AGENTS.md section 0 for every builder; every feature names its outcome and where it shows (fitness outcomes-declared); ./securax progress shows your Life OS rhythm, what made the estate stronger and the one next step, and the progress routine sends it every Sunday. Not yet seen on your own estate: it fills in as you use the Life OS. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** robustness, security and resilience are not the goal. The goal is that the person or team using SecuRAX is **immensely better off, and can see it**, and keeps using it until it reaches its full potential for them: their purpose (ikigai), their work, their life. Growing stronger from every shock (antifragility) is part of that. If none of this turns into a real outcome in the physical world, it is paper. Keep this goal in front of everyone, always.

**The answer in one line:**
- The goal is now written into the first section every builder reads.
- Every feature must name what gets better for a person and where they see it, or it does not ship.
- Every Sunday you see your own progress, and the one next step.

## 1. Kept in front of everyone, always

| Where | What it says | What enforces it |
|---|---|---|
| `AGENTS.md` §0, **the north star** | Every agent (Claude, the open models, OpenCode, the local builder) reads it first. A change must answer three questions: what gets better for the person this week, where they will see it, and how it gets them to use the estate more fully | It is the first thing in the file every agent is told to read |
| `features.json` | Every feature carries an `outcome` (what gets better, in the person's words) and `shows` (where they see it) | Fitness `outcomes-declared` fails a feature without both |
| This page | The outcome of every capability, and how to see it | The docs build |

## 2. Your progress, every week

```bash
./securax progress
```

| Part | What it shows | Why |
|---|---|---|
| **Your rhythm** (Life OS) | Check-ins this week and in 30 days; your last weekly review; your last quarterly check-in | These turn purpose into days: the wheel and your OKRs (ikigai), habits, and the weekly review. When a rhythm slips you get one gentle, two-minute way back, never a lecture |
| **Stronger than before** | Drills passed, failures the estate learned from and recovered, restores proven, tabletop exercises, postmortem actions open, single points of failure still open | Antifragility you can count: each shock leaves a test, a drill and a fix |
| **The one next step** | The most useful thing not yet set up, with its one command | The estate grows to its full use one step at a time, never through a manual |

The `progress` routine sends the short version to your phone every Sunday at 6:40 pm, from one machine only. It reads the Life OS data on your own machine, and nothing leaves it.

## 3. What each capability is for

Every feature's `outcome` and `shows` are in `features.json`, where every builder sees them. Showing them on each Command Center card is the next step, due 2026-11-10. A few examples:

| Feature | What gets better | Where you see it |
|---|---|---|
| Life OS | Your days line up with what matters to you, and you can see it happening | the wheel, goals, streaks and weekly review |
| Accurate answers | You can act on what the AI says, because it does not make things up | `./securax ai honesty`, weekly |
| Ransomware recovery | Ransomware costs you an evening, not your data | `./securax progress` |
| Incident clock | No regulator deadline is missed | a phone alert before each deadline |

## 4. Proof

- **`test_progress.py`:**
  - the rhythm is read from the exact shape the Life OS syncs (storage keys, JSON text, per-key times);
  - a healthy rhythm gets no nagging, and a slipped one gets one specific nudge;
  - only drills from the last 30 days are counted;
  - the report and the phone message always name one next step.
- **Fitness `outcomes-declared`:** every feature names its outcome and where it shows.
- **Sandbox `machine_alone`:** on the real estate, `progress` reads the Life OS data that was just saved.
