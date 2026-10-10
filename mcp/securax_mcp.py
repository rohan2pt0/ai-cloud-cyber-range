#!/usr/bin/env python3
"""SecuRAX MCP server — the intelligent control layer for the whole estate.

MCP (Model Context Protocol) lets any MCP-capable AI client — Claude Desktop, Claude Code,
or a local agent — *operate* SecuRAX by calling its capabilities as tools. Instead of you
running scripts, you just ask: "classify this", "triage these alerts", "what's my posture?",
"plan my FI" — and the AI calls the right tool. That is the "magic": the estate becomes a
set of safe, auditable actions an intelligent assistant can take on your behalf.

Design choices that make it turnkey:
  * ZERO external dependencies — pure Python standard library (no `pip install mcp`).
    It speaks MCP's newline-delimited JSON-RPC 2.0 over stdio directly.
  * It reuses the estate's real code (guardrails, AI-SOC triage, AI-SPM, red-team,
    FIRE, OPSEC), loaded by file path so there are no package-name clashes.
  * Every tool is read-only or local-only and safe to expose to an assistant.

Run it from an MCP client with:  python3 mcp/securax_mcp.py   (see mcp/README.md)
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(mod_name: str, rel_path: str):
    """Load a module by file path and register it so dataclasses resolve correctly."""
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# --- load the estate's real capability modules (fail soft; a missing one disables its tools) ---
_mods: dict[str, object] = {}
for name, path in {
    "gw_guardrails": "apps/llm-gateway/app/guardrails.py",
    "soc_triage": "ai-soc/soc/triage.py",
    "aispm": "redteam/aispm_scan.py",
    "attacks": "redteam/run_attacks.py",
    "fire": "personal-rnd/fin_freedom.py",
    "opsec": "personal-rnd/self_opsec.py",
    "antifragile": "learning/antifragile.py",
    "assistant": "assistant/enhance.py",
    "intel": "intel/global_intel.py",
    "agents": "agents/personas.py",
    "planner": "finance/planner.py",
}.items():
    try:
        _mods[name] = _load(name, path)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[securax-mcp] could not load {name}: {exc}\n")

G = _mods.get("gw_guardrails")
ALLOWED_DOMAINS = {"vulnbank.example", "rbi.org.in", "cybercrime.gov.in"}


# --------------------------------------------------------------------------- #
# Tool implementations — each returns a plain string (rendered to the assistant)
# --------------------------------------------------------------------------- #
def t_classify_tier(text: str) -> str:
    """Red/Yellow/Green data classification — decides what may leave the machine."""
    import re
    red = re.compile(r"(aadhaar|\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]\b|customer|account\s*no|internal ip|incident)", re.I)
    yellow = re.compile(r"(employee|salary|vendor|contract|roadmap|strategy|non-public)", re.I)
    tier = "Red" if red.search(text) else ("Yellow" if yellow.search(text) else "Green")
    route = {"Red": "local model only (never leaves the machine)",
             "Yellow": "local preferred; cloud only after masking",
             "Green": "cloud acceptable"}[tier]
    return f"Tier: {tier}\nRouting: {route}"


def t_guard_input(text: str) -> str:
    v = G.inspect_input(text)
    rules = sorted({f.rule for f in v.findings})
    return json.dumps({"allowed": v.allowed, "risk": v.risk, "rules": rules,
                       "sanitised_text": v.text}, indent=2)


def t_guard_output(text: str) -> str:
    v = G.inspect_output(text, ALLOWED_DOMAINS, {"CANARY-7f3a9c"})
    rules = sorted({f.rule for f in v.findings})
    return json.dumps({"allowed": v.allowed, "risk": v.risk, "rules": rules,
                       "sanitised_text": v.text}, indent=2)


def t_redact_pii(text: str) -> str:
    clean, findings = G.redact_pii(text)
    return json.dumps({"redacted_text": clean,
                       "identifiers_removed": sorted({f.rule for f in findings})}, indent=2)


def t_soc_triage(events_json: str) -> str:
    recs = json.loads(events_json) if events_json.strip() else []
    if isinstance(recs, dict):
        recs = [recs]
    report = _mods["soc_triage"].triage(recs, summarize=True)
    return json.dumps(report, indent=2, default=str)


def t_aispm_posture() -> str:
    m = _mods["aispm"]
    controls = m.posture(ROOT)
    passed = sum(c["status"] == "PASS" for c in controls)
    inv = m.inventory(ROOT)
    gaps = [c["control"] + ": " + c["description"] for c in controls if c["status"] == "GAP"]
    return json.dumps({"posture_score": round(passed / len(controls), 3),
                       "controls_passed": passed, "controls_total": len(controls),
                       "gaps": gaps, "inventory": inv}, indent=2)


def t_redteam_scorecard() -> str:
    m = _mods["attacks"]
    results = [m.run_one(a) for a in m.ATTACKS]
    attacks = [r for r in results if r["expected_blocked"] or r["id"].startswith("pii")]
    defended = sum(r["defended"] for r in attacks)
    benign = [r for r in results if not r["expected_blocked"] and not r["id"].startswith("pii") and r["direction"] != "out"]
    fp = sum(not r["defended"] for r in benign)
    return json.dumps({"total_attacks": len(attacks), "defended": defended,
                       "defense_rate": round(defended / len(attacks), 3),
                       "false_positives": fp}, indent=2)


def t_fire_plan(monthly_expense: float, current_corpus: float = 0.0,
                monthly_invest: float = 0.0, annual_return: float = 0.10,
                inflation: float = 0.06, swr: float = 0.035) -> str:
    plan = _mods["fire"].fi_plan(float(monthly_expense), float(annual_return), float(inflation),
                                 float(swr), float(current_corpus), float(monthly_invest))
    return json.dumps(plan, indent=2)


def t_opsec_footprint(text: str) -> str:
    return json.dumps(_mods["opsec"].footprint_review(text), indent=2)



def t_learn_from_failure(kind: str, summary: str, payload: str = "", direction: str = "input") -> str:
    af = _mods["antifragile"]
    entry = af.record_failure(kind, summary, payload, direction, source="mcp")
    rule = af.propose_rule(payload or summary)
    return json.dumps({"recorded": entry, "proposed_rule": rule,
                       "next": "A human reviews the rule, ships it, then verify() makes this failure a permanent strength."}, indent=2)


def t_antifragility_report() -> str:
    return json.dumps(_mods["antifragile"].report(), indent=2)



def t_assist(question: str, context: str = "") -> str:
    """Prompt-engineer the user's plain question into an expert, low-hallucination request."""
    en = _mods["assistant"]
    plan = en.enhance(question, context)
    out = {"intent": plan["intent"], "data_tier": plan["data_tier"],
           "enhanced_prompt": plan["messages"], "suggested_followups": plan["followups"]}
    gw = os.getenv("GATEWAY_URL")
    if gw:
        try:
            import httpx
            r = httpx.post(gw.rstrip("/") + "/v1/chat/completions", timeout=60,
                           json={"model": "bank-assistant", "messages": plan["messages"]})
            if r.status_code == 200:
                out["answer"] = r.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            out["answer_error"] = str(exc)[:120]
    return json.dumps(out, indent=2)


