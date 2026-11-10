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
- **One door, no passwords (`one-door`):** a person signs in once, with an account they already have (a passkey, Microsoft or
  Google), and that is the only door. A new feature that needs sign-in never builds its own login screen and never keeps a password:
  add one entry to `governance/identity.json` (what it needs, the narrowest permission, what works as a guest, how one switch takes
  it away). Ask for a permission only when the feature is used. Everything works as a guest first. Fitness `signin-declared` fails an
  incomplete entry, an over-broad permission, and any new separate login: the count of separate logins only goes down.
- **Think like the attacker first (`threat-model`):** a component that crosses a trust boundary gets a plain-text threat model in
  `governance/threat-models.json` (parts, data flows, trust boundaries, then all six STRIDE ways) BEFORE it is built; each threat is mitigated
  with evidence that exists, accepted with a reason and a review date, or ruled out with a reason. Fitness `threat-modelled` holds it;
  the number of models only goes up. Doc 133 has the template.
- **Enterprise grade (`enterprise-grade`):** design every component as if for the largest organisations. Section 7 is the review to run
  FIRST in every session and before every merge, and how to spend a session's room.
- **Built for a human mind (`human-first`):** design for how people really behave, not how a spec says they should. People
  judge in seconds by the look (first impressions colour how usable and trustworthy everything else seems), then stay or leave
  by how it feels to use. Apply the vital few, in this order, to anything a person sees:
  1. **First seconds:** one clear promise, one obvious action, the premium look, useful in under a second, nothing to read first.
  2. **First week:** the right choice is the default; it works as a guest; it is already partly done for them (example data
     they correct); one tap, never a form.
  3. **Every day:** progress they can see; end each visit on a small win; recall a slip once and kindly, then help.
  4. **Never against them:** invite, never command (pressure makes people resist: "Mandatory" loses, "the floor is enough" wins);
     give them the choice and the off switch; no guilt, no fake urgency, no hidden costs, no dark patterns.
- **See the whole (`whole-view`):** think like the great generalists. Before you build, run the **360 review** on the change and
  write the answers in the PR:
  1. **Person:** who uses this, in what moment and mood, and what do they feel at each step? (`human-first`)
  2. **First principles:** what is the real need? Question the requirement, delete a part, simplify, and only then speed up and automate.
  3. **Whole system:** what else does it touch: other apps, data, identity, failure, cost, the next ten years? (`./securax impact`)
  4. **Craft:** is the unseen part (errors, empty states, slow network, dark mode, a screen reader) as finished as the demo?
  5. **Proof:** which test, audit or number shows it worked for a person, not just that it runs?
  6. **Ethics:** would we be proud to show the person exactly how and why it nudges them?
- **A system lives in the calendar (`in-the-calendar`):** anything that repeats (a ritual, a review, a check-up, a renewal) gets
  "Add to calendar" next to it, made from the ONE registry in `guiding-map/ops.js` (`CALENDAR`), never a one-off file. The contract,
  so a later version never clashes with an earlier one:
  - an item's id, and so its UID, is permanent: never delete or reuse one; retire it (`retired` date: UNTIL plus CANCELLED);
  - its start date is fixed, not "next from today";
  - raise its `v` (SEQUENCE) whenever its time, rule or wording changes;
  - tell the person to import into the same calendar each time (apps match by UID per calendar).

  `guiding-map/tests/test38.js` lists every id ever handed out and fails if one disappears.
- **Small wins, shown:** progress you can see keeps people going.
- **Least effort for the person:** the estate does the remembering, the checking and the reminding.
- **Start as an amoeba, carry the DNA (`amoeba`):** ship the simplest living thing that helps today — one person, no
  server, offline — but carry the full blueprint inside it and build the dormant seam (the *rail*) that lets each part
  grow into its enterprise form. When you offer options, make the simplest that works the natural first choice, and still
  lay the rails for the larger ones so they can self-assemble when conditions call for them. Nature is the architect: a
  cell becomes an organism only as conditions warrant. So the estate senses its own conditions — favourable (more nodes,
  more teams, traffic north-south and east-west, spare resources) and unfavourable (load, failure, a lost node) — and
  grows the next form when they warrant it: the safe, in-box steps by itself, the ones that provision, cost or touch
  endpoints behind a human's approval. Declare each capability's growth path in `governance/evolution.json`; fitness
  `evolution-declared` fails an enterprise-capable feature that ships no rail to become one, and `./securax evolve` shows
  what is ready to grow. Never build the organism before the amoeba is alive and used; never ship an amoeba with no DNA.

