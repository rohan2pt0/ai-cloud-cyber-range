# garak - LLM vulnerability scanner (NVIDIA)

garak probes the *model behind the gateway* for jailbreaks, prompt injection,
toxicity and data leakage. Use it to show depth on adversarial ML (OWASP LLM01/LLM07,
MITRE ATLAS AML.T0051/T0054/T0057).

## Install & run (local, free)
```bash
pipx install garak      # or: pip install garak
# Point garak at the gateway via its OpenAI-compatible REST endpoint:
export OPENAI_API_KEY=sk-range-dev
export OPENAI_BASE_URL=http://localhost:8080/v1
garak --model_type openai --model_name bank-assistant \
      --probes promptinject,dan,leakreplay,encoding \
      --report_prefix range-$(date +%F)
```

The HTML/JSONL report lands in `~/.local/share/garak/garak_runs/`. Compare a run with
`GUARDRAIL_MODE=enforce` vs `monitor` to quantify how much the guardrails reduce the
attack success rate - that delta is the headline metric for the board report.

## What each probe maps to
| garak probe   | OWASP LLM | MITRE ATLAS        |
|---------------|-----------|--------------------|
| promptinject  | LLM01     | AML.T0051          |
| dan           | LLM01     | AML.T0054          |
| leakreplay    | LLM07     | AML.T0057          |
| encoding      | LLM01     | AML.T0051 (obfusc) |
