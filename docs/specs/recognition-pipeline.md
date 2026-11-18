# Spec: recognition-pipeline — fellowships, awards, papers and a book, on purpose, from one body of work

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** Spec and queue item; the content file and the Career card are next. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Queue item `recognition-pipeline` · owner 2026-11-18: "propel my career with fellowships and similar accolades, and a
book, in parallel; the rest of my career should be the best of it, not by accident but by targeted, genuine effort, 80/20."

## The idea in one line

One theme, one flagship body of work, many outputs: the same work becomes the paper, the talk, the book chapter, the
episode and the evidence an application or a nomination asks for. No separate effort per accolade.

## The loop (build-the-system)

- **Cue:** a calendar of windows (each fellowship's and award's usual opening and closing months, `where`-tagged), each
  with a dated "start the evidence" step eight weeks before it opens. Dates come through `gmCalendarDated`.
- **Smallest step:** a weekly 90-minute flagship block (write, measure, or record), plus one monthly visibility act
  (a talk, an article, a panel, a mentoring session).
- **Visible win:** an evidence ledger on the Career tab: papers, talks, articles, chapters, citations, references secured.
- **Feedback:** after each outcome (selected, reserve, rejected), a two-line lesson: what the panel likely weighed, what
  evidence was missing. It drives the next cycle's first step.

## What the Career tab shows (one open action)

1. The next window that matters and its one next step ("Ask a senior referee", "Publish the paper", "Draft essay 1").
2. The evidence ledger, counted.
3. "Later (n)": every other window, folded.

## Content (generic, in the product; personal facts stay on the device)

Opportunity types with their usual cycle, eligibility shape and evidence they weigh: government-funded fellowships for
mid-career professionals (UK, US, Germany, others), leadership fellowships by nomination, national and professional-body
awards, conference talks, peer-reviewed papers, a book. Each is checked against its official page before a date is shown;
a date not yet announced reads "usually opens in <month>; check the official page".

## Slices

1. This spec and the queue item (2026-11-18).
2. The content file (opportunities with cycles, evidence and official links), verified, `where`-tagged.
3. The Career card: next window, one step, the evidence ledger (test-first, open models).
4. The outcome lesson after each result, feeding the next cycle.
