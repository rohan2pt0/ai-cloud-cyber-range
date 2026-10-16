# SecuRAX — Kaizen & Antifragility (the UPSC lens)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Ratchets and fitness budgets run; the wider improvement loop is manual. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Looked at the way a well-run state is run — the UPSC/public-administration view — a system is
judged not by how it looks, but by **outcomes delivered to people, under constraints, over
time, with integrity, and improving every cycle.** This page is how SecuRAX is governed to
that standard: continuous improvement (Kaizen) where **every failure becomes a future
strength** (antifragility), powered by AI.

## 1. The policy cycle (how every change is governed)
The classic public-administration loop, applied to the estate:
```
  FORMULATE → IMPLEMENT → MONITOR → EVALUATE → FEEDBACK → (FORMULATE…)
  policy/rule   as code     metrics   red-team    ledger      better rule
  (docs+OPA)   (PR+CI)    (Prom.)   (scorecard) (antifragile)  (kaizen)
```
Nothing changes by decree; it changes through this cycle, with evidence at each step.

## 2. Each failure becomes a strength — the antifragility engine
This is the heart of it (`learning/antifragile.py`):
1. **Capture** every failure — a guardrail bypass, an incident, even a false positive — into
   an append-only **failure ledger** (institutional memory, kept in Git; PII redacted).
2. **Generalise** it with AI from a one-off into a *class* (`propose_rule`, and the local LLM
   via `self_improve.py --ai`), so the whole family is caught, not just the exact string.
3. **Harden** — a human reviews and ships the rule (HITL; the system never rewrites its own
   security rules unattended — the integrity guardrail).
4. **Verify** — the engine re-runs **every past failure** against today's defences. The share
   it now blocks is the **antifragility score**, and it only goes up.
```bash
python3 learning/self_improve.py      # red-team → capture gaps → AI proposes fixes (HITL)
python3 learning/antifragile.py verify  # prove past failures are now strengths
./securax learn                        # the whole loop, one command
```
> "A failure we learned from is permanent capital." The ledger is that capital, compounding.

## 3. Outcome-orientation (measure what matters, not vanity)
UPSC discipline: judge **outcomes**, not outputs. The metrics that govern SecuRAX:
| Not this (output) | This (outcome) |
|---|---|
| "we have guardrails" | **defence rate** on the live attack corpus (and it rises) |
| "we log things" | **mean-time-to-detect / respond** on real incidents |
| "we're compliant" | **antifragility score** — past failures now withstood |
| "it runs" | **signal/noise** — % of alerts that were real, agent-triaged |
| "we're busy" | **Q1 completion** (Eisenhower), deep-work hours protected |

## 4. Integrity & ethics (the non-negotiables)
- **Human-in-the-loop on anything irreversible or high-impact** — AI proposes, a human decides.
- **Assume breach, zero trust, least blast radius** — every component least-privileged, local-bound.
- **Privacy-by-design** — PII redacted even inside our own institutional memory.
- **Transparency** — every decision is auditable; evidence is auto-generated, not curated.
- **Responsible AI** — aligned to NIST AI RMF, RBI FREE-AI, ISO/IEC 42001 (see compliance map).

## 5. The maturity ladder toward "perfection" (asymptotic, by design)
Perfection is a direction, not a destination — Kaizen means you never stop climbing:
| Level | State | Evidence |
|---|---|---|
| L1 Reactive | fixes after incidents | ad-hoc |
| L2 Defined | rules as code, tests in CI | **where we are** |
| L3 Measured | outcome metrics, posture score, antifragility score | dashboards |
| L4 Self-improving | AI proposes hardening from its own red-teaming (HITL) | `self_improve.py` |
| L5 Antifragile | every class of failure strengthens the system; MTTR→0 | rising antifragility score |

## 6. Institutional memory (so lessons are never re-learned)
- The **failure ledger** is the "file notings" of the estate — every lesson, dated, kept.
- Docs are the **standing orders**; policy-as-code is the **enforced rule**; the review cadence
  (`08-OPERATING-MODEL.md`) is the **inspection regime**.
- Because it is all in Git and code, the knowledge survives people leaving — the system
  outlives any individual, which is the whole point of a well-run institution.

> Kaizen in one line: **do today a little better than yesterday, make every failure pay
> forward, and let the AI handle the repetition so your judgement goes to what only you can do.**
