# Policy-exception request — run forensic collectors on production

> Fill every `<…>` placeholder. This is a generic template, not legal or policy advice: your own
> information-security policy and approving authority govern. Keep the signed copy with the case.

| Field | Value |
|---|---|
| Reference | `<EXCEPTION-REF>` |
| Date | `<DATE>` |
| Department / office | `<DEPARTMENT>` / `<SITE>` |
| Asset(s) in scope | `<SYSTEM NAME>` — host `<HOSTNAME>`, address `<SERVER-ADDRESS>`, location `<DC or DR>` |
| Requested by | `<NAME, ROLE, EMP-REF>` |
| Approving authority | `<NAME, ROLE>` |

## Exception requested

Temporary, one-time permission to run digital-forensic collection tools (`<TRIAGE COLLECTOR>`,
`<ANALYSIS TOOL>`, `<PROCESS/ARTEFACT TOOL>`) from **approved external media**, with administrator
access, on the systems listed above, and to save the output to **approved external storage only**.
The activity needs administrator / privileged-shell access for the duration.

## Justification

The sectoral / national CERT (ref `<INCIDENT-REF>`) has asked us to share forensic artefacts from the
affected systems for analysis; the requested artefacts cannot be collected any other way. The work is
done **in the presence of the system administrator**. No other change is made to the servers.

## Controls applied

- Tools run from a **scanned** external medium; the system administrator is present throughout.
- Output saved to **approved media only**; a **time-wise log of every action** is kept.
- Privileged / shell access is **removed immediately after** the activity.
- The activity is performed in the **lean / low-traffic window** to minimise impact on service.

## Risk rating

| Risk | Current controls | Additional controls | Residual risk | Rating |
|---|---|---|---|---|
| Change in server state/load during collection | Access limited to authorised administrators; activity logged | Tools from scanned media; admin present; output on approved media; time-wise log; privileged access removed after | Low | **Low** |
| Malware entry through external media | Media scanned before use | Read-only handling; single approved medium | Low | **Low** |

**Window:** one-time, `<FROM datetime>` – `<TO datetime>`.

Requested: `<SIGNATURE / NAME>`   ·   Approved (Y/N): `<____>`   ·   Approver: `<SIGNATURE / NAME>`
