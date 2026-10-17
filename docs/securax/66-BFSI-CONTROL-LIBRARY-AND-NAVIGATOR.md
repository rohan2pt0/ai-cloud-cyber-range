# 66 · The BFSI control library, the navigator, and a dark cockpit

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Import, profiles, dominance, packs, navigator and the dark cockpit are built and tested; the library itself stays private on your machine. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

One library for every Indian BFSI cyber obligation (RBI, SEBI, IRDAI, IFSCA, NPCI/PCI/SWIFT, NCIIPC, CERT-In, DPDP),
mapped to controls with per-class applicability, citations, evidence and audit tests. SecuRAX reads it, shows what it
proves for each control, and draws it the way a mission cockpit would: the abnormal first, the rest one click away.

## Get it running (2 minutes)

```bash
./securax controls import          # finds the workbook in Downloads / Documents / Desktop (Windows ones too) and asks once
./securax controls dominance        # does complying with SCB/PSB cover every other class?
./securax controls gaps RRB         # the vital few for one class
```

Then open `http://localhost:8088/portal/navigator.html` (the cockpit's **Controls** lamp links to it).

- The library is **private**: it is written to `vault/controls/library.json`, which is never committed. The workbook's
  author metadata is never read.
- **Your scores** come from the workbook's yellow cells (Current and Target maturity, Likelihood, Impact). Fill them in
  Excel and import again; the navigator, radar and heat map update.
- **New regulations** are added as a pack in `governance/controls/packs/` (a JSON file with new controls, or extra
  citations for existing ones), or by importing a newer workbook. No code changes.

## The highest standard, and why "SCB/PSB covers everyone" is almost true

Each control says, per regulated-entity class, whether it is MUST, SHOULD, MAY or not applicable. Complying with the
strictest class covers a weaker one only if no control is stricter for the weaker class. Checking all 202 controls
against all 22 classes:

| Covered by SCB/PSB alone | Stricter than SCB/PSB on |
|---|---|
| Private, foreign, small finance and payments banks; UCB tiers; **RRB**; NBFC-ML/BL; HFC; ARC; CIC; PA/PG/PPI; NPCI/CCIL; FinTech/SRO | — |
| NBFC-UL, AIFI, IFSC IBU, MII (SEBI), stockbrokers/DPs | AUD-002 (SEBI system audit), AUD-006 (ISO 27001) |
| Insurers (IRDAI) | AUD-003 (IRDAI annual ISMS audit) |

So SecuRAX targets the **ceiling profile**: for every control, the strictest requirement of any class. Meeting the
ceiling meets every class, including RRBs and the classes above. `./securax controls dominance` re-checks this after
every import, so a new regulation that breaks the rule is flagged at once.

## What SecuRAX proves, control by control

`governance/controls/securax-map.json` lists the controls where SecuRAX itself supplies evidence, each with the files
that prove it. CI fails if one of those files disappears.

| | Controls |
|---|---|
| **Proven** (a file plus a test or CI check) | API authentication, default credentials, cryptographic inventory, PQC roadmap and hybrid pilot, data localisation, cross-border routing, encryption in transit, secure SDLC, API security, supply chain, security headers, IaC scanning, CERT-In 6-hour clock, multi-regulator notification, lessons learned, restore verification, continuous control monitoring, AI model risk, GenAI use and DLP, quantum-threat assessment, multi-regulator compliance register |
| **Partly** | MFA, least privilege, privileged audit, DLP and masking for AI traffic, backups, segmentation, remote access, code review, open-source scanning, container and cloud posture, vulnerability scanning, red team, KEV prioritisation, threat intel, ATT&CK-mapped triage, SOAR, playbooks, tabletop, ransomware drill, the board dashboard, the risk register, KRIs |
| **The organisation's** | the rest: board and committees, policies, people, contracts and vendors, physical sites, insurance, audits by third parties |

Grey cells in the navigator are not failures. They mark duties only an organisation can meet; a tool claiming them
would be wrong.

## The navigator

One page per profile (the ceiling plus each of the 22 classes):

- **Master caution panel.** Five lamps, lit only when something is abnormal: critical MUST controls not proven or at
  target, the vital few, proven or at target, controls you have scored, and controls stricter than SCB/PSB for this
  class.
- **The vital few (80/20).** The applicable MUST controls that are critical, not proven and below target. They are
  ranked by tier, your likelihood × impact score, and how many classes require them.
- **Navigator grid.** MITRE ATT&CK Navigator style: one column per domain (20), one cell per control (202).
  - **Colours:** green is proven by SecuRAX or at your target; amber is partly, or one level short; red is two or more
    levels short; grey is the organisation's.
  - **Shape:** a white edge marks a Critical control; faded cells are SHOULD or MAY.
  - **Hover** a cell for its requirement, citations and SecuRAX evidence.
- **Maturity by domain** (the spider web, as for NIST CSF): target, what SecuRAX proves, and your scored maturity.
- **5 × 5 risk heat map** from your likelihood and impact scores.
- **Regulators:** for RBI, SEBI, IRDAI, IFSCA, NPCI/PCI/SWIFT and NCIIPC/CERT-In/DPDP, how many applicable controls
  cite each, and how many SecuRAX proves, partly covers, or leaves to the organisation.
- **The SCB/PSB exceptions** table above, for this library.

Like the cockpit, it has no script, no external request, and nothing to click that changes the system.

## The cockpit, decluttered: the dark-cockpit rule

Aircraft and mission-control displays follow one rule: **when everything is normal, nothing is lit.** The crew's eye goes
straight to the one thing that needs a decision. The cockpit now does the same:

1. **Headline and "Do next"** (at most three actions), as before.
2. **Master caution:** warnings (act today), cautions (schedule), nominal count, and the **Controls** lamp to the
   navigator.
3. **Vital signs:** only red and amber tiles are shown. Nominal readings, and readings with no data right now, are
   folded away with their count.
4. **Mission planning** (Eisenhower, 80/20 themes, posture by area, AI risk, trends) is folded into one section you open
   when you plan, not when you check.

## Limits

- The library is a self-assessment aid built from a workbook, not an official regulator publication and not an audit
  opinion. Check circular numbers against the regulator before relying on them.
- SecuRAX's evidence covers the estate it runs. It does not show that an organisation's own systems meet a control.
