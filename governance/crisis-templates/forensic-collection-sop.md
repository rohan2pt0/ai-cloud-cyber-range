# Forensic collection SOP (on a running production system)

> Generic order of work for collecting artefacts a CERT / IR firm asks for, without disturbing a
> live system. Have the signed tool-exception in hand first, the system administrator present, and a
> running time-wise log. Order of volatility: collect the most perishable evidence first.

## Before you touch anything
1. Confirm written, time-boxed authority (the tool-exception form) and scope. Note start time.
2. Scan the external collection medium. Record its label. Nothing else gets plugged in.
3. Start a **time-wise action log**: every command, who ran it, on which host, and the output file.

## 1 — Volatile data first (do NOT power off yet)
- Memory capture (full RAM image) of each affected host.
- Running processes, loaded modules, services, scheduled tasks.
- Network connections, listening ports, ARP/DNS cache, logged-on users and sessions.
- Compute **SHA-256** of each output file as it is written.

## 2 — Targeted triage artefacts
- System, security and application event logs for the incident window.
- Registry/config hives, autoruns, prefetch, shell/command history, browser history.
- Application / gateway / messaging / database-audit / firewall logs for the window.
- Use an approved triage collector; keep everything read-only; hash every file.

## 3 — Disk image (only where required)
- Image with a write-blocker or a forensically-sound live method; record the imaging log and hash.

## 4 — Seal and hand over
- Write a **SHA-256 manifest** of every artefact.
- Complete a **chain-of-custody** form per artefact (see `chain-of-custody`).
- Hand over to the CERT / IR firm against the manifest; both sides sign; re-check hashes on receipt.
- Remove the privileged/shell access granted for the activity. Note end time in the action log.

> Golden rules: preserve before you analyse; never work on the original; hash at every step; one
> administrator present; change nothing else on the box; keep the clock (`./securax incident`) running
> so each agency's deadline is visible while you work.