def t_assistant_feedback(question: str, answer: str, rating: str) -> str:
    return json.dumps(_mods["assistant"].record_feedback(question, answer, rating), indent=2)


def t_financial_plan(inputs_json: str) -> str:
    """Future Financial Planner: from your numbers, the corpus needed at retirement, what your
    assets will grow to, the shortfall/surplus, and the extra monthly SIP that closes it.
    inputs_json shape: see finance/examples/sample-plan.json. Sovereign/offline; verify with a SEBI adviser."""
    pl = _mods["planner"]
    inp = json.loads(inputs_json)
    return json.dumps({"summary": pl.plan(inp), "projection_sample": pl.project(inp)[:3]}, indent=2)


def t_list_advisors() -> str:
    """List the stealth advisor agents you can summon for a first-draft opinion."""
    return json.dumps(_mods["agents"].list_agents(), indent=2)


def t_ask_advisor(agent: str, question: str, context: str = "") -> str:
    """Summon one specialist advisor (legal/finance/cfo/cto/ciso/tax/dietician/coach/chef/
    event/intel/career/engineer). First-draft, grounded, anti-hallucination advice to prepare
    you before a real professional. Runs on the estate's local/free model (no Claude credits)."""
    return json.dumps(_mods["agents"].ask_agent(agent, question, context), indent=2)


