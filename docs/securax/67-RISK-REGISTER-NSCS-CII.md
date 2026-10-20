# 67 · Risk register, the NSCS audit baseline and national CII guidance, all linked

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Risk register, packs, links, CII self-check and the edge device ports are built and tested; the device ports with a real Tailscale serve are verified only on your laptop. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Risks, controls, audits and incidents describe the same things from different sides. SecuRAX keeps them as one picture:

```text
  NSCS audit markers ─┐                         ┌─ navigator (grid, radar, heat map, vital few)
  CII guidance ───────┼─► BFSI control library ◄─┼─ SecuRAX evidence (what it proves)
  RBI/SEBI/IRDAI/... ─┘        ▲                 └─ cockpit (master caution)
                               │ links
  V/T/R register + treatment plans ─► open risks ─► heat map, ranking, overdue lamp ─► postmortems
```

## 1. The risk register (`./securax risks`)

```bash
./securax risks import          # finds your registers in Downloads / Documents / Desktop (Windows ones too) and asks once
./securax risks list --open
./securax risks overdue                                    # exit 1 when a treatment is late (a routine can nag)
```

No path to type: it lists the workbooks that read as a register (the control-library workbook and unrelated sheets are
skipped) and asks `Import them? [Y/n]`. To import one file only, give its path: `./securax risks import FILE.xlsx`.

| What it reads | How |
|---|---|
| **V/T/R registers**: risk-wise and asset-wise registers, and the observations tracker | by **column name**, two-row headers included, so a re-ordered or extended workbook still imports |
| **Risk assessment + treatment plan** (probability × impact, inherent / reduced / residual, treatment type, owner, planned and actual end) | the assessment rows are joined to their treatment-plan rows by the treatment reference |
| **Scores** | the workbooks' own scale: inherent = likelihood (1–5) × impact (1–5); 20–25 critical, 12–19 high, 6–11 medium, 1–5 low |

- **Private by design.** The register is written to `vault/risks/register.json`, which is never committed. Registers name
  people, systems and findings; they stay on your machine and in your backups.
- **Linked to controls.** Each risk is linked to the library controls that would treat it, from what it is about:
  access, patching, vendors, backups, malware, physical, encryption, logging, and so on.
- **Re-import is safe.** Importing the same file again replaces that file's rows only.

## 2. How the links show up

| Where | What changes |
|---|---|
| **Navigator heat map** | if you have not scored controls yet, it plots your **open risks** by likelihood × impact |
| **The vital few** | a control that would treat a high open risk ranks higher (your risk score lifts it) |
| **Navigator master caution** | a lamp for **risk treatments overdue** |
| **Cockpit master caution** | the same lamp, lit **only** when something is overdue (dark-cockpit rule) |
| **Postmortems** | after an incident, `./securax postmortem new` records the mechanism; the related risk's treatment is where it is tracked |

## 3. NSCS Cyber Security Audit Baseline (NSCS-46-16, Oct 2020)

A pack, `governance/controls/packs/nscs-audit-baseline-2020.json`, links each of the **68 audit markers** to the library
controls they test:

- csm.1–19: management
- pro.1–21: protection
- det.1–9: detection
- res.1–11: response
- rec.1–3: recovery
- imp.1–5: lessons learnt

The navigator's regulator table gains a row for it, and every linked control's hover shows its markers. Marker `pro.19`
(change control) had no matching control, so it became a new one, **AS-101**.

The baseline has three **risk profiles**, all recorded in the pack:

| Profile | Which markers are mandatory |
|---|---|
| High risk | all markers |
| Medium risk | all except `pro.12`, `pro.13`, `pro.20`, `det.3`, `res.1`, `res.8`, which are recommended |
| Low risk | 18 markers are recommended |

The publication is licensed CC BY-NC-SA 4.0 (non-commercial), so the pack carries marker IDs and links only, never its
text.

## 4. National CII guidance: evaluating and identifying Critical Information Infrastructure

The pack `governance/controls/packs/cii-guidance.json` links library controls to two national CII guidance documents.

The **Framework for Evaluating Cyber Security in CII** (v1) has five phases:

| Phase | What it covers | Linked controls include |
|---|---|---|
| I · Identify infrastructure | structure, systems, ICS/SCADA, networks, services, criticalities, interdependencies, owners | asset inventory, data flows, BIA, concentration risk |
| II · Assess | V/T/R, network architecture, standards, policies, HR, compliance | risk assessment, segmentation, policy library, HR controls, compliance register |
| III · Implement controls | — | — |
| IV · Verify | verifying the controls are implemented | continuous control monitoring, VAPT |
| V · Ensure compliance to audit | audit | IS audit, special audits |

The **Guidelines for Identification of CII** (v1.0, Aug 2019) supply four impact tests: national-scale impact on
customers and business, the timeframe to serious impact, geographic spread, and cascading dependency.
`./securax risks cii` asks them and records the answer:

| Result | Meaning |
|---|---|
| **Likely CII** | treat the systems as **High-risk** infrastructure: every NSCS marker is mandatory. Engage the national CII agency through your sector regulator. |
| **Possibly CII** | document the assessment and re-check yearly; use the Medium profile |
| **Unlikely CII** | use the profile your risk assessment sets |

It is a self-check: designation is the Government's (section 70, IT Act), on the national CII agency's advice. The issuing agency reserves all rights
to its documents, so the pack holds phase and paragraph references only.

## 5. Professional names and phones together

The `https://hub.securax.localhost` names come from the HTTPS edge (`./securax tls on`). Phones over Tailscale used to
need it off, because `tailscale serve` forwards to a **port** and the edge hid every port behind its single named one.

The edge now also listens on two **loopback-only device ports**: 9443 for the app (with `/v1`, `/healthz`, `/version` and
`/sync` on the same origin) and 9444 for Chat. `./securax go` and `./securax phones --apply` point Tailscale at them when
the edge is on. So:

| Device | App | Chat |
|---|---|---|
| This laptop (edge on) | `https://hub.securax.localhost` | `https://chat.securax.localhost` |
| Phones | `https://<laptop>.<tailnet>.ts.net` | `https://<laptop>.<tailnet>.ts.net:10000` |

To switch: `./securax tls on && ./securax go`. Each address keeps its own app data, so open the laptop sync link from
`./securax sync-link` once at the new address.

**When another program already uses port 80 or 443** (on Windows often IIS, a VPN client or another web server):

- `./securax tls on` checks first, changes nothing, and tells you how to find the program
  (`netstat -ano | findstr :80` in PowerShell; the last number is its PID, Task Manager > Details shows the name).
- If the ports become busy later, `./securax up` and `./securax go` switch back to `http://localhost:8088` by themselves,
  so you are never left with nothing running. Free the port, then `./securax tls on && ./securax go` again.

## Limits

- A risk-to-control link is a pointer to the control family that treats the risk, made from the risk's wording. Review it,
  and treat it as a starting point, not as an assessment.
- The NSCS and national CII mappings are this project's reading of those documents. Check them against the originals before an
  audit.
