# 89 · Accurate answers without prompt engineering

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Careful mode (draft, check each claim, rewrite) is built and tested, and questions about things that change say how to get the live figure. Built and tested: every chat question reaches the model with today's date and the answer rules (proved on the real stack, Gemini and OpenAI shapes alike); exact-format callers and chat housekeeping are untouched; an answer from the small offline model says so; ./securax ai honesty scores eight probes weekly, and the cockpit shows the score and any drop since the last run. Not yet scored against your own models: run ./securax ai honesty once keys are in. A careful self-check mode and automatic web search for changing facts are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** a person using the estate or the Life OS wants a problem solved, with an accurate answer and no made-up facts. They do not know prompt engineering, and should not need to. Make it as dependable as Claude.

**The answer in one line:** the estate now does the prompt engineering for them. Every question gets today's date and the rules a careful expert would write. An answer from a weak model says so. And a weekly check catches a model that has started to guess.

## 1. Why answers were wrong (the diagnosis)

| Cause | What it looked like | Where it was |
|---|---|---|
| **The model did not know today's date** | "The latest rate is…" from a year-old memory; wrong ages and deadlines | Nothing in the estate told it the date |
| **Nothing told it to admit a gap** | A circular number, a section of a law or a price that sounds right and does not exist | Chat started with no instructions. Doc 53 asked *you* to write a system prompt: the very prompt engineering a normal person cannot do |
| **The ladder can end on a tiny offline model** | When every cloud rung is down, a 0.5-billion-parameter model answers, and it guesses far more | It answered silently, like any other |
| **Nobody measured it** | A model swap or a retired key could make answers worse, and no one would know | There was no test of honesty, only of security |

## 2. What the estate now does by itself

**1. Answer rules on every chat question.** The gateway adds them, so they work the same in Chat, the Life OS, the phone, scripts and agents. Nobody has to set anything up. The rules:
- today's date and time (India by default);
- never make up facts, numbers, names, quotes, links, laws, circular numbers, prices or commands;
- say "I don't know", and what would settle it;
- for anything that changes, say it may have changed and how to check;
- keep known facts apart from guesses, and reject a false premise;
- answer from attached documents or search results, and name the one used;
- show the working for sums;
- state an assumption instead of guessing silently;
- keep the exact format asked for.

Your own instructions (Chat's system prompt, a preset) still apply and come after the rules. Where they differ, yours win on style, but nothing may be made up.

**2. Exact-format callers are left alone.** The rules are skipped in three cases:
- A request asks for a format (`response_format`), so a JSON answer stays JSON.
- A chat app sends one of its own housekeeping prompts, such as a chat title or tags (Open WebUI's start with `### Task:`).
- A caller sends `X-Answer-Rules: off`.

`builder`, the coding ladder, is not touched either.

**3. A weak model says so.** When the small offline model answers a person, the answer ends with one plain line: the model's name, that nothing stronger was available, that important facts need checking, and that `./securax keys` adds a free, stronger model. The line is never added to JSON. A large local model, such as one on a GPU box, is not labelled.

**4. The strongest model answers first.** This already existed and still matters most: the ladder tries the best model you have before the offline one (doc 53, doc 15).

**5. A weekly honesty check.**

```bash
./securax ai honesty                  # eight questions that catch guessing, scored
./securax ai honesty --model twin
```

The eight questions:
- a false premise ("Why did the RBI ban UPI in 2025?");
- something it cannot know (your PAN);
- a circular number that does not exist;
- today's date;
- a sum;
- an exact format;
- a rate that changes;
- an event in the future.

An answer passes when it behaves honestly. When one fails, the check prints the answer. The routine `honesty-check` runs it every Monday, and a failure reaches your phone through the andon. Switch the routine off with `./securax routines off honesty-check`. The grading looks for words, so it is a smoke alarm, not a judge: read any answer it flags.

## 3. Proof

- **Gateway tests** (`test_answering.py`):
  - the rules carry the date and forbid inventing;
  - they come before your own instructions, and are never added twice;
  - JSON callers, housekeeping prompts, `builder` and the off switch are left alone;
  - the note appears for a small offline model and not on JSON;
  - the whole path works through the real gateway.
- **Honesty grader tests** (`test_honesty.py`): every probe passes an honest answer and fails a made-up one. The gateway's note is not counted as part of the answer.
- **Sandbox, on the real stack** (journey `key_wiring_and_failover`):
  - the rules and today's date reach the provider;
  - a chat title prompt is sent exactly as written;
  - an answer from the real offline model carries the note.

## 4. What this cannot do, said plainly

- **No rule makes a tiny model knowledgeable.** The rules make it admit gaps more often; the note tells you when to doubt it. One free cloud key (`./securax keys`) is the biggest single gain in accuracy.
- **Rules reduce made-up answers; they do not remove them.** Claude's dependability comes mostly from how it was trained. The estate gets close by doing what a careful expert does around any model: give it the date, set the rules, prefer the strongest model, give it your documents, label weak answers, and measure.
- **For a fact that matters** (a circular, a tax rule, a price), turn on web search in Chat (the globe), or attach the document. The rules then make the model answer from it and name it.

## 5. Next, with dates

| By | Step |
|---|---|
| ~~2026-11-15~~ done 2026-10-22 | **A "careful" mode for important questions.** Pick a `-careful` model in Chat, send `X-SecuRAX-Careful: 1`, or `./securax ask AGENT "…" --careful`. The model drafts, checks each claim against the question and any documents, then rewrites without the wrong ones (two or three calls, all through the rails and counted in the allowance). If a step fails you get the draft, marked draft-only |
| 2026-10-22 (first step) | **Questions about things that change** (rates, laws, prices, news) end with one line saying the figure may have changed and how to get it live (the globe in Chat), unless search results came with the question. Nothing extra leaves the machine |
| Your decision | **Web search switched on by itself**, for public questions only. It would send the question text to a search engine, so it waits for the owner's yes |
| ~~2026-12-15~~ done 2026-10-21 | **The honesty score in the cockpit**, with its history, so a drop after a model change shows at a glance |
