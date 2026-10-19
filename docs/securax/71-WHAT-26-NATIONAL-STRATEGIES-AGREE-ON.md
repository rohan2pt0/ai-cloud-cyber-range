# 71 · What 26 national strategies agree on, and what SecuRAX does about it

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The UK CAF 4.0 map and the tamper-evident audit chain are built and tested; the eight proposed changes are listed with what each needs. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Doc 70 read five documents; this one reads 21 more and keeps only what **several of them agree on**. A pattern that one
country uses may be local habit. A pattern that four or five unrelated governments arrived at separately is closer to a
law of how long-lived, resilient systems are run.

**The 26 documents:**

- **UK:** NCSC Cyber Assessment Framework 4.0; Government Resilience Framework (2022).
- **Singapore:** Smart Nation 2.0; National AI Strategy 2.0; Digital Government Blueprint; Digital Connectivity
  Blueprint; RIE2025.
- **Estonia:** X-Road and the digital state (2025 paper); once-only principle (ministerial slides); e-Estonia's
  pages on X-Road and the data embassy.
- **Japan:** 5th Science and Technology Basic Plan; Society 5.0; Cross-ministerial Strategic Innovation Promotion
  Program (SIP); Moonshot; Smart City Guidebook.
- **United States:** State Department Strategic Plan 2026-30; Department of Commerce Strategic Plan 2004-09; Joint
  Vision 2020; 2025 National Security Strategy.
- **Israel:** International Cyber Strategy.
- **International:** OECD Recommendation on Digital Government Strategies; G20 Framework for Digital Public
  Infrastructure (2023); G20 Digital Economy outcome document.
- **Read in doc 70:** Saudi Vision 2030; Vision India@2047; RBI Payments Vision 2028; RBI draft model-risk guidance.

Politics, national budgets, and region- or country-specific policy are left out.

**Corrections to the file names:**

- `us219117` is the Department of **Commerce** plan, not State/USAID.
- The scanned GPO file is **Joint Vision 2020** (US Joint Chiefs, 2000).
- The Moonshot file is a news page; its 2050 targets are not in it.

## The eight patterns several of them agree on

| # | Pattern | Who says it | In SecuRAX |
|---|---|---|---|
| 1 | **Every goal is measurable: a baseline, a target, a date, an owner; outcome and output kept apart** | Saudi 2030; Singapore Digital Government Blueprint (a dated KPI table, with exemptions marked); Japan Smart City (KGI and KPI, outcome vs output); US Commerce (goal → annual measure); UK Resilience (named owner per risk) | KRIs with thresholds; risk owners. **Proposed for the Life OS:** key results "from X to Y by a date" (doc 70). |
| 2 | **A plan does not count until it is exercised** | UK Resilience (national exercising programme); CAF D1.c; Joint Vision 2020 (keep working when the technology fails); US Commerce (continuity testing) | **Built:** game days with SLOs and nightly journeys. Next: a cockpit lamp for any plan not exercised in 90 days. |
| 3 | **Resilience comes from diversity and fallback, not from one strong part** | Singapore Connectivity Blueprint (diverse routes, failover); Estonia (data embassy abroad); CAF B5; US NSS (no single foreign source for core parts) | **Built:** provider ladder ending in a local model; restore-verified, encrypted backups. **Gap:** the off-site copy is still a manual step. |
| 4 | **Records that cannot be quietly changed, and people can see who touched their data** | Estonia (signed, logged exchange; citizens see who looked at their data); CAF C1.b securing logs; G20 DPI (trust and transparency) | **Built now:** a tamper-evident audit chain and `./securax audit verify`. **Proposed:** a "who touched my data" view. |
| 5 | **Give information once; one owner per data type** | Estonia once-only (since 2007); Singapore Digital Government Blueprint; OECD (data re-use) | Partly: the Life OS is local-first and the Twin reads it. Next: declare the owning store for each data type. |
| 6 | **Stage gates with a kill or pivot decision; failure is allowed but recorded** | Japan Basic Plan and SIP; Saudi 2030 (halt what shows no impact); Joint Vision 2020 (tolerate errors when experimenting) | Partly: lifecycle stages, the admission gate, the quarterly keep-or-drop of goals. Next: a recorded pass, hold or kill at each lifecycle promotion. |
| 7 | **Measure against an outside standard, honestly, every year** | CAF profiles; UK annual statement; Saudi 2030 (benchmarks); OECD | **Built now:** a UK CAF 4.0 map (`./securax comply caf`, 41 outcomes). With the RBI, SEBI, NIST and NSCS maps that makes seven external yardsticks, all checked in CI. |
| 8 | **Share early warning with trusted peers** | Israel (CyberNet, early warning, speed, trusted platforms); CAF C1.f; G20 (sharing vulnerability trends) | **Gap:** no outbound sharing. Next: TLP-labelled indicator export through the MISP organ. |

## Built in this change

- **UK CAF 4.0 map** (`governance/regmap-uk-caf-4.json`, `./securax comply caf`). Each of the 41 contributing outcomes
  is scored supported, partial, gap or the organisation's, with evidence that CI verifies.
  - Result: 15 supported, 18 partial, 2 gaps (C2.a threat hunting, B3.d mobile data), 6 for the organisation.
  - It is our own judgement, not an official CAF assessment.
- **Tamper-evident gateway audit** (CAF C1.b, Estonia):
  - Every audit event carries its run, its sequence number and the hash of the event before it.
  - `./securax audit verify` names any event that was edited, deleted, inserted or reordered.
  - A restart starts a new chain. Lines Docker rotates out are not counted as tampering.

## Proposed next, in order of value for effort

| # | Change | Why | Needs from you |
|---|---|---|---|
| 1 | **Life OS: key results from X to Y by a date; drop, re-scope or recommit after 6 idle weeks; strengths first** | pattern 1 and 6, seven sources | a yes (it changes the app you use daily) |
| 2 | **Automated off-site encrypted copy** ("data embassy") and a quarterly restore drill from it | pattern 3; closes SEBI CSCRF RC.RP.S1/S4 | where it goes: an India-region bucket (pay-as-you-go, about the price of a coffee a month at your size) or an external disk you plug in weekly |
| 3 | **"Who touched my data" view** in the Life OS, from the gateway and sync logs | pattern 4; the highest-trust feature Estonia has | a yes |
| 4 | **"Not exercised in 90 days" lamp** for backups, restores, game days and the kill switch | pattern 2 | none |
| 5 | **Recorded gate decision** (pass, hold or kill, with the lesson) at each lifecycle promotion | pattern 6 | none |
| 6 | **Hunting and sharing:** documented hunts over the audit log, and a TLP-labelled indicator export | pattern 8; CAF C2.a | none |
| 7 | **Appeal a block:** a "this block was wrong" path that records a decision (G20 DPI grievance redress) | trust in the rails | none |
| 8 | **No-legacy check:** an age and end-of-life date for pinned images, models and packages (Estonia; CAF B4.d) | pattern 3 | none |

## What not to copy

- National budgets, cable landings, broadband, spectrum, data-centre programmes.
- Legislation and treaties.
- Talent and immigration policy.
- Region- or country-specific geopolitics.
- Ideology, and centralising power. A single-person estate still keeps separation of duties: the kill switch and the
  allowance extensions need a person at the machine, never an API caller.
