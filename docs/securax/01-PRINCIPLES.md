<!--
  SecuRAX — Design Principles (the "constitution").
  These are the non-negotiable reasoning rules every decision in the estate obeys.
  When a future choice is unclear, resolve it against THIS file, in order. If two
  principles conflict, the lower-numbered one wins (they are ordered by priority).
-->

# SecuRAX — Design Principles

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Enforced in code by the build contract, diffcheck and the fitness functions. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

These are the rules the whole estate obeys. They are deliberately few, ordered by priority,
and phrased so a decision can be checked against them in seconds. Think of them as the
"constitution": architecture serves the principles, not the other way round.

## P-0 · Survive first (antifragility over optimisation)
The system must **not fail catastrophically in any situation, however bad** — that is the
prime directive. Concretely:
- **No single point of failure (SPOF).** Every critical function has a fallback: local model
  ↔ cloud model, three independent clouds, stateless replicas, everything-as-code so any
  node is re-creatable in minutes.
- **Fail *closed* on security, fail *open* on convenience.** A guardrail/detector outage
  blocks sensitive actions; a nice-to-have outage degrades gracefully.
- **Antifragile, not just resilient** (Nassim Taleb): each incident becomes a test case, a
  rule, or a drill, so the system gets *stronger* from stress. Red-team findings feed the
  guardrails; outages feed the runbooks.
- **3-2-1 backups** (3 copies, 2 media, 1 offsite/immutable) for anything you cannot
  regenerate from code.

## P-1 · Start at zero, earn every rupee of spend (calculated risk, 80/20 cost)
- Begin on free/open-source software on hardware you already own. Hard monthly ceiling
  (₹2,500) with automated kill-switches; default posture costs ₹0.
- Spend only when a **documented trigger** is hit (load, client, data-residency, SLA). Cost
  is treated as a security control (economic denial-of-service is a real threat).
- **80/20 (Pareto):** always ship the vital 20% that delivers 80% of the value first. Do not
  build a module before a real need exists for it.

## P-2 · Vendor- and tool-agnostic (no lock-in, ever)
- Program against **open standards and interfaces**, not products: OpenAI-compatible APIs,
  OpenTelemetry, OCI containers, S3-compatible storage, SAML/OIDC for identity, Rego/Policy-
  as-Code, STIX/TAXII for threat intel.
- Any single tool must be **swappable** behind that interface (Ollama↔vLLM, Wazuh↔Elastic,
  Terraform↔OpenTofu, AWS↔GCP↔Azure↔on-prem). The catalog lists at least one alternative per
  capability for exactly this reason.

## P-3 · Don't reinvent the wheel (compose proven building blocks)
- Prefer **globally tried-and-tested open-source** components with large communities over
  bespoke code. You are an *integrator and architect*, not a re-implementer.
- Write bespoke code only for the thin "glue" and the differentiated 20% (e.g. the guardrail
  policy engine, the data-tier router). Everything else is configuration of proven tools.

## P-4 · Secure, private, and compliant by design (not bolted on)
- **Data classification drives routing** — the Red / Yellow / Green model governs where data
  may go *before* any processing happens (see Architecture §Data tiers).
- **Privacy-by-design & security-by-design** (ISO/IEC 27001:2022, DPDP Act 2023, GDPR): least
  privilege, encryption in transit and at rest, secrets never in code, PII minimised/redacted
  at the boundary.
- **Compliance-by-design:** map a control to its framework(s) *before* building it, and emit
  audit evidence automatically. Align to the Reserve Bank of India (RBI) FREE-AI guidance:
  **F**airness, **R**eliability/robustness, **E**xplainability, **E**thics, and **AI**-specific
  human oversight, with full decision auditability and data residency in India.

## P-5 · Everything-as-code, self-documenting, and teachable
- Infrastructure, policy, pipelines, and configuration all live in Git (version history =
  source of truth, tamper-evident, reproducible).
- **Documentation and comments everywhere, full-forms on first use.** A newcomer (including
  future-you) must be able to *learn by browsing* the repo. If a file cannot teach what it
  does and why, it is not finished.
- Apply **recognised design patterns** and name them (Policy Enforcement Point, Strategy for
  swappable providers, Adapter for tools, Pipeline for data flow, Circuit-Breaker for
  fail-closed, Sidecar for observability) so the structure is predictable.

## P-6 · Risk-managed and measurable (decide like an operator)
- **Risk = likelihood × impact.** Maintain a living risk register; prioritise by that score;
  prefer mitigations with the best effort-to-impact ratio ("low-hanging fruit": <2 hours of
  effort for >80% risk reduction).
- **Calculated risk, risk aversion where it counts:** take asymmetric bets with capped
  downside and large upside; never bet the foundation. Reversible decisions are made fast;
  irreversible ones are made carefully (Bezos' one-way vs two-way doors).
- **Measure everything that matters:** defence rate, false-positive rate, posture score,
  mean-time-to-detect/respond, cost, and personal OKRs. What is not measured cannot be
  improved.

## P-7 · Gradual, with the end in mind (crawl → walk → run)
- A clear end-goal (the north-star) with **small, independently useful steps** toward it.
  Each phase ships something you can actually use on the ground that day.
- **Keep it simple first; let it earn complexity.** Simplicity is the default; every added
  moving part must justify its maintenance cost. Delete ruthlessly (Musk's "the best part is
  no part").

---
### How to use these principles
When unsure, ask in order: *Does it survive the worst case (P-0)? Can I start free (P-1)? Am
I locked in (P-2)? Am I reinventing something (P-3)? Is it secure/compliant by design (P-4)?
Is it in code and teachable (P-5)? Is the risk worth it (P-6)? Is it the simplest next step
(P-7)?* The first "no" tells you what to change.
