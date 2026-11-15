# Spec: icp-declared

Queue item `icp-declared` in `governance/queue.json` · due 2026-11-30 · added 2026-10-26.

**The ask, as the queue holds it:** Enforce the choose-your-customer principle (doc 116): a fitness/suite guard that makes every product in governance/suite.json declare its ideal customer (one named best-fit person), the customer it deliberately does not serve, its self-selection mechanic (honest friction, never a dark pattern), its margin shape …

## Outcome for the person

Each product is built and priced for one named kind of person, and says honestly who it is not for.

## Data

An `icp` block per paid component in `governance/suite.json` (for, not for, mechanic, margin, first market).

## Screen (one action)

`./securax suite check`: one line per product missing its customer.

## Test that proves it

A fitness check: a product with revenue intent and no `icp` fails; the free safety floor can never be gated.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A declared block and a check.
- **Enterprise, when conditions call for it:** The declaration drives edition packaging and the site's `Is this for you?` page.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
