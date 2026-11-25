# Horizon watch: be ready for the big waves (plan, 2026-11-25)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** A plan, not a build (2026-11-25): six global waves checked against the person's own numbers, each with its fixes; a feed from reputable forums; forecast practice. Each slice turns the light. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask (owner, 2026-11-25, paraphrased):** global shifts such as those in the World Economic Forum's outlooks reach every
household. SecuRAX should keep watching what reputable forums report, think about it the way a top civil servant would, and turn it
into a few steps that leave the person ready and safe. The Life OS should get a little better at this every week.

## 1. What gets better for the person (north star)

1. **This week:** one card shows how ready they are for six big waves, from their own numbers, and the one step that helps most.
2. **Where they see it:** the Life OS Today screen (one line) and a Horizon card on the Money and Risk tabs; a monthly phone message.
3. **How it grows use:** each wave's step opens a screen that already exists (Money health, Risk drills, Career compass).

## 2. What already exists (diagnose before building)

| Part | Where | Reuse for |
|---|---|---|
| News to drills, safe by design (titles and links only, news ranks but never writes a drill) | `intel/threatwatch.py`, `intel/threat-feeds.json` | the feed in slice 2 |
| Every issue shows its 2-3 best fixes, from the person's own numbers | `REMEDIES`, `gmRemedies` in `guiding-map/ops.js` | each wave's steps |
| Money health facts, asked once | `gm_mhealth`, the money model | the readiness check |
| One idea a week, aimed at a weak spot | `governance/insight.py` | the weekly brief in slice 4 |
| One lever a week | `improve` | the self-improving loop |
| Consensus vs edge, pre-mortem | `intel/global_intel.py` | the forecasting practice |

Nothing new is needed for identity, storage or the look. The new parts are one registry and one card.

## 3. What the research says (cited by reference, paraphrased)

- **WEF Global Risks Report 2026 (January 2026).** Over two years, the top risks are geo-economic confrontation, conflict between
  states, extreme weather, a divided society, and false information. An economic downturn and inflation each rose eight places.
  Over ten years, extreme weather and nature loss lead, and the risk from AI rises fastest of all 33 risks.
- **Forecasting can be trained.** In the Good Judgment Project (Tetlock and colleagues, IARPA tournament 2011-2015), less than an
  hour of training improved accuracy (Brier score) by about 6-11%. Practice, frequent small updates and starting from a base rate
  ("how often does this usually happen?") helped most. So the habit we build is: make a forecast, update it, and score it.
- **The civil-service lens.** Top UPSC answers follow one shape: the causes, the effects across every side of life (political,
  economic, social, technology, environment, legal), the people affected, then "the way forward". Each wave card uses that shape,
  with the way forward made personal.

We could not find a WEF report called "Strategic Outlook 2027". The registry cites the reports we could check, and it carries a
`reviewed` date so a newer report replaces a claim, never sits beside it.

## 4. The design (80/20)

**Code decides; AI only proposes.** The waves, the checks and the steps are curated data plus pure code. A feed can raise a wave's
heat, but it can never change a step. No AI touches the person's numbers.

### The six waves (slice 1)

| Wave | What it does to a household | Checked against their own numbers | Steps (existing fixes) |
|---|---|---|---|
| Slowdown and job loss | income stops for months | months of spending in cash | `cash-idle`, `debt-costly` |
| Prices and interest rates | savings lose value, loans cost more | mix vs target, costly or floating debt | `alloc-drift`, `debt-costly`, `fund-regular` |
| Trade fights and supply shocks | prices jump, one market falls | a mix spread across asset types | `alloc-drift` |
| Fraud and false information | a scam empties an account | threat drills done this quarter | Risk tab drill of the month |
| AI changes work | a role shrinks or changes | a learning goal in the Career compass | one learning OKR |
| Extreme weather and health | a hospital bill or a damaged home | health cover vs floor, life cover gap | `health-below-floor`, `life-cover-gap` |

Each wave shows: ready, partly ready, or not ready yet; why, in one line; then its 2-3 steps through `gmRemedies`. As a guest it
shows example numbers that the person corrects. Plain words first; "Why this wave" folds open the source, the six sides and the
causes for anyone who wants to dig deeper.

## 5. Slices

| Slice | What | Tier |
|---|---|---|
| 1 | `intel/waves.json` registry plus the Horizon card (readiness from own numbers, steps via REMEDIES), one test | opencode |
| 2 | Weekly feed: titles and links from WEF, IMF, RBI, World Bank, OECD, CERT-In, on the threatwatch engine; heat per wave | opencode |
| 3 | Forecast practice: one question a month, a probability, scored by Brier when it resolves; a calibration line | opencode |
| 4 | Self-improving loop: the weakest wave feeds `improve` and `insight`; a quarterly wave review in `CALENDAR` | local |
| 5 | Local model (on the device) drafts the "why" for a new headline; the rejection pipeline checks it before it shows | strong |

What waits, and why: country-specific shocks beyond India and a shared community view wait until slice 2 has run for a month
(target 2027-01-31).

## 6. Proof

- Slice 1: a jsdom test fills a guest profile, checks each wave's verdict against hand-worked numbers, and checks each step comes
  from `REMEDIES`.
- Later: `progress` counts waves moved from "not ready" to "ready" each month; that is the outcome, not page views.

## 7. Ethics and safety

Calm, never alarming: no countdowns, no fear words, the floor step is enough. Sources are named, never copied. The feed is
titles and links only, and nothing personal leaves the device.
