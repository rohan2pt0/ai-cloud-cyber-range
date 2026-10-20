SECURAX RESPONDER USB  ·  READ THIS FIRST  ·  case: see the file CASE_ID
===========================================================================

Before you touch anything
  1. Get written permission from the system owner: who, which systems, what you may do. No permission, no collection.
  2. Write the time and your name on CUSTODY-FORM.csv (one row per step, by hand or in a spreadsheet).
  3. Do NOT switch the machine off, restart it, run antivirus clean-ups, or delete anything. Memory and running state
     are evidence and they vanish on power-off.
  4. Isolate it from the network instead: pull the network cable or turn off Wi-Fi. Leave the power ON.
     (If the machine is a server others depend on, agree the isolation with its owner first and note it on the form.)

Collect (one machine at a time, the USB plugged straight into it)
  Windows:  open PowerShell as Administrator, then run (E: is this USB; use its real letter):
                powershell -ExecutionPolicy Bypass -File E:\SECURAX\collect.ps1
  Linux / macOS / ESXi shell:
                sudo sh /media/<this-usb>/SECURAX/collect.sh      (find the path with:  lsblk  or  df -h)

  It takes 2 to 10 minutes, longer if memory capture or a full triage tool is on the USB (see tools/README.txt).
  It writes ONLY to this USB, under evidence/<machine>-<time>/, and finishes by hashing every file (MANIFEST.sha256).

After each machine
  5. Note the folder name it printed and the finish time on the custody form.
  6. Safely eject the USB (Windows: "Safely Remove Hardware"; Linux:  sync  then  umount).
  7. Keep the USB with you or sealed in an evidence bag. Every hand-over gets a row on the form.

Back at the SecuRAX machine
  ./securax respond intake <CASE> /path/to/usb/SECURAX      checks every hash, records the hand-over, copies it in read-only
  ./securax respond triage <CASE>                           looks for known bad addresses, domains, hashes and odd persistence
  ./securax respond report <CASE>                           timeline, custody record, findings and next steps

Report the incident within the required time (CERT-In: 6 hours; your regulator's clock may also apply):
  ./securax incident open "..." --regulators cert-in,...    keeps every deadline and drafts each notice

This kit follows public good practice: RFC 3227 (order of volatility), NIST SP 800-86 and NIST SP 800-61.