def t_global_intel(goal: str, items_json: str, mode: str = "replicate", vocabulary: str = "",
                   profile_json: str = "", opportunities_json: str = "", volume: str = "") -> str:
    """Community-signal decision engine. Paste the high-ranked items YOU collected (Reddit
    Top/All-time, Amazon best-seller/BIFL, top YouTube videos) as a JSON list; get the
    consensus, your capability-fit, the adoption-curve timing (edge mode) and a worst-case plan.
    Grounded only in the data you pass — it never invents rankings."""
    gi = _mods["intel"]
    items = json.loads(items_json) if items_json.strip() else []
    if isinstance(items, dict):
        items = items.get("items", [items])
    vocab = [v.strip() for v in vocabulary.split(",") if v.strip()] or None
    profile = json.loads(profile_json) if profile_json.strip() else None
    opps = json.loads(opportunities_json) if opportunities_json.strip() else None
    vol = [float(x) for x in volume.split(",") if x.strip()] or None
    return json.dumps(gi.decide(goal, items, mode, vocab, profile, opps, vol), indent=2)


# --------------------------------------------------------------------------- #
# Tool registry (name -> (fn, description, inputSchema))
# --------------------------------------------------------------------------- #
def _schema(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required}


_STR = {"type": "string"}
_NUM = {"type": "number"}

