# 42 · OpenCode Go and the OpenCode terminal agent

*Written 14 Oct 2026 from the vendors' own pages (linked at the end). Prices and limits change: check them before you pay.*

> The cheap-model path is held to a stricter gate since doc 44 (`./securax forge gate`).

## What they are
- **OpenCode** is an open-source (MIT) coding agent that runs in a terminal. You type a task; it reads and edits files and runs commands.
- **OpenCode Go** is a subscription from the same team: **$10 a month** (a "Go Plus" tier is $40), billed in US dollars. It gives you hosted **open models** (DeepSeek V4.1 Flash, GLM, Kimi, MiMo, Qwen and others) behind one key. It is sold for **coding-agent traffic** and, unlike Cursor or Claude's own plans, it is not Claude or GPT: your veteran's point is that the open models are good enough for most coding work. I could not verify that claim; the build ladder below means you find out on your own tasks at no risk.

## What SecuRAX does with them (two things, both optional)
### 1. OpenCode Go as a model plugin (the BUILD ladder only)
```
./securax providers add opencodego      # paste the key (https://opencode.ai/go)
./securax keys                          # checks the key and the model name against the provider
```
One key turns on two rungs: **DeepSeek V4.1 Flash** and **GLM Flash** (`opencodego`, `opencodego-glm`). They head the **build ladder** (`./securax build`, `autobuild`, and OpenCode below): OpenCode Go, then DeepSeek (your own key, if any), then the free tiers, then your local model. If the plan's usage cap is reached or the provider has an outage, the next rung answers; nothing stops.

**OpenCode gets the build chain only.** It never sees a Chat chain (`bank-assistant`, `twin`), which can carry personal data. `./securax opencode --check` prints its default model, the build chain's live rungs in order, and confirms no Chat chain is offered (exit 1 otherwise).

**Deliberately NOT in Chat.** Chat carries personal and business data, and the plan is sold for coding agents (it asks clients to identify with a custom user agent and a session id; SecuRAX sends `securax-gateway` and a per-install id; per conversation is not possible through the router, so that part is per install). Change the chain in `plugins/catalog.json` if you decide otherwise.

Switch model any time: `OPENCODEGO_MODEL=openai/glm-5.3` in `local/compose/.env`. Only models on the provider's **chat/completions** endpoint work through this plugin (DeepSeek, GLM, Kimi, MiMo, LongCat...); the Claude, GPT and Grok variants Go also lists use other endpoints. `./securax models` lists what is live and repairs a retired name itself.

### 2. The OpenCode terminal agent, guarded
```
npm install -g opencode-ai@1.19.0       # pinned, MIT; Ubuntu/WSL needs:  sudo apt install nodejs npm
./securax opencode                      # run it from the project folder you want it to work on
```
`./securax opencode` writes a config and starts OpenCode with it, so that:
- **every model call goes to the SecuRAX gateway** (guardrails, audit lines, residency rules, the build ladder, one set of keys in `.env`); OpenCode's other providers are switched off, so there is no side door around the guardrails;
- it **asks before editing a file or running a command** (its own default is to allow everything);
- **auto-update and public sharing (`/share`) are off**: nothing new arrives by itself and no conversation can be published to a link;
- the file holds no secret; the key is read from the environment when it starts.

Proven: the real OpenCode 1.19.0 was run against a stand-in gateway with this exact config; it used `securax/builder`, sent the gateway key and made no other connection. Not proven: an interactive session in a full terminal.

## Where your data goes (read this before you use it on real code)
- Hosting: the provider says all its models are hosted in the **US and EU**; its Go page lists no regions.
- Retention: the open models show **0 days retention and no training**. DeepSeek's zero-retention agreement is **renewed monthly and valid through 31 October 2026**: re-check after that. The Claude / GPT / Grok variants keep data for 30 days; SecuRAX does not use those through this plugin.
- For you (Indian BFSI): this is a **third-party processor outside India**. The residency policy treats it as a `global` zone, so with residency enforced only data classed `public` can reach it, and anything the gateway recognises as Aadhaar, PAN, card numbers and the like is rerouted to your local model. The gateway **cannot** know that ordinary source code or a design document is confidential: do not point this at a repository that holds customer data or regulated logic unless your vendor-risk process has approved the provider. Treat the monthly invoice as a foreign digital service (USD, card forex fee, GST treatment): confirm the tax handling with your accountant; I have not verified it.

## Honest limits
- The $10 plan has usage caps (the provider's docs describe dollar allowances per 5 hours, week and month, and per-model monthly limits; its pages disagree in places): the ladder hides a cap by sliding to the next rung, but you will notice slower or weaker answers.
- Model quality claims (including "you will not need anything else") are the veteran's and the vendor's, not measured here.
- OpenCode has its own extras (web fetch, MCP servers, plugins). Anything you add there is outside the gateway.
- OpenCode 1 and 2 can conflict if both are installed; the npm version is pinned for that reason.

## Sources
- OpenCode Go: <https://opencode.ai/go>, API and privacy table: <https://opencode.ai/docs/go/>, hosting statement: <https://opencode.ai/docs/zen/>
- OpenCode config (providers, `enabled_providers`, `autoupdate`, `share`, `permission`): <https://opencode.ai/docs/config/>, <https://opencode.ai/docs/providers/>
- Source code: <https://github.com/anomalyco/opencode> (MIT); npm package `opencode-ai`
