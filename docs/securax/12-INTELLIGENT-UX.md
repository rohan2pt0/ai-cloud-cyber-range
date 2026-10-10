# SecuRAX — Intelligent UX (the operator's lens: simple on top, disciplined underneath)

The best institutions — MBB consulting, the Big 4, well-run central banks — are not good
because their people are individually superhuman. They are good because the **method is the
default**: a junior analyst produces partner-grade work because the firm's templates, review
gates and house style do the heavy lifting. SecuRAX borrows exactly that idea for its AI:

> **Make the expert's method the default, so an ordinary user gets an expert-grade, trustworthy
> result by just asking plainly — no prompt-engineering, no jargon, no footguns.**

This page is the design contract behind the "Ask" experience (`assistant/enhance.py`, mirrored
in the Guiding-Map PWA and exposed as the `assist` MCP tool). Three promises, each a
time-tested institutional practice rendered into code.

## 1. Prompt-engineering, done for the user (the "firm template")
A user types a plain question — *"summarise this", "should I move to X?", "draft a reply"*.
Behind the scenes, before anything reaches the model, the question is rewritten into a
disciplined brief, the way an engagement manager would scope a task:

| What the user gives | What the system adds, automatically |
|---|---|
| a casual sentence | a clear **role** (precise advisor, India/BFSI context) |
| no structure | the **Pyramid Principle** — answer first, then the reasons |
| no format | the right **output format for the intent** (MECE) — see table below |
| no safeguards | a hard **anti-fabrication contract** (section 2) |

Intent is detected deterministically (keywords → format), so it works offline and never
surprises the user. The output format per intent:

| Intent | Expert format applied for you |
|---|---|
| **Summarise** | one-line takeaway → 3–5 bullets that matter → one "so what / next action" |
| **Explain** | plain definition → real-world analogy → why it matters → one example (no jargon) |
| **Draft** | ready-to-send: tone, opening, the ask, a close — nothing extra |
| **Decide** | decision frame → options → MECE pros/cons → recommendation + the one tipping reason + main risk |
| **Extract** | clean list; missing field = "(not stated)", never inferred |
| **General** | answer first → the few reasons that matter → one next step |

The user sees none of this machinery — only one-tap **recipe chips** (Summarise / Explain /
Draft / Decide / Extract) and a text box. That is the whole point: the discipline is invisible.

## 2. Least hallucination, by construction (the "review gate")
The single most effective, lowest-cost way to cut fabrication is not a bigger model — it is a
**non-negotiable contract** carried on every request, exactly as a firm forbids juniors from
inventing a number in a client deck. Every SecuRAX answer is bound to:

1. **Answer first**, then the reasons (Pyramid Principle — easy to verify, hard to waffle).
2. Use **only** facts the user gave or the model is confident of; otherwise say *"I'm not
   certain"* and state what would be needed. **Never guess.**
3. **Never invent** numbers, names, dates, citations, prices or links. A live figure (a price,
   a rate, today's law) must be flagged for primary-source verification, not fabricated —
   which is also why the user's standing rule is *always web-search before product/price advice*.
4. Be **concise and plain**; bullets when they help.
5. If ambiguous, ask **one** clarifying question instead of assuming.
6. **Flag** when a decision truly needs a professional (medical/legal/financial/tax).

Grounding is enforced structurally too: when context is supplied, the prompt says *answer only
from this; if the answer isn't here, say so*. And because every request still flows through the
guardrail gateway, Red-tier data is pinned on-device and attack patterns are blocked — safety
and honesty are layered, not either/or.

## 3. Improves after every use (the "lessons-learned file")
A well-run institution keeps a lessons-learned file and actually reads it. SecuRAX does the
same automatically and with **human oversight, never silently**:

- Every answer offers a one-tap **👍 / 👎**.
- A **👎** is captured and routed to the antifragility ledger (`learning/antifragile.py`) as a
  quality failure — the same loop that turns a security bypass into a permanent strength
  (see [Kaizen](11-KAIZEN.md)). A human reviews; the method improves; the fix is verified.
- In the PWA, feedback stays **on-device** (localStorage) — sovereign by default.

This is RLHF-lite done responsibly: real usage sharpens the system, but no rule or prompt is
rewritten unattended (NIST AI RMF, RBI FREE-AI human-in-the-loop).

## 4. Why "simple on top" is a feature, not a compromise
| The operator's principle | How SecuRAX honours it |
|---|---|
| **Don't make the user think** (Krug) | plain box + recipe chips; the brief is written for them |
| **Answer the question** (Minto/Pyramid) | enforced by the contract, every time |
| **MECE, no overlap/gaps** | the per-intent format is MECE by design |
| **Fail safe** | unknowns surface as "I'm not certain", not as a confident wrong answer |
| **Kaizen** (1% better) | 👎 → ledger → review → verified strength, each cycle |
| **One source of truth** | `assistant/enhance.py` is the method; the PWA and MCP mirror it |

## 5. Where it lives (one method, three front doors)
| Front door | For | Entry point |
|---|---|---|
| **Guiding-Map PWA → "Ask"** | the everyday user, zero setup | `guiding-map/index.html` |
| **MCP `assist` tool** | an AI client (Claude, etc.) orchestrating the estate | `mcp/securax_mcp.py` |
| **CLI** | scripts and power users | `python3 assistant/enhance.py enhance "…"` |

All three call the **same contract and the same intent logic**, so the quality and the safety
floor are identical no matter how you ask. That consistency — the firm's house style, enforced
by the system rather than by willpower — is what lets a non-expert operate at an expert level,
every time, with the least chance of being misled.

> Intelligent UX in one line: **the user asks like a human; the system thinks like an expert,
> refuses to make things up, and gets a little better every time you tell it how it did.**