TOOLS: dict[str, tuple] = {
    "classify_data_tier": (t_classify_tier,
        "Classify text as Red/Yellow/Green and say where it may be processed.",
        _schema({"text": _STR}, ["text"])),
    "guardrail_check_input": (t_guard_input,
        "Scan an inbound prompt through the input rails (prompt-injection, PII, secrets, limits).",
        _schema({"text": _STR}, ["text"])),
    "guardrail_check_output": (t_guard_output,
        "Scan model output through the output rails (secrets, exfil links, canary, active content).",
        _schema({"text": _STR}, ["text"])),
    "redact_pii": (t_redact_pii,
        "Redact India BFSI PII (Aadhaar/PAN/card/UPI/mobile/email) from text, checksum-verified.",
        _schema({"text": _STR}, ["text"])),
    "soc_triage": (t_soc_triage,
        "Correlate security telemetry (JSON list of gateway/Falco/cloud events) into incidents mapped to MITRE ATLAS/ATT&CK.",
        _schema({"events_json": _STR}, ["events_json"])),
    "aispm_posture": (t_aispm_posture,
        "Run the AI Security Posture Management scan over the estate and return the score, gaps and inventory.",
        _schema({}, [])),
    "redteam_scorecard": (t_redteam_scorecard,
        "Run the adversarial-ML attack suite and return the defence rate and false-positive count.",
        _schema({}, [])),
    "fire_plan": (t_fire_plan,
        "Financial-independence (FIRE) plan: corpus target and years-to-FI from your numbers (Indian context).",
        _schema({"monthly_expense": _NUM, "current_corpus": _NUM, "monthly_invest": _NUM,
                 "annual_return": _NUM, "inflation": _NUM, "swr": _NUM}, ["monthly_expense"])),
    "opsec_footprint": (t_opsec_footprint,
        "Review text about YOURSELF for over-shared identifiers and embedded prompt-injection (self-OPSEC).",
        _schema({"text": _STR}, ["text"])),
    "learn_from_failure": (t_learn_from_failure,
        "Record a failure (bypass/incident/false-positive) so it becomes a permanent strength; returns a proposed detection rule (human ships it).",
        _schema({"kind": _STR, "summary": _STR, "payload": _STR, "direction": _STR}, ["kind", "summary"])),
    "antifragility_report": (t_antifragility_report,
        "Report the antifragility score: how many past failures the current defences now withstand.",
        _schema({}, [])),
    "assist": (t_assist,
        "Answer a plain question the expert way: auto prompt-engineering + anti-hallucination contract; returns the answer when the gateway is up.",
        _schema({"question": _STR, "context": _STR}, ["question"])),
    "assistant_feedback": (t_assistant_feedback,
        "Record thumbs up/down on an answer so the system improves from real use (down = a lesson for review).",
        _schema({"question": _STR, "answer": _STR, "rating": _STR}, ["question", "rating"])),
    "financial_plan": (t_financial_plan,
        "Future Financial Planner: corpus needed at retirement, projected corpus, shortfall/surplus and the extra monthly SIP to close it (from finance/examples/sample-plan.json shape). Sovereign/offline.",
        _schema({"inputs_json": _STR}, ["inputs_json"])),
    "list_advisors": (t_list_advisors,
        "List the stealth advisor agents (legal, finance, CFO, CTO, CISO, tax, dietician, coach, chef, event, intel, career, engineer).",
        _schema({}, [])),
    "ask_advisor": (t_ask_advisor,
        "Summon one specialist advisor for a first-draft, anti-hallucination opinion before you see a real professional. Runs on the estate's local/free model (no Claude credits).",
        _schema({"agent": _STR, "question": _STR, "context": _STR}, ["agent", "question"])),
    "global_intel": (t_global_intel,
        "Decide the community-proven way: paste ranked items you collected (Reddit Top/All-time, "
        "Amazon best-seller/BIFL, top videos) -> consensus + your capability-fit + adoption-curve "
        "timing + worst-case plan. mode='replicate' to copy a proven playbook, 'edge' to get in "
        "before it commoditises. Grounded only in your data; never invents rankings.",
        _schema({"goal": _STR, "items_json": _STR, "mode": _STR, "vocabulary": _STR,
                 "profile_json": _STR, "opportunities_json": _STR, "volume": _STR},
                ["goal", "items_json"])),
}


# --------------------------------------------------------------------------- #
# Minimal MCP (JSON-RPC 2.0 over newline-delimited stdio) — no dependencies
# --------------------------------------------------------------------------- #
PROTOCOL_VERSION = "2024-11-05"


def _result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(msg: dict):
    method = msg.get("method")
    req_id = msg.get("id")
    if method == "initialize":
        return _result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "securax", "version": "1.0.0"},
        })
    if method in ("notifications/initialized", "initialized"):
        return None  # notification: no response
    if method == "ping":
        return _result(req_id, {})
    if method == "tools/list":
        tools = [{"name": n, "description": d, "inputSchema": s} for n, (_, d, s) in TOOLS.items()]
        return _result(req_id, {"tools": tools})
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        entry = TOOLS.get(name)
        if not entry:
            return _error(req_id, -32602, f"unknown tool: {name}")
        fn = entry[0]
        try:
            text = fn(**args)
            return _result(req_id, {"content": [{"type": "text", "text": text}], "isError": False})
        except Exception as exc:  # noqa: BLE001
            tb = traceback.format_exc(limit=3)
            return _result(req_id, {"content": [{"type": "text", "text": f"error: {exc}\n{tb}"}],
                                    "isError": True})
    if req_id is not None:
        return _error(req_id, -32601, f"method not found: {method}")
    return None


def main() -> int:
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
