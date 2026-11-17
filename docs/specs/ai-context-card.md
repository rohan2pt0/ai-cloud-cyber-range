# Spec: ai-context-card

Queue item `ai-context-card` in `governance/queue.json` · due 2026-12-08 · added 2026-11-17.

**The ask:** LifeOS loads a "TELOS" context file into every AI session so that the AI knows who it is helping.
We want the same in one tap: a short brief built from what the Life OS already knows.

## Outcome for the person

The estate's AI answers as if it knows them: their mission, their goals this quarter, this week's lever. They stop
re-explaining themselves in every chat.

## Data

Nothing new is stored. The card is built when needed from the profile, the mission line (`why-chain`), the OKRs and the current lever.
It contains words only. Money figures, family names, dates of birth, account details and papers are left out unless the person ticks each one.

## Screen (one action)

On the Ask screen: "Let the AI know me" (one tap, sent to the estate's own gateway). A secondary "Copy as text" is folded away and marked as leaving the device.

## Threat model (lands as `lifeos-context` in `governance/threat-models.json` with the card's test)

Boundaries: the browser's storage for this app → the person's own estate gateway; the clipboard → any other app.

| Id | STRIDE | Threat | Answer |
|---|---|---|---|
| ctx-i1 | I | The brief reaches a cloud model and exposes the family's private life. | Sent only to the estate gateway, whose rails route anything marked private to a local model. No figures or names by default. |
| ctx-i2 | I | "Copy as text" leaves a readable profile on the clipboard, where other apps and keyboards can read it. | Folded, never the primary action. It says what leaves, and it is logged in "Who touched my data". |
| ctx-t1 | T | A planted profile field (synced or restored) carries a prompt injection into the AI ("ignore your rules…"). | Fields go in as quoted data under a fixed frame. Length is capped and markup is stripped at the profile's one door (test47). The gateway's rails still apply. |
| ctx-s1 | S | A page on another origin asks for the brief. | No API: the brief is built in the page and posted to the page's own estate origin only (test120 holds egress). |
| ctx-r1 | R | Nobody can tell later what the AI was told. | Each send is logged on the device and in the gateway's audit chain, with a hash of the brief. |
| ctx-d1 | D | A huge profile makes the brief too long for a small local model. | Capped at about 1,500 characters. The vital few go first. |
| ctx-e1 | E | The brief is treated by the agent as instructions with authority, such as "approve payments". | The gateway's human-in-command rule stands: context never grants a tool. |

## Test that proves it

A jsdom test: a guest sees no card; with a profile, the brief has the mission and goals and no rupee figure, no family name and no date of birth.
It posts only to the estate origin. A planted field arrives quoted.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** one person, built on the device, sent to their own gateway.
- **Enterprise, when conditions call for it:** an organisation's "telos" (mission, risk appetite, policies) as a governed context, versioned and approved,
  injected by the gateway per team (the shared platform's tenancy and policy).
