# 78 · Crisis response kit: step in, collect properly, find what is wrong, report

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: the response case with a permission gate and a hash-chained custody log, the USB kit (the Linux collector run in tests; the Windows collector parse-checked, not yet run on Windows), intake, private TLP-marked IOC import, triage, the report and the request list. The cloud GPU node and the AI case summary are next (targets in the doc). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The aim.** When an organisation is hit, for example by ransomware, its own SOC may be down too. SecuRAX should let one prepared person step in within the hour. That person must be able to:

- collect evidence the way a court or regulator expects
- find the known-bad addresses, files and footholds
- hand over a report the organisation's teams can act on

The same kit protects your own estate.

## In an emergency: the whole flow

```bash
./securax respond open "codename" --kind ransomware --for "Organisation" \
    --authorised-by "Name, CISO" --scope "file servers and two laptops, collect only"
./securax respond kit IR-20261102-codename /media/usb        # collectors, read-me card, custody form, tools list
#   on site: plug the USB into each affected machine and run collect.ps1 (Windows) or collect.sh (Linux, macOS, ESXi)
./securax respond intake IR-20261102-codename /media/usb/SECURAX --from "who handed it to you"
./securax respond triage IR-20261102-codename                # leads: known-bad IPs, domains, hashes, files; odd persistence
./securax respond report IR-20261102-codename                # custody record, evidence, leads, next steps (TLP-marked)
./securax respond requests IR-20261102-codename              # the information-request list for the organisation's teams (CSV)
./securax incident open "codename" --regulators cert-in,...  # the 6-hour reporting clock and drafted notices (doc 36)
```

Every step prints the next one.

## What the collectors take, and in what order

They follow the order of volatility (RFC 3227): what disappears first is taken first. Nothing is written to the affected disk, and nothing on the machine is changed or deleted.

| Step | Windows (`collect.ps1`) | Linux, macOS, ESXi (`collect.sh`) |
|---|---|---|
| 1. Memory | winpmem, if on the USB | AVML, if on the USB |
| 2. Running state | time; sessions; `netstat -ano`, plus each connection with its process and path; DNS cache; ARP; routes; processes with command line, parent and binary hash; shares; firewall; Defender | time; users; processes; connections (`ss`/`netstat`, `lsof`); interfaces; routes; ARP; programs running after their file was deleted |
| 3. Persistence | Run keys, services, scheduled tasks, both startup folders (listed with hashes, instead of screenshots), WMI subscriptions, Autoruns if on the USB | cron, systemd units and timers, start-up files, `authorized_keys`, recent files in temp folders, launchd on macOS |
| 4. Logs | Security, System, Application, PowerShell, Task Scheduler, RDP, Defender and Sysmon event logs; PowerShell histories | journal and `/var/log` for the last 3 days; shell histories |
| 5. Full triage | KAPE or a Velociraptor offline collector, if on the USB | UAC, if on the USB |

