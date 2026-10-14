# 44 · The admission gate (`forge`) and the self-healing sandbox

**Goal:** you should not be the one who finds that a change is hollow or that a red run was only Docker dying. The harness
decides, mechanically, with no tokens, and tells the next attempt exactly what is wrong.

## What the research says (and what we took from it)

| Observation | Source | What we built |
|---|---|---|
| The harness around a model matters as much as the model (one model scored 43.2% in one scaffold and 59.8% in another). | [Trae AI overview, 2026](https://learn.traeai.com/t/ai-engineering/phases/15-autonomous-systems/09-coding-agent-landscape) (secondary; verify) | Put the rigour in the gate, not in a more expensive model: `forge` |
| A patch can pass weak tests without fixing the defect; verifier loops overfit to the verifier. | [InfCode](https://www.emergentmind.com/topics/infcode) (preprint) | Fail-to-pass and mutation checks: the tests must be able to fail |
| Repeating generate-test-revise is not reliable by itself; stale traces make later revisions worse. | [Looping Is Not Reliability](https://www.alphaxiv.org/abs/2607.24604) (30-case preprint, suggestive) | Every attempt starts from a clean tree and gets a short typed brief of the *current* failure, never a log dump |
| DeepSeek V4 gets its cost down by architecture and precision (sparse/compressed attention, mixture-of-experts, FP8/FP4 for experts); no official training cost was found. | [Simon Willison](https://simonwillison.net/2026/apr/24/deepseek-v4), [primer](https://aman.ai/primers/ai/deepseek-v4/) (secondary) | Not copyable: that is model training. What *is* transferable is the principle: spend compute only where it changes the answer. Cheap checks first, expensive ones (mutation, sandbox) only on a green candidate; cheap model first, escalate only on a verified failure |

The honest reading: nobody can make software "flawless" or "unoptimisable". Whether a program has a flaw is undecidable in general, and a mutation
score is evidence, not proof. What can be done is to make "done" expensive to fake and cheap to check. That is what this does.

## `./securax forge gate [--base REF]`

Run by `autobuild` after `verify` and `diffcheck`; you can run it yourself on any branch.

| Check | Question | Result |
|---|---|---|
| **fail-to-pass** | Do the tests the change added also pass on the code from *before* it? | WARN: they prove nothing |
| **mutation** | Break the changed lines on purpose (flip `==`, `<`, `and`/`or`, `not`, `+1` on constants, drop a return value): do the tests notice? | BLOCK below 60% caught (3+ mutants); survivors listed. A deterministic sample (24 by default) keeps it fast; the working tree is always restored |
| **budget** | Is any function this change touched above complexity 15 *and* worse than before? | BLOCK. Legacy complexity is not punished |
| **`--strict`** | WARN also fails | for release branches |

Equivalent mutants exist (a change that cannot alter behaviour), so the threshold is 60%, not 100%.

## Typed failure briefs and the infrastructure/code split

`./securax forge classify FILE` says whether a red log is **infrastructure** (Docker daemon down, DNS, registry rate limit, disk full) or **code**.
`autobuild` re-runs the gate (twice, after a wait) on infrastructure reds instead of asking the model to "fix" code that is not broken, and
(proven by the `autobuild_loop` journey: the gate goes green on the re-run and the agent is called once) `./securax forge brief FILE` replaces the old 60-line tail with the typed, de-duplicated evidence plus the no-weakening reminder.

The **sandbox** does the same: if every failed check of a journey carries infrastructure evidence and nothing code-shaped, it restores/checks Docker and
re-runs that journey once. The retry is recorded in `sandbox/out/results.json` (`infra_retry`) and printed ("passed only after an infrastructure retry"), so
it is never silent. A failure with any code-shaped evidence is never retried. `--no-retry` turns it off. It does not restart your Docker for you.

## Reducing the dependency on the paid tier

Already in place (docs 23, 42): the *builder ladder* (OpenCode Go DeepSeek/GLM, then DeepSeek, free tiers, local coder), `autobuild`
with `verify`, `diffcheck` and now `forge` as the gate, and `escalate` for the hard 10%.
`forge` is what makes the cheaper tier trustworthy: a cheap model's change is accepted only if it survives a verifier that fights back.

## Not built, and why

* **Measured pass-rate per model.** Doc 23 still says the quality of cheap models inside the loop is unmeasured. A benchmark of ~10 real tasks run against each rung needs
  your provider keys and tokens; I did not fake it. Run `./securax autobuild` on real tasks and keep the results; a `forge bench` can be built once there is data.
* **Independent reviewer pass** (a second model that did not write the code). Needs a second provider rung; worthwhile once the above is measured.
* **Performance benchmarks as a gate.** The existing fitness ratchets cover size/latency budgets; per-function benchmarks would be noisy on a laptop.
* **Autonomous merge.** Deliberately not: `autobuild` stops at a reviewed branch.
