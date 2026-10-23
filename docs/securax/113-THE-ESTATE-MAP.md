# The estate map: see the whole thing at once

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: ./securax map generates an interactive, self-contained HTML picture of the whole estate from features.json and governance/suite.json — 43 components coloured by area around the 16 shared platform services they use, with hover, click-for-detail, filter and search; works offline in light or dark. Tested by tools/tests/test_estate_map.py (every component a node, every 'uses' an edge, no external resource). A Command Center link and resilience/compliance overlays are queued. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

A long list of 43 components tells you what exists; it does not show you how the estate hangs together. `./securax map`
builds an **interactive picture** of the whole AI estate from its own declarations — no hand-drawn diagram that drifts out
of date, because it is generated from the same `features.json` and `governance/suite.json` that everything else reads.

## What it shows

- **Every component is a node**, coloured by what it is for (your own tools, keep it running, comply and govern, practise
  and defend, use AI safely).
- **Every shared platform service is a hub in the middle** — identity, audit, policy, residency, metering, tenancy, export
  and the rest (`governance/suite.json`).
- **An edge joins a component to each service it is built on.** A service with many spokes is load-bearing; a component
  with many edges leans on a lot of the platform. This is the "built for one, ready for many" story (doc 97) made visible:
  nothing builds a private copy of a platform service, and the map shows it.

Hover a node to light up what it touches, click it for the detail (what it does, the command to open it, the services it
uses, what its enterprise edition adds), filter by area, or search.

## Use it

```
./securax map                 build the map and say where to open it
./securax map OUT.html        write it somewhere of your choosing
```

It is **one self-contained HTML file** — the data is baked in at build time and there is no library, no network call and no
build step, so it opens on a phone or a laptop, online or off, and is safe to send to anyone. It reads as well in light mode
as in dark. The file is generated (git-ignored); re-run `./securax map` any time to refresh it.

## Where this is going

Next: a link from the Command Center so the map is one tap from the cockpit; a second view that overlays resilience (which
single machine carries which component) and the compliance maps (which control each component evidences); and the same
engine, pointed at a customer's estate, as a one-page assurance picture. Tracked in `governance/queue.json`.
