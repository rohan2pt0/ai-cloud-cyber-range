# 43 · Look inside third-party software before you trust it (REA, sandboxed)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** `inspect_sandbox` journey. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

*Written 14 Oct 2026. Facts about REA are from its own README and npm page (linked at the end); what was run here is stated as such.*

## What REA is, and what the LinkedIn post gets right and wrong
**REA ("Reverse Engineer Anything")** is an open-source (MIT) tool that lets an AI agent, or you in a terminal, take software apart: JavaScript and Electron apps, .NET, Android packages, websites and, with an extra disassembler installed, native binaries. It is one command-line tool and one MCP server (the plug that lets an agent such as OpenCode use it).
- **True:** it is real, MIT-licensed, installable from npm (`rea-agents`, 6.5.0 today; the post says 6.4.0) with **no install scripts**, and its JavaScript analysis works on a plain Linux machine: it parses code as inert text and never runs it.
- **Marketing:** "one paste can reverse-engineer anything". Native code needs Hopper, Ghidra or IDA (Hopper and IDA are commercial; REA grants no licence for them). Its *runtime* modes **do run the target** under your user account, which is exactly what you must not do with untrusted software on a work machine.
- **The warning in the post is real and worth copying:** get it only from `github.com/morluto/rea`, `rea.tools` or the `rea-agents` npm package. Look-alike repositories with copied READMEs are how people get hurt by tools like this. SecuRAX pins the exact version and every dependency by hash, so a look-alike cannot arrive through us.
- **Responsible use:** analyse only software you own or are authorised to examine. Many licences and vendor contracts forbid reverse engineering, and unauthorised access is an offence under India's IT Act: check your contract before you point it at a vendor's product.

## What SecuRAX does with it (static, sandboxed, nothing on your host)
REA runs only inside a container with **no network, a read-only disk, no privileges, a non-root user and hard limits**; what you inspect is mounted read-only. `./securax inspect --selftest` proves that on your machine.

```
./securax inspect --build                       # once: builds the pinned sandbox image (needs Docker + internet)
./securax inspect npm:some-package@1.2.3        # fetch (no scripts run) and read it
./securax inspect ./vendor-sdk.tgz              # a tarball, a folder or a single file
./securax inspect --diff npm:pkg@1.2.3 npm:pkg@1.2.4     # what the new version can do that the old one could not
./securax inspect --watch                       # compare every pinned dependency with the registry; inspect any newer one
./securax inspect --watch --schedule weekly     # let your own crontab do that every Monday (opt-in)
./securax opencode --rea                        # give the OpenCode agent REA over MCP, still inside the sandbox
```
You get a plain-English report: what it can do (network, running programs, files, environment, dynamically built code, native code), what is worth knowing (an install-time script, a hard-coded IP, an encoded blob that is decoded and run, shipped binaries) and a verdict: **OK**, **REVIEW** or **BLOCK**. `--strict` turns REVIEW/BLOCK into exit codes 1/2 for scripts.

### The one idea that does the work: capability drift
A library you trust does not suddenly learn to open network connections, launch programs and add an install script in a patch release: that is the signature of a hijacked package. `--diff` and the weekly `--watch` compare *what the code can do*, not just version numbers, so an accepted install script (such as OpenCode's launcher) is quiet until it **changes**.

### What it said on real packages (run here, 14 Oct 2026)
- `left-pad@1.3.0`: OK, nothing beyond plain computation. `express@4.19.2`: OK, it can use the network (it is a web server), reads files and the environment. Both as expected.
- `opencode-ai@1.19.0`: **BLOCK**, because it has an install-time script that runs a program and ships a native stub. That is how it fetches its platform binary, a known and accepted trade-off, and the reason the watchlist records it as accepted: a single inspection is deliberately strict, and only *changes* to it are reported by the watch.
- A synthetic "compromised release" built for the tests (new install hook, `child_process`, `https`, a raw IP, eval of an encoded blob): BLOCK with every reason named, and `--diff` against the clean version names each new power.

## The autonomous part
- **Weekly watch** (your crontab, or the `supply-chain-watch` GitHub workflow): every package in `integrations/rea/watchlist.json` is compared with the registry; any newer version is inspected next to the pinned one; exit code 2 (or a red job) means a person should look. Reports are saved in `~/.securax/inspect/`.
- **The sandbox serves agents too:** `./securax opencode --rea` lets the agent ask REA questions about the folder you are in (mounted read-only). OpenCode has no per-call approval for MCP tools, so the container is the control.

## Honest limits
- Static triage by heuristics: it shows where to look; it does not prove software safe. A clever package can hide behaviour that static reading cannot see, and a clean report is not a clearance.
- Native binaries are fingerprinted only (type, hash, strings, addresses); disassembly needs Hopper / Ghidra / IDA, which are not in the sandbox image and are not licensed by REA.
- REA's runtime and dynamic modes (running the target) are **not** exposed by any SecuRAX command. Through `opencode --rea` an agent can reach all 207 REA tools, but only inside the closed container, where the target is read-only and nothing can leave.
- Built once from the lockfile; upgrading REA is a deliberate change to `integrations/rea` that the watch itself will inspect.

## More places this can go (suggested, not built)
1. **AI-SOC attachment triage:** hand a suspicious file from an alert to `inspect` and attach the report to the incident case.
2. **Vendor assessments for RBI para 117:** run `inspect` on each vendor SDK or installer you evaluate and file the report as evidence.
3. **Pre-merge gate for dependency bumps:** run `--diff` on every Dependabot bump and block the merge on BLOCK.
4. **Understanding legacy or undocumented internal software** with the agent and REA together, on code you own.
Say which you want first.

## Sources
- REA: <https://github.com/morluto/rea> (README, MIT), npm `rea-agents` 6.5.0 (no install scripts, Node 22+), <https://rea.tools>
- OpenCode MCP configuration: <https://opencode.ai/docs/mcp-servers/>
