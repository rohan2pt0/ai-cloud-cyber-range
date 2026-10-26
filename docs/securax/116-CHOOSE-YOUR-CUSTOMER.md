# Choose who you serve: the customer is a decision, not an accident

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and propagating: choose-your-customer is a core principle in governance/principles.json, so every app from the OS kit and every future product carries it (os check and kit1.js enforce that the core principles reach each app). This playbook is the rubric — the Price Club / Costco lesson read correctly (serve one chosen customer completely; honest self-selection, not a dark pattern; the free safety core stays free), the barbell margin model, the market-sequencing score, the ICP template and the reusable prompt-engineered directive. A fitness/suite guard that makes every product declare its chosen customer and self-selection mechanic is queued (icp-declared). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Most products drift into their customer base. The best ones **choose** it, on purpose, and build a mechanism that keeps
the wrong fit away. This is now a **core principle** (`governance/principles.json`: `choose-your-customer`), so every app
built from the OS kit — and every digital product you build on the estate from here on — carries it automatically.

## The lesson, read correctly

Sol Price built Price Club in a San Diego hangar, then *fixed the model*: a membership fee at the door. Warren Buffett
put it in one picture — Price "figured out the customer he didn't want, and set up a system that would keep that customer
away." The fee killed the drop-in, one-item shopper (the business that belonged to the 7-Eleven) and kept the steady
member with the full basket. Jim Sinegal carried it into Costco; **about nine in ten members renew every year.**

The shallow read is "repel customers to make money." The real lesson, and the one that fits this estate's north star
(*the person using it is visibly better off*), is deeper:

> **Serve one clearly-chosen customer completely, instead of everyone shallowly.** The fee is not cruelty; it is a
> *self-selection mechanic* that aligns the business with the customer it serves best — which is exactly why they renew.

Two guardrails make this safe to hold forever, and they are written into the principle itself:

1. **The free safety core stays free for everyone.** Choosing a paying customer governs the *premium* design and pricing,
   never a locked door in front of what a person needs to be safe (SSO and export included; `LICENSING.md`).
2. **The mechanic is honest friction** — a fair price, a genuine fit signal — **never a dark pattern or a denial of
   safety.** We repel the wrong *fit*, not the person in need.

## The default DNA: a barbell

Every product chooses one of three margin shapes; the estate's default, unless a product has a clear reason otherwise,
is the **barbell**:

- **The heavy end — a chosen few, high margin.** UHNW / HNI individuals, family offices, and enterprises buying
  assurance, concierge and white-glove outcomes. Few customers, high price, deep service. This end **funds and de-risks**
  everything else.
- **The light end — the many, low friction, tiny margin.** Self-serve, low price, huge volume — the Jio lesson: a small
  amount from a vast population aggregates to a large number, and the low price is itself the moat. Only works when the
  **cost to serve one more is near zero** (which a well-built digital product on this estate is).
- **The bar between them** is the estate itself: *built for one, ready for many* (doc 97). The same code serves the
  single premium client and the millionth free user, so the premium margin subsidizes the reach instead of fighting it.

Each end needs **its own self-selection mechanic** — the premium end selects by a qualification and a price that signals
seriousness; the mass end selects by a frictionless tiny-price (or free-with-a-fair-upgrade) door that the wrong fit
simply won't bother to misuse.

## Who to serve, in order (the sequencing rubric)

When a new product chooses its first market, rank candidate segments and geographies by a single score — **take the
highest first**:

```
priority  =  ability_to_pay  ×  margin_per_customer  ×  renewal_or_repeat
             ──────────────────────────────────────────────────────────
             cost_to_serve  ×  friction_to_land  ×  time_to_first_rupee
```

In plain words: **go first where people can and will pay the most, for the least cost, friction, time and marketing to
win and keep them.** Concretely, that usually means:

- **By ability to pay:** price to the value delivered and the local purchasing power, not one global number — the same
  product can be premium in one market and mass in another (purchasing-power-adjusted pricing).
- **By cost and friction to serve:** favour markets with low regulatory drag for *this* product, a language and channel
  you already have, and payment rails that already work. For a BFSI-grade product, "friction" includes the compliance
  and residency burden — sequence so the first market is the one where that burden is lowest for the value won.
- **By time to first rupee:** prefer the segment that pays soonest; early margin funds the slower, bigger segments.

Do **not** start in the hardest, lowest-margin, highest-friction market because it is the biggest. Start where you win
fastest and cheapest, prove the model, then descend the ranked list.

## The ICP template every product fills

Before a line of a new product is built, answer these — it is the 20% of thinking that saves 80% of the wasted build:

1. **The one best-fit customer**, named concretely (not "SMEs" — "a 2–10 person BFSI compliance team at an Indian NBFC").
2. **The customer we deliberately do *not* serve**, and why serving them would dilute the fit.
3. **The self-selection mechanic** at the door — the honest friction (price, qualification, fit signal) that attracts
   the first and turns away the second.
4. **The margin shape** — premium, mass, or barbell — and, for a barbell, what the heavy end funds.
5. **The first market**, chosen by the sequencing score above, with the next two named.
6. **The free safety floor** this product still gives everyone, so the principle's guardrail holds.

## The reusable directive (prompt-engineered)

This is the mantra compressed into an instruction the estate — and any AI model building on it (`autobuild`, the open
models, a future me) — applies to **every** product decision. It is deliberately a prompt, so it steers generation, not
just documentation:

> **When designing or changing any product, first choose the customer, then build the door.**
> 1. Name the *one* best-fit customer and the one you will *repel*; if you cannot name both, you have not chosen.
> 2. Give the right fit an honest self-selection mechanic (fair price / fit signal) and the wrong fit a reason to leave —
>    never a dark pattern, never a locked safety floor.
> 3. Default to a **barbell**: high margin from a chosen few funds low-friction reach to many; keep cost-to-serve near
>    zero so the light end is profitable.
> 4. Sequence markets by `(ability_to_pay × margin × repeat) ÷ (cost_to_serve × friction × time)` — win fastest and
>    cheapest first, then descend.
> 5. Apply 80/20: ship the smallest thing that fully serves the chosen customer; cut everything the wrong fit would want.
> 6. State where the person is **visibly better off**, or it does not ship (the north star).

Hold this at the top of every product brief, every `./securax route` for a new product, and every autobuild spec.

## Where this came from

This principle was distilled, in our own words, from a shared account of Sol Price / Price Club and Costco and Buffett's
explanation of choosing the customer, plus your direction to target UHNW–HNI margins and Jio-style mass aggregation,
sequenced by who can pay most for the least friction. The source material stays private; only this paraphrased principle
and rubric are recorded.

## Where this is going

Today the principle propagates to every app and this playbook is the rubric. Queued in `governance/queue.json`
(`icp-declared`): a fitness/suite guard that makes every product in `governance/suite.json` **declare** its chosen
customer, its self-selection mechanic, its margin shape and its first market — so the mantra is not just written but
checked, and a product that skips the choice fails the gate. That turns "choose your customer" from advice into a
promise the architecture keeps.
