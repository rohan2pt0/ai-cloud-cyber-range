# Spec: ip-and-papers — every build also yields patents and papers, with one write-up

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The rule, the template and the queue item; ./securax ip and its fitness check are next. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Queue item `ip-and-papers` · owner 2026-11-18: "whatever I am building also yields patents, research papers or research
publications which build my profile in parallel, without much overlapping effort."

## The one rule: decide before it goes public

The repository is public. In India an inventor's own publication before filing can destroy novelty: Section 31 of the
Patents Act exempts only narrow cases (a government exhibition, a paper read before a learned society, with Form 31 under
Rule 29A). The US gives one year of grace; Europe effectively none. So **a new technical mechanism is decided before its
first public commit, post, video or talk**: file (a provisional), publish (a paper, which then makes it prior art for
everyone), or keep it as know-how. Business methods and a program as such are excluded in India (Section 3(k)); a claim
needs a technical solution to a technical problem with a technical effect (the 2025 guidelines for computer-related
inventions). Check the Patent Office's own pages for the current form and fee before filing.

## One write-up, three outputs (no overlapping effort)

1. **Invention note** (private, `vault/ip/`, never committed; template: `docs/templates/invention-note.md`): the technical
   problem, the mechanism, the measured effect, the closest prior art, the date. Twenty minutes, written while building.
2. **Provisional application** from the note (Form 1 and Form 2, as a natural person), when the note shows a technical
   effect and the prior-art check finds nothing the same. Twelve months to the complete specification.
3. **Paper** from the same note plus the data the estate already records (tests, the four delivery keys, LESSONS.md, the
   friction meter), once filed or once the owner chooses to publish instead. Then the **episode** (build-in-public) from
   the paper's figures.

## Guard rails

- The owner's employment terms come first: read the IP-assignment and outside-work clauses, and get written approval for
  filing and publishing where the conduct rules ask for it. Never name the employer or use anything learned there.
- Nothing from `vault/`, no personal data and no regulator text in a paper or a filing.
- What is already public in this repository is prior art: it can be a paper, not an Indian patent.

## The loop (build-the-system)

- **Cue:** every new queue item a builder thinks is new gets `"ip": "candidate"`; the monthly review lists them.
- **Smallest step:** the twenty-minute note, before the first public commit of the mechanism.
- **Visible win:** `./securax ip` (slice 2) shows notes, filings, papers and episodes, and their dates.
- **Feedback:** one paper a quarter; a filing when a note qualifies.

## Paper candidates from work already public (papers, not Indian patents)

1. Gated delegation of software work to open models: gates, a stall watchdog that tells a hang from a long test run, and
   lessons that turn red builds green (data: the month's share of commits, red-to-green attempts, LESSONS.md).
2. Measuring user friction on the device, privately: abandoned sheets, repeated taps and tab bouncing (the friction meter).
3. A local-first personal estate for one person that grows to an organisation (the amoeba rail), with tested recovery.
4. An AI gateway's rails for Indian personal data (PII redaction, residency routing, the tamper-evident audit chain under
   concurrent writers).

Venues to weigh per paper: arXiv (cs.SE, cs.CR, cs.HC), IEEE and ACM conferences and workshops, and Indian security forums.

## Slices

1. This spec, the template, the queue item and the rule in AGENTS.md (done 2026-11-18).
2. `./securax ip`: lists queue items marked `"ip": "candidate"` and the private notes in `vault/ip/` (names and dates only).
3. A fitness check: a queue item marked candidate has a decision (file, publish, know-how) and a date before it closes.
