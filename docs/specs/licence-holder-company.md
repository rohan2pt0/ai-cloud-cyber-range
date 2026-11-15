# Spec: licence-holder-company

Queue item `licence-holder-company` in `governance/queue.json` · due 2027-01-31 · added 2026-10-22.

**The ask, as the queue holds it:** Once the company exists, assign the code and the marks to it in writing and change LICENSE's copyright line to the company

## Outcome for the person

Customers and investors deal with one clear owner of the code and the marks: the company.

## Data

A written assignment (private, with the lawyer) and the copyright line in LICENSE.

## Screen (one action)

Nothing for the person; LICENSE names the company.

## Test that proves it

The licence test expects the company's name once the assignment is signed; `./securax config check` stays green.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One assignment and one line changed.
- **Enterprise, when conditions call for it:** Rights held per entity and market, with contributor terms pointing to the company.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
