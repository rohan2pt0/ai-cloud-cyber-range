# Incident playbooks — run a response as a live checklist

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Mattermost-style Playbook runs for a SOC: ./securax playbook runs an IR scenario (ransomware, data-exfiltration, zero-day) as a live, ticked checklist across the NIST phases, each step pointing at the estate's own command (respond, incident, findings, restore); it records who/when, will not close while a critical step is open, and ends by writing a postmortem seeded with the run timeline. Library is data (governance/playbooks.json). Tests: test_playbook.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Borrowed from the way Mattermost runs a **Playbook** — a template you start as a *run*, tick through, and close with a
retrospective — but for a SOC, and wired to the estate's own commands. Under pressure you follow one calm checklist
instead of trying to remember every step; nothing critical gets skipped; and the run ends as a blameless postmortem.

```bash
./securax playbook list                              # the library: ransomware, data-exfiltration, zero-day
./securax playbook start ransomware "files encrypted on the share"   # begin a run — prints the ordered checklist
./securax playbook status                            # progress of the latest run
./securax playbook step <run> contain-isolate --by asha   # tick a step done (records who and when)
./securax playbook retro <run>                       # close it → writes the postmortem (critical steps must be done first)
```

## How it works

A playbook is an ordered checklist for one scenario, with its steps grouped by the **NIST SP 800-61** phases — **triage,
contain, eradicate, recover, report, learn**. Each step's `how` is the estate command that already does the work, so the
playbook is the connective tissue, not a replacement:

- **triage / report** → [`./securax respond`](78-CRISIS-RESPONSE-KIT.md) (forensic kit, IOCs) and `./securax incident` (the
  regulator clock for RBI / SEBI / CERT-In / DPDP, with deadlines and drafts);
- **eradicate** → `./securax findings add` (a fix-by date from the severity);
- **recover** → `./securax restore latest` (ransomguard proves the copy is clean first);
- **learn** → the run's `retro` writes a `./securax postmortem`, seeded with the run's timeline, and points you to
  `./securax adversary` to turn the root cause into a permanent probe.

A run records **who did each step and when**, and `retro` **will not close while a critical step is open** (pass
`--force` only when you deliberately accept that) — so an incident cannot be marked "handled" with the critical work
undone. Runs live in `vault/playbook-runs/` (private, in your backups, never in git).

## Make it yours

The library is **data**, in `governance/playbooks.json` — add a scenario or a step with no code change. Keep steps
pointed at a command where one exists, and mark the ones that must not be skipped `"critical": true`. The three that ship
(ransomware, data exfiltration, exploited zero-day) are a starting set for a BFSI SOC, not the last word.