Every feature in `features.json` carries its `outcome` (what gets better) and `shows` (where the person sees it); fitness
`outcomes-declared` fails one that does not.

**Built for one, ready for many (doc 97).** Every component is built once, for a person first, on the shared platform
(identity, roles, audit, tenancy, policy, metering, export, residency, continuity), so the same code can later serve an
organisation of any size. Declare each feature in `governance/suite.json`:
- the edition it starts in;
- the platform services it uses;
- what its enterprise version adds.

Never build a private copy of a platform service inside a component: if a component needs roles or audit, use or improve
the shared one. Fitness `enterprise-declared` fails an undeclared feature and any service claimed as built without its files.
The core stays free to use: everything a person needs to be safe, SSO and export included (FSL-1.1-MIT, each release MIT after two years; LICENSING.md).

**One source for principles and news (doc 95, section 6).**
- The principles live in `governance/principles.json`. Improve them there, never in one app. `./securax os check` then makes every app rebuild with the change.
- Every feature in `features.json` carries its `added` date, so the Command Center, the docs, the README and the weekly progress message all show what is new.
- A kit change that people would notice gets a line in `guiding-map/kit/whatsnew.json`.

## 1. Pick the tier before you start

Run `./securax route "the task"`. It names the tier, and why:

- **local**: one area, an existing pattern, a clear test. `./securax autobuild "…"`.
- **opencode**: several files, but the design is decided. `./securax opencode`.
- **strong**: security, crypto, auth, sync or merge logic, regulator mapping, or a change across many areas. `./securax autobuild "…"` uses the strong open models by itself; work on it by hand in `./securax opencode --strong` (doc 83).

Before you start, `./securax brief "the task"` prints the likely files, the lessons that apply and the checks that prove it (autobuild sends it to the model by itself).
From a Claude chat, the `delegate` skill (`.claude/skills/delegate/`) does this for the owner: it routes the task, sends local and opencode work
to the open models (`autobuild.yml`), and keeps Claude for strong-tier work and the review before merge.
To ship, `./securax ship pr`, then `./securax ship watch N --fix 2 --merge` (doc 98): it watches CI, fixes red with autobuild and merges when green.
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
   - **Its suite entry:** add it to `governance/suite.json` (edition, services used, what enterprise adds); `./securax suite check`.
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
- **Names, not ports (doc 99).** Never show a person `localhost:PORT`. Use `web_url` in the shell, or `governance/addr.py` in Python. Fitness `no-raw-addresses` fails a new one.
- **Links never break (doc 99).**
  - A doc may link to any repository file: the build sends it to GitHub.
  - A link to something that exists nowhere fails `mkdocs build --strict`.
  - Never write the brand domain into a link: use `{{SITE_URL}}`, which stays on GitHub Pages until `./securax site live`.
- **No hand-kept counts.** A number on a page (tests, journeys, maps) is a `<!-- fact:NAME -->` that the generator fills.
- **Write plainly:** short sentences, one idea each, no jargon without a gloss.
- **Calm screens (doc 100).** Show what needs the person, why, and one action; fold what is fine. Use the tokens in `governance/design.json`; a page in its `pages_on_the_standard` is held there by `test_design_standard.py`.

## 5. When you learn something

When a check failed for a reason the next agent could avoid, add one line:
`./securax lessons add "what happened → what to do instead"`. Autobuild does this by itself when a red attempt turns green.

## 5b. A session can end at any time: leave nothing only in your head

A usage limit, a restart or a closed laptop can end a session mid-task. Work that is not on GitHub, and asks that are not
written down, are then lost. So:
1. **Push each round** before any long wait (a CI run, an agent): a cloud container is reclaimed when the session ends.
2. **Write down every ask you have not finished** in `governance/queue.json`, in our own words, with a due date and the next
   step, in the same commit as the work you did finish. Close an item (`"state": "done"`) where it was finished.
