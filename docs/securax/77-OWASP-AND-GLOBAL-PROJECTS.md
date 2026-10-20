# 77 · OWASP and other global projects: what SecuRAX uses, what it adds now, what waits

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: the EPSS snapshot and its use in the findings register, and the OWASP Agentic Skills Top 10 tags and three new checks in ./securax vet. The projects marked later are decisions, not gaps. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The question.** OWASP and other well-known open projects keep publishing standards, tools and data. Which of them make SecuRAX safer, simpler or smarter, and are worth their cost?

**The rule used:** adopt a project when it removes real work or a real risk, runs offline, and fits what is already here. Otherwise, write down why not, and what would change that.

## Already in the estate

These were checked against the code, not only the docs:

| Area | Projects |
|---|---|
| **AI and agent risk** | OWASP Top 10 for LLM applications and agentic AI (gateway rails, compliance map), MITRE ATLAS, garak and promptfoo (red team), the MIT AI Risk Repository, NIST AI 600-1 |
| **Code and supply chain** | Semgrep, Gitleaks, OSV, Trivy, CycloneDX SBOM, OpenSSF Scorecard, SLSA provenance, Sigstore |
| **Run and detect** | OWASP ZAP, Falco, Wazuh, MISP, TheHive, Suricata, CIS checks through kube-bench, OPA policies |
| **Threat data** | CISA KEV and MITRE ATT&CK, kept as offline snapshots |

## Added now

### 1. FIRST EPSS: which vulnerabilities are likely to be attacked soon

**What it is:** FIRST, the global incident-response forum, publishes EPSS every day. It is an estimate, per CVE, of the chance that it is exploited in the next 30 days. KEV says "already exploited". EPSS says "likely next".

**What SecuRAX does with it:**

- `./securax offline sync epss` keeps a snapshot on disk: about 17,000 CVEs at 10% or more, 0.4 MB. A CVE that is not in it is under 10%.
- In the findings register (doc 76), a CVE at 50% or more is treated as at least **high**, so it gets the high fix-by date.
- `./securax findings` shows each finding's EPSS score, and the report counts the open ones at 50% or more.

**Why it is worth it:** most CVEs are never exploited. A small team that patches by EPSS and KEV first fixes what matters most with the same hours.

### 2. The OWASP Agentic Skills Top 10 (AST10, 2026) in `./securax vet`

**What it is:** OWASP's list of the ten biggest risks in AI agent skills and plugins: malicious skills, supply chain, over-privilege, metadata, remote instructions, isolation, drift, scanning, governance and cross-platform reuse.

**What SecuRAX does with it:**

- **Tagged findings:** every finding from `./securax vet` is tagged with the risk it is evidence of, in the terminal and in the report.
- **Three new checks**, for gaps the list exposed:

  | Risk | The check |
  |---|---|
  | AST05 Untrusted external instructions | Skill text that tells the agent to fetch instructions from a web address and follow them. The real instructions could change after vetting. |
  | AST03 Over-privileged skills | A skill that asks for unrestricted tools (`Bash` or `*`). A scoped grant such as `Bash(git status:*)` is fine. |
  | AST04 Insecure metadata | A skill that says it is read-only or offline while its code runs a shell or calls the network. |

- **The full mapping:** `./securax vet ast10` shows how each of the ten is handled, either by a check or by how the estate runs skills:
  - **AST06 isolation:** skill text only; third-party code is inspected in a sandbox, never run.
  - **AST07 drift:** pins, plus `vet verify`.
  - **AST09 governance:** the pin manifests are the inventory.
  - **AST10 cross-platform reuse:** a port is a new source, vetted again.

**Why it is worth it:** autobuild and the escalation brief use vetted skills. This is exactly the layer AST10 covers, and SecuRAX already had the gate. The work was to map it and close three gaps.

## Not now, and why

The target date for each is in doc 78 ("When later happens").

| Project | What it offers | Decision |
|---|---|---|
| **OWASP Juice Shop** and **CTF-in-a-Box** | A modern vulnerable web app for training, and a one-machine platform for CTF events | **Later:** worth adding as an optional practice target beside the AD range, for ZAP and purple-team drills. It adds a training target, not protection for the estate. CTF-in-a-Box is still an incubator project. |
| **OWASP Dependency-Check** | Software composition analysis | **Skip:** OSV and Trivy already cover it, offline, with no NVD API key. A second scanner would mostly repeat findings, and the register would merge them anyway. |
| **OpenCRE** | A graph linking standards (ISO 27001, ASVS, NIST 800-53, the OWASP Top 10) | **Later:** useful to show one control's equivalents across standards. It is an online service, and no offline bulk export was confirmed. Revisit when an export exists, or link out from the navigator. |
| **OWASP ASVS** | A checklist for verifying web application security | **Later:** an ASVS level-1 self-check of the gateway and the Life OS would be good evidence. It is mapping work, so it goes to the Claude tier when scheduled (doc 23). |
| **OWASP MASVS / MASTG** | Mobile app security standard and testing guide | **With the Play Store build** (doc 75): check the Android wrapper against MASVS before publishing. |
| **OWASP SAMM** | Software assurance maturity model | **Later:** the cockpit radar already scores maturity against CSCRF and RBI. SAMM would add a developer-process view only a team needs. |
| **MITRE D3FEND** | Defensive techniques mapped to ATT&CK | **Later:** a natural next layer on the purple-team report, from "attack detected" to "which defence stops it". |
| **Atomic Red Team** | Small tests that run one ATT&CK technique each | **Later:** the purple loop could run a few safe ones in the range. Each one runs real attack code, so it needs vetting first. |

## Sources and tests

- **Sources:**
  - [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/) · [the ten risks](https://owasp.github.io/www-project-agentic-skills-top-10/top10.html)
  - [FIRST EPSS](https://www.first.org/epss/): daily file at `epss.empiricalsecurity.com`, and the API at `api.first.org/data/v1/epss`
  - [OWASP CTF in a Box](https://owasp.org/projects/ctf-in-a-box) · [OpenCRE and the CSA mapping](https://cloudsecurityalliance.org/articles/opencre-org-the-how-and-the-why-of-security-best-practices) · [opencre-lib](https://pypi.org/project/opencre-lib)
- **Tests:**
  - `lifecycle/tests/test_vet.py`: the AST tags and the three new checks, including no false alarm on scoped grants
  - `lifecycle/tests/test_offline.py`: the EPSS snapshot
  - `governance/tests/test_findings.py`: EPSS raising severity and staying current
