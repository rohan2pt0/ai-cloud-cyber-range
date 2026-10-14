# 35 · Regulatory gap assessment — RBI NBFC Directions 2026 and SEBI CSCRF

```
./securax comply                      both, summary + top of the backlog
./securax comply rbi | cscrf          one regulation   (--md for the full table, --json for machines)
./securax comply cscrf --category qre only what applies to that SEBI category (mii | qre | mid | small | self)
./securax comply --verify             consistency only (also in ./securax verify, ./securax fitness and the evidence pack)
```
Full requirement-by-requirement tables: [`regulatory/rbi-nbfc-gap-assessment.md`](regulatory/rbi-nbfc-gap-assessment.md) and [`regulatory/sebi-cscrf-gap-assessment.md`](regulatory/sebi-cscrf-gap-assessment.md) (generated; a test fails if they drift from the maps). Both also ship in `./securax evidence`.

## First: "100% compliant" is not a property software can have
Compliance belongs to the **regulated entity**. Roughly a third of both texts is Board and committee constitution, the CISO's reporting line, people, premises, contracts, a DR *site*, auditors and filings. Those rows are marked 🏛 *entity* and are **never counted as covered by software**. What this estate can honestly claim is narrower: for the requirements software can address, which are demonstrably met, which partly, and which not at all.

## What was assessed, and what was not
| | RBI | SEBI |
|---|---|---|
| Text | *RBI (NBFCs – Cybersecurity, Technology: Risk, Resilience and Assurance Framework) Directions, 2026*, RBI/DoS/2026-27/461, 31 Jul 2026, from the copy you supplied | **CSCRF circular** SEBI/HO/ITD-1/ITD_CSC_EXT/P/CIR/2024/113 (20 Aug 2024; 205 pages), fetched from sebi.gov.in, read with the clarifications of 31 Dec 2024, 30 Apr 2025, 28 Aug 2025 and the June 2025 FAQs |
| Scope | **NBFCs only**; chapter by layer and size (III < ₹500 cr, IV ≥ ₹500 cr, V Middle/Upper/Top) | SEBI-regulated entities; five categories (MII, Qualified RE, Mid-size, Small-size, Self-certification) |
| Rows | 58 paragraph groups | 75 standard groups |

Not assessed: SEBI's separate cloud framework, the Annexure-K CCI scoring itself, circulars after 28 Aug 2025 (a vendor blog mentions a 2026 advisory; I could not confirm one), and anything the supplied RBI text does not contain. **If your institution is a bank, this RBI document is not the one that applies to it** (it is the NBFC direction): tell me the entity type, layer/size and SEBI category and I will narrow the output and re-check the right text.

## Result (software-scope coverage; entity items excluded)
| | Supported | Partial | Gap | Entity | N/A | Coverage |
|---|---|---|---|---|---|---|
| RBI NBFC | 1 | 27 | 6 | 21 | 3 | **42.6 %** |
| SEBI CSCRF (all categories) | 1 | 45 | 9 | 16 | 4 | **42.7 %** |

Scoring: supported 1, partial 0.5, gap 0. "Supported" needs a journey or test as proof, so it is rare by design. These percentages describe a **lab estate against the regulator's text**; they are not an audit opinion and not a statement about your institution.

## The gaps that matter (found by reading the code against the text)
1. **The gateway does not authenticate callers.** The "principal" is a hash of whatever `Authorization` string (or client IP) arrives. There are no users, roles, lock-out, MFA, privileged-user logging or auditor role at the AI access point (RBI 113-116, 21(3); CSCRF PR.AA.S1-S3, S7, S9 and PIM). This is the biggest single gap and it also blocks non-repudiation in the audit trail.
2. **No incident-reporting clock.** RBI para 28/141: DAKSH within **6 hours** of detection plus CERT-In; CSCRF RS.CO: SEBI and CERT-In within **6 hours**, SEBI portal details within 24 hours, quarterly report within 15 days. Nothing tracks, templates or reminds.
3. **Data localisation.** CSCRF requires Regulatory Data to stay within India; the router can send prompts to Gemini/Groq/OpenRouter. PII redaction reduces exposure but nothing enforces "classified data never leaves India". Cloud stages are not constrained to India regions or MeitY-empanelled offerings (Annexure-J).
4. **Backups and RPO.** CSCRF RPO is 15 minutes and RTO 2 hours; RBI wants near-zero RPO. Restore speed is fine (12.5 s etcd restore on the twin) but backups are periodic, unencrypted tar.gz with no immutable/off-site copy.
5. **Audit trail integrity.** Gateway audit lines are verified end to end but are not tamper-evident, carry no authenticated identity, and retention is whatever the shipper keeps (RBI 21(8), 109-110).
6. **Patch SLA clock and end-of-life tracking** (CSCRF PR.MA.S3: High 1 week, Moderate 2 weeks, Low 1 month; RBI 92-93).
7. **CCI** (CSCRF Annexure-K, MII/Qualified RE, half-yearly) is not computed; **threat hunting** (quarterly), **DAST**, **signing** of evidence packs, **IPv6** readiness are absent.

## Honest limits
- Status is our own judgement of one estate against the text as read on 2026-10-14; read the notes, challenge them, and check every row you rely on against the primary text.
- A row marked *supported* means a mechanism exists **and** a test proves it, within the scope stated in its note (usually the AI channel only).
- SEBI's grouping of standard IDs follows its own guideline blocks; the rows are therefore groups, not one row per ID.
- Nothing here has been shown to an auditor or regulator. It is a working plan, not evidence of compliance.

## Proposed build order (each closes high-priority rows; each gets a journey)
1. Identity-aware gateway (OIDC/JWT, roles, lock-out, subject in audit) → RBI 113-116, CSCRF PR.AA.
2. `./securax incident` (6-hour clock, DAKSH/CERT-In/SEBI field sets, quarterly roll-up, evidence sealing) → RBI 28/141, CSCRF RS.CO.
3. Classification-aware routing + India-region guard for cloud stages → CSCRF data localisation and Annexure-J.
4. Encrypted, checksummed, off-site/immutable backups + Postgres WAL archiving + scheduled drills → RC.RP.S2/S4, RBI 128-135.
5. Hash-chained audit log and signed evidence packs → RBI 21(8), 21(9), 31.
