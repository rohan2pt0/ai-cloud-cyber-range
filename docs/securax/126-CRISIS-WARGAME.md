# 126 · Crisis wargame — practise the coordination that decides a crisis

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Crisis-coordination tabletop, scored: ./securax wargame runs a scenario as a timeline of injects (each owned by a team, with an expected action and an SLA); you respond in free text and the estate scores it deterministically (keyword rubric for correctness + timeliness vs SLA, so it is identical offline and in CI), then writes an after-action report with the coordination gaps and an owned improvement action each (--lessons turns each into a standing lesson). Worst-cases built in (colliding deadlines, key person away, clock node down). A gateway, when present, also grades the free text and plays the sender under its rails/audit — additive, never required. Ships payment-fraud (8 injects) and ransomware (6). Runs private in vault/wargame-runs/. Scenarios are data (governance/wargames.json). Tests: test_wargame.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The problem this solves.** A crisis drill teaches the same lesson every time: the attack is the easy part. What
decides the outcome is **coordination under a clock** — the right action reaching the right team in time, while two
agencies' deadlines collide, the one person who knows the payment rail is on leave, and a second batch of fraud lands
while you are still answering the first. You cannot rehearse that from a runbook, and a full tabletop with every team in
a room happens once a year if you are lucky. The 80/20: make the coordination itself a **frictionless weekly drill** that
scores honestly and tells you exactly which handoff slipped.

**What it does.** A scenario is a **timeline of injects**. An inject is a thing that happens — an agency sends a
requisition, a bank asks for a recall, the press calls, a second incident lands, a key person is unavailable — each
owned by a team, each with an **expected action** and a deadline (**SLA**). You run it as a tabletop: the clock starts,
each inject fires on time, you respond in free text, and the estate scores whether the right action reached the right
owner in time. At the end it writes an **after-action report** with the coordination gaps and a specific, owned
improvement action for each. Worst-case is built in — colliding deadlines, missing people, a second hit mid-response —
because those are the moments a real crisis fails.

## The least-friction path

```bash
./securax wargame start payment-fraud
./securax wargame respond <run> i1 --action "declare an incident, start the regulator clock and the crisis requisitions, hold outward payments"
./securax wargame advance <run>
./securax wargame aar <run> --save --lessons
```

- **start `<scenario>`** — begins a run, starts the clock at t=0, and fires the first inject. Scenarios:
  `payment-fraud` (payment-rail fraud, multi-agency) and `ransomware` (data-centre wide). List them with
  `./securax wargame list`.
- **now** — every inject that has fired and you have not answered: who it is from, which team owns it, its SLA, and the
  command that would really do it.
- **respond `<run> <inject> --action "…"`** — record what you did, in your own words. It is scored at once (see below).
  `--minutes N` records that you acted at sim-minute *N* (otherwise it uses the clock's current position).
- **advance** — move the clock to the next inject (or `--to <min>` / `--by <min>`), firing whatever is now due.
- **aar** — the after-action report. `--save` writes it into the run folder; `--lessons` prints a
  `./securax lessons add` line for each gap so a weakness becomes a standing lesson in one step.

## How the scoring works (and why it is honest)

Each response gets a deterministic score, so the same run scores the same offline, on any node, and in CI:

- **Correctness** — a keyword rubric: the content words of the inject's *expected action* that your response covered.
  It rewards naming the real moves (isolate, preserve memory, start the clock, name who has authority, chain of
  custody), not prose.
- **Timeliness** — measured against the inject's **SLA**. On time if you acted within the SLA of the inject firing;
  after that the timeliness score decays.
- **Inject score** = 0.6 × correctness + 0.4 × timeliness. An inject that has fired but was **never answered counts as
  zero** — a missed coordination is the whole point, so it cannot be hidden by not responding.

**An optional second opinion, never a dependency.** When a gateway is configured (`GATEWAY_URL`), the estate also asks a
model to grade your free text and to **reply in character as the inject's sender**, pressing for what is still owed —
inheriting the gateway's rails, allowance and audit trail. This is additive: with no gateway, or if the model is down,
the deterministic rubric is the score of record and everything works exactly the same. Nothing leaves your box.

## The after-action report

`aar` is the deliverable. It gives the overall coordination score, a timeline table (every fired inject, its owner, its
score and whether it was on time), the **coordination gaps** grouped by what failed — unanswered, late, or incomplete —
with the designed worst-cases called out, and an **owned improvement action** for each gap: the team that must drill it
and the exact expected action, with the real command that does it. `--lessons` turns each gap into a one-line
`./securax lessons add` so the weakness is remembered and the next run can prove it closed.

## Where it fits

- **The real thing:** `./securax crisis` coordinates an actual multi-agency crisis and hits every agency deadline; the
  wargame rehearses the same coordination so the real one is reflex. The improvement actions point straight back into it.
- **The technical tabletop:** `./securax continuity` drills RTO/RPO and the restore steps; the wargame drills the human
  coordination around them.
- **The clock and the checklist:** the injects point at `./securax incident` (the regulator clock) and
  `./securax playbook` (the live response checklist) — the same commands you would run for real.

## No single point of failure

The scenarios ship with the code, so a tabletop runs on **any** node with no gateway and no network. A run in progress
and its after-action report live in the vault of the node you run it on and are in your backups; run it on the always-on
node, or copy the vault across (`./securax backup`, then `./securax restore`), to pick it up elsewhere. The optional
model grading degrades to the deterministic rubric whenever a gateway is absent — the drill never stops because a
service is down.

This is a rehearsal, **not** a substitute for a real exercise programme, and not legal advice. Its value is making the
coordination cheap enough to practise every week, and honest enough that the gaps are undeniable.
