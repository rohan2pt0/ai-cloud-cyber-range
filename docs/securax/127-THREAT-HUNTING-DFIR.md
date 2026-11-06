# 127 · Threat hunting & post-crisis DFIR — find the foothold, at any scale

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Enterprise threat hunting & post-crisis DFIR: ./securax hunt drives Velociraptor (fetch-not-vendor; ships no proprietary binary) as a self-contained offline collector for minimal/pipeline mode or across a fleet at scale. The tool manifest declares each tool's licence + redistribution status + pinned hash (KAPE/FTK/Autoruns/Resource Hacker gated behind an audited EULA acceptance; KAPE-style triage via Velociraptor's open Windows.KapeFiles.Targets, no Kroll binary). Hunt packs (data, mapped to crisis scenarios) collect artefacts, score the output into prioritised findings deterministically (AI second opinion via the gateway when up), and list response actions — every endpoint action behind ./securax approve. The estate auto-prepares the hunt when a crisis is open (hunt-sweep routine, one node, no SPOF). Runs private in vault/hunt-runs/. Tests: test_hunt.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The problem this solves.** When a crisis is contained, the real work starts: *where was the foothold, how far did it
spread, and what did they leave to get back in?* Answering that means reaching endpoints — one suspect host, or
thousands — collecting the right artefacts, and triaging them fast. Most teams have neither the tooling wired nor the
muscle memory, and a post-incident hunt turns into days of manual collection. The 80/20: make the collection and the
first-pass triage **a push-button that runs in the infrastructure you already have**, and keep a human in command of
anything that touches a machine.

**What it does.** `./securax hunt` drives [Velociraptor](https://docs.velociraptor.app/) — the Apache-2.0 endpoint
engine — to collect and hunt, in two modes from the same packs:

- **Minimal / pipeline mode** — a single self-contained **offline collector** with *no server*. It runs on the suspect
  host or inside your DevSecOps pipeline, collects to a zip, and you triage it locally. This is the mode for when there
  is no standing DFIR infrastructure, which is most of the time.
- **Fleet mode** — a Velociraptor **server + clients** at mass scale (rolled out by GPO/Intune/WMI/WinRM/Ansible), with
  RBAC and multi-org for many teams, for hunting across the whole estate.

It grows from one to the other without changing the packs: the same artefacts run offline on one host or as a fleet
hunt across ten thousand.

## It ships no proprietary binary — fetch, don't vendor

Forensic tools have licences that forbid redistribution, so SecuRAX bundles none of them. `./securax hunt tools` is a
**manifest**: each tool is declared with its licence, whether it may be redistributed at all, its official source and a
pinned SHA-256, and is **fetched on first use** into a private cache (`vault/hunt-tools/`) — or from your own internal
mirror (`SECURAX_HUNT_MIRROR`), which is what mass deployment should always use.

| Tool | Licence | Redistributable? | In v1 |
|---|---|---|---|
| Velociraptor | Apache-2.0 | yes | **active** (the engine) |
| System Informer | MIT | yes | **active** |
| KapeFiles targets (via Velociraptor) | open KapeFiles | yes | **active** — KAPE-style triage, no Kroll binary |
| KAPE | Kroll EULA | **no** | gated — needs `hunt tools accept kape` |
| FTK Imager | Exterro EULA | **no** | gated |
| Autoruns (Sysinternals) | Microsoft EULA | **no** | gated |
| Resource Hacker | angusj freeware | **no** | gated |

The four non-redistributable tools are listed for completeness but stay **disabled** until a human accepts their EULA
(`./securax hunt tools accept <id>`), which is recorded. KAPE-style triage needs none of them: Velociraptor's
`Windows.KapeFiles.Targets` is built from the **open-source KapeFiles project**, not the Kroll binary, so it carries no
Kroll licensing exposure.

## Hunt packs — the artefacts, the scoring, and the actions

A **pack** (data, in `governance/hunt-packs.json`, mapped to the crisis and wargame scenarios) bundles three things:

1. the **Velociraptor artefacts** to collect;
2. **deterministic triage rules** that score the collected output into prioritised findings — a first pass to focus a
   human, *never* a verdict;
3. the **response actions** each finding may warrant.

```bash
./securax hunt packs                         # the library (ransomware-aftermath, payment-fraud-persistence, lateral-movement-sweep, quick-triage)
./securax hunt plan ransomware-aftermath     # what it collects, how it scores, what it may warrant — no execution
./securax hunt collector ransomware-aftermath   # generate a self-contained offline collector (minimal mode)
./securax hunt triage <run> --input <dir>    # score the collected output into prioritised findings
./securax hunt act <run>                     # the response actions — each as an approve-gated command
```

`collector` writes a run folder with `collect.sh` / `collect.ps1` (the exact `velociraptor artifacts collect …`
commands) and a spec — run it in the pipeline, bring the zip back, and `triage` it. Triage scoring is **deterministic**,
so it runs the same offline and in CI; when a gateway is configured, an AI agent adds a **second-opinion** triage through
the governed rails and audit trail, but it never replaces the deterministic findings.

## Automated, with a human floor

The user's hard requirement is *least human intervention, except where it matters*. So:

- **The estate prepares the hunt itself.** `./securax hunt sweep` (run as the `hunt-sweep` routine, every 30 minutes
  during a crisis, from **one node only** — no duplicate nudges, no single point of failure) notices when a crisis is
  open and no hunt has been gathered, and nudges to auto-prepare one. `./securax hunt auto <scenario>` prepares the
  matching pack's collector in one step.
- **Collection changes nothing on the endpoint** — it is read-only forensics, safe to automate.
- **Every action that touches a machine stays behind `./securax approve`** — isolate a host, capture memory, rotate
  credentials, remove persistence. AI and the estate *draft*; a human grants a **single-use, time-boxed, audited** yes.
  No agent isolates a host or rotates a credential on its own.

## Mass deployment, horizontal and vertical

The offline collector launches across a network by GPO, WMI or WinRM; the fleet server scales clients the same way, with
Velociraptor's built-in RBAC and multi-org carrying many teams. The enterprise edition adds a managed fleet, an internal
tool mirror with org-governed EULA acceptance, scheduled throttled hunts, a shared hunt-pack and detection library, and
AI-agent triage and drafted remediation behind the approval workflow. Watch the scale cost: a bulk triage collection on
ten thousand endpoints can pull **terabytes** ([server performance](https://docs.velociraptor.app/docs/deployment/resources/)),
so throttle fleet hunts.

## No single point of failure

The fleet Velociraptor server is a natural single point of failure — so it is never the only way in. The **offline
collector mode needs no server at all** and is the fallback: a self-contained collector runs anywhere and is triaged
locally. The tool manifest and packs ship with the code, so a hunt can be prepared on any node; a run's results and
findings live in that node's vault and are in the backups.

## Where it fits

- **After the coordination:** `./securax crisis` runs the multi-agency response; `hunt` finds the technical foothold the
  crisis was about, and auto-prepares itself while the crisis is open.
- **The clock and the kit:** `./securax incident` holds the regulator deadlines; `./securax respond` is the evidence kit
  and IOC triage; `hunt` reaches the endpoints at scale.
- **Practise it:** `./securax wargame` rehearses the coordination; the same scenarios drive the hunt packs here.

This is a collection and triage aid, **not** a verdict and **not** legal advice. A human owns every endpoint action,
behind `./securax approve`, and your forensic process owns admissibility.
