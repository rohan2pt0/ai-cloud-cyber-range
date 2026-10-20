# 81 · The range against the market, and how it teaches: MITRE frameworks, learning paths, players and badges

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: ATT&CK 20.0 / D3FEND / ATLAS 5.6.0 tags on tasks, attacks and incident reports (checked against MITRE data), the coverage screen, six learning paths, personal players with XP from judged work, levels and badges. The AI zone, multi-tenancy and commercial readiness are dated in the doc. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The aim:** make the exercise range (doc 79) worth paying for. Teams, client organisations and government should both practise against adversaries, frontier-AI threats included, and come out knowing how to use the industry's shared language for attack and defence.

## 1. Where the range stands against commercial platforms

This comparison draws on public sources (listed below). Vendors' own claims are marked as such.

| | Live-fire team exercise | Scoring and judging | Simulated users and traffic | Framework mapping | Individual skills and gamification | AI/ML threat content | Where it runs |
|---|---|---|---|---|---|---|---|
| **CybExer** (Estonia) | Yes: government, defence, critical infrastructure | Yes (the portal you used) | Yes | Not confirmed in sources | Limited | Not confirmed | Cloud, on-premises, hybrid |
| **Cyberbit** (now with RangeForce) | Yes: SOC live-fire with real tools | Yes | Yes | ATT&CK-aligned (vendor claim) | Yes: RangeForce's individual and team measurement | Not confirmed | Cloud |
| **SimSpace** (MIT Lincoln Laboratory roots) | Yes: replicated corporate networks, users include US Cyber Command | Yes | Yes | Not confirmed in sources | Limited | Not confirmed | Cloud or on-premises; priced for large programmes |
| **Hack The Box Enterprise** | Team exercises | Yes | Partial | Labs mapped to ATT&CK and NIST (third-party listing) | Strong: ranks, paths, certifications | Some | Cloud |
| **TryHackMe** | Team formats (King of the Hill etc.) | Yes | No | Tabletop exercises based on ATT&CK (vendor) | Strong: guided paths, beginner-friendly | Some | Cloud |
| **Immersive Labs** | Cyber drills | Yes | Partial | Results mapped to NIST and ATT&CK (vendor) | Yes | Some | Cloud |
| **Locked Shields 2026** (NATO CCDCOE event, not a product) | 4,000+ participants, 41 nations, ~6,000–8,000 attacks; power grid, 5G, satellite, battle management, elections | Yes | Yes | — | — | AI research team present | Event |
| **SecuRAX range (today)** | One team, lite range on a laptop; full range planned | Yes (doc 79), tamper-evident | SSH logins with documented passwords; richer in stage 2 | **Yes, per event:** every task, attack and incident report tagged with ATT&CK 20.0, D3FEND and ATLAS 5.6.0, checked against MITRE's data, linked to MITRE's pages | **Yes:** personal players, XP from judged work only, levels, badges, six learning paths | ATLAS-tagged AI-defence task now; a real AI zone in stage 2b | **Laptop, offline, your own cloud; data stays in India** |

**Where we are honestly behind:**
- **Content scale:** commercial platforms have years of scenarios, large lab libraries and staff who write new content weekly.
- **Infrastructure depth:** they have full Windows, OT, 5G and satellite environments.
- **Proof:** they have been assessed by customers. Ours is new and has been tested only by us.

**Where we can lead:**
- **Owned and private:** it runs offline and inside India, and client data never leaves.
- **Built into the estate:** the GOAD AD lab, the purple-team loop, the AI gateway, the crisis kit (`respond`) and the regulatory incident clock all sit in one estate.
- **Defence as the primary language:** D3FEND is mapped alongside ATT&CK, not as an afterthought, so defence is scored, not just attack.
- **Built for frontier AI:** ATLAS is first-class and the estate already carries its own AI red team.
- **Cheaper** for an Indian team or client than a per-seat foreign platform.

## 2. Learning the frameworks by using them

- **One vocabulary for every event:**
  - The red team names the **ATT&CK** (or **ATLAS**) technique it used.
  - The blue team names what it **saw** (ATT&CK/ATLAS) and what it **did** (**D3FEND** technique or ATLAS mitigation) in each incident report.
  - Every task carries the techniques it is about.
- **Framework coverage screen.** Grouped by tactic, it shows which techniques the exercise threw at the team, which the team **detected** (an accepted incident report naming it), and which defences it **applied**. Each identifier opens MITRE's own page. Read it after every exercise; that is how the frameworks stick.
- **The after-action report** carries the same table.
- **The catalogue** (`exercise/frameworks.json`) holds only the 64 identifiers the range uses, with MITRE's official names, rebuilt from MITRE's own data:
  - **ATT&CK** 20.0 STIX
  - **D3FEND** CSV export
  - **ATLAS** 5.6.0. MITRE marks this file as no longer updated; the catalogue will follow the new ATLAS distribution when its format settles.
- **No tag is ever taken on trust.** A scenario, attack report or incident report with an unknown identifier is refused.
- **Links verified:** every D3FEND link, and the ATT&CK and ATLAS link patterns, were opened during the build.

## 3. Learning paths and certifications

Six paths: Identity and Active Directory · Linux hosts and services · Network edge · Data theft and ransomware · AI and LLM systems · Reporting under pressure.

