# 101 · A sandbox that proves more, with less of your time

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: ./securax proofs ranks the claims a journey could prove next; any journey runs on demand in CI; every PowerShell script is parsed, linted and (where safe) run on a real Windows machine. Two live nodes, a phone as a second device, chaos on the everyday estate and mutation testing of the rails are next, with dates. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** the sandbox should test things it never could before, in the most prudent way, using what the best engineering organisations do. It should also cut the human steps, so the owner spends time on real life rather than on the estate.

## 1. What the sandbox could not prove, and why

The sandbox runs 46 journeys against the real stack on every change; a pull request runs only the journeys that guard the files it touches (`lifecycle/impact.json`), and the full set runs on main and every night.

The pages still amber mostly say the same thing: their proof needs something the sandbox never had.
- **A second machine:** sync and failover between a laptop and a server (docs 86 and 91).
- **A second device:** the Life OS on a phone (doc 58).
- **Windows:** the PowerShell scripts were checked by reading only (docs 78 and 80).
- **Faults on the everyday estate:** the game day breaks the k3s twin, not the compose estate people use daily.
- **Proof that the tests bite:** a test suite that passes says nothing about whether it would catch a weakened rail.

## 2. What the best organisations do, and what we take

| Who | Practice | What SecuRAX takes |
|---|---|---|
| Meta, Google | Test impact selection: run the tests a change can affect | Already in place (impact map); on-demand single-journey runs added so a fix is proved in minutes |
| Netflix | Chaos engineering: a steady-state hypothesis, real-world faults, automated and continuous | A chaos runner for the everyday estate, seeded so every failure can be replayed |
| Google (DiRT) | Disaster drills that start safe, stop when the fix is not quick, and test people and process too | Every fault has a recovery time limit and is always reverted; the existing restore drill and tabletops stay |
| Google | Mutation testing on the code that matters, reported at review | Mutation testing of the safety rails, with a ratchet so the number of surviving mutants can only shrink |

## 3. Built in this round

- **`./securax proofs`** (`governance/proofs.py`): reads the status lights and the journeys, and lists the claims a journey could prove next, ranked (an unproven claim before a plan on paper), with the closest existing journey. Choosing what to prove next no longer needs a person.
- **Any journey on demand:** the e2e workflow takes a `journeys` input, so one journey runs on GitHub's machines in about 5 to 10 minutes instead of the full 40.
- **Windows scripts on a real Windows machine:** the `windows-scripts` workflow parses and lints every `.ps1` (PSScriptAnalyzer) and runs `free-c-drive.ps1` in its report-only mode, weekly and on any change to a script.

## 4. Next, in this order

| Step | What it proves | Target |
|---|---|---|
| Two live nodes in one sandbox | Sync both ways, one node down then catching up, a conflict resolved the same on both | 2026-10-31 |
| A phone as a second device (emulated) | HTTPS by name, installable, works offline, fits the screen, syncs to the laptop | 2026-10-31 |
| Chaos on the everyday estate | Each fault is detected and recovered within its time limit; seeded and replayable; nightly, not on every pull request | 2026-11-07 |
| Mutation testing of the rails | The tests would catch a weakened guardrail, residency, identity, kill switch, budget or sync guard | 2026-11-07 |

These four were started by build agents that stopped on a weekly usage limit; their partial work is kept and resumes after 2026-10-26.

## 5. What it changes for you

The estate proves more of itself every night and says plainly what it cannot prove. The messages that reach you are only the ones that need your hands: an account to open, a decision to make. Everything else is checked, repaired or reported without you.

## Sources

- [Principles of Chaos Engineering (arXiv 1702.05843)](https://arxiv.org/pdf/1702.05843)
- [Weathering the Unexpected: Google DiRT (ACM Queue)](https://queue.acm.org/detail.cfm?id=2371516)
- [State of Mutation Testing at Google](https://research.google/pubs/state-of-mutation-testing-at-google/)
- [Practical Mutation Testing at Scale: a view from Google](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/)
- [Predictive Test Selection: a replication study (TU Wien)](https://repositum.tuwien.at/bitstream/20.500.12708/215633/1/Aichmann%20Stefan%20-%202025%20-%20Predictive%20Test%20Selection%20A%20Replication%20Study.pdf)
