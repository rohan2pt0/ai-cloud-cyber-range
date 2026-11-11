# 134. Use it now: freeze, harden, live in it

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** In force from 11 November 2026: a feature freeze, three audit rounds and the daily routine. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

> **Status: 🟢 In force from 11 November 2026.** The owner's decision: stop building, make it safe and correct, and use it for real life.

## The rule: feature freeze until two weeks of real use

From 11 November 2026 until **25 November 2026** (and two weeks of daily use after that), nothing new is built. Only:

1. what is already in flight (one-command setup, the app lock);
2. the app lock for the Life OS (queue `app-lock` slice 2), because real data is going in;
3. fixes for problems the owner hits while using it (the friction log below).

Everything else in `governance/queue.json` waits, including the UHNW edition, the launch languages and the Local/Global
switch. A session or routine that picks work takes only the three kinds above.

## Three audit rounds, each in a fresh short session

Each round is one session with one checklist. The open models make the fixes; Claude reviews and merges. A round is done when
every line is green or dated in the queue.

| Round | Checklist | Done means |
| --- | --- | --- |
| 1. Safety | Lock on, on phone and laptop · encrypted backup made and a **test restore** done on another device · nothing private in the repository · sync works after unlock | A lost phone costs nothing but the phone |
| 2. Correctness | Income, expenses, net worth, insurance cover, renewals and tax figures checked against the real papers · every date in the calendar right | Every number on Today can be trusted |
| 3. Real-day use | One week of daily use; every annoyance written in the friction log; the top five fixed | The daily routine takes under 10 minutes |

## Day 0: set it up once (about 30 minutes)

1. Laptop: the one command in `WINDOWS-QUICKSTART.md`.
2. Phone: open the Life OS, **Add to Home Screen**, turn on the lock (one tap, Face ID or fingerprint).
3. Drop your papers into the Inbox (policy schedules, Form 16, statements). Answer the four quick questions.
4. Add the calendar (Today → calendar), so the reviews and renewals come to you.

## Every day after that

| When | What | Time |
| --- | --- | --- |
| Morning | Today: the one open action, the daily three | 5 min |
| Evening | One line in the friction log if anything annoyed you (Inbox → note, start it with "friction:") | 1 min |
| Sunday | The weekly review: what moved, what slipped, the one change for next week | 30 min |
| Month end | Money review and the After-Action Review (in the calendar) | 45 min |

## Spending Claude well

- One short session per task, started from the queue. Never one long conversation: a full context window costs more and remembers worse.
- Claude reviews and audits; the open models build. Keep about 30% of the weekly allowance for troubleshooting.
- A free full reset of the usage limit is kept for an emergency, never spent on routine work.
- The daily routine runs in hardening mode: merge what is green, fix what the friction log says, otherwise stop.
