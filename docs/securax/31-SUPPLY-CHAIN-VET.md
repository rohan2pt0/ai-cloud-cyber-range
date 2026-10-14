# 31 · Supply-chain gate — `./securax vet`

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

## It found something in our own repo
Scanning this repository: `curl … | sh` in `local/scripts/bootstrap-laptop.sh`, `local/scripts/wsl-setup.sh` and the tree node's `user_data` (Tailscale installer). They are real. Follow-up, **not yet done**: pin those installers by checksum or package repo instead of piping a download into a shell.

## Honest limits
Static analysis finds the lazy and the obvious. It cannot prove a repo benign, and a patient attacker can avoid every pattern here. Treat PASS as "nothing obvious", keep pins, re-vet on every bump, and run third-party code in a sandbox regardless. Not covered: transitive npm/pip dependencies (flagged, not scanned), runtime behaviour, and typosquatting of the *source URL*.
