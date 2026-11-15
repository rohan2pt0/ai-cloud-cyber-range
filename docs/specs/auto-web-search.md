# Spec: auto-web-search

Queue item `auto-web-search` in `governance/queue.json` · due 2026-11-26 · added 2026-10-21.

**The ask, as the queue holds it:** Let the AI search the web by itself for questions about things that change

## Outcome for the person

Questions about things that change (prices, news, versions) get a current answer without the person searching.

## Data

Only the public question text goes out; a per-day cap; a threat model first.

## Screen (one action)

In chat: answers show `Searched the web` with its sources; one switch turns it off.

## Test that proves it

Gateway tests: personal or vault text never goes out, the cap holds, off means off, fetched pages are treated as data.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Search behind the gateway's rails.
- **Enterprise, when conditions call for it:** An allow-list of sources and policy per team.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
