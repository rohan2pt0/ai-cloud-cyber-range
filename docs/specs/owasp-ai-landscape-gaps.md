# Spec: owasp-ai-landscape-gaps

Queue item `owasp-ai-landscape-gaps` in `governance/queue.json` · due 2026-12-15 · added 2026-10-23.

**The ask, as the queue holds it:** Cross-checked the estate against the OWASP AI Security Landscape (the full project set). Already covered: OWASP LLM Top 10 + Agentic Top 10 (./securax comply owasp-ai), GenAI red-teaming (purple loop + adversary ledger), GenAI incident response (incident runbooks), model security (ai check: digests, pickle scan). …

## Outcome for the person

A team can show how its AI estate stands against each OWASP AI project, not only the Top 10.

## Data

New comply and readiness maps (requirements cited by reference and paraphrased), scoring on findings, an AI bill of materials export.

## Screen (one action)

`./securax comply <map>`: the score and the one requirement to close next.

## Test that proves it

Map well-formedness tests as for existing maps; the count in `sandbox/run.py` updated; each requirement points to evidence that exists.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Maps on the existing engine.
- **Enterprise, when conditions call for it:** Signed official maps and auditor-ready evidence packs.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
