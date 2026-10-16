# AI Security Assurance - Board Brief (2026-10-10)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The original cyber-range lab; superseded by the SecuRAX docs. [What the lights mean](index.md#the-status-lights)
<!-- status:end -->

## Residual risk: 🟢 **LOW**  (composite assurance 100%)

| Dimension | Score | Reading |
|---|---|---|
| Adversarial-ML defence rate | 100% | 11/11 OWASP-LLM/ATLAS attacks defended |
| False-positive (business impact) | 0/5 | legitimate banking queries wrongly blocked |
| AI-SPM control coverage | 100% | 16/16 baseline controls implemented |

## What this estate is
A multi-cloud AI cyber range (AWS + GCP + Azure + on-prem/laptop) with a single
guardrail gateway enforcing input/output policy in front of every model, defended
by Kubernetes admission control, zero-trust egress and runtime detection, all under
a hard monthly cost ceiling.

## Top risks & remediation roadmap (prioritised)
- No open control gaps or undefended attack classes in the current baseline. Focus shifts to **continuous assurance**: expand the red-team corpus (agentic tool-abuse, multi-turn), add drift monitoring, and run the suite on every deploy.

## Regulatory posture (India BFSI)
- **DPDP Act 2023 / DPDP Rules 2025**: Aadhaar/PAN/card/UPI redacted at the gateway before any model call; audit log retained for breach reporting.
- **RBI FREE-AI (Aug 2025) & cyber-resilience directions**: data residency in Mumbai regions, fail-closed guardrails, human-in-the-loop on high-impact actions, full decision audit.
- **Frameworks evidenced**: NIST AI RMF, ISO/IEC 42001, CSA AI Controls Matrix, Google SAIF, OWASP LLM & Agentic Top 10, MITRE ATLAS (see docs/compliance-matrix.md).

## Spend
- Default posture runs on free tiers / credits; hard budget 2,500 INR/month with automated kill-switches on every cloud. Paid detectors are opt-in per drill.

---
_Generated from `redteam/results.json` and `docs/aispm-report.json`. Re-runs on every CI pipeline so the brief never goes stale._
