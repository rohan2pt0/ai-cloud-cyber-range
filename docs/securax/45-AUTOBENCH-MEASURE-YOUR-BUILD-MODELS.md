# 45 · `./securax autobench`: measure each build model before you trust it

Doc 23 said the quality of the cheap and local models inside the `autobuild` loop was unmeasured. This measures it, on your machine, with your keys,
so the ladder order (docs 23, 42) rests on numbers instead of reputation ("DeepSeek and GLM are enough" is one person's experience; this tells you about *your* work).

## What it does

```bash
./securax autobench selftest                         # the benchmark proves itself first: no model, no tokens, about a minute
./securax autobench run --models builder,coder       # runs the models through your gateway (aider); asks before more than 20 calls
./securax autobench run --models builder --prompt both   # also compares the plain prompt with the BUILD-CONTRACT prompt
./securax autobench report                           # table + what to do with each model
./securax autobench list                             # the ten tasks
```

* **Ten small tasks** in the shape of your own work: Indian rupee formatting, PAN validation, Aadhaar/PAN masking, GST split with exact paise, token bucket,
  path-traversal-safe join, constant-time token check, LRU cache, plus two bug-fix tasks (one a classic mutable-default state leak).
* **Hidden grading.** The model sees only a thin visible test file. A different file of tests it never sees decides the result, so satisfying or editing the visible tests is not enough.
* **The same loop as `autobuild`.** The model edits; the visible tests run; on red it receives a typed brief of the failure (doc 44) and tries again (default 2 tries).
  A task whose visible tests are already green stops after attempt 1, as `autobuild` would (that is a real hazard, kept on purpose: `verify_token`, `ledger_state_leak`).
* **Cheating is detected and never credited.** Editing or skipping the visible tests, or any `diffcheck` blocking rule, means not solved, with no second chance.
* **Complexity budget** (`forge`) is applied to each solution. (Mutation and fail-to-pass are not: they judge tests, and here the tests are given.)
* **Prompt variants.** `plain` is the task only; `contract` adds five rules (never touch the tests, treat every sentence as a requirement and re-check each before finishing, smallest change,
  standard library, fail closed). The report says whether the contract helped or hurt that model, with the noise caveat.
* **Results** accumulate in `~/.securax/autobench/results.jsonl`; only the newest run of a (model, prompt, task) counts.

## Reading the report

`solved` is hidden-test passes out of tasks. `95% range` is the Wilson interval: with ten tasks, 7/10 means "somewhere between about 40% and 89%". Trust the range, not the point.
`budget-ok` is solved tasks within the complexity budget; `cheated` counts tampering or contract-rule breaks. The advice per model:

| Lower end of the range ≥ 50% | good first rung |
|---|---|
| Solved ≥ 60% | usable first rung with review: probably fine, sample too small to be sure |
| Less | easy work only; escalate the rest (`./securax escalate`) |
| Any cheating | do not use unattended |
| Fewer than 10 tasks run | incomplete: run all before trusting it |

Costs: a full run is at most `models × prompts × 10 tasks × tries` model calls and is shown before it starts. A free or local model costs nothing but time. Cloud models may cost money: check the provider.

## Proof and honest limits

* `selftest` (and the `autobench_selftest` journey) shows the benchmark discriminates: a perfect agent solves 10/10, an empty agent 0/10, both test-cheating agents 0/10 (caught as tampering),
  and a retrying agent is credited with its second attempt only where the visible tests started red. It also checks that no starting task is already solved.
* It found two real defects on its way: the forge mutation gate could leave stale bytecode of a mutant behind (fixed, tested), and mutation against thin visible tests blames the task, not the model (so it is not applied here).
* **Not measured yet: any real model.** That needs your gateway, keys and tokens. The aider options were checked against its documentation (`--yes`, `--no-auto-commits`, `--message-file`) but not run here;
  if your aider version differs, use `--agent 'cmd:<your command>'` (it receives `AUTOBENCH_MODEL`, `AUTOBENCH_PROMPT_FILE`, `AUTOBENCH_ATTEMPT` and runs in the task folder).
* Ten small Python tasks are not your whole codebase; a model that solves them may still fail on a cross-file change. It ranks models; it does not certify them.
* Model-written code is executed by the tests. The default runs it locally with a stripped environment (no API keys) and a 60-second timeout; `--sandbox docker` runs it with no network, dropped capabilities and limits.
