"""Careful mode: draft, check each claim, rewrite (doc 89, a chain-of-verification pass).

For an important question a person can ask the gateway to check the answer before they see it. The model drafts an answer as
usual, then a second call lists each factual claim in the draft and marks it SUPPORTED, UNSURE or WRONG against the question and
any documents in the chat. If anything is UNSURE or WRONG, a third call rewrites the draft without the wrong claims, with the
unsure ones marked as unsure, in the format the person asked for. It costs about twice the tokens, so it is opt-in per request:

    X-SecuRAX-Careful: 1                  the request header, or
    model "bank-assistant-careful"        any alias with the suffix -careful (it runs on the base alias)
    CAREFUL=off                           the operator's switch: the header and suffix are ignored (the suffix still resolves)

Every extra call goes through the same input and output rails, residency decision, allowance and audit as the first one; the
gateway in main.py does that. If the check or the rewrite cannot be done (a model error, a rail, the allowance), the person
gets the draft and the response says `X-SecuRAX-Careful: draft-only`. Exact-format callers (response_format, chat apps'
housekeeping) and tool-calling requests are left alone, like the answer rules (answering.exact_format). Standard library only.
"""
from __future__ import annotations

import os
import re

from . import answering

SUFFIX = "-careful"
HEADER = "x-securax-careful"
VERDICTS = ("SUPPORTED", "UNSURE", "WRONG")
_ROW = re.compile(r"\b(SUPPORTED|UNSURE|WRONG)\b")

CHECK = (
    "Check the answer you just gave before the person sees it. List each factual claim in it (a fact, number, name, date, "
    "law, price, quote, link or command), one per line, in this form:\n"
    "<the claim> | <verdict> | <why, in a few words>\n"
    "The verdict is one word, one of SUPPORTED, UNSURE, WRONG: SUPPORTED when the question, the documents in this chat or "
    "well-established knowledge back it; UNSURE when you cannot be sure it is right or current; WRONG when it is false or "
    "contradicts the question or a document. Judge only; do not rewrite the answer. If the answer makes no factual claim, "
    "reply: NO CLAIMS.")

REWRITE = (
    "Here is a claim-by-claim check of your answer:\n\n{check}\n\n"
    "Rewrite your answer for the person. Remove every claim marked WRONG (correct it only if the question or a document gives "
    "the right fact). Keep a claim marked UNSURE only if it matters, and then say plainly that it is unsure and how to check "
    "it. Keep everything SUPPORTED. Keep the format, language and length the person asked for. Reply with the rewritten answer "
    "only, with no mention of this check.")


def enabled() -> bool:
    return os.getenv("CAREFUL", "on").strip().lower() not in ("off", "0", "false", "no")


def split_alias(model: str) -> tuple[str, bool]:
    """('bank-assistant-careful') -> ('bank-assistant', True); any other name -> (name, False)."""
    m = model or ""
    if m.endswith(SUFFIX) and len(m) > len(SUFFIX):
        return m[: -len(SUFFIX)], True
    return m, False


def wanted(by_alias: bool, headers=None) -> bool:
    """Did the caller ask for careful mode (the -careful alias, or the header)?"""
    if not enabled():
        return False
    h = (headers.get(HEADER) or "").strip().lower() if headers is not None else ""
    return by_alias or h in ("1", "on", "true", "yes")


def eligible(payload: dict, headers=None) -> bool:
    """Only a plain chat answer is checked: never an exact-format caller (JSON, housekeeping) or a request with tools."""
    return not answering.exact_format(payload, headers) and not payload.get("tools") and not payload.get("functions")


def aliases(ids: list[str]) -> list[str]:
    """The -careful names to offer in /v1/models: one per chat model that exists in the list."""
    if not enabled():
        return []
    have, chat = set(ids), answering.models()
    return [i + SUFFIX for i in ids if i in chat and not i.endswith(SUFFIX) and i + SUFFIX not in have]


def check_messages(messages: list[dict], draft: str) -> list[dict]:
    return list(messages) + [{"role": "assistant", "content": draft}, {"role": "user", "content": CHECK}]


def rewrite_messages(messages: list[dict], draft: str, check: str) -> list[dict]:
    return list(messages) + [{"role": "assistant", "content": draft},
                             {"role": "user", "content": REWRITE.format(check=check.strip())}]


def flagged(check: str) -> int:
    """How many claims the check marked UNSURE or WRONG. A line naming more than one verdict (an echo of the instruction) is
    not a verdict."""
    n = 0
    for line in (check or "").splitlines():
        found = _ROW.findall(line)
        if len(found) == 1 and found[0] != "SUPPORTED":
            n += 1
    return n


def judged(check: str) -> bool:
    """The check gave verdicts (or said there was nothing to check); anything else is a failed step."""
    lines = (check or "").splitlines()
    if any(line.strip().strip(".").upper() == "NO CLAIMS" for line in lines):
        return True
    return any(len(_ROW.findall(line)) == 1 for line in lines)


def footnote(content: str, n: int) -> str:
    """Say so, in plain text, when the check removed or flagged claims (never on a JSON-looking reply)."""
    body = (content or "").strip()
    if n <= 0 or not body or body[:1] in "{[":
        return content
    what = "1 claim" if n == 1 else f"{n} claims"
    return (content.rstrip() + f"\n\n(Checked carefully: {what} in the first draft could not be supported, so the answer "
            "leaves them out or marks them unsure. Check anything important against a primary source.)")