**Sealing:** each run ends by writing `MANIFEST.sha256` (every file's hash) and `collector.json` (who, when, which host, which collector).

**Quick mode:** `-Quick` or `--quick` takes running state and persistence only. Use it when minutes matter or there are many machines.

**What is verified, and what is not yet:**

- **The Linux collector** is run for real in the tests.
- **The Windows collector** passes PowerShell's own parser, but has not yet been run on a Windows machine in CI. Do a dry run on a lab machine before the first real one.

## Chain of custody

- **Permission is recorded first.** A case for another organisation cannot be opened without who authorised it and the scope.
- **Every step is an entry in a hash-chained log:** kit prepared, received (with who handed it over and the result of the hash check), analysed, notes. Editing or deleting any entry is caught by `./securax respond verify`, which also re-hashes every evidence file.
- **Intake checks every hash.** It also catches files that are missing or were added after sealing. Problems are kept and flagged, never silently dropped.
- **The evidence is made read-only** in `vault/respond/<case>/evidence/`. Analyse working copies, never the USB original.
- **The paper form** (`CUSTODY-FORM.csv`) rides on the USB for the hand-overs that happen away from a computer.

## Advisories and their IOCs, kept private

```bash
./securax respond ioc import ~/Downloads/advisory.pdf --source "advisory number" --tlp amber
./securax respond ioc import ~/Downloads/advisory-addendum.pdf --source "advisory number, addendum 1" --tlp amber
./securax respond ioc list
./securax respond ioc export --format csv      # for the firewall or DNS team: containment
```

**What it reads:**

- **IP addresses:** with the ranges advisories use (`a.b.c.1–11`, `.5, .7`, `147–175, 234–251`).
- **Domains and URLs:** written defanged (`[.]`). Plain addresses in prose are not taken.
- **Hashes:** including the ones a PDF table wraps over two lines.
- **File names:** taken from table rows. Windows's own programs, such as `cmd.exe`, are left out.

PDFs need `pdftotext` (`sudo apt install poppler-utils`).

**Privacy:** IOC files live in `vault/intel/iocs/` with their TLP. They are never committed, and every report and export carries the highest TLP among the sources used. A TLP:AMBER advisory may be shared only on a need-to-know basis, so this repository holds the method, never an advisory's text or indicators.

## The tools to put on the USB

The collectors work with what every system already has. Each optional tool adds depth; `tools/README.txt` on the USB lists the official sources:

| Tool | Use | Licence |
|---|---|---|
| WinPmem | Windows memory | Apache-2.0 |
| AVML | Linux memory | MIT |
| UAC | Unix-like triage | Apache-2.0 |
| Velociraptor | Offline collector; fleet-wide hunting later | AGPL-3.0, free |
| Autoruns | Windows persistence | Sysinternals licence, free |
| System Informer | Process, service and network detail, by hand | MIT |
| FTK Imager | Disk images, by hand | Free with registration |

**KAPE licensing:** Kroll's free licence does not cover commercial or professional work for another organisation; that needs Kroll's Enterprise licence. For work at other organisations the default is therefore Velociraptor plus UAC. KAPE stays where the affected organisation runs its own copy, or once you hold an Enterprise licence.

## Is a Raspberry Pi useful here?

**Yes, as a clean, dedicated responder box.** A Raspberry Pi 5 with 8 GB is about ₹7,000–8,500 at Indian retailers (unverified range; confirm with an official reseller). It can:

- run the intake, triage and reporting above, and a Velociraptor server for a few dozen machines;
- act as a passive network tap with a second network adapter, for traffic capture with Suricata;
- travel sealed with the USB kits, so the analysis machine never touches the affected network's systems.

**It cannot run the AI models at a useful speed, and it is not a disk imager.** Keep the models on the laptop, a GPU box, or the cloud tier below.

## The cloud GPU tier: pay only while it runs

**The scaffolding is already here:**

- Terraform for AWS, GCP and Azure (docs 25 and 29)
- the `tree` and `canopy` stages, which sleep and wake
- `./securax hibernate`
- the router, which already reaches Bedrock, Vertex and Azure

**The missing piece is a GPU node that wakes on demand and goes back to sleep:**

| Tier | What | Idle cost | Running cost (Mumbai, October 2026, check before use) |
|---|---|---|---|
| **1. Pay per token** | Hosted open models (for example Amazon Bedrock in Mumbai) through the existing router | none | DeepSeek v3.2 on Bedrock: about $0.74 per million input tokens, $2.22 per million output |
| **2. Spot GPU node** | One NVIDIA L4 VM running the estate's own models (Ollama or vLLM), started by one command, joined to the router, stopped after 30 idle minutes | the disk only | AWS g6.xlarge: about $0.97/h on demand, $0.39–0.60/h spot. GCP g2-standard-4: about $0.74/h on demand, $0.31–0.64/h spot |
| **3. Your GPU box** | A machine you add later joins the cluster as a GPU node (`./securax burrow`, doc 29). The router then prefers it automatically | electricity | — |

**The routing order:** your GPU box first, then the cloud GPU while it runs, then pay-per-token. A machine you add later needs no configuration change: it joins, and the router prefers it.

**Spot capacity can be taken back at short notice.** One tracker reports interruption rates above 20% for this instance type, so the node keeps its models on a persistent disk and restarts quickly. Customer data stays in India: the region is pinned to `ap-south-1` or `asia-south1` by the residency guard (doc 36).

## When "later" happens

These are target dates, not promises. Each needs your merge, and some need an account or a purchase.

| Item | Target | Needs |
|---|---|---|
| Cloud GPU node, `./securax burst up / down / status`, with idle auto-stop and router wiring | 2026-10-31 | An AWS or GCP account with a GPU quota in Mumbai |
| AI summary of a response case (the local model reads the leads and drafts the narrative; a person approves it) | 2026-10-31 | — |
| Velociraptor offline collector build helper, and fleet hunting | 2026-11-15 | — |
| Loading an advisory's detection rules into Suricata and Wazuh, privately from the vault | 2026-11-15 | The sprout stage with the Wazuh organ |
| OWASP ASVS level-1 self-check of the gateway and the Life OS (doc 77) | 2026-11-30 | — |
| MITRE D3FEND in the purple-team report | 2026-12-15 | — |
| Juice Shop as an optional practice target | 2026-12-31 | — |
| OWASP MASVS check of the Android build | With the Play Store build | The public site and a Play account (doc 75) |
| Atomic Red Team tests in the range | 2027-01-31 | Vetting each test first |
| OpenCRE links, and OWASP SAMM | Reviewed 2027-01-15 | An offline OpenCRE export; a second team member, for SAMM |

## What it does not do

- **It does not decide.** Triage gives leads to check, not findings of fact. A person signs the report.
- **It does not replace legal advice or the regulator's process.** The incident clock (doc 36) drafts notices; you file them.
- **It does not image disks.** For a full disk image use a hardware imager or FTK Imager, as your organisation's procedure says.

## Sources and tests

- **Public sources:** [RFC 3227, evidence collection](https://www.rfc-editor.org/rfc/rfc3227) · [NIST SP 800-86, forensics in incident response](https://csrc.nist.gov/pubs/sp/800/86/final) · [NIST SP 800-61, incident response](https://csrc.nist.gov/pubs/sp/800/61/r3/final) · [Velociraptor offline collections](https://docs.velociraptor.app/docs/deployment/offline_collections/) · [UAC](https://github.com/tclahr/uac) · [AVML](https://github.com/microsoft/avml) · [KAPE licence](https://www.kroll.com/en/kape-license-agreement) · [CERT-In CIAD-2021-0004, data breaches (TLP:WHITE)](https://www.cert-in.org.in/)
- **Prices:** [g6.xlarge, ap-south-1](https://www.doit.com/compute/spot/ap-south-1/g6.xlarge) · [g2-standard-4, asia-south1](https://calculator.holori.com/gcp/vm/g2-standard-4/asia-south1) · [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) · [Raspberry Pi 5 in India](https://thinkrobotics.com/blogs/learn/raspberry-pi-5-8gb-price-in-india-complete-buying-guide-2025)
- **Tests:** `governance/tests/test_respond.py` covers the permission gate, advisory-style IOC reading, a real collector run, intake, triage, the report, tamper detection and the request list.
