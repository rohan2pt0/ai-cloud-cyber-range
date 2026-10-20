# 83 · Build with open models: leave the Claude Code subscription without losing the rigour

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the strong chain (DeepSeek V4 Pro, Kimi K3, GLM 5.3 on OpenCode Go), routing hard work to it in autobuild, OpenCode with the build rules and --strong, ./securax review, and open-model work counted in ai share. Not yet proven: a full day of real work on these models, measured by autobench (dated in the doc). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** do the estate's development work through SecuRAX itself, on strong open models, so a subscription's usage limit is never again the bottleneck.

**The short answer:** use OpenCode inside SecuRAX for everyday coding. The strong open models take the hard work. A second model reviews your change before you merge. The local model handles anything private. Claude stays optional, for when you want it.

## 1. What to use for what

| Work | Command | Models (first that answers) |
|---|---|---|
| Everyday coding, fixes, docs | `./securax opencode` | **Build chain:** DeepSeek V4.1 Flash, GLM 5.3 Flash (OpenCode Go), then the free tiers, then local |
| Hard work: security, crypto, sync, regulator maps, many areas | `./securax opencode --strong`, or `./securax autobuild "task"` (it picks the strong chain by itself) | **Strong chain:** DeepSeek V4 Pro, Kimi K3, GLM 5.3 (OpenCode Go), then the free NVIDIA tier, then the build rungs, then local |
| A second look before you merge | `./securax review` | Strong chain |
| Not sure which | `./securax route "the task"` | Names the tier and the next command |
| Anything private (vault, client data) | Never to a cloud model | The local model only. `review` refuses vault/ and .env files |

Every call still goes through the gateway: guardrails, audit, residency and the kill switch all apply. OpenCode can reach nothing else.

## 2. What it costs, in rupees

| Plan | Price | What you get |
|---|---|---|
| **OpenCode Go** | $10 a month (about ₹970) | 30+ open models. Each has its own monthly allowance: the strong ones (DeepSeek V4 Pro, Kimi K3, GLM 5.3) about $15 of use each; the flash ones $60–80. At most 20% of an allowance in any 5 hours and 50% in a week |
| **OpenCode Go Plus** | $40 a month (about ₹3,860) | The same models, with about 4× the allowance (strong models about $60 each) |
| Claude Pro (for comparison) | about ₹2,399 a month (₹2,000 billed yearly), GST included | One provider; one shared limit |
| Claude Max 5× (for comparison) | about ₹11,999 a month, GST included | Five times Pro's limit |

