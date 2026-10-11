"""Smoke test: the MCP server answers initialize, tools/list and a tools/call."""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVER = ROOT / "mcp" / "securax_mcp.py"

def _rpc(messages):
    inp = "\n".join(json.dumps(m) for m in messages) + "\n"
    out = subprocess.run([sys.executable, str(SERVER)], input=inp, capture_output=True,
                         text=True, timeout=60).stdout
    return [json.loads(l) for l in out.splitlines() if l.strip()]

def test_handshake_list_and_call():
    resps = _rpc([
        {"jsonrpc":"2.0","id":1,"method":"initialize","params":{}},
        {"jsonrpc":"2.0","id":2,"method":"tools/list"},
        {"jsonrpc":"2.0","id":3,"method":"tools/call",
         "params":{"name":"classify_data_tier","arguments":{"text":"Aadhaar 2345 6789 0123"}}},
    ])
    by_id = {r.get("id"): r for r in resps}
    assert by_id[1]["result"]["serverInfo"]["name"] == "securax"
    names = {t["name"] for t in by_id[2]["result"]["tools"]}
    assert "classify_data_tier" in names and "soc_triage" in names and "learn_from_failure" in names and "assist" in names and "global_intel" in names and "ask_advisor" in names and "financial_plan" in names and "web_research" in names and "image_generate" in names and len(names) == 19
    assert "execute_action" not in names  # HITL writes are CLI-only; never model-callable
    assert "Red" in by_id[3]["result"]["content"][0]["text"]

def test_unknown_tool_errors():
    resps = _rpc([{"jsonrpc":"2.0","id":9,"method":"tools/call",
                   "params":{"name":"nope","arguments":{}}}])
    assert resps[0].get("error") or resps[0]["result"].get("isError")