3. **Bring back agents' work** before you stop: an agent's scratch copy (`.claude/worktrees/`) lives only in this session.
4. `./securax backlog` lists what is not finished from every source; the daily `backlog` workflow keeps it in one GitHub
   issue, so the next session (or the owner, on a phone) starts from it rather than from memory.

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

## 7. Enterprise grade, and a session that does not run out of room

**Run these five lenses first in every session, on what you will touch, and before every merge.** Fix the cheap findings now; put the rest in
`governance/queue.json` with a date and the next step. Say plainly what you could not test.
1. **Single points of failure.** What stops if one machine, host, account, key or person is gone? (`./securax resilience`; the register in doc 131.)
   Add a second node, active-active where it can be, active-passive where it cannot.
2. **Friction.** Any login, step or screen a person repeats or needs a manual for? (`one-door`; `governance/identity.json`; fitness `signin-declared`.) Guest first.
3. **UI and UX.** Both themes, a 390 px screen, keyboard, offline, no page errors, no contrast failures, in a real browser, not only jsdom
   (`python3 guiding-map/tests/ui_audit.py OUTDIR`).
4. **Security and privacy.** A threat model for anything that crosses a trust boundary (`governance/threat-models.json`); the narrowest permission; the origin and the headers of anything hosted (`website/_headers`); no secret or personal data in
   the repository; sensitive data stays on local models.
5. **Operate.** Can it be seen, recovered and taken away (offboarding)? A test or a drill proves it, not a sentence.

**Spend the room like money.** Read the queue and only the lines of a file you need (`grep -n`, `sed -n`, `head`, `tail`); never print a whole file. Run the
fast gates first and the full tests in the background, reading only the last lines. Do not subscribe to pull-request events (each is thousands of tokens):
open the PR, set ONE check-in, merge when green. One PR per round, pushed once. Replies: the result, what was not tested, the next step. At about 60% of
the room, push, update the queue and stop; the next session starts from the repository, not from this conversation.

**The reference bar (the vital few, from the AWS, Azure and Google Well-Architected frameworks, Google SRE, Netflix resilience, Cloudflare
Zero Trust and the open-core model).** Judge every change against these; each is held by a check or dated in the queue, never just stated:
- **Modular, loosely coupled, contract-first:** a clear owner and interface per component (`lifecycle/impact.json`); versioned APIs; a
  modular monolith beats needless microservices.
- **No unmitigated single point of failure, recovery proven:** tested RTO/RPO and restore drills, not diagrams (`resilience`, `continuity`,
  `spof-ratchet`); count correlated failures too (one identity, DNS, credential or person).
- **Fault isolation:** timeouts, retries with backoff, rate limits, graceful degradation (the gateway's ladder and kill switch).
- **Zero Trust and identity first:** no trust by network location; one door, least privilege, MFA or passkeys (`one-door`).
- **Secure by design and supply chain:** a threat model, signed artefacts, an SBOM, pinned dependencies (`threat-model`, Trivy, gitleaks).
- **Observable and operable:** logs, metrics and traces with one correlation id; a runbook and `./securax why` for every failure.
- **Delivered safely:** infrastructure as code, staged rollout, one-command rollback (`update` rolls back by itself).
- **Documentation as a product:** a fresh engineer can install, run, troubleshoot, upgrade and recover from the docs alone.
- **Fails well:** every error says what happened, why, and the one next step, in plain words; a failure seen twice gets an entry `./securax why`
  can find (a known-error list), not a second investigation.
- **Evolves without breaking:** versioned contracts, a deprecation named a release ahead, upgrade and rollback tested in the sandbox (doc 21).
- **Simple beats clever:** the fewest moving parts that meet the need today (the amoeba); a part is added only when a measured condition calls for it.
- **Measured by outcomes, not activity:** the four delivery keys (how often we ship, how long a change takes, how often a change fails, how fast
  we restore) come from git and CI and show in `progress` (queue `delivery-four-keys`).
**Applying it, 80/20:** list the gaps a change touches, rank them by risk × how many people it reaches ÷ effort, fix the top three this round and
date the rest in the queue. Hard gates (security, recoverability, regulation) are pass/fail regardless of any score.
