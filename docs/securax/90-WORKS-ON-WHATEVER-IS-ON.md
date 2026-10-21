# 90 · It works on whatever machine is on

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and proved on the real containers (journey machine_alone): with a model machine, two VPS peers and an off-site folder configured but switched off and no cloud key, up succeeds and says so, the router leaves the model machine out (no 5-minute waits), chat answers here, the Life OS saves and reads, nodes names the unreachable peers, a backup is taken and the home screen serves. The model machine is added back by itself within 5 minutes of answering. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** even when no VPS, no Mac mini or GPU box, and no AWS, GCP, Azure or private-cloud instance is connected, the whole estate must work as expected on the machine that is there.

**The answer in one line:** every other machine is an extra, never a dependency. When one is off, this machine carries on by itself, says so in plain words, and takes the extra back when it returns.

## 1. What each extra machine adds, and what happens when it is off

| Extra machine | What it adds | When it is off | Proof |
|---|---|---|---|
| **A model machine** (Mac mini, GPU box: `REMOTE_OLLAMA_BASE`, doc 56) | Faster, stronger local answers | **Fixed in this change.** It used to stay in the router's ladder, so each question could wait up to 5 minutes for a machine that was off. Now it is left out while it does not answer, so this machine answers at once. `up` says so. The `home-machine` routine checks every 5 minutes and puts it back first when it answers again. Its wait is also cut to 90 s, in case it goes off mid-day | Unit test; sandbox `machine_alone` |
| **A VPS or another node** (`nodes`, doc 86) | Your data on every device; something always on | This machine keeps every person's data itself and serves the Life OS. The sync service retries the peers in the background and never blocks. When a peer comes back, the merge catches up in any order | `machine_alone`; doc 86's two-node tests |
| **The online tunnel** (`online`, doc 85) | Your own addresses from anywhere | Local addresses keep working. `up` says the tunnel did not start and goes on | `up` treats it as optional |
| **Cloud AI providers** | Stronger answers | The ladder ends on this machine's own model, which needs no key and no internet | `local_model_answers`; `key_wiring_and_failover` |
| **AWS, GCP, Azure, private cloud** (lifecycle stages, doc 29) | Scale, when you choose to grow | Dormant by default. Nothing in daily use needs them, and nothing is created without `--apply` | `lifecycle_cloud_is_safe` |
| **An off-site folder** (OneDrive, doc 88) | A copy away from this machine | The backup is still taken here, with a warning. The restore drill proves the local copy and says that it is not off-site | `machine_alone`; doc 88 |

## 2. The proof: one machine, everything else switched off

The sandbox journey `machine_alone` starts the real estate with:
- a model machine configured at an address that does not answer;
- two VPS peers configured that cannot be reached;
- an off-site folder that is unplugged;
- no cloud key at all.

It then checks, on the real containers:
1. `up` succeeds, and says the model machine is off and this one answers.
2. The router leaves the model machine out.
3. A chat question is answered here, and well inside the 5 minutes it used to cost.
4. The Life OS saves and reads its data, and the sync service records the peers as unreachable while it keeps serving.
5. `nodes` names the unreachable peers without breaking.
6. `models home` reports the model machine off.
7. A backup is taken.
8. The home screen serves.

## 3. Commands

```bash
./securax models home     # is your model machine on? (the home-machine routine runs this every 5 minutes)
./securax nodes           # which other nodes this one syncs with, and whether each answered
./securax online status   # whether the tunnel is connected
```

## 4. Limits, said plainly

- **On its own, this machine answers with its own model.** That is slower and less knowledgeable than a cloud or GPU model, and doc 89's note says so on each such answer.
- **With no internet**, web search and cloud models are off until it returns. Everything else works.
- **A peer that was off misses nothing.** Its data merges when it is back. Two people editing the same item while apart is resolved by the latest edit (doc 86).
