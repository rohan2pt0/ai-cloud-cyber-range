# 31 · Supply-chain gate — `./securax vet`

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** `vet_gate` journey. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Popular is not safe. A skill is text an agent **obeys**; a plugin's hooks run with **your** privileges; an MCP server is code your agent trusts. 2026 research reports malicious skills and repo configs stealing keys and planting backdoors (e.g. [MintMCP](https://www.mintmcp.com/blog/claude-code-supply-chain-attacks); the headline figures there are not independently verified). So nothing from the internet gets near an agent until it has been **vetted, pinned and hash-checked**.

```bash
./securax vet check <git-url|dir> [--ref SHA] [--out DIR]              # exit 0 PASS · 1 REVIEW · 2 BLOCK
./securax vet check <url> --ref SHA --accept --vendored vendor/<x> --note "what I read"   # pin it (never for BLOCK)
./securax vet verify                                                   # also part of ./securax verify and the unit tests
```

## What it checks (static: **nothing from the repo is executed**)
| | |
|---|---|
| **Pin** | the exact commit and a hash of the whole tree |
| **Licence** | MIT/Apache/BSD/ISC/MPL/Unlicense OK; none, unknown, GPL/AGPL flagged |
| **Executable surface** | agent hooks, MCP servers, npm install scripts, permission-widening settings, `curl \| sh`, decode-and-exec, credential reads, env-near-network, persistence, destructive commands, binaries, symlinks that escape the repo |
| **Text** | every markdown/text file goes through SecuRAX's **own guardrail engine**: prompt injection, hidden Unicode ("ASCII smuggling"), secrets, plus instructions hidden in HTML comments |

**BLOCK** can never be pinned. **REVIEW** means a human must read the listed lines; the manifest records *why* they were accepted. **Vendored copies must be byte-identical to upstream at the pinned commit** (otherwise `--accept` refuses), and `vet verify` fails if even one byte later changes. `./securax escalate` attaches vetted third-party skills to its brief **only while they verify**.

## First real use: agent-skills (MIT) — [source](https://skills.addy.ie/)
Verdict **REVIEW**: it ships agent hooks (**not** vendored) and two skills that *quote* attack strings to teach agents to ignore them (**not** vendored). Vendored only `security-and-hardening` and `code-review-and-quality`, pinned at `aeac41d4d005`, for the escalation tier (a stronger model benefits from them; small local models get `BUILD-CONTRACT.md`, which is short enough for their context). Provenance: `vendor/agent-skills/PROVENANCE.md`.

## Adoption ledger — what we took from the most-starred agent repos, and what we did not
Rule of thumb (80/20): take the **principle**, write it as our own small tested code or words; vendor third-party text only when it is vetted, pinned and byte-identical; never install a whole harness.
| Repo | Verdict (`vet`) | Taken | Not taken, and why |
|---|---|---|---|
| **andrej-karpathy-skills** (forrestchang; 4 rules from Karpathy's observations) | REVIEW: **no licence** → cannot vendor | The four behavioural rules, **in our own words**, in `BUILD-CONTRACT.md` (which `./securax build` feeds to the agent on every run). The mechanical parts are enforced by `./securax diffcheck` | Verbatim text (no licence). Note: the rules bias toward caution over speed; for trivial tasks use judgement |
| **agent-skills** (addyosmani, MIT) | REVIEW | 2 skills vendored, pinned, byte-identical, escalation tier only | hooks; the other 23 skills (many KB each: too long for small-model context) |
| **everything-claude-code** (affaan-m, MIT; 71 agents, 97 commands, 613 skill files, hooks, MCP config, ~109 MB) | **BLOCK** (9 critical, 341 high, 357 medium on first scan; some are test fixtures, but the volume and the install/hook surface are the point) | **Ideas only**: the *pre-commit guard* idea became `diffcheck` (our own code; it enforces the contract's hard rules on the diff) | Wholesale install (unreviewable surface, agent hooks run with your privileges). Candidates for later, **not built**: a generator/evaluator split in `autobuild` (an independent review pass), continuous-learning lessons from failed builds, context-budget discipline |
| **freellmapi** (MIT) | not run | its provider list informs which free providers our plugins should add | deploying it: free tiers may train on your prompts; our router ladder already fails over |
| **context-mode** (licence unconfirmed) | not run | nothing in the estate | optional developer-side token saver; read its LICENSE and pin it before use |
| **claude-mem** (thedotmack) | not run | the idea only: memory carried across sessions, as `LESSONS.md` that every builder reads (doc 23) | the plugin: it summarises every session with a Claude call, which spends the tokens we are trying to save, and adds hooks on every tool use |
| **paperclip** (MIT) | not run | nothing new: budgets (the AI allowance), audit trail and goals already exist | an org chart of agents is overhead for one person; revisit if several agents run in parallel |
| **OpenJarvis** (Stanford, Apache-2.0) | not run | two ideas: route each task to the cheapest builder that can do it (`./securax route`), and learn from your own history (`LESSONS.md`) | the framework: our gateway, ladder and local models already do local-first inference |
| **skills** (Matt Pocock) | not run yet | candidates for the escalation tier, after `./securax vet` and a pin | — |

## It found something in our own repo — and we fixed it
Scanning this repository, `vet` flagged `curl … | sh` in `local/scripts/bootstrap-laptop.sh`, `local/scripts/wsl-setup.sh` and the tree node's `user_data` (Tailscale). All three are fixed, plus two of the same kind the scanner's pattern could not see (`curl … | VAR=x sh`: k3s in the tree `user_data` and in the burrow spore; the pattern now catches it):

| Was | Now |
|---|---|
| helm `get-helm-3 \| bash` | pinned `helm v3.16.3` tarball, SHA-256 checked before unpacking (amd64 + arm64) |
| kind / kubectl downloaded straight into `/usr/local/bin` | downloaded to a temp file, SHA-256 checked, then installed |
| Tailscale `install.sh \| sh` | pinned `1.78.1` static tarball, SHA-256 checked (amd64 + arm64) |
| k3s `get.k3s.io \| sh` (tree node + spore) | the k3s `install.sh` at the pinned tag is saved to a file and hash-checked before it runs (`burrow.json: k3s_installer`; the module default is kept in step) |
| WSL one-paste `curl … \| bash` | two lines: save the script, then run it, so you can read it first |

What a pinned hash does and does not give you: the hash was taken from the vendor's own download on 2026-10-14, so it stops a *later* swap or a tampered mirror, not a vendor that was already compromised on that day. Re-pin on every version bump (the commands are in the files). A test serves a tampered k3s installer to the real spore and proves it is refused before it runs.

## Honest limits
Static analysis finds the lazy and the obvious. It cannot prove a repo benign, and a patient attacker can avoid every pattern here. Treat PASS as "nothing obvious", keep pins, re-vet on every bump, and run third-party code in a sandbox regardless. Hardening note: `vet` itself crashed on a malformed URL (`http://[abc`) while scanning ECC. The same unhandled error existed in the gateway's output rails (a model reply containing such a URL could 500 the request). Both are fixed: the gateway treats a malformed URL as an untrusted host and removes it; `vet` reports a file it cannot scan as a **finding** instead of dying (an attacker must not be able to hide behind a parser bug). Not covered: transitive npm/pip dependencies (flagged, not scanned), runtime behaviour, and typosquatting of the *source URL*.
