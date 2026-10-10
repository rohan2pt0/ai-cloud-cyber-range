#!/usr/bin/env python3
"""Agents army — a roster of specialist advisors, stealth until you summon one.

Each agent is a role-specialised wrapper around the SAME anti-hallucination contract the
Guiding Map's assistant uses (assistant/enhance.py), plus a hard rule that it gives a
*first-draft* opinion to prepare you — never the final word. You take the first advice from
the agent (fast, free, grounded in globally accepted standards), then a second and final
advice from a real licensed professional. 80/20: the agent gets you 80% of the way for 0 cost.

Design that matches SecuRAX principles:
  * STEALTH: nothing runs in the background. An agent exists only when you call it.
  * SOVEREIGN + FREE: runs through the estate gateway / LiteLLM, which defaults to the LOCAL
    model (Ollama). No Claude credits are spent. Works offline as a deterministic prompt builder
    when no gateway is configured (which is how the tests run).
  * LEAST HALLUCINATION: every agent inherits the "answer first, never invent numbers/laws/
    prices, say 'I'm not certain', flag when a professional is needed" contract.

    python3 agents/personas.py list
    python3 agents/personas.py ask ciso "How should I phase zero-trust at home?"
    python3 agents/personas.py ask tax  "Old vs new regime for my salary?"   # verify current law!
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Reuse the ONE anti-hallucination contract (single source of the method).
_ASSIST = _load("assist_enhance", "assistant/enhance.py")
BASE_CONTRACT = _ASSIST.CONTRACT if hasattr(_ASSIST, "CONTRACT") else (
    "Answer the question first, use only facts you are confident about, never invent "
    "numbers/dates/citations/prices, and flag when a professional is needed.")

# The rule that makes an agent a safe FIRST opinion, not a substitute for a professional.
ADVISOR_RULE = (
    "\n\nYou are acting as a {role}. Give practical, first-draft advice grounded in globally "
    "accepted standards and Indian / BFSI context by default. State your key assumptions in one "
    "line. This is a FIRST opinion to help the user prepare and ask better questions — it is NOT "
    "a final or binding decision. For anything high-stakes or binding, tell the user to confirm "
    "with {professional}. Never fabricate laws, figures, prices or rules; if a current value is "
    "needed, say it must be verified from a primary source.")

# key -> (display name, role, who to consult for the final word, one-line expertise)
PERSONAS: dict[str, tuple] = {
    "legal":     ("Legal Advisor", "legal advisor (India)", "a licensed advocate",
                  "Contracts, rights, consumer/property/employment basics, compliance red flags."),
    "finance":   ("Personal Finance Advisor", "personal-finance advisor", "a SEBI-registered investment adviser",
                  "Budgeting, investing, FIRE, insurance, debt payoff — Indian context."),
    "cfo":       ("CFO", "chief financial officer", "a qualified CA / finance head",
                  "Cash flow, unit economics, pricing, fundraising, financial controls for a venture."),
    "cto":       ("CTO", "chief technology officer", "a senior architect you trust",
                  "Architecture, build-vs-buy, scaling, tech-debt and delivery trade-offs."),
    "ciso":      ("CISO", "chief information security officer", "a security lead / auditor",
                  "Security strategy, risk, RBI/ISO/NIST alignment, incident response, zero-trust."),
    "tax":       ("Tax Advisor", "tax advisor (India)", "a practising chartered accountant",
                  "Income tax, capital gains, deductions, regime choice — verify current-year rates."),
    "dietician": ("Dietician", "dietician", "a registered dietician or doctor",
                  "Balanced Indian diet, portion/macros, sustainable eating habits."),
    "coach":     ("Fitness Coach", "fitness coach", "a certified trainer or physiotherapist",
                  "Progression, form cues, recovery, home/band workouts."),
    "chef":      ("Chef", "chef", "—",
                  "Quick healthy Indian meals, batch cooking, ingredient substitutions."),
    "event":     ("Event Planner", "event planner", "your venue/vendors in writing",
                  "Logistics, budgets, timelines, checklists, vendor coordination."),
    "intel":     ("Intelligence Analyst", "open-source intelligence analyst", "legal counsel if anything is sensitive",
                  "Ethical OSINT, trend/pattern analysis, self-OPSEC — defensive and lawful only."),
    "career":    ("Career Coach", "career coach", "a mentor in your field",
                  "BFSI/cyber career moves, certifications, interview and positioning strategy."),
    "engineer":  ("SecuRAX Engineer", "senior software engineer working on SecuRAX", "a code review before shipping",
                  "Proposes code/architecture changes to SecuRAX itself — the credit-saver: runs on your local/free model."),
}


def list_agents() -> list[dict]:
    return [{"key": k, "name": v[0], "consult": v[2], "expertise": v[3]} for k, v in PERSONAS.items()]


def build_messages(agent: str, question: str, context: str = "") -> list[dict]:
    if agent not in PERSONAS:
        raise KeyError(f"unknown agent '{agent}'. Options: {', '.join(PERSONAS)}")
    _name, role, professional, _exp = PERSONAS[agent]
    system = BASE_CONTRACT + ADVISOR_RULE.format(role=role, professional=professional)
    user = (("CONTEXT (use only this where relevant):\n" + context.strip() + "\n\n") if context.strip() else "") \
        + "QUESTION:\n" + question.strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def ask_agent(agent: str, question: str, context: str = "", call_gateway: bool = True) -> dict:
    """Summon one agent. Returns the grounded message set, and the answer if a gateway is up.
    Defaults to the estate's local/free model via GATEWAY_URL — zero Claude credits."""
    messages = build_messages(agent, question, context)
    out = {"agent": agent, "name": PERSONAS[agent][0], "consult": PERSONAS[agent][2], "messages": messages}
    gw = os.getenv("GATEWAY_URL")
    if call_gateway and gw:
        try:
            import httpx
            r = httpx.post(gw.rstrip("/") + "/v1/chat/completions", timeout=90,
                           json={"model": "bank-assistant", "messages": messages})
            if r.status_code == 200:
                out["answer"] = r.json()["choices"][0]["message"]["content"]
            else:
                out["answer_error"] = f"gateway HTTP {r.status_code}"
        except Exception as exc:  # noqa: BLE001
            out["answer_error"] = str(exc)[:120]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Agents army — summon a specialist advisor (first-draft opinion).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list the advisors")
    a = sub.add_parser("ask", help="ask an advisor")
    a.add_argument("agent"); a.add_argument("question"); a.add_argument("--context", default="")
    args = ap.parse_args()
    if args.cmd == "list":
        print(json.dumps(list_agents(), indent=2))
    else:
        print(json.dumps(ask_agent(args.agent, args.question, args.context), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
