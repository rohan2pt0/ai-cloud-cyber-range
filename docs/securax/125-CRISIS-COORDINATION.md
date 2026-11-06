# 125 · Crisis coordination — hit every agency deadline

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Multi-agency crisis coordination: ./securax crisis opens an agency requisition from a ready, generic template (law-enforcement production notice, sectoral CERT forensic requisition, regulator incident report), every item pre-assigned to its owning team; tracks done/pending/overdue against the deadline; and generates the response pack (register + filled cover letter). Ships ready documents (forensic-tool-exception, chain-of-custody, forensic-collection SOP, duty roster, cover letter). Runs private in vault/crisis-runs/. Pairs with incident (the clock) and playbook. Templates are data (governance/crisis.json, governance/crisis-templates/). Tests: test_crisis.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The problem this solves.** In a real cyber crisis the attack is only the start. Within hours a sectoral or
national **CERT** wants forensic artefacts, the **financial regulator** wants an incident report, and the
**police / state cyber agency** send a production notice — a long schedule of questions, each needing a
*specific record* from a *specific team*, with a short, hard deadline. Teams that have never rehearsed this
lose days hunting for who owns what, and a missed deadline turns into a show-cause notice. The 80/20: the work
is **coordination and completeness against a clock**, not the writing of each answer.

**What it does.** Each requisition is a ready **template** (generic data — no organisation, person or case in
it): sections, each owned by a team, each item a question plus the record to attach. You open a run, every item
is pre-assigned, and you track it to done.

## Least-friction path (you, alone, under pressure)

One command stands the whole crisis up; one command tells you what to do next. No remembering, no juggling tools.

```bash
./securax crisis start payment-fraud --title "<codename>"
./securax crisis next
./securax crisis comms exec-sitrep
```

- **start `<scenario>`** — opens the standard requisitions for the scenario (ransomware, payment-fraud,
  data-breach, outage) in one step, and prints the ordered next moves: start the regulator clock, open the
  response checklist, and the first messages to send.
- **next** — the single most urgent action right now, named with the exact command: the requisition nearest
  its deadline, the section with the most pending items, and who owns it. Zero thinking required.

## The full flow

```bash
./securax crisis templates
./securax crisis new le-production-notice --agency "<agency>" --ref "<their ref>" --due 72h
./securax crisis status
./securax crisis assign <id> makers --to "<Payments SPOC>"
./securax crisis set <id> 2.3 --done --evidence "<file or location>"
./securax crisis set <id> 10.4 --na --note "<why it does not apply>"
./securax crisis pack <id>
```

- **templates** — the library: law-enforcement production notice (state), sectoral CERT forensic requisition
  (national), financial-regulator incident report (national), plus the ready documents below.
- **new** — open a requisition from a template; the deadline is set from `--due` (e.g. `72h`, `3d`, or an exact
  time) or the template default.
- **status** — progress by team, what is overdue, and the time left on the clock. Exit code is non-zero when
  something is due soon or overdue, so a routine can watch it.
- **assign / set** — give a section or item to a team or named single-point-of-contact; mark each item
  *done*, *not-applicable* or *pending*, and record where the evidence is.
- **pack** — write the response pack: a register (Markdown + CSV) keyed to the agency's item numbers, and a
  cover letter filled with the agency and reference. Fill the evidence references, attach each record, and
  have legal sign the cover letter before it goes out.

Runs live in `vault/crisis-runs/` — private, in your backups, never in git.

## The ready documents

The moments that stall a real response have a template, so they are a fill-in, not a first draft:

```bash
./securax crisis doc forensic-tool-exception
./securax crisis doc chain-of-custody
./securax crisis doc forensic-collection-sop
./securax crisis doc duty-roster
./securax crisis doc agency-cover-letter
```

- **forensic-tool-exception** — a policy-exception request to run forensic collectors on production (the
  authority a CERT artefact requisition needs before anyone touches a live server).
- **chain-of-custody** — one form per artefact; the hash is what makes the copy admissible.
- **forensic-collection-sop** — the order of work on a running system: volatile data first, hash everything,
  change nothing else.
- **duty-roster** — the shift-wise roster agencies almost always ask for first; keep it current so it is a
  copy-out, not a scramble.
- **agency-cover-letter** — the covering letter for the response pack.

## Crisis communications — everyone on the same page

In a crisis people write too much, too slowly, and in ways that create legal and reputational risk. `crisis
comms` is a library of **short, factual, legally-defensible** drafts — one source of truth per audience, so
every channel says the same thing.

```bash
./securax crisis comms                              # list all drafts + the rules
./securax crisis comms staff-alert-sms              # one draft, with guidance
./securax crisis comms --audience customers --medium sms
```

Audiences and media: an executive **SITREP** (email), a **staff alert** (SMS) and brief (email/broadcast), a
**frontline script** (one line the whole counter says), **customer** reassurance (SMS/WhatsApp) and a data
notice (letter), a **public holding statement**, a **partner recall** request (beneficiary banks), and an
**IR-vendor activation** note. Every draft obeys the same rules — facts only, no admission of fault, no
sensitive detail, one action and one contact, keep it short — and carries a fold-in anti-fraud line where it
faces customers. Fill the `<…>` placeholders; legal / compliance / communications **approve before anything
goes out**.

## Where it fits

- **Deadlines:** `./securax incident` runs the exact regulator clock (which regulator, what channel, by when);
  `crisis` tracks the *content and coordination* of each requisition. Start both when a crisis opens.
- **The response itself:** `./securax playbook` is the live triage→contain→recover→report checklist.
- **Modes:** it works for a single responder (just the register) and for a large organisation (per-team owners
  and SPOCs); the enterprise edition adds shared runs, SLA timers and an organisation-governed library.

This is a coordination aid, **not legal advice**. Your legal and compliance teams own the actual response and
sign off before anything leaves the building.
