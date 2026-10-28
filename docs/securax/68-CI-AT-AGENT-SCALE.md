# 68 · CI at agent scale: prove what changed, not everything, every time

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The four tiers, impact-picked PR journeys, cancel-superseded and the nightly full run are built and tested; merge trains, auto-revert, the CLI split, sharding and prebuilt images are queued with triggers. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Without the tiers, every push would run all <!-- fact:journeys -->50<!-- /fact --> real-product journeys, which takes about 40 minutes. That is fine for one person. It does
not survive a coder agent, or a team of them, committing all day: the queue grows faster than CI drains it.

Anthropic hit the same wall at a far larger scale and replaced Git in its monorepo with an in-house system, Scion
(engineering post, 13 Oct 2026). Daily merges went from about 2,500 in May to more than 30,000 by September. Its stated
lesson applies here too: **writing code is no longer the bottleneck; the infrastructure around it is** (source control,
builds, CI).

## What we take from Scion, and what we do not

| Scion idea | For SecuRAX |
|---|---|
| Replace Git | **No.** Scion is internal and not offered for general use, and Anthropic itself says it is not a general Git replacement. It solves a repository of about 100 GB with tens of thousands of merges a day; ours is small. Git stays. |
| Fetch only what the job needs | **Yes:** each job proves only what the change can affect (below). The fast jobs already check out a shallow copy. |
| Infrastructure built for machines as the main clients | **Yes:** agents run the same gate locally before they push (`./securax verify`, the autobuild gate), so CI confirms work instead of discovering it. |

## The tiers (built)

| Tier | When | What runs | Time |
|---|---|---|---|
| **L0 · local** | before every commit, by people and agents | `./securax verify`: lint, unit tests, budgets, maps. `autobuild` commits only when it passes. | seconds |
| **L1 · pull request** | every push to a PR | unit tests, lint, scans (about 1 minute), plus **only the journeys that guard what the PR touches**, chosen from `lifecycle/impact.json` | 0 to a few minutes for a small change |
| **L2 · main** | every merge | **all <!-- fact:journeys -->50<!-- /fact --> journeys** | about 40 minutes, off the critical path |
| **L3 · nightly** | 02:00 IST | all journeys on main, before the laptops' 3:15 am safe update | about 40 minutes |

- **A newer push cancels the older run** of the same PR, so superseded commits stop using runners.
- **What a push never cancels:** a run on main, the nightly, a dispatched run or a release. Every workflow that runs on pull requests keys its group by the PR number and cancels only `pull_request` runs; releases queue one at a time. `test_a_new_push_never_cancels_a_run_it_should_not` fails a workflow that breaks this.
- **Each change is checked once:** devsecops runs for the pull request, and on main after the merge, not also for every push to the PR's branch (which ran everything twice).
- **A cancelled run proves nothing:** the Go/No-Go poll and the Monday release agent look past a run that was cancelled or skipped to the last one that ran to the end, so a replaced nightly never holds an update or a release.
- **Minutes:** standard GitHub-hosted runners are free for a public repository; the Free plan's real limit is 20 jobs at once, and jobs over it wait in a queue, they are not dropped.
- **The selection is the impact map.** Every tracked file belongs to a component, and every component names the journeys
  that guard it. CI runs `python3 lifecycle/impact.py --journeys` and passes the list to `sandbox/run.py -j`.

| A change to | Journeys on the PR |
|---|---|
| docs only | none (unit tests and fitness still run) |
| the Life OS (`guiding-map/ops.js`) | 4 |
| the risk register (`governance/risks.py`) | 8 |
| the gateway | 23 |
| the `securax` CLI, the sandbox, the map or the e2e workflow, or a file the map does not know | all |

**Why narrowing is safe:** what the map narrows away still runs at L2 on the merge and at L3 every night, so a miss is
caught within one merge and can be bisected between the last green and the first red commit. Nothing is skipped; it is
only moved off the path that blocks the next change.

## Next, as the agent count grows

| Step | Why | Trigger |
|---|---|---|
| **Merge trains** | 20 agent commits in an hour become one PR and one L1 run | more than about 10 PRs a day |
| **Auto-revert on a red main** | L2 finds the breaking merge and opens the revert itself, so main stays green without a person | the first L2 failure that a person had to chase |
| **Split the `securax` CLI** into one module per command | today one file is guarded by most journeys, so any CLI edit re-proves almost everything | when CLI changes dominate L1 time |
| **Shard L2 across runners** | 40 minutes becomes about 10 minutes with 4 runners (Actions minutes are free on public repositories) | when L2 lags behind merges |
| **Prebuilt sandbox images** | stop rebuilding the same images in every run | when image builds pass 10% of L2 |

Each step has a trigger, so none is built before it pays for itself.
