# 70 · What national strategies teach a personal estate (80/20)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Analysis is complete and most patterns are already built; the three proposed Life OS changes (baseline-to-target key results, the stale-goal prompt, strengths first) wait for your go-ahead. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Three national strategy documents, read for **design patterns, not policy**:

- Saudi Vision 2030 (2016 edition)
- a state-level Vision India@2047 submission to NITI Aayog
- the 2025 US National Security Strategy

Politics, ideology and region-specific positions are left out. What is left is how serious long-range plans are built,
measured and kept honest. Most of it transfers directly to the Life OS and to the estate.

## The six patterns that matter most

| # | Pattern | Seen in | Already in SecuRAX | Next |
|---|---|---|---|---|
| 1 | **Choose, and drop the rest.** "Focusing on everything means focusing on nothing." A few core goals, the rest visibly parked. | US NSS (pp.1, 8) | OKRs capped at 3 objectives; the cockpit shows only what is abnormal (dark cockpit); the vital few in the navigator | — |
| 2 | **Every goal is from X to Y by a date.** A baseline, a target and a deadline, with interim milestones. | Saudi 2030 (pp.25, 39, 75; 2020 checkpoints) | KRIs have thresholds and RAG bands; OKRs are graded 0.0–1.0 | **Proposed:** key results with a baseline, a target and a date ("from 12% to 30% by March"), shown as a line, not only a percent |
| 3 | **Kill what shows no impact.** Halt initiatives that do not deliver; review what was approved. | Saudi 2030 (p.65) | the quarterly check-in offers to keep or drop unfinished goals | **Proposed:** a goal with no progress for 6 weeks asks once: drop, re-scope or recommit |
| 4 | **Start from what you have.** Plans are built on existing strengths and an inventory of means. | Saudi 2030 (pp.9, 13); US NSS (Section III) | the model inventory; the control library's evidence map (what SecuRAX already proves) | **Proposed:** the yearly setup starts with "my 3 strengths", and each goal names one |
| 5 | **Never depend on one outside source for a core part; low cost can hide costs.** | US NSS (pp.13-14, 18) | the failover ladder ending in a local model; pinned and vetted dependencies; vendor-neutral configuration (doc 65) | a hidden-cost line in vendor and tool reviews: telemetry, residency, lock-in, exit cost |
| 6 | **A delivery unit separate from doers, publishing honest indicators.** | Saudi 2030 (pp.65, 81) | the cockpit and status lights; every claim has a proof (doc 55); CI journeys | — |

## Smaller cues, already true or cheap later

- **Cheap defences first against cheap attacks** (US NSS p.14). The gateway does exactly this: deterministic rails and
  rate limits before any model-based check, and now per-caller allowances.
- **Bold, binary targets** (India@2047): "100% of AI calls through the gateway", "100% of backups restore-tested". These
  fit the cockpit as single percentages.
- **Approvals automated; only exceptions to a person** (India@2047 p.7). This is how the admission gate and the safe update
  already work.
- **Benchmark against outside standards** (Saudi 2030): the control library scores you against RBI, SEBI, NSCS, NCIIPC
  and the RBI drafts, not only pass/fail.
- **Resilience built in by default** (India@2047; US NSS p.3): every module ships with a backup, a stop path and a rollback.

## What not to copy

- **Vanity rankings** you do not control.
- **Jumps with no causal model.** A target needs the driver that moves it.
- **Two numbers for the same metric.** Saudi 2030 gives two different figures for one goal; SecuRAX keeps one source of
  truth per metric.
- **Programmes with no owner or data source.**

## Documents worth adding

The most useful next uploads, in order:

1. **Singapore Smart Nation 2.0** and **Singapore Cybersecurity Strategy 2021**: the closest model for a small, secure,
   digital-first operation.
2. **UK National Cyber Strategy 2022** and the **UK Cyber Assessment Framework (CAF)**: outcome-based security, which fits
   the cockpit.
3. **Estonia's e-Governance / X-Road principles**: once-only data, data embassy, digital continuity. These are direct cues
   for sync, backup and the Twin.
4. **India's National Cyber Security Strategy** (when published) and **CERT-In directions**: already partly in the
   incident clock.
5. **NIST CSF 2.0** and **NIST AI RMF Playbook**: already mapped. Upload them only if you want paragraph-level citations
   like the RBI packs.

Personal-scale equivalents also work well:

- **Toyota Production System (Andon, Kaizen)**: the andon is already in the estate.
- **Amazon's Working Backwards and COE**: postmortems are built on COE.
