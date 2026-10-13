# 30 · The purple-team loop — would anyone *know*?

`./securax purple` fires the attack set through the **real gateway application**, captures the **real audit lines** it emits, runs the **real AI-SOC triage** over them, and reports three independent facts per attack:

| | Question | Source |
|---|---|---|
| **Prevented** | did the gateway stop it? | the response / decision |
| **Logged** | does an audit event with the right rule exist for that identity? | the captured audit stream |
| **Alerted** | did the SOC raise an incident covering that identity? | `ai-soc/soc/triage.py` |

"Prevented but never alerted" is a **detection backlog item**, not a pass. The report (`evidence/purple-<time>.md` + `.json`) lists them with a concrete suggestion each.

```bash
./securax purple               # report into ./evidence (host Python, or the gateway image if the host lacks fastapi/httpx)
python3 redteam/purple.py --out docs/purple --fail-on-gap     # what CI runs
```

## What the first run found — and what was fixed because of it
* 11 of 12 attacks were stopped, but only **3 of 12** would have alerted anyone. Fixed by new SOC rules, tuned to be low-noise (one incident per identity per rule): `injection-probe` (LOW, replaced by the burst rule when it repeats), `agentic-tool-coercion` (MEDIUM), `output-exfil-channel` (HIGH), `pii-harvesting` (MEDIUM, needs a burst). Now **11 of 12** alert.
* A **real bug**: a request whose PII was redacted was audited as `decision: allow`, so the SOC (and an auditor) could not tell data had been removed. It is now `sanitise`.
* Remaining gap, accepted on purpose: a single PII redaction is log-only (it escalates on a burst). The report still names it so the decision stays visible.

## Honest limits
* Deterministic rails only: **no** model-based detectors (Llama Guard etc.), **no** real LLM, **no** runtime (Falco) detections, **no** SIEM. It proves the gateway → audit → SOC chain as shipped, offline and repeatably.
* The attack set is the one in `redteam/run_attacks.py` plus a 4-request campaign. Passing it is not a statement about attacks it does not contain.
* Alert thresholds are lab-grade defaults; tune them to your traffic before pointing a pager at them.
* For OSCP-style practice the attacker-side lab is the sleeping Active Directory range (`./securax range`, doc 29); wiring its network telemetry into this loop is **not built**.
