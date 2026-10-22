# 96 · One platform, many products: how the estate pays its way

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: ./securax venture computes break-even, payback and unit economics with your time counted, logs hours, spend and revenue privately, and writes a stress-test prompt. The strategy (one platform, many products, dual use, free to Pro to Concierge, stage gates) is written down; prices are hypotheses to test, and licence keys and payments wait, with dates. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

> **Prices for the business product are now set in [doc 106](106-WHO-SECURAX-IS-FOR.md)** (a hypothesis to test with design partners). The tables below are kept as history.

**The ask:** build once and sell many times, as the people who built Zomato's and Zepto's systems reused them for new businesses, and as reusable rockets and robots serve both Earth and Mars. Keep no single point of failure, as India is doing with payment rails beside SWIFT. Start free and open for common people, learn from their friction, then offer the matured product to people who pay a subscription. Make the whole thing self-funding, and prove it with break-even and payback, counting time as well as money.

**The answer:**
- **The platform:** the estate (kit, gateway, sync, govern, range, continuity).
- **The products:** editions on top of it, in three tiers.
- **The proof:** `./securax venture`, which tells you every month whether it is paying its way.

## 1. The patterns, and what we take from each

| Who | What they did | What we take |
|---|---|---|
| **Eternal (Zomato)** | Food delivery's customers, technology and last-mile network carried new businesses: Blinkit (quick commerce), District (going out) and Hyperpure (supplies for restaurants). [Overview](https://en.wikipedia.org/wiki/Eternal_Limited) · [network-effects analysis](https://digitalstrategy.rsm.nl/2025/09/17/from-food-delivery-to-quick-commerce-giant-zomatos-art-of-harnessing-network-effects/) | One user base, one kit and one sync carry every edition. The second app costs one JSON file. |
| **Snabbit** | Founded by a former Zepto chief of staff. It applies the quick-commerce operating playbook (micromarkets, density before expansion, a full-stack workforce) to 10-15 minute home services. [Profile](https://yourstory.com/2025/01/funding-quick-service-startup-snabbit-series-a) · [2026 round](https://india.entrepreneur.com/business-news/quick-home-services-startup-snabbit-raises-usd-56-mn-in-series-d-round) | One playbook (rhythm, registers, the next step, visible progress) applied to a new role. Depth before breadth: make one edition loved before the next. |
| **Dual use (reusable rockets, satellites, robots)** | Things built for paying customers on Earth now also become the parts of a future mission. Today's revenue funds tomorrow's bet. | Every estate part must earn on its own now, and serve the bigger product later (section 2). |
| **India's payment rails beside SWIFT** | UPI linked abroad (UPI–PayNow with Singapore), rupee trade settlement through Special Rupee Vostro Accounts, SFMS studied as a model for messaging, and e-rupee cross-border pilots. The RBI frames it as more options, not de-dollarisation. [UPI–PayNow and SRVA background](https://www.iibf.org.in/documents/VISION/2023/IIBF_Vision%20March%202023.pdf) · [e-rupee cross-border](https://cointelegraph.com/news/why-india-wants-the-e-rupee-to-move-beyond-borders) | A second rail you control. The estate runs on any one machine (doc 91), keeps a code mirror off GitHub (doc 74), and every app works offline with export. No customer is ever locked to one host, one cloud or one AI provider. |
| **Open core** | GitLab keeps most features free and earns almost all its revenue from paid tiers aimed at managers and executives. [GitLab pricing handbook](https://handbook.gitlab.com/handbook/company/pricing) | Free and open source for the person; paid tiers for the people who carry responsibility for others. |
| **Conglomerate habits, at small scale** | Shared services across businesses, a profitable unit funding the next bet, a holding structure that keeps one failure from sinking the rest | The shared services are the estate's core. The first paying tier funds the next edition. Each edition can be stopped without touching the others (section 6 has the gates). |

One habit we deliberately do **not** copy: lock-in. Export always works, and the data format is plain JSON. People stay because the product makes them better off (the north star in AGENTS.md), not because leaving is hard.

## 2. Dual use: every part earns twice

| Part of the estate | Use 1: for you, now | Use 2: in a product someone pays for |
|---|---|---|
| OS kit | The Life OS, free for everyone | Vantage for CISOs, and any new role app in one file |
| AI gateway with rails and audit | Safe AI for the estate's own users | A governed AI front door a regulated firm can buy |
| Estate sync | Your devices stay in step | The multi-device promise of every paid app |
| Govern catalog and templates | A CISO's own plan and Board report | A consulting deliverable produced in an afternoon |
| Cyber range | Your team's practice | Paid training and assessments |
| Continuity, ransomguard, restore drills | Your own data survives | Proof to an HNI or a small firm that theirs survives |
| Nodes on any machine | No single point of failure for you | A private node sold with the Concierge tier |

`./securax venture json` carries this table, so a dashboard can show it.

## 3. The ladder: free first, paid when it has earned it

| Tier | Who | What they get | Price (example, to test) |
|---|---|---|---|
| **Community** | Anyone: students, families, small teams | The free-to-use estate (FSL-1.1-MIT): Life OS, Vantage, Govern, the range, all core features, export always | Free |
| **Pro** | One professional: a CISO, a founder, a DPO | All editions kept current, sync hosted on an always-on node, updates and fixes first, playbook packs | Rs 999 a month |
| **Concierge** | HNIs, family offices, entrepreneurs, public figures | Set-up done for them, a private node, a human who reviews their risks monthly, an incident hotline, family devices covered | Rs 25,000 a month |

**Never behind a paywall:**
- security fixes;
- export of your own data;
- the core of every feature.

The paid tiers sell time, care and assurance, not hostages.

**Price reference:**
- Published listings put one global executive digital-protection service at about USD 3,000-7,000 a person a year, with family members extra ([listing](https://www.capterra.in/software/1028297/blackcloak)). That is roughly Rs 2.5-6 lakh a year, so the Concierge example sits inside the band.
- Free-to-paid conversion for open-source products is quoted anywhere from 0.5-3% ([benchmarks](https://www.getmonetizely.com/articles/whats-the-optimal-conversion-rate-from-free-to-paid-in-open-source-saas)). The example plan uses the low end.

Every price here is a hypothesis to test, not a decision.

## 4. The friction loop: common people make the product mature

1. **Free users use it.** Every friction they hit is a bug report in disguise.
2. **Friction becomes a lesson.** It goes into `./securax lessons add` and becomes a test and a fix (AGENTS.md section 5). The estate gets stronger from each problem: antifragility in practice.
3. **Fixes reach everyone,** free users included. That is how trust is earned.
4. **What people pay for shows itself.** Watch what free users ask a human to do for them (set-up, a review, a restore): that is the Concierge offer.

There is no tracking. Feedback is opt-in and goes to your own estate.

## 5. The money: break-even and payback, with your time counted

```bash
./securax venture                              # where you stand: invested, break-even, payback, what must be true
./securax venture log time 3 "built Vantage"   # hours, valued at your hour rate
./securax venture log money 1200 "VPS"         # spend
./securax venture log revenue 999 "first Pro"  # income
./securax venture plan hour_value=2000 tiers.pro.price=1499 tiers.pro.conv_pct=1.5
./securax venture ask                          # a prompt that makes an AI stress-test the plan
```

The formulas (MBA standard, kept explainable):

| Measure | Formula | Healthy |
|---|---|---|
| Contribution margin | price - cost to serve one user | positive, and well above zero |
| Break-even users | fixed costs a month / weighted contribution margin | small and reachable |
| Break-even with your time | (fixed costs + your hours × hour value) / margin | the real target |
| Lifetime value (LTV) | margin / monthly churn | at least 3× CAC ([benchmark](https://chargebee.com/resources/glossaries/ltv-cac-ratio)) |
| CAC payback | cost to win a customer / margin | under 12 months for small customers |
| Payback | the month your running total, starting from everything you put in (money + time), turns positive | as early as you can make it |

The example plan uses deliberately conservative numbers. It reaches cash break-even early, but it pays for your time only once enough people pay. `venture` says which number to move first. Usually that is churn or conversion, not more free users.

**Why time counts:** an hour spent on the estate is an hour not spent elsewhere (opportunity cost). Without it, a project can look profitable while quietly costing its builder a fortune.

## 6. Stage gates: small bets, clear exits

| Gate | By | Pass when | If it fails |
|---|---|---|---|
| 0. People use it | 2026-12-31 | 50 people use the Life OS or Vantage weekly; 10 interviews on what they would pay for | Fix the friction they name before building anything new |
| 1. It covers its costs | 2027-03-31 | 10 Pro subscribers pay the running costs | Re-price or re-package; do not add editions |
| 2. It pays for your time | 2027-09-30 | 3 Concierge clients, or Pro at break-even with time | Keep it as a free public good, and keep the skills and reputation it built |

These are proposals: change the numbers to fit your life. `venture` shows where you are against them every month.

## 7. India: what to get right before the first rupee

- **GST:** software and services carry 18%. Registration is needed once turnover crosses Rs 20 lakh a year for services (lower in some states). Confirm with your chartered accountant.
- **DPDP Act:** a paid service that holds clients' personal data has clear duties: consent, purpose limits, breach notice and a grievance contact. The estate's design helps (data on the device, a private node, export), but it does not replace a written privacy notice.
- **Licence and brand:** v0.3.0 and earlier are MIT, so anyone may use and even sell those; from v0.4.0 the code is FSL-1.1-MIT, which forbids competing resale for two years per release (LICENSING.md). The moat is the service, the trust and the brand, so register the name as a trademark before marketing it.
- **Employment terms:** if you are employed, check your contract and your employer's policy on outside business and conflict of interest before selling to anyone.

## 8. Prompt engineering, used where it pays

`./securax venture ask` writes a structured prompt:
- **Role:** a sceptical investor and an Indian chartered accountant.
- **Context:** your real numbers.
- **Task:** a pre-mortem; each assumption graded optimistic, fair or conservative; the three cheapest experiments; ways to break even sooner.
- **Constraints:** mark unknowns rather than invent them; say where each benchmark comes from.
- **Output:** a fixed format of at most 400 words.

The same rules keep the estate's own answers honest (doc 89). Paste the prompt into the estate's chat or any AI.

## 9. What waits

| Item | Target |
|---|---|
| Licence keys for the Pro tier, and a payment gateway chosen after comparing fees | 2027-01-31 |
| Hosted sync for Pro users on an always-on node, with per-user rows and limits | 2027-03-31 |
| The Concierge runbook: onboarding, monthly review, incident hotline | 2027-02-28 |
| An opt-in feedback form that goes to your estate | 2026-12-15 |

## 10. Proof

- **`governance/tests/test_venture.py`:**
  - The unit economics are right.
  - Logged time and money delay payback, and revenue brings it back.
  - A good plan breaks even.
  - A bad plan says why.
  - The plan is private (0600) and refuses unknown settings.
  - The stress-test prompt carries the numbers.
  - The report shows leverage and dual use.
- **`./securax os check`:** proves the "many products" half. Every edition builds from the same kit.