- **Rupee figures:** at about ₹96 to the dollar (one converter's figure, October 2026). Your card adds its foreign-exchange markup.
- **GST:** a foreign online service sold to a person in India attracts 18% IGST when the seller is registered for it. Your card statement shows the final amount.
- **The allowances work as a chain:** when one strong model's allowance runs out, the chain moves to the next one, then to the free NVIDIA tier, then to the build models. Work slows; it does not stop.

**Recommendation:**
1. Start on Go at $10 for one month.
2. Keep Claude for two more weeks, then cancel it if `./securax ai share` shows you no longer reach for it.
3. Move to Go Plus only if your OpenCode Go account page shows the strong allowances running out before the month ends.

## 3. Honest about quality

- **The best closed models still lead.** Claude Sonnet and Opus top the October 2026 coding leaderboards.
- **The best open models are close behind** on agentic coding benchmarks: DeepSeek V4 Pro, Kimi K3 and GLM 5.x.
- **The sources disagree.** Rankings change with the benchmark and the source, so treat any single number as a lead, not a verdict.

What closes the remaining gap here is not the model alone. It is the gates:

- **verify, diffcheck and forge** refuse a change that is not proven.
- **The router** sends the hard work to the strong chain.
- **`review`** gives every sensitive change a second, independent look.

## 4. The move, step by step

1. **Get a key:** at opencode.ai/go, subscribe to Go and copy the API key.
2. **Add it:** `./securax providers add opencodego` and paste it. One key serves both chains.
3. **Restart the router:** `./securax up`.
4. **Check:** `./securax opencode --check` lists the build chain and the strong chain, and confirms OpenCode can use no Chat chain.
5. **Install OpenCode once:** `npm install -g opencode-ai@1.19.0` (doc 42).
6. **Work:** in your `ai-cloud-cyber-range` folder:
   - `./securax opencode` for normal work
   - `./securax opencode --strong` for hard work
   - switch models any time with `/models`
7. **Before you merge:** `./securax review`. It sends the change, never vault/ or .env, to the strong chain and lists real defects with the fix.
8. **Ship:**
   - `./securax verify`
   - `git push`
   - open the pull request on GitHub (or `gh pr create`)
9. **Each month:** `./securax ai share` shows how much of the work Claude, the open models and you did. Commits made in OpenCode end with the line `Assisted-by: SecuRAX open models` and count as open-model work.

## 5. What Claude Code did, and what does it now

| Claude Code gave you | Here | Status |
|---|---|---|
| An agent that edits, runs tests and fixes | OpenCode (and Aider in `autobuild`) through the gateway | ✅ |
| The repository's rules in every session | OpenCode reads AGENTS.md; the config adds BUILD-CONTRACT.md and LESSONS.md | ✅ |
| A strong model for the hard parts | The strong chain, picked by `route` and `autobuild` | ✅ |
| A review before merging | `./securax review` | ✅ |
| Proof before a commit | `verify`, `diffcheck`, `forge` (they are stricter than a chat assistant) | ✅ |
| Watching a pull request and fixing CI by itself | Not yet: you read CI on GitHub and paste the failure into OpenCode | 🔴 dated below |
| Cloud sessions you can leave running | Not yet: OpenCode runs on your laptop | 🔴 dated below |

## 6. Data: what may go to these models

- **May go:**
  - the public repository's code and docs
  - anything you would accept a US or EU cloud seeing
- **Where the models run:** OpenCode Go's models are hosted outside India. The Go plan lists most open models as no training and zero retention.
- **DeepSeek's zero-retention agreement** is renewed monthly; Go's page says it is valid through 31 October 2026. Check it each month (dated below).
- **On OpenCode Go, SecuRAX uses only the open models with zero retention and no training.** Two kinds are in no chain:
  - the "Contributor" models, which may train on prompts
  - the models Go keeps data for 30 days
- **The free rungs further down the chains** (Groq, NVIDIA, Gemini and others) have their own terms (doc 23). That is one more reason only public code goes to a cloud model.
- **Never goes:**
  - vault/, .env, keys
  - client or personal data (the gateway's residency rules keep regulated data local)

## 7. Next steps (dated)

| By | Step |
|---|---|
| 2026-10-31 | Re-check DeepSeek's zero-retention renewal on OpenCode Go's page. If it lapsed, move it behind Kimi and GLM: `./securax providers chain strong remove opencodego_pro`, then `./securax providers chain strong add opencodego_pro --before nvidia_nim` |
| 2026-11-15 | Run `./securax autobench` on the build and strong chains: replace reputation with measured numbers for this repository |
| 2026-11-30 | Show which model answered each call in the cockpit, so a quiet fall to a weaker rung is visible |
| 2026-12-31 | A CI watcher: when a pull request goes red, write the failure brief for OpenCode by itself |

## Sources

- [OpenCode Go: plans, models, allowances, data retention](https://opencode.ai/docs/go/) (read 20 October 2026)
- [BenchLM coding leaderboard, October 2026](https://benchlm.ai/coding) and [Vellum open-model leaderboard](https://www.vellum.ai/open-llm-leaderboard): rankings disagree between benchmarks
- [Claude India pricing, July 2026 (Open magazine)](https://openthemagazine.com/technology/claude-ai-gets-india-pricing-in-rupees-heres-what-pro-max-team-plans-cost) and [Outlook Business](https://www.outlookbusiness.com/deeptech/claude-pro-now-costs-2000-in-india-as-anthropic-localises-subscription-pricing)
- [USD to INR converter (Pluang)](https://pluang.com/en/tools/currency-converter/usd-inr): an indicative rate only
