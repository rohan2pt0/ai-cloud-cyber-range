# AGENTS.md: how to work on SecuRAX

Read this first, whoever you are: the local builder (`./securax build` / `autobuild`), OpenCode, Codex or Claude.
It is the short version of what a new contributor would otherwise rediscover by trial and error. The hard rules are
in `BUILD-CONTRACT.md`; what went wrong before, and why, is in `LESSONS.md`. Read both.

## 0. The north star (read this before anything else)

SecuRAX exists for one reason: **the person or team using it must be visibly better off**. That means better work, better
decisions, a calmer and more purposeful life, risks really reduced. A feature that is secure, resilient and compliant but
unused, or that changes nothing a person can see, is paper: it does not count.

Before you build, answer three questions in the PR:
1. **What gets better for the person this week?** Name the outcome in their words (time saved, a risk closed, a goal moved,
   a decision made easier), not the mechanism.
2. **Where will they see it?** `./securax progress`, the Life OS, a phone message, the cockpit. If they cannot see it, they
   will not use it, and it will not help.
3. **How does it get them to use the estate more fully?** One clear next step, never a manual to read.

The principles behind it:
- **Purpose (ikigai):** what they love, are good at, are valued for and the world needs. The Life OS wheel, OKRs and career
  compass carry it; never bury it under tooling.
- **Antifragility:** every failure must leave the estate stronger. A lesson, a test and a drill come out of it, and
  `progress` counts them.
- **Small wins, shown:** progress you can see keeps people going.
- **Least effort for the person:** the estate does the remembering, the checking and the reminding.

Every feature in `features.json` carries its `outcome` (what gets better) and `shows` (where the person sees it); fitness
`outcomes-declared` fails one that does not.

## 1. Pick the tier before you start

Run `./securax route "the task"`. It names the tier, and why:

- **local**: one area, an existing pattern, a clear test. `./securax autobuild "…"`.
- **opencode**: several files, but the design is decided. `./securax opencode`.
- **strong**: security, crypto, auth, sync or merge logic, regulator mapping, or a change across many areas. `./securax autobuild "…"` uses the strong open models by itself; work on it by hand in `./securax opencode --strong` (doc 83).

Before you start, `./securax brief "the task"` prints the likely files, the lessons that apply and the checks that prove it (autobuild sends it to the model by itself).
Before merging anything the router calls strong, get a second look: `./securax review`. `./securax ai share` shows who did this month's work
(Claude, the open models, you). Commits made with SecuRAX's own models end with the line `Assisted-by: SecuRAX open models`.

## 2. Where things are

| Path | What it is | Its tests |
|---|---|---|
| `securax` | the one CLI (bash): each command is a `case` branch with a usage comment | `sandbox/` journeys |
| `governance/*.py` | standard-library Python modules, each with a docstring that is its CLI help | `governance/tests/` |
| `apps/llm-gateway/` | the AI gateway (FastAPI): rails, identity, allowance, kill switch, audit chain | `apps/llm-gateway/tests/` |
| `guiding-map/` | the Life OS PWA: edit `ops.js` (or the app code above the ops marker in `index.html`), then `node build.js` | `cd guiding-map && npm test` (jsdom), `guiding-map/tests/*.py` |
| `lifecycle/` | fitness checks, impact map, forge gate, diffcheck, vet, routing | `lifecycle/tests/` |
| `website/`, `docs/` | product site and MkDocs docs; `bash website/build.sh` builds both | `mkdocs build --strict` |
| `vault/` | private data (workbooks, registers, ticks). Never commit it, never paste it | — |
| `features.json` | the one list of what SecuRAX can do; `python3 tools/features_sync.py` writes it into the Command Center, website, docs home and README | fitness `features-current` |

## 3. Before you call it done

1. `ruff check .` and `python3 -m pytest -q` (or `./securax verify`, the same floor CI enforces).
2. A PWA change: `node build.js`, then `npm test` in `guiding-map/`, then `python3 guiding-map/tests/ui_audit.py OUTDIR`. It must report 0 page errors and 0 contrast failures, in both themes.
3. `git add -A`, **then** `python3 -m lifecycle.fitness`: untracked files are invisible to the impact-map check.
4. The paperwork that rides with every change:
   - **CHANGELOG:** a line under `[Unreleased]`.
   - **Status lights:** edit `docs/status.yml`, then run `python3 docs/sync_status.py`.
   - **Docs nav:** a new doc goes in `mkdocs.yml` nav.
   - **README:** `python3 tools/readme_sync.py`.
   - **A new or renamed feature:** edit `features.json`, then `python3 tools/features_sync.py` (it also refreshes every counted fact).
   - **A new command:** a line in `./securax help` (fitness `commands-in-help`).
   - **Docs build:** `mkdocs build --strict`.
5. Re-read your own diff as a reviewer would. Fix what you find before anyone else sees it.

## 4. Rules that are easy to break

- **Brand values** (domain, e-mail, names) live only in `brand.env`; `./securax config check` fails otherwise.
- **The repository is public:**
  - no personal data, no employer or role hints, no uploaded document text
  - no name on the private list: `./securax privacy check` (only fingerprints are stored; `privacy add "Name"` adds one)
  - regulator documents are cited by reference and paraphrased, never copied
- **Test data must not look like real data.** The PII gate flags 13–19 digit runs, including all-zero GUIDs. Use obviously fake values.
- **Generated files stay out of git:** `portal/cockpit*`, `portal/navigator*`, `portal/setup.json`, `website/docs/`.
- **No new dependency or network call** without a reason in the PR. The estate must run offline.
- **Never weaken a rail, skip a test or fake a green** to finish (`diffcheck` and `forge gate` catch it).
- **Users are not experts.** Every command a user sees must work exactly as printed. Never print a placeholder such as `FILE.xlsx` without a fallback that finds the file.
- **Never depend on a file the user may not have.** Ship a working default (like the starter control library) and let their own file improve it.
- **No hand-kept counts.** A number on a page (tests, journeys, maps) is a `<!-- fact:NAME -->` that the generator fills.
- **Write plainly:** short sentences, one idea each, no jargon without a gloss.

## 5. When you learn something

When a check failed for a reason the next agent could avoid, add one line:
`./securax lessons add "what happened → what to do instead"`. Autobuild does this by itself when a red attempt turns green.

## 6. When the owner shares documents or a new idea

1. **Read all of it, and keep it private.** Uploaded material stays in `vault/` or a scratch folder. The repository gets only the cue, in our own words.
2. **Diagnose before building.** Compare it with what already exists. Fix what is broken; do not rebuild what works.
3. **Take the 20% that gives 80%.** Risk first, then what the current machine and budget allow. Say plainly what waits, and give it a target date.
4. **Apply it without breaking anything.**
   - **Blast radius:** run `./securax impact` to see what the change can affect.
   - **Proof:** tests and a sandbox journey for the new behaviour.
   - **No new single point of failure:** a second copy, a fallback, or a way back.
5. **Bound what grows.** Anything new that writes data names its limit and its storage tier (doc 80), and `storage --auto` can clean it.
6. **Record it.**
   - **Ledger:** one row in the ledger of the doc it touched (for the range, "Cues taken from your material" in doc 79).
   - **CHANGELOG:** one line.
   - **Status:** the doc's status light.
