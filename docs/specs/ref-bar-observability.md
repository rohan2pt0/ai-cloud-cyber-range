# Spec: ref-bar-observability

Queue item `ref-bar-observability` in `governance/queue.json` · due 2026-12-12 · added 2026-11-08.

**The ask, as the queue holds it:** One correlation id across gateway, sync and hub logs, with OpenTelemetry-shaped traces, so any failure is traced end to end

## Outcome for the person

Any failure can be followed from the edge to its cause with one id.

## Data

A request id added at the edge and passed through gateway, sync and hub logs.

## Screen (one action)

`./securax why <id>`: the path of that request.

## Test that proves it

A journey: one request, one id in all three logs; no personal content in traces.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** An id in logs.
- **Enterprise, when conditions call for it:** OpenTelemetry traces exported to an organisation's collector.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
