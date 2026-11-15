# Spec: landlord-desk

Queue item `landlord-desk` in `governance/queue.json` · due 2026-11-29 · added 2026-11-15.

**The ask, as the queue holds it:** Owner, 2026-11-15: managing let-out homes is hard: maintenance, property tax, misc charges, tracking whether tenants paid, electricity and other bills, agreement end, registration, police verification, repairs and leakages; do something simple

## Outcome for the person

A person who lets out a home knows, for each home, the one thing due next, and never misses rent, a renewal, registration or a tax date.

## Data

`guiding-map/levers/landlord.json` (duties, rules with sources, ready messages). Per home: rent amount and day, agreement end, a monthly tick list. Bounded to the homes in the profile and 24 months of ticks.

## Screen (one action)

On Property, per let-out home: `Next for this home` shows one duty with one button (`Mark rent received`, or `Send the reminder`, which opens the ready message). The rest folds under `Later (n)`.

## Test that proves it

A jsdom test: a home with an agreement ending in 50 days shows the renewal first; a tick moves to the next duty; the ready message carries no stored personal detail it was not given.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** One landlord, ticks by hand, rent matched from pasted bank messages.
- **Enterprise, when conditions call for it:** Many homes and co-owners: shared ledger, a manager role, tenant-facing receipts, with audit and export.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
