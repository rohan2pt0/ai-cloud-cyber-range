# Chain of custody

> One form per artefact (or one row per artefact in the table). The hash is what makes the copy
> admissible: compute SHA-256 at collection and re-check it at every handover. Never edit an artefact.

| Field | Value |
|---|---|
| Case / codename | `<CASE>` |
| Artefact ID | `<ARTEFACT-ID>` |
| Description | `<what it is — e.g. memory image of HOSTNAME / event-log export / triage package>` |
| Source system | host `<HOSTNAME>`, address `<SERVER-ADDRESS>` |
| Collected by | `<NAME, ROLE>` |
| Collected at | `<DATE TIME, time zone>` |
| Method / tool | `<TOOL + VERSION>` |
| Original size (bytes) | `<SIZE>` |
| SHA-256 at collection | `<HASH>` |
| Storage medium / label | `<MEDIA LABEL>` |

## Handover log

| # | From (name, role) | To (name, role) | Date & time | Purpose | SHA-256 re-checked | Match (Y/N) | Signature |
|---|---|---|---|---|---|---|---|
| 1 | `<…>` | `<…>` | `<…>` | `<collection → secure store>` | `<HASH>` | `<Y>` | `<…>` |
| 2 | `<…>` | `<…>` | `<…>` | `<store → IR firm / CERT>` | `<HASH>` | `<…>` | `<…>` |

> If a re-checked hash does **not** match, stop: the copy is compromised. Record it here, keep the
> artefact sealed, and raise it with the case lead and legal before any further handling.
