# Spec: synthetic-people

Queue item `synthetic-people` · due 2026-12-20 · added 2026-11-17.

**The ask:** Reporting friction and steering its fixes distracts the owner from living the system, which defeats the point of SecuRAX.
Build agents that use the apps the way people do, on emulated phones and in browsers, find what is hard or broken, and get it fixed automatically.
Use the open-source tools that already exist (Selenium/Playwright, Postman, Burp and their open alternatives), at a light weight. The bar is
autonomous agents like Manus that act in the real world as a person would.

## Outcome for the person

The owner reports nothing. Every night, synthetic people with different habits try to do real things in the Life OS and the estate. Each failure becomes a fix
that waits in one weekly pull request. The owner sees one line a week: "Found 7, fixed 5, 2 waiting (dated)."

## The stack: four layers, the cheapest first

| Layer | Runs | Tool (open source) | What it catches |
|---|---|---|---|
| 1. Scripted people | every PR, free | Playwright (already in CI): persona, device (9 phones and tablets), robustness and UI audits | broken screens, nonsense values, contrast, sideways scroll |
| 2. **Goal-driven people** | every night | `sandbox/synthetic_users.py` (new): a person with a goal in plain words ("note what Amit said after the call"). It sees only what a person sees (the accessibility tree: roles, names, text) and taps by visible words, with a simple brain today and an LLM brain once a model is available (browser-use, MIT, any OpenAI-compatible model, local or open) | dead ends, too many steps, a wrong tap, a word that does not say what it does, a goal it cannot reach |
| 3. Attackers and API callers | every night | Schemathesis (MIT; property-based fuzzing from the gateway's OpenAPI, the open answer to Postman collections) and OWASP ZAP baseline (Apache-2.0; the open answer to Burp) against the sandbox estate | 500 errors, schema breaks, missing headers, injection |
| 4. Real phones | weekly, later | a real Android emulator (android-emulator-runner, KVM on GitHub's Linux runners) driven by Midscene.js (MIT; vision, natural language, adb), with an open vision model (UI-TARS, Qwen-VL) | what only a real phone shows: the keyboard covering a field, install-to-home-screen, notifications |

## The personas

Each persona is a set of habits, not a script:
- the busy professional on a phone who reads nothing;
- a newcomer who has never seen the app;
- a parent with one free hand;
- a person reading in a second language;
- a screen-reader user;
- someone on a slow network.

Each persona is given the same goals list, and the runner counts steps, wrong taps, dead ends and time to the goal.

## Fix it automatically (agentic)

- **From finding to fix:** each finding becomes a written friction (the register) and a one-step brief from the golden template, with the failing goal as its test.
  The open models build it (`autobuild`), and the gates and a re-run of the same goal prove it.
- **Waiting for the owner:** fixes ride in one weekly pull request. The owner merges with one tap, because merging stays a human decision
  (AGENTS.md). A finding the models cannot fix twice goes to the queue with a date, and to the navigator.
- **Ranking:** risk × reach ÷ effort. A goal that fails for every persona comes first.

## Threat model (the agent is a new actor)

- **Scope:** it runs only in the sandbox, on fake data. It has no secret, no push right and no network beyond the sandbox and the model endpoint.
- **Page content is untrusted:** text in the app cannot instruct the agent. The runner gives the model the goal and the accessibility tree as data. The only actions it can take are tap, type and scroll inside the page.
- **Its output is a report:** the fixer is autobuild, behind the same gates as any change. Nothing the agent writes reaches main without CI and the owner's merge.

## Slices

1. Goal-driven people, with a simple brain: the runner, a goals file, a JSON and Markdown report, and a sandbox journey (test first).
2. The LLM brain (browser-use) behind the same interface. It is used when a model endpoint is configured; otherwise the simple brain runs.
3. Schemathesis on the gateway and the ZAP baseline on the hub, run nightly in the sandbox.
4. From findings to fixes: the brief generator, autobuild, and the weekly pull request with its one-line digest.
5. The real Android emulator with Midscene, run weekly.

## What it needs from the owner, once

To run the LLM brain and the fixer in GitHub Actions without this chat, the repository needs the `OPENCODE_GO_API_KEY` secret (Settings → Secrets → Actions). Until then,
layers 1 and 3 and the simple brain run in CI, and the LLM brain runs in a Claude Code session or on the estate with a local model.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** nightly runs on the owner's apps.
- **Enterprise, when conditions call for it:** synthetic users per tenant journey, run before every staged rollout (queue `staged-update`). This is the continuous UX-assurance evidence a regulator or a buyer can read.
