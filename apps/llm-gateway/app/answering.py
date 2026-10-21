"""Accurate answers without prompt engineering: the rules a careful expert would write, added by the gateway (doc 89).

A person asking the estate a question should not need to know how to prompt a model. Most wrong answers come from a few causes:
the model does not know today's date, fills a gap with something that sounds right (a circular number, a price, a law), treats
a guess as a fact, or quietly answers from a tiny offline model. So, for the chat models, every request gets one short set of
answer rules in front of the conversation, and an answer from a small offline model says so.

    ANSWER_RULES=on|off              default on
    ANSWER_MODELS=a,b,...            the models the rules apply to (default: the chat models, not `builder`)
    ANSWER_CONTEXT="..."             the default context the rules name (default: India, rupees, Indian law and tax)
    ANSWER_UTC_OFFSET_MIN=330        the clock the rules give the model (default India, UTC+5:30)
    ANSWER_WEAK_BELOW_B=4            a local model smaller than this many billion parameters is labelled "small"

Left alone on purpose, because their callers need an exact format: requests that set `response_format`, chat apps' own
housekeeping tasks (Open WebUI's title, tag and follow-up prompts start with "### Task:"), and any caller that sends
the header `X-Answer-Rules: off`. The person's own instructions still apply and come after the rules; where they differ, theirs
win, except that nothing may be made up. Standard library only.
"""
from __future__ import annotations

import datetime as dt
import os
import re

MARK = "Answer rules (added by SecuRAX for accuracy"
NOTE = "Answered by the small offline model"
DEFAULT_MODELS = "bank-assistant,bank-assistant-gemini,bank-assistant-local,twin"
SIZE = re.compile(r"[:\-_](\d+(?:\.\d+)?)b\b", re.I)


def enabled() -> bool:
    return os.getenv("ANSWER_RULES", "on").strip().lower() not in ("off", "0", "false", "no")


def models() -> set[str]:
    return {m.strip() for m in os.getenv("ANSWER_MODELS", DEFAULT_MODELS).split(",") if m.strip()}


def now() -> dt.datetime:
    off = int(os.getenv("ANSWER_UTC_OFFSET_MIN", "330") or 0)
    return dt.datetime.now(dt.timezone(dt.timedelta(minutes=off)))


def rules(at: dt.datetime | None = None) -> str:
    at = at or now()
    off = at.utcoffset() or dt.timedelta(0)
    sign, mins = ("+" if off >= dt.timedelta(0) else "-"), abs(int(off.total_seconds() // 60))
    ctx = os.getenv("ANSWER_CONTEXT", "India (amounts in rupees, Indian law and tax)").strip()
    return "\n".join([
        f"{MARK}; the person did not write them. Follow them in every answer.)",
        f"- Today is {at:%A, %d %B %Y}, {at:%H:%M} (UTC{sign}{mins // 60:02d}:{mins % 60:02d}). Your training data is older than today.",
        "- Never make up facts, numbers, names, quotes, links, laws, section or circular numbers, prices or commands. "
        "If you do not know, say so plainly, and say what would settle it.",
        "- For anything that changes (prices, interest rates, laws and rules, versions, news, who holds a post), say it may "
        "have changed since your training and how to check it, unless documents or search results in this chat give it.",
        "- Keep what you know apart from what you infer. Mark a guess as a guess. Do not accept a false premise in the question: "
        "say what is wrong with it.",
        "- When the chat has documents or search results, answer from them and say which one. If they do not cover it, say that.",
        "- For sums, show the working in short steps and check the result.",
        "- If the question can be read two ways and the answer depends on it, answer the likely reading and state the "
        "assumption in one line. Ask a question instead only when a wrong guess would be costly.",
        "- Give exactly the format asked for (JSON, a table, one word). Be brief unless asked for detail.",
        f"- Default context: {ctx}, unless the person says otherwise.",
        "- Instructions from the person that follow take priority over these, except that nothing may be made up.",
    ])


def _text(m: dict) -> str:
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):                                   # multimodal: [{"type": "text", "text": ...}, ...]
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
    return ""


def applies(payload: dict, headers=None) -> bool:
    if not enabled() or (payload.get("model") or "") not in models() or payload.get("response_format"):
        return False
    if headers is not None and (headers.get("x-answer-rules") or "").strip().lower() == "off":
        return False
    msgs = payload.get("messages") or []
    users = [m for m in msgs if isinstance(m, dict) and m.get("role") == "user"]
    if users and _text(users[-1]).lstrip().startswith("### Task:"):
        return False
    return not any(MARK in _text(m) for m in msgs if isinstance(m, dict) and m.get("role") == "system")


def apply(payload: dict, headers=None, at: dt.datetime | None = None) -> bool:
    """Put the rules first in the conversation (before the person's own system prompt, which then wins on style). True if added."""
    if not applies(payload, headers):
        return False
    payload["messages"] = [{"role": "system", "content": rules(at)}] + list(payload.get("messages") or [])
    return True


def weak(served: str) -> bool:
    """A local (Ollama) model small enough that its facts need checking."""
    s = (served or "").lower()
    if "ollama" not in s and "qwen" not in s and "llama" not in s and "gemma" not in s and "phi" not in s:
        return False
    m = SIZE.search(s)
    return bool(m) and float(m.group(1)) < float(os.getenv("ANSWER_WEAK_BELOW_B", "4") or 4)


def footnote(content: str, served: str, payload: dict, headers=None) -> str:
    """Say so when a small offline model answered a person (never on a JSON or exact-format reply). Plain text, so it reads
    the same in Chat, the Life OS and a terminal. A caller that shows the text in its own page can send X-Answer-Note: off."""
    if not enabled() or (payload.get("model") or "") not in models() or payload.get("response_format"):
        return content
    if headers is not None and (headers.get("x-answer-note") or "").strip().lower() == "off":
        return content
    body = (content or "").strip()
    if not body or body[:1] in "{[" or not weak(served):
        return content
    name = served.split("/")[-1]
    return (content.rstrip() + f"\n\n({NOTE} {name}, because no stronger model was available. Check anything important; "
            "./securax keys adds a free, stronger one.)")