Each path lists its techniques, why they matter, where to practise in the estate, and your progress through it.

**On certifications:**
- **What each path names:** the certifications whose *published syllabus* covers the same skill area:
  - Altered Security CRTP for Active Directory
  - OffSec OSCP+
  - HTB CPTS, which also requires a professional report
  - HTB CDSA for defensive analysis
- **The range helps** with the skills and the habits: enumeration discipline, Active Directory concepts, persistence, detection and report writing.
- **What it does not hold:** any exam content. Exam agreements forbid sharing exam material, and copying it would put a candidate's certification at risk.
- **Offensive practice belongs in labs you own:** the GOAD Active Directory lab (`./securax range`) and the vendors' official labs.
- **For AI systems** there is no mainstream certification yet. The path points to the OWASP Top 10 for LLM applications and NIST AI 600-1, both already mapped in the estate.

## 4. Players, levels and badges

- **Personal tokens:** `./securax exercise player NAME` gives one person a personal token, so their work is credited to them as well as to the team.
- **XP** comes only from:
  - points a judge awarded to accepted work
  - 10 per team-plan item closed
  - 5 per staff password change documented

  Submitting earns nothing until it is judged, and a rejected report earns nothing.
- **Levels:** Recruit 0 · Analyst 100 · Defender 250 · Hunter 500 · Architect 1,000.
- **Badges,** each one saying why it was earned:

  | Badge | Earned when |
  |---|---|
  | First detection | An incident report of yours is accepted |
  | Tactician | 3+ ATT&CK techniques detected across 3+ tactics |
  | Hardener | 5+ D3FEND hardening techniques applied |
  | AI defender | An ATLAS technique detected or defended |
  | Reporter | 3 situation reports accepted |
  | Planner | 5 team-plan items closed |

- **Visibility:** the blue team sees its own players; exercise control sees everyone.

## 5. The path to a paid offering (target dates, each needs your merge)

| Stage | What | Target |
|---|---|---|
| 2 · Realism | Richer simulated users (web, mail, files). Adversary emulation in the lab with ATT&CK-tagged, vetted steps. An ICS zone (OpenPLC). Wazuh and Suricata in the security zone | 2026-11-10 |
| 2b · AI zone | The estate's real AI gateway and a tool-using assistant as range hosts. ATLAS-tagged injects. Rule checks that guardrails stay on and the AI service stays up | 2026-11-15 |
| 3 · Blue-team kit | The safe hardening playbook; report drafts from evidence; team dashboard | 2026-11-25 |
| 4 · Full range, several teams | The Windows estate and network gear in the cloud or on Proxmox; VM console; team chat | 2026-12-20 |
| 5 · Commercial readiness | A separate, isolated range per client; SSO (Keycloak); metering (the tenants stage); instructor dashboard; completion certificates; scenario authoring with peer review | 2027-Q1 |
| 5 · Legal and trust | Compliance and licensing:<br>• **Learner data:** under India's DPDP Act.<br>• **MITRE content:** attribution and licence notices, kept as each framework's terms require.<br>• **Trademarks:** no other vendor's names or marks in the product.<br>• **Contracts and terms of use.**<br>**Independent checks:**<br>• **Security test:** an outside test of the platform itself.<br>• **ISO 27001:** controls aligned before selling to government. | 2027-Q1 |

## Sources

- [Best cyber range platforms (CyberDefenders)](https://cyberdefenders.org/blog/best-cyber-range-platforms/)
- [Top cyber range providers (HackRead)](https://hackread.com/top-cyber-range-providers-comparison-leading-platforms/)
- [Cyber range training platforms 2026](https://guptadeepak.com/tools/top-5-cyber-range-training-platforms-2026/)
- [Cyberbit vs CybExer (CB Insights)](https://www.cbinsights.com/compare/cyberbit-vs-cybexer-technologies)
- [TryHackMe vs HTB Enterprise (TryHackMe)](https://tryhackme.com/compare/hackthebox-enterprise)
- [Immersive Labs vs Hack The Box (Immersive)](https://www.immersivelabs.com/h2h/immersive-vs-hackthebox)
- [Immersive Labs Cyber Drills vs HTB Enterprise](https://cybersectools.com/compare/immersive-labs-cyber-drills-vs-hack-the-box-enterprise-platform)
- [Locked Shields 2026 (CCDCOE)](https://ccdcoe.org/news/2026/locked-shields-2026-united-the-power-of-41-nations-to-defend-cyberspace)
- [Locked Shields 2026 (SecurityWeek)](https://www.securityweek.com/locked-shields-2026-41-nations-strengthen-cyber-resilience-in-worlds-biggest-exercise/)
- [MITRE ATT&CK data](https://github.com/mitre-attack/attack-stix-data)
- [MITRE D3FEND](https://d3fend.mitre.org/)
- [MITRE ATLAS data](https://github.com/mitre-atlas/atlas-data)

## Tests

- **`exercise/tests/test_learning.py`:**
  - official names and links
  - unknown tags refused
  - met / detected / applied coverage
  - XP only from judged work
  - badges with their thresholds
  - levels and paths
  - personal tokens through the portal
  - red seeing attack techniques only
- **`exercise/tests/ui_audit.py`:** every new screen, for every role, in both themes and at phone width (342 checks).
