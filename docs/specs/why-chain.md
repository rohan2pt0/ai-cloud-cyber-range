# Spec: why-chain

Queue item `why-chain` in `governance/queue.json` · due 2026-12-15 · added 2026-11-17.

**The ask:** TELOS chains Problems → Mission → Goals → Projects, so no work goes on without a reason. We want the same, gently.

## Outcome for the person

They can see in one glance why each goal matters. Busywork with no reason behind it is folded away.

## Data

One `mission` line in the profile. It is a fixed fact, asked once (`ask-by-frequency`). The OKRs already carry a `why`.

## Screen (one action)

The mission line sits above the OKRs. Goals with no why are folded under "No reason yet (n)", with one tap to add one or let the goal go. There is no guilt and no red.

## Test that proves it

A jsdom test: the mission shows above the OKRs, and a goal without a why is folded. As a guest, an example mission that the person can correct.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one person's mission and goals.
- **Enterprise, when conditions call for it:** a company's mission → objectives → team OKRs, each traced up (the corporate TELOS).
