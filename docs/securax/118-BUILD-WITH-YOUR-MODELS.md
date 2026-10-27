# SOP — finish the remaining work with SecuRAX's own models (near-zero Claude tokens)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** An SOP for finishing work on the estate with SecuRAX's own open models (autobuild/opencode on the OpenCode Go and local Ollama ladder) instead of spending Claude: the universal route -> brief -> autobuild -> verify -> ship loop, ready-to-paste commands per task, and the rule to reserve Claude for the strong-tier 20% and its review. The same gates (verify, fitness, selftest, suite check, ui_audit) make it safe to let the open models drive. Grounded in the choose-your-customer and least-effort principles. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Who this is for:** you, driving the four remaining tasks through the estate's integrated open
models (OpenCode Go flat-rate — DeepSeek V4.1 Flash + GLM — and local Ollama) instead of spending
Claude. Claude is reserved only for the one high-blast-radius task (D), and only for a *review*.

**Why it works (80/20):** `./securax autobuild` and `./securax opencode` route every model call
through your own gateway to the open-model BUILD ladder — **0 Claude tokens**. `./securax route`
tells you which tier a task needs; only "strong/Claude" tier should ever touch Claude, and even then
usually just for `./securax review`. The estate's own gates (`verify`, `fitness`, `selftest`,
`suite check`, `os check`, `ui_audit`) make it impossible for a weaker model to weaken a rail, skip a
test, or fake a green — so you can let the open models do the bulk safely.

---

## 0. One-time setup for the session

```bash
cd <your SecuRAX checkout>
./securax update                 # pull the 5 merged changes; self-heals the TLS drift
./securax opencode --check       # confirm which open-model rungs are live for builds
```

If a build model isn't wired yet: `./securax providers add` (adds the OpenCode Go key, etc.).

---

## 1. The universal loop — run this for EVERY task below

```bash
./securax route  "<task in one line>"      # -> local | opencode | strong, and WHY
./securax brief  "<task in one line>"       # -> files it touches, lessons that apply, how "done" is proven
# --- build ---
#   local / opencode tier:  unattended ...
AUTOBUILD_PUSH=0 ./securax autobuild "<task>"     # builds, self-verifies, retries on red, commits ONLY when green
#   ... or interactive:
./securax opencode                                 # (add --strong for the hard tier)
# --- prove it ---
./securax verify            # fast floor (lint + unit + config), seconds
./securax verify --full     # + the real-container + browser sandbox (~10 min) — REQUIRED for C and D, and for B
# --- ship it (no Claude) ---
./securax ship pr
./securax ship watch --fix 2 --merge    # watches CI; on red, autobuild pushes one fix/round; merges when green
```

