# One idea a week: signal, not a feed (`./securax insight`)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: ./securax insight serves one durable idea a week from a bounded, curated, on-device library (decision-making and leadership, security and AI-risk craft, mental models, money and financial independence), aimed by your OKRs first and then your weakest Wheel area, with a per-machine seen ledger so it never repeats until a theme is exhausted (falling back to a weekly rotation when the ledger can't be written). The weekly insight routine sends it on Wednesdays. governance/tests/test_insight.py covers the aiming order, the never-repeat guarantee and the honest fallbacks. A one-tap Life OS surface and letting you add your own ideas are queued. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

You already get one calm nudge a week that changes your *environment* (`./securax improve`, doc 112). This is its
sibling for your *mind*: one durable **idea** a week that sharpens how you think, decide and work — aimed at a goal you
actually set.

## Why this is not a feed

Every feed fails the same way: it is live, high-volume, recency-biased, unaimed, and inert. You wade through it and keep
almost nothing. So `./securax insight` is built as the deliberate inverse. An idea earns its one slot a week **only if it
passes all four tests**:

1. **Durable** — still true and useful in five years. A timeless idea, never today's headline. *(Kills news noise.)*
2. **Actionable** — it ships with exactly **one** concrete thing to do this week. *(Kills "interesting but inert".)*
3. **Aimed** — it targets a goal or a weakness *you* declared, not a generic topic. *(Kills irrelevance.)*
4. **Finite and non-repeating** — it comes from a **bounded, curated library**, and never repeats until its theme is
   used up. *(Kills volume and filler.)*

The important consequence is the fourth test: **this is not a scraper.** There is no live feed, no network call, no new
dependency — pulling from the world's firehose would manufacture the exact noise you are trying to escape (and break the
estate's offline rule). Instead the ideas live in a small, hand-curated library in the repository
(`governance/insight.json`), each one paraphrased in plain words with its **source named** and a single action. It
compounds; it never floods.

## What it draws from

The library covers four themes, chosen for a senior professional:

| Theme | What it sharpens |
|---|---|
| **Decision-making & leadership** | Judgement under uncertainty, leading and growing a team, delegation, influence |
| **Security & AI-risk craft** | The durable principles of the field — assume-breach, least privilege, risk as probability × impact, design for the worst day — the ideas that outlast any one tool or CVE |
| **Mental models & clear thinking** | Cross-domain models: inversion, second-order effects, base rates, incentives, *via negativa*, circle of competence |
| **Money & financial independence** | Avoiding ruin, compounding, pay-yourself-first, the freedom to walk away — tied to your own FI numbers in the Career compass (doc 49) |

Every idea is an original paraphrase of a well-known principle; the source (the author and work) is cited as a
reference, never copied — the same rule the estate applies to regulator documents.

## How it aims

"Useful to *you*" means tied to what you are trying to move. Each week it chooses the theme in this order:

1. **Your OKRs first.** It reads the goals you set in the Life OS quarterly check-in (the `okrs` you score), finds the
   one with the **lowest progress** whose wording matches a theme, and serves an idea from that theme — so the idea
   serves the goal you are furthest behind on.
2. **Then your weakest Wheel area.** With no matching OKR, it falls to the lowest-scored Wheel-of-Life area that a theme
   covers (career → leadership, personal growth → thinking, money → money).
3. **Otherwise it rotates.** With nothing to aim at yet, it rotates across the four themes week to week, so there is
   always a useful signal — and scoring your wheel or setting an OKR immediately makes it sharper.

## Never the same twice

A small ledger on the always-on machine (`~/.securax/insight/seen.json`) remembers which ideas have been sent, so you
are never shown one twice until its whole theme is exhausted — at which point it tells you and starts the theme again.
If that ledger can't be written (a read-only box), it falls back to a weekly rotation, so the idea still varies; only
the never-repeat guarantee lapses. Nothing about your goals, your wheel or what you've seen ever leaves your machine.

## Use it

```
./securax insight            print this week's one idea, its source and its one action
./securax insight --send     the same, short, to your phone (the weekly insight routine, Wednesdays) — and mark it seen
./securax insight --json     for the cockpit and other tools
```

The weekly `insight` routine sends it on **Wednesday mornings** — a midweek sharpener, paired with the Saturday
`improve` lever (doc 112) and the Sunday progress message (doc 93): three aimed, high-quality signals across the week,
the opposite of the chaos of a notification feed.

## Where this is going

Today it is delivered in the shell and to your phone. Queued in `governance/queue.json`: a one-tap Life OS card (tap the
idea, tap "done" on the action), letting you **add your own ideas** to the library (a book you read, a lesson you
learned), and surfacing the week's idea on the Command Center. The library will grow, always curated, never a feed.
