# 107 · The conglomerate playbook: built to survive, not to bet

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Ten mechanisms from Berkshire, Constellation, Danaher, Amazon, Jio, Tata, Microsoft, Alphabet, Haier and Tencent, mapped to SecuRAX. Built: every product is a core line or a bet with a dated stop test, enforced by CI; the operating system, dual use, free core and trust rules. Next: per-product revenue in venture, the estate bundle, a partner programme. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** use the success strategies of the world's biggest conglomerates to make the SecuRAX business model impossible to
fail.

**The honest answer first:** no business model is impossible to fail, and none of these companies claims one is. What they share
is narrower and more useful. They make failure **small** (one unit fails, the group does not), **uncorrelated** (units do not
fail for the same reason at the same time) and **fast to cut** (a dated test decides, not hope). They also keep the cost of being
wrong low enough to survive many tries. This doc applies those mechanisms to SecuRAX, says what is already built, and says
what each one asks of the owner.

## 1. The ten mechanisms, and how SecuRAX uses each

| # | Who | The mechanism (evidence) | In SecuRAX | State |
|---|---|---|---|---|
| 1 | **Berkshire Hathaway** | Decentralised operations, central capital allocation; never risk what you have for what you do not need | Each product runs on its own (its own page, price and stop test); the owner decides only where time and money go. Fixed costs stay tiny (the venture model's example is ₹3,000 a month), with no debt and no hire before revenue | ✅ the venture model; the rule is the owner's |
| 2 | **Constellation Software** | Many small, niche vertical businesses, each judged against a return hurdle before money goes in; capital follows the returns | Eight products, each a small vertical line. Each carries a dated **stop-or-change test** (`kill_if` in `products.json`; CI refuses a product without a dated one) | ✅ built in this change |
| 3 | **Danaher (DBS)** | One operating system, kaizen, applied to every business, old and acquired | The SecuRAX way of working applies to every product: tests behind every claim, status lights, lessons from every failure, fitness checks, the sandbox. A new product inherits it on day one | ✅ built (docs 33, 55, LESSONS.md) |
| 4 | **Amazon** | Sell what you built for yourself (AWS began as internal infrastructure); a flywheel where each turn makes the next one easier | Dual use (doc 96): every tool built for the owner is a product. Flywheel: the free Community edition brings users, users bring regulations and gaps, maps and fixes make it better, and a better product brings more users | ✅ dual use; the flywheel needs users |
| 5 | **Reliance Jio** | Win the base with a near-free entry, then raise prices once people depend on you (free launch; 330 million+ subscribers by 2019; prices raised in 2024) | Community is free for ever; the free AI-risk check and the readiness demo cost nothing; prices are set after a 90-day pilot. **Not copied:** Jio's loss-leading needed enormous capital. SecuRAX gives away software that costs it almost nothing to serve, never service hours | ✅ |
| 6 | **Tata Group** | Trust as the brand, held for the long term (charitable trusts own most of Tata Sons) | In security, trust *is* the product: open source, offline, a public "what we do not claim" page, no claim without a test, and no fake customers or numbers anywhere | ✅ built; the brand is earned with references |
| 7 | **Microsoft** | Bundle into what customers already own; the bundle beats the point product | The whole estate as one bundle (Shield + Readiness + Respond); connectors into tools buyers already run (Microsoft Sentinel, Splunk, ticketing) | 🟡 the bundle is priced per deal; connectors are P3 in doc 106 |
| 8 | **Alphabet** | A core business that pays, and "Other Bets" with their own accountability | Each product is a **core** line (Shield, Readiness, Recipes, Respond) or a **bet** (CISO OS, Cyber Range, Quantum-safe, Personal). Bets get a stop date; the core funds them | ✅ `role` in `products.json` |
| 9 | **Haier (Rendanheyi)** | Many small, self-managed units, each with its own customers and its own P&L | Each product line to be judged on its own revenue and time, not the estate's total | ⬜ next: per-product totals in `./securax venture` (section 4) |
| 10 | **Tencent** | An ecosystem: partners distribute and build on the platform | Auditors and consultants resell Readiness to many clients; plugins and maps can come from others (vetted by `./securax vet`) | 🟡 the auditor edition exists; partners next |

## 2. The failure modes, and the guard for each

A pre-mortem: assume SecuRAX failed by 2028, and ask why.

| How it could fail | The guard | Where |
|---|---|---|
| Nobody buys | A dated stop test per product; the 30-day discovery across segments; follow the pull | `products.json` `kill_if`; doc 106 section 8 |
| One product fails and drags the rest | Eight lines for different buyers, B2B and personal; no product above half of revenue (owner's rule, checked once revenue is logged per product) | Section 1, rows 2 and 9 |
| The founder burns out, or the day job conflicts | The estate does the remembering (Life OS, backlog, autopilot); the employment and conflict-of-interest position is settled before the first paid pilot | doc 106 P0; queue `employment-position` |
| A big vendor gives the same thing away (Microsoft, Palo Alto, Check Point) | Compete where they are thin: India depth (RBI chapters, SEBI categories, Aadhaar/PAN rails), offline use, open code that buyers can escrow | doc 106 section 2 |
| A regulator changes the rules | Maps carry a source date; `regwatch` fetches new RBI and SEBI circulars; one engine serves every map | `./securax comply`, `regwatch` |
| An AI provider raises prices or goes down | The model ladder always ends on a local model; per-user allowances cap spending | Shield, doc 25 |
| A security flaw in SecuRAX itself | Every claim tested; supply-chain checks; signed releases; a disclosure policy | SECURITY.md, docs 31, 87 |
| Cash runs out | Fixed costs near zero; no debt; no hire before revenue covers it; the venture model shows break-even and payback | `./securax venture` |
| The code is lost, or the account is | Mirrors, backups, restore drills | docs 74, 88 |

## 3. The rules, short enough to remember

1. **No product without a dated stop test.** CI enforces it.
2. **No spend that one bad month cannot absorb.** No debt, no hire before revenue.
3. **Give away what costs nothing to serve; charge for what saves a person time.**
4. **No claim without a test.** Trust is the brand.
5. **Every failure leaves a lesson, a test and a drill** (antifragility: the north star in AGENTS.md).
6. **Core lines pay for the bets; a bet that misses its date is folded or stopped.**
7. **Sell through people who already serve many buyers** (auditors, consultants).

## 4. Next, with dates

| Step | By |
|---|---|
| Per-product revenue and time in `./securax venture` (the Haier row), with the "no product above half" check | 2026-11-30 |
| The estate bundle as one priced offer once two core lines have paying customers | after the first two paid customers |
| A partner programme for auditors and consultants (terms, a sample engagement) | 2026-12-15 |

## 5. Sources

Read on 2026-10-22; most are secondary write-ups, so treat the details as indicative:
- Constellation Software's decentralised model and hurdle rates: [Morningstar](https://www.morningstar.com/stocks/xtse/csu/quote), [Fool.ca](https://fool.ca/2021/07/17/top-tsx-tech-stock-to-load-up-on-right-now), [Margin Valley](https://marginvalley.substack.com/p/constellation-software-csu-deep-dive)
- The Danaher Business System: [Danaher](https://danaher.com/kaizen-unlocks-operational-excellence-danaher), [Kaizen Institute](https://kaizen.com/insights/article-danaher-corporation-uk/)
- Reliance Jio's pricing and growth: [Inc42](https://inc42.com/?p=467531), [Tech Insider](https://tech-insider.org/?p=36543)
- Berkshire Hathaway's model: [Think Insights](https://thinkinsights.net/strategy/berkshire-hathaway-business-model)
