#!/usr/bin/env python3
"""Intelligent Assistant — world-class answers without the user knowing prompt engineering.

The principle the best institutions run on: make the expert's method the *default*, so an
ordinary user gets an expert-grade result by just asking plainly. This module does three
things that a McKinsey/Big-4 engagement manager would insist on, automatically:

  1. PROMPT ENGINEERING, DONE FOR YOU. A casual question ("summarise this", "should I do X?")
     is rewritten into a disciplined prompt: a clear role, the right output format, the
     Pyramid Principle (answer first, then why), MECE structure, and India/BFSI context —
     without the user doing any of it.

  2. LEAST HALLUCINATION, BY CONSTRUCTION. Every request carries a hard anti-fabrication
     contract: answer only from what is known or provided, say "I'm not certain" rather than
     guess, never invent numbers/citations/links, and flag when live data is needed. This is
     the single most effective, time-tested way to cut hallucination.

  3. IMPROVES AFTER EVERY USE. Thumbs up/down on an answer is captured; a thumbs-down becomes
     a learning item (fed to the antifragility ledger for review), so the system gets better
     from real usage — with human oversight, never silently.

Pure standard library; works offline (deterministic templates). An optional model pass can
enrich it, but the value is in the method, which never fails.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FEEDBACK_LOG = ROOT / "assistant" / "feedback-log.jsonl"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# The non-negotiable contract every answer must honour (anti-hallucination)
# --------------------------------------------------------------------------- #
CONTRACT = (
    "You are a precise, trustworthy advisor for a user in India (BFSI context by default). "
    "Rules you must follow without exception:\n"
    "1. Answer the question first in one line (Pyramid Principle), then the key reasons.\n"
    "2. Use ONLY facts you are confident about or that the user provided. If you are not "
    "sure, say 'I'm not certain' and state what you would need to be sure. Never guess.\n"
    "3. Never invent numbers, names, dates, citations, prices or links. If a current/live "
    "figure (price, rate, law as of today) is needed, say it must be verified from a primary "
    "source and do not fabricate one.\n"
    "4. Be concise and plain. No jargon unless asked. Structure with short bullets when it helps.\n"
    "5. If the question is ambiguous, ask ONE clarifying question instead of assuming.\n"
    "6. Flag clearly when a decision needs a professional (medical/legal/financial/tax)."
)

# Intent → the expert output format for that kind of request (MECE, so-what, actionable).
INTENTS: dict[str, tuple] = {
    # intent: (keywords, format instruction, follow-ups)
    "summarise": (r"summari[sz]|tl;?dr|key points|\bgist\b|\bbrief\b",
        "Give: a one-line takeaway, then 3-5 bullets of the only points that matter, then "
        "one 'so what / next action'.",
        ["Make it even shorter", "What are the risks?", "Draft an email about this"]),
    "explain": (r"\bexplain|what is|what are|how does|how do|help me understand|teach me|eli5|simpl[ey]",
        "Explain simply (as to a smart non-expert): a plain definition, a real-world analogy, "
        "why it matters, and one example. Avoid jargon.",
        ["Give me an example", "How is it used in banking?", "What are common mistakes?"]),
    "draft": (r"\bdraft|\bwrite|compose|e-?mail|message|\breply|letter|\bpost\b",
        "Write it ready-to-send: appropriate tone, clear subject/opening, the ask, and a close. "
        "Keep it tight. Offer nothing the user did not ask for.",
        ["Make it more formal", "Make it shorter", "Add a polite follow-up line"]),
    "decide": (r"should i|decide|compare|\bvs\b|versus|pros and cons|which is (better|best)|\boptions\b",
        "Use a decision frame: state the decision, list options, give a MECE pros/cons table, "
        "then a clear recommendation with the one reason that tips it, and the main risk.",
        ["What would change your recommendation?", "What's the cheapest option?", "What's the safest option?"]),
    "extract": (r"\bextract|find all|\blist\b|pull out|identify|action items|tasks from",
        "Extract exactly what was asked as a clean list. If a field is not present, write "
        "'(not stated)' — do not infer or invent it.",
        ["Turn these into tasks", "Prioritise these (Eisenhower)", "Summarise the list"]),
    "code": (r"\bcode\b|script|function|regex|command|\bbug\b|\berror\b|python|bash|\bsql\b",
        "Give working, minimal code with a one-line explanation. Note any assumption. If you "
        "are unsure it runs, say so and explain how to test it.",
        ["Explain this code", "Make it safer", "Add error handling"]),
}
DEFAULT_FOLLOWUPS = ["Summarise that", "Give me the risks", "What should I do next?"]


def detect_intent(text: str) -> str:
    for name, (kw, _fmt, _f) in INTENTS.items():
        if re.search(kw, text, re.I):
            return name
    return "general"


def classify_tier(text: str) -> str:
    red = re.compile(r"(aadhaar|\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]\b|customer|account\s*no|internal ip|incident)", re.I)
    yellow = re.compile(r"(employee|salary|vendor|contract|roadmap|strategy|non-public)", re.I)
    return "Red" if red.search(text) else ("Yellow" if yellow.search(text) else "Green")


def enhance(user_text: str, context: str = "") -> dict:
    """Turn a casual question into an expert-grade message set for the model."""
    intent = detect_intent(user_text)
    tier = classify_tier(user_text)
    fmt = INTENTS[intent][1] if intent in INTENTS else \
        "Answer directly and usefully: the answer first, then the few reasons that matter, then one next step."
    system = CONTRACT + "\n\nFor THIS request: " + fmt
    if tier == "Red":
        system += ("\n\nNOTE: this contains sensitive/personal data. Stay strictly factual, "
                   "do not suggest sending it anywhere, and assume it must never leave the user's control.")
    parts = []
    if context.strip():
        parts.append("CONTEXT (answer only from this where relevant; if the answer isn't here, say so):\n" + context.strip())
    parts.append("QUESTION:\n" + user_text.strip())
    return {
        "intent": intent,
        "data_tier": tier,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": "\n\n".join(parts)}],
        "followups": (INTENTS[intent][2] if intent in INTENTS else DEFAULT_FOLLOWUPS),
    }


# --------------------------------------------------------------------------- #
# Improve-after-every-use: capture feedback; a thumbs-down becomes a lesson.
# --------------------------------------------------------------------------- #
def record_feedback(question: str, answer: str, rating: str) -> dict:
    """rating: 'up' or 'down'. Stored locally; a 'down' is also logged for review (HITL)."""
    entry = {"ts": dt.datetime.now().isoformat(timespec="seconds"),
             "rating": rating, "question": question[:300], "answer": (answer or "")[:300]}
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    if rating == "down":
        try:
            af = _load("af_engine", "learning/antifragile.py")
            af.record_failure("quality", f"user marked an answer unhelpful: {question[:80]}",
                              question, direction="input", source="assistant-feedback")
        except Exception:  # noqa: BLE001
            pass
    return {"stored": True, "rating": rating}


def feedback_stats() -> dict:
    if not FEEDBACK_LOG.exists():
        return {"total": 0, "up": 0, "down": 0, "satisfaction": None}
    rows = [json.loads(l) for l in FEEDBACK_LOG.read_text().splitlines() if l.strip()]
    up = sum(r["rating"] == "up" for r in rows)
    return {"total": len(rows), "up": up, "down": len(rows) - up,
            "satisfaction": round(up / len(rows), 3) if rows else None}


def main() -> int:
    ap = argparse.ArgumentParser(description="Intelligent assistant — prompt engineering done for you.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enhance"); e.add_argument("question"); e.add_argument("--context", default="")
    f = sub.add_parser("feedback"); f.add_argument("--question", required=True); f.add_argument("--answer", default=""); f.add_argument("--rating", required=True, choices=["up", "down"])
    sub.add_parser("stats")
    a = ap.parse_args()
    if a.cmd == "enhance":
        print(json.dumps(enhance(a.question, a.context), indent=2))
    elif a.cmd == "feedback":
        print(json.dumps(record_feedback(a.question, a.answer, a.rating), indent=2))
    elif a.cmd == "stats":
        print(json.dumps(feedback_stats(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