Rules the loop already enforces for you (don't fight them): `autobuild` never pushes unless
`AUTOBUILD_PUSH=1`, never touches your current branch, and **commits only when `verify` is green**.
After N red attempts it stops and writes an **escalation brief** — *that* is your signal to hand just
that one piece to Claude's strong tier (see §3).

---

## 2. The four tasks — ready to paste

Order is by value ÷ effort. A and B are quick wins; C is a real feature; D is the one to supervise.

### A. GitHub Pages can't silently drift off again  ·  expected tier: **local/opencode**
The website 404'd because `deploy-pages` 404s when Pages isn't enabled at the API level. Make the
workflow enable Pages itself, so it never depends on the Settings dropdown being set.

```bash
./securax route "add actions/configure-pages to the docs workflow so GitHub Pages self-enables before deploy"
AUTOBUILD_PUSH=0 ./securax autobuild "In .github/workflows/docs.yml, add a step 'uses: actions/configure-pages@v5' with 'enablement: true' in the build job, before the 'upload-pages-artifact' step, gated by the same condition (push/workflow_dispatch and SITE_PAGES/DOCS_PAGES true). Pin to a published version at least two weeks old. Do not change the publish job or any other workflow."
./securax verify     # test_workflows_parse must still pass (valid YAML)
./securax ship pr && ./securax ship watch --fix 2 --merge
```
**Watch out:** workflow YAML must stay valid (a `: ` in a step name breaks the whole file —
`test_workflows_parse` guards this). Files: `.github/workflows/docs.yml` only.

### B. Stop the recurring CI flake wasting your merge cycles  ·  expected tier: **local**
`phone_device` fails intermittently on `net::ERR_NETWORK_CHANGED` on the Pixel's *first* page load.

```bash
./securax route "make the phone_device sandbox journey retry the first navigation once on ERR_NETWORK_CHANGED"
AUTOBUILD_PUSH=0 ./securax autobuild "In sandbox/run.py, in the phone_device journey, wrap ONLY the first Playwright page.goto to the HTTPS hub so that a net::ERR_NETWORK_CHANGED navigation error is retried exactly once (after a short wait) before failing. Do not change what the journey asserts, and do not add a retry to any other error or any other journey. Add a one-line LESSONS entry."
./securax verify --full    # the phone_device journey must pass
./securax ship pr && ./securax ship watch --fix 2 --merge
```
**Watch out:** retry *only* ERR_NETWORK_CHANGED, *only* the first goto — never broaden a retry to hide
a real failure (that would mask product bugs). Files: `sandbox/run.py`, `LESSONS.md`.

### C. Calendar .ics export — put time-based Life OS items on your phone calendar  ·  tier: **opencode**
You asked for the Family preventive calendar (and other dated items) to drop into your calendar.

```bash
./securax route "add an on-device .ics export of time-based Life OS items (preventive calendar, cadence, due dates) with a one-tap download, nothing leaving the device"
./securax brief "on-device .ics calendar export for the Life OS"
./securax opencode    # interactive: feed it the brief; design is decided below
```
Spec to give OpenCode (paste after the brief):
- A new on-device function in `guiding-map/ops.js` that builds a **VCALENDAR / VEVENT** string from the
  app's dated items (preventive-health cadence, ritual cadence, due dates), standard-library string
  building only — **no new dependency, nothing leaves the device**.
- A one-tap **"Add to calendar (.ics)"** button on the relevant screen that downloads the file
  (Blob + object URL, the same pattern the Export button already uses).
- Escape text per RFC 5545 (commas, semicolons, newlines), fold long lines, use a stable UID per item.
- Then: `node build.js` (rebuild index.html), a new `jsdom` test asserting a valid VEVENT is produced
  for a seeded item, `npm test` (all suites rc 0), and `python3 tests/ui_audit.py` (0 page errors, 0
  contrast failures, both themes).
- Paperwork: `features.json` (+ `tools/features_sync.py`), `suite.json`, `resilience.json`, a doc +
  `mkdocs.yml` nav, CHANGELOG, `docs/status.yml` (+ `sync_status.py`).
```bash
./securax verify --full
./securax ship pr && ./securax ship watch --fix 2 --merge
```
**Watch out:** on-device only (DPDP); don't pull a calendar library; give every new Life OS section the
`active` class or it renders blank on real browsers (passes jsdom, fails the eye — a logged lesson).

### D. Ponytail-native + token discipline  ·  tier: **STRONG — supervise this one**
This changes `governance/principles.json`, which **propagates to every app** via `os check` — highest
blast radius. Run it `--strong` and **always** get a review before merge; or hand just this to Claude.

```bash
./securax route "add a code-minimalism principle that propagates to every app, upgrade ./securax review, add a route nudge, write the 'spend Claude on the 20%' playbook"
./securax opencode --strong
```
Spec:
1. **Principle** in `governance/principles.json` — a `code-minimalism` (laziness-ladder) principle:
   *reuse before build — already-in-repo → stdlib → native platform → installed dep → one line →
   the minimum that works; and **never** cut validation, error handling, security or accessibility.*
   Then `./securax os check` and `./securax os build --all` so every app carries it (`kit1` must pass).
2. **`./securax brief`** injects the ladder into the spec it hands any model, so autobuild/opencode are
   lazy-by-default.
3. **`./securax review`** upgraded to the "senior dev who gets paged" checks: read the code the change
   *touches* (not just the diff), rank findings, each finding = what it does / what breaks / the fix /
   cost of skipping.
4. **`./securax route`** prints, when a task is local/opencode tier: *"this is <tier> — don't spend
   Claude on it."*
5. **Playbook doc** "Spend Claude on the 20%": Sonnet as the Claude-Code default, Opus only for the
   strong tier, offload build/paperwork to `autobuild`/`opencode` (0 Claude tokens).
```bash
./securax verify
./securax review          # MANDATORY for this one (strong tier)
./securax ship pr && ./securax ship watch --fix 2 --merge
```
**Watch out:** edit hand-formatted JSON with textual replacements, never load-and-dump (it reflows
`vantage.json` to 1,500 lines — a logged lesson). **Do NOT install the third-party
`DietrichGebert/ponytail` plugin/hooks** — author the prompt natively (offline + supply-chain rule).
This is the one task where, if the open models struggle, it's worth Claude's strong tier.

---

## 3. When to spend Claude anyway (the honest 20%)

- `autobuild` hit its retry limit and wrote an **escalation brief** → paste that brief to Claude Code
  (Sonnet first; Opus only if Sonnet stalls) for *that one task*.
- Task D's `./securax review` flags a real correctness/security issue the open models can't resolve.
- Anything touching crypto, auth, the gateway rails, or merge logic — `route` will say "strong".

Everything else: open models. In Claude Code itself, run **`/model sonnet`** and keep Opus for the
strong 20% — that alone roughly 3–5× your 5-hour session window.

## 4. Proof it's safe to let the open models drive

Every path above ends at the same gates CI enforces, so a weaker model **cannot** ship a regression:
`./securax verify` (lint + unit + config), `python3 -m lifecycle.fitness` (22 checks),
`./securax selftest` (every command wired + loads), `./securax suite check`, `./securax os check`,
and for the PWA `npm test` + `ui_audit.py`. `diffcheck` and `forge gate` block any attempt to weaken a
rail, skip a test, or fake a green. `./securax ai share` shows afterwards who did the month's work.

## 5. Suggested run order for one sitting

A (≈5–10 min) → B → C → **then** D with `--strong` + review. Push once per task (each push restarts the
~40-min sandbox, so batch within a task). Stop and call Claude only on an escalation brief.
