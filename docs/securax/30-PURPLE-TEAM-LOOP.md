# 30 · The purple-team loop — would anyone *know*?

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** `purple_loop` journey + CI gate. Probes all 22 AI risk categories (OWASP LLM and Agentic, bias, toxicity); open gaps named, never passed. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

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
* 11 of 12 attacks were stopped, but only **3 of 12** would have alerted anyone (a `skill-poisoning` attack, from doc 31, was added later: now 13 attacks, 12 alert). Fixed by new SOC rules, tuned to be low-noise (one incident per identity per rule): `injection-probe` (LOW, replaced by the burst rule when it repeats), `agentic-tool-coercion` (MEDIUM), `output-exfil-channel` (HIGH), `pii-harvesting` (MEDIUM, needs a burst). Now **11 of 12** alert.
* A **real bug**: a request whose PII was redacted was audited as `decision: allow`, so the SOC (and an auditor) could not tell data had been removed. It is now `sanitise`.
* Remaining gap, accepted on purpose: a single PII redaction is log-only (it escalates on a burst). The report still names it so the decision stays visible.

## Every category, every run (doc 105, G5)
The loop now probes all ten OWASP LLM risks, all ten Agentic risks, bias and toxicity: 22 categories. Each probe attacks the
control that claims the category, through the real gateway where there is one:

* **Through the gateway.** These run as attacks and are scored prevented, logged and alerted like the prompts:
  * a forged key, and a user-role caller reaching an admin endpoint;
  * a runaway agent past its allowance, and a request while a person has stopped all AI;
  * a denied tool, a payment tool that needs a person, and destructive tool arguments;
  * a detector that crashes, which must fail closed;
  * a poisoned retrieved document, and an injected tool result;
  * a write from a foreign web page.
* **Offline gates.** Nothing runs at request time, so these only have to catch the bad input:
  * pickle weights that would run code on load, and changed weights under a familiar name (`ai check`);
  * a skill that fetches its real instructions from the web (`vet`);
  * a confident, made-up regulator circular (the honesty check).

The report opens with a coverage table:
* **held:** every probe in the category was stopped or caught (the probes held; the OWASP map still rates how fully the category is covered);
* **open:** the probe got through, and the item that will close it is named;
* **no probe:** a category nothing tests.

An open gap is never counted as a pass. `./securax purple` fails if:
* a category has no probe;
* an offline gate misses;
* an attack that used to alert stops alerting.

The first run (2026-10-23): 18 of 22 categories held. History/memory poisoning (ASI06) was closed the same day — the gateway now inspects earlier assistant turns, so its probe was promoted from a gap to an attack — bringing it to 19 of 22.

| Open gap | Why it got through | Owner |
|---|---|---|
| A plain "ignore previous instructions" inside a retrieved document | Recorded at medium, not blocked: system prompts legitimately contain such words | G15 retrieval checks |
| A loan decision based on gender or religion | No rail refuses it; the optional Llama Guard detector covers part | G5b |
| An abusive reply | No deterministic output rail; only the optional detector | G5b |

* **Fixed on the way:** a write refused because it came from a foreign web page was counted, but never written to the audit log. It is audited now, with its origin.
* **Detection backlog:** ten rows are prevented and logged, but no SOC rule pages anyone for a single event. They are tool calls withheld, identity refusals, an exhausted allowance, a stopped AI, a detector outage and the foreign write. Each row carries the rule to write, and the queue item `soc-control-alerts` owns them.

## Honest limits
* Deterministic rails only: **no** model-based detectors (Llama Guard etc.), **no** real LLM, **no** runtime (Falco) detections, **no** SIEM. It proves the gateway → audit → SOC chain as shipped, offline and repeatably.
* The attack set is the one in `redteam/run_attacks.py`, the control probes in `redteam/purple.py` and a 4-request campaign. One probe per category is a floor, not a proof: passing it is not a statement about attacks it does not contain.
* Alert thresholds are lab-grade defaults; tune them to your traffic before pointing a pager at them.
* For OSCP-style practice the attacker-side lab is the sleeping Active Directory range (`./securax range`, doc 29); wiring its network telemetry into this loop is **not built**.
