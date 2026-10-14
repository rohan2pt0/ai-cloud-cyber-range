# 33 · Fitness functions and game days — promises as numbers, resilience as rehearsal

## Fitness functions — `./securax fitness`
The architecture makes promises: a guardrail in every request that never becomes the bottleneck; a footprint that fits a 16 GB laptop; a supply chain that does not quietly grow new `curl | sh`; commands that are documented. Promises erode one innocent commit at a time, so each one is a check with a number (`lifecycle/fitness.json`) that **fails the build** when crossed (the *evolutionary architecture* idea: Thoughtworks/Google).

| Check | Measured today | Budget | Why it exists |
|---|---|---|---|
| **rails-latency** (worst of 12 adversarial 8 KB inputs, in and out) | ~7–11 ms | 100 ms | **ReDoS guard**: the rails sit in every request; one quadratic regex would make the gateway the outage |
| rails-memory (RSS after importing the guardrails) | 13 MB | 40 MB | low-resource promise |
| gateway-cold-start / gateway-memory | ~0.4 s / 46 MB | 5 s / 120 MB | wake-up and footprint |
| runtime-deps (gateway) | 3 | 6 | every dependency is attack surface and RAM |
| **supply-chain** *(ratchet)* | 6 known critical `vet` findings in our own tree (was 9: the three real `curl \| sh` installers are fixed) | may only shrink | new `curl \| sh` or decode-and-exec fails the build. the remaining 6 are the scanner's own patterns and test fixtures|
| **commands-documented** *(ratchet)* | 0 undocumented | 0 | a command nobody can find does not exist. It caught `organ`/`organ-check` (now documented in doc 29) and, on its own first day, its own sibling commands |
| burrow wake-time budgets | enforced in the `lifecycle_burrow` journey | first dig ≤ 120 s, wake ≤ 90 s | "wakes when you want it" is a number |

Budgets are generous on purpose (CI machines are noisy): they catch a **regression**, not a 10 % wobble. `./securax fitness --update-baseline` rewrites the ratchets and is a deliberate, reviewed act. The fast checks run inside `./securax verify`; the full set runs in the unit tests and CI.

## Game days — `./securax gameday list | run <scenario> | all [--out DIR]`
A resilience claim that has never been tested is a hope. Each scenario injects **one real failure** into the burrow twin (real k3s), then checks that it was **detected**, the **blast radius** stayed small, and it **recovered within its SLO**. The twin is left exactly as found unless you pass `--keep`.

| Scenario | What breaks | Measured on the twin (SLO) |
|---|---|---|
| `node-loss` | the GPU node is powered off | noticed in ~42 s (90); other nodes and the API unaffected; rejoined Ready in ~2 s (90) |
| `control-plane-restart` | the control plane restarts | API back in ~16 s (90); data intact |
| `snapshot-restore` | **disaster-recovery drill**: the cluster is corrupted after a snapshot, stopped, **rewound from the etcd snapshot** | restore ~12 s (120); pre-disaster data back, the rogue change gone, nodes Ready |

`./securax burrow …` gained the building block: `twin_restore` rewinds the control plane to a snapshot (`k3s --cluster-reset` in a throwaway container sharing the data volume). Reports (`--out`) are Markdown + JSON, with the SLO of every step and a plain statement of what the drill does *not* prove.

## Honest limits
* Game days run against the **twin**: they prove detection, containment and recovery of the *cluster layer* and a working etcd restore. They do **not** prove real NICs, disks or power, and on a kernel that cannot start containers inside k3s-in-Docker (e.g. this build sandbox) they do not exercise *workload* recovery. The estate's compose services are covered by the journeys `self_healing` and `watchdog_heals_and_alerts`, not here.
* The SLOs are for a laptop-class twin and were set from measurements with generous margins; real hardware will differ. Re-measure when it exists.
* Fitness budgets guard against regression; they are not a statement that the numbers are *good* for your workload.
* Not built: chaos for the compose estate (kill the router, fill the disk, cut the network) as a packaged scenario; scheduled game days (monthly restore drill via `./securax rhythm`).
