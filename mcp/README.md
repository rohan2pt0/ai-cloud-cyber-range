# SecuRAX MCP Server — let an AI operate the estate

**MCP (Model Context Protocol)** is the "magic" that makes SecuRAX simple and intelligent:
instead of running scripts, you *talk* to an AI assistant (Claude Desktop, Claude Code, or a
local agent) and it calls the estate's capabilities as tools. "Classify this." "Triage these
alerts." "What's my security posture?" "Plan my financial independence." The assistant does it.

- **Zero dependencies** — pure Python standard library. No `pip install` needed.
- **Safe** — every tool is read-only or local-only; nothing destructive is exposed.
- **Reuses the real engines** — the same guardrails, AI-SOC, AI-SPM, red-team and personal
  tools the rest of the estate uses.

## Tools exposed (9)
| Tool | What it does |
|---|---|
| `classify_data_tier` | Red/Yellow/Green — what may leave the machine |
| `guardrail_check_input` | scan a prompt (injection, PII, secrets, limits) |
| `guardrail_check_output` | scan model output (secrets, exfil links, canary) |
| `redact_pii` | strip Aadhaar/PAN/card/UPI (checksum-verified) |
| `soc_triage` | correlate telemetry into MITRE-mapped incidents |
| `aispm_posture` | AI-security posture score + gaps + inventory |
| `redteam_scorecard` | run the adversarial-ML suite, return defence rate |
| `fire_plan` | financial-independence plan (Indian context) |
| `opsec_footprint` | self-OPSEC review of text about yourself |

## Connect it to Claude Desktop (Windows/Mac)
Edit `claude_desktop_config.json` (Settings → Developer → Edit Config) and add:
```json
{
  "mcpServers": {
    "securax": {
      "command": "python3",
      "args": ["ABSOLUTE/PATH/TO/ai-cloud-cyber-range/mcp/securax_mcp.py"]
    }
  }
}
```
On Windows use the full path, e.g. `C:\\Users\\You\\ai-cloud-cyber-range\\mcp\\securax_mcp.py`
and `"command": "python"`. Restart Claude Desktop — the SecuRAX tools appear in the hammer menu.

## Connect it to Claude Code (CLI)
```bash
claude mcp add securax -- python3 /ABSOLUTE/PATH/ai-cloud-cyber-range/mcp/securax_mcp.py
```

## Try it (from the AI assistant)
> "Use securax to classify: *Customer Aadhaar 2345 6789 0123 wants a loan*"  → **Red, stays local**
> "Use securax to run the red-team scorecard"  → **100% defended, 0 false positives**
> "Use securax: fire_plan for monthly expense 150000, corpus 2500000, invest 200000"

## Quick self-test (no AI client needed)
```bash
python3 -m pytest mcp/tests -q        # smoke test the server
# or a manual handshake:
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 mcp/securax_mcp.py
```
