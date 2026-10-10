# AI-SOC — defensive "AI for security" / Agentic SecOps

The mirror image of the guardrail gateway. The gateway is **security for AI**; this is
**AI for security**: it consumes the estate's telemetry and uses correlation + (optional)
LLM assistance to turn raw events into analyst-ready incidents.

Covers the "Agentic SecOps / AI-for-security", "AI-SOC / autonomous detection", and
"monitoring, anomaly detection & incident response" asks in the PwC, C-DOT and Abu Dhabi JDs.

## What it does
- **Ingests** heterogenous telemetry into one schema: the gateway's audit JSON, Falco
  runtime alerts, and cloud findings (CSPM/DSPM-style).
- **Correlates** per identity within a time window into incidents:
  repeated prompt-injection, data-exfil attempt, runtime compromise, and a cross-source
  **injection→runtime kill-chain** (when workload identity is resolved across sources).
- **Maps** every incident to **MITRE ATLAS** (AI threats) and **MITRE ATT&CK** (infra).
- **Recommends** a next action per incident (contain, rotate, isolate, invoke IR).
- **Summarises** each incident for the on-call analyst — the LLM call is routed through the
  guardrail gateway, with a deterministic fallback so it runs fully offline.

## The key idea: the SOC doesn't trust its own inputs
Alert text is attacker-influenced. An attacker can plant an instruction in a prompt that
later lands in a log an LLM summarises — a **second-order prompt injection against the SOC
itself** (OWASP LLM01 / Agentic ASI01). So every event is sanitised through the *same*
guardrail engine (normalise + PII-redact) before any model sees it. This is the kind of
threat-model depth these senior roles are screening for.

## Run
```bash
python3 ai-soc/soc/triage.py ai-soc/samples/events.jsonl            # with summaries
GATEWAY_URL=http://localhost:8080 python3 ai-soc/soc/triage.py ai-soc/samples/events.jsonl
python3 ai-soc/soc/triage.py ai-soc/samples/events.jsonl --no-summary --out incidents.json
```

## Where it plugs in the estate
Gateway audit (stdout JSON) + Falco (JSON output) + cloud findings → Promtail/Fluent Bit →
file/Loki → this engine (batch or streaming) → incident cards → SIEM/SOAR (Wazuh / Sentinel
/ Chronicle). In production the correlation rules become SIEM detections and the LLM triage
becomes a SOAR enrichment step; this is the reference implementation you can reason about.
