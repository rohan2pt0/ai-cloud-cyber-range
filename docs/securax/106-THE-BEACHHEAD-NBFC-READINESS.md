# 106 · The beachhead: NBFC cyber readiness

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Decided from an audit of the code and sourced market research: NBFCs under the RBI cyber directions 2026 first, IS auditors as the channel. Built and tested: ./securax readiness (by chapter, evidence and provenance, the vital few, recurring duties, board pack, auditor sheet) and the NBFC landing page. Not yet proven: that NBFCs or auditors will use or pay for it; the 30-day plan tests it. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** turn SecuRAX into a product that a security team understands, trusts, adopts, pays for and renews. Audit first,
pick one market, build the one workflow that matters there, and plan how to prove it with real customers.

**How this was decided:** an audit of the code, not the docs (2026-10-22), and market research with a source for every fact.
Anything not verified is marked as such. No customer, price or result below is invented. Where a number is a hypothesis, it says
so.

## 1. The audit, in short

**What SecuRAX is today:** a very broad estate built for one owner on one machine. It has:
- 39 features and about 110 commands;
- over 1,300 tests and 49 sandbox journeys;
- about 15 product names.

The engineering is unusually well proven. But most of its "security team" modules measure SecuRAX itself, not a customer:
- the regulatory maps;
- the cockpit;
- crown jewels and continuity;
- the board report.

**The five most serious obstacles to selling it**

| # | Obstacle | Impact | Fix effort |
|---|---|---|---|
| 1 | The compliance modules assess SecuRAX, not the customer. The RBI map shows 1 of 58 rows supported *by SecuRAX* | High | Medium (this change starts it) |
| 2 | No enterprise plumbing: tenancy, licensing, an admin console, SCIM; gateway sign-in is off by default on a laptop | High for enterprises, low for the beachhead | High |
| 3 | No connectors to customer tools (SIEM, ticketing, scanners) | High for a SOC product, low for readiness | High |
| 4 | Too many names, three price tables that disagree (docs 09, 96, 97), personal tools next to business ones | Medium: confuses buyers | Low |
| 5 | Looks like a one-person project: a public repo under a personal name, v0.2.0, no references | High for regulated buyers | Partners and time |

**The five strongest assets**

| # | Asset | Why it matters |
|---|---|---|
| 1 | The paragraph-level map of the RBI NBFC cyber directions 2026, with chapter applicability | The core of the beachhead product; few tools have it |
| 2 | The regulator incident clock (RBI, SEBI, CERT-In, DPDP, IRDAI as data) | The six-hour duty, with drafts and a tamper-evident log |
| 3 | Proof-native engineering: every claim tied to a test | Matches what an auditor wants to see |
| 4 | Runs offline, open source (MIT) | Fits the Directions' vendor clauses: right to audit, source code available |
| 5 | The India-aware AI gateway | A second product for when NBFCs adopt AI (RBI FREE-AI) |

**Fixed in this change:** a public repository must carry no employer or role hints. Several files still referred to the job
descriptions they were first built against. Those references are removed.

## 2. The decision

### Segments compared

Scores are 1 to 5; higher is better for us. "Reach" is how easy decision-makers are to reach.

| Segment | Urgency | Budget | Reach | Competition (5 = little) | Sales cycle | Support load | Expansion | Total |
|---|---|---|---|---|---|---|---|---|
| **NBFCs under the 2026 directions** (Chapters IV and V) | 5 | 3 | 3 | 4 | 3 | 4 | 4 | **26** |
| **IS auditors and consultants** serving NBFCs and SEBI entities (channel) | 4 | 3 | 4 | 4 | 4 | 4 | 4 | **27** |
| SEBI CSCRF entities (brokers, DPs) | 4 | 2 | 3 | 2 | 4 | 4 | 3 | 22 |
| Indian MSSPs | 3 | 3 | 3 | 2 | 3 | 2 | 4 | 20 |
| Mid-market enterprises, general | 2 | 3 | 2 | 1 | 2 | 2 | 3 | 15 |
| Large enterprises with many tools | 3 | 5 | 1 | 1 | 1 | 1 | 5 | 17 |

**Choice:** NBFCs under the 2026 directions are the customer. IS auditors and consultants are the first channel, because one
auditor serves many entities.

**Why:**
- **The trigger is real and dated.** RBI's NBFC cyber directions took effect on 31 July 2026, with no transition period. They
  repealed the 2023 IT governance direction.
- **The duties recur.** Vulnerability assessment every six months, penetration testing every year, an annual IS audit and IT
  risk assessment, a six-hour incident report, and a quarterly CISO review with the Board for the middle layer.
- **The segment is reachable.** There are 493 middle-layer NBFCs (RBI, FY25). The count of base-layer NBFCs at ₹500 crore and
  above is **unverified**.
- **The alternatives are weak.** The packaged compliance offers found are SEBI-focused. No mapping for the 2026 NBFC directions
  was found in the global GRC tools (inference, to be checked in discovery).

**Explicit assumptions, each to be tested (section 7):**
1. An NBFC compliance or IT head will run a self-assessment tool, not only hire a consultant.
2. Auditors will use it in their engagements.
3. A yearly price per entity in the range below is acceptable.

**First, not only.** The beachhead says where selling starts, not who may use SecuRAX:
- **Anyone can use it.** The readiness engine runs on every regulation SecuRAX maps: `--map rbi|cscrf|caf|nist-ai-600-1|mit-ai-risk|pqc`, with SEBI's categories and RBI's chapters. The open-source edition is free for anyone.
- **Why one segment first:** a founder with limited hours can run discovery, pilots and support for only one buyer at a time.
  - One sharp message ("the RBI Directions, for your chapter") converts better than "compliance for everyone".
  - Proof from one segment (a pilot, a reference, an auditor who uses it) is what opens the next one.
  - Broad positioning means competing with every GRC vendor at once.
- **The order after NBFCs:**
  1. SEBI entities through the same auditors (CSCRF readiness, P2).
  2. Then any DPDP-bound firm (DPDP core obligations apply from 13 May 2027).
  3. Then AI governance for all of them (Shield and the AI maps).

  Each step reuses the engine; only the map and the message change.

**Not chosen, and why:**
- **An AI SOC copilot.** It is crowded (Microsoft, Google, CrowdStrike and well-funded startups), and it needs SIEM data
  SecuRAX cannot reach yet.
- **A standalone AI firewall.** It is being consolidated by the large vendors (Palo Alto bought Protect AI; Check Point is
  buying Lakera). Doc 62 already judged it "a feature, not a company".
- **The same pitch to SEBI's small brokers.** The exchanges' Market SOC and packages from ₹50,000 compress the price.

### The customer, and the offer

| | |
|---|---|
| **Ideal customer** | An NBFC in the base layer at ₹500 crore and above, or in the middle layer; a small IT and security team (often one CISO or IT head plus vendors); an IS audit due in the next six months |
| **Economic buyer** | The CISO or CRO (middle layer); the Head of IT or Compliance (base layer) |
| **Daily user** | The CISO or IT head, and the compliance officer; the external IS auditor |
| **Purchase trigger** | The Directions in force; an IS audit or RBI inspection coming; a Board asking "where do we stand?" |
| **What they use today** | A consultant's spreadsheet, and email |
| **Main objection** | "You are small and new; can we rely on you?" Answer: open code they can inspect and escrow, offline use (no data leaves), an auditor partner, and a free 90-day pilot |
| **Value they can measure** | Time to a board-ready view of where they stand; how many gaps have an owner and a date; recurring duties with no missed date |

### Positioning

- **Statement:** for NBFCs under RBI's 2026 cyber directions, SecuRAX Readiness shows where you stand, paragraph by paragraph
  for your layer, with the evidence, owner and date for every item. It runs on your machine and is open source, so your
  auditor can test the tool as well as the results.
- **Headline:** "Know where your NBFC stands. Show your Board the proof."
- **The problem it solves:** the Directions apply now and recur. Today the answer to "where do we stand?" lives in a
  consultant's spreadsheet that is out of date the week after it is delivered.
- **Three value propositions:**
  1. Only your chapter's requirements, each with evidence and provenance.
  2. The recurring duties tracked, so a VA, PT, audit or Board review never slips.
  3. A board pack and an auditor's sheet in one command, kept on your own machine.
- **Three use cases:**
  1. A first assessment before the IS audit.
  2. The quarterly CISO-to-Board review.
  3. An auditor running the same assessment across five clients.
- **Why it is different:**
  - paragraph-level, chapter-aware and India-specific;
  - offline and open source, which fits the Directions' own vendor clauses (right to audit, source-code escrow);
  - an "unknown is never met" rule, enforced in code.
- **How a buyer verifies it:**
  - the sample board pack;
  - their own first assessment in the free pilot;
  - the tests in this repository;
  - their auditor reading the CSV.
- **"Why not our existing tools?":** the general GRC tools and the SEBI-focused packages found do not map the 2026 NBFC
  directions by chapter (to be verified per tool). A consultant's spreadsheet has no recurring-duty dates and no provenance.
  SecuRAX Readiness does not replace the consultant; it makes the consultant's work last.

## 3. The business model (a hypothesis)

This section replaces the three earlier price tables (docs 09, 96 and 97) for the business product. Those stay as history.

| Edition | Who | Price (hypothesis, to test in section 7) |
|---|---|---|
| Community | anyone | free, open source, self-hosted, readiness included |
| Readiness | one NBFC | **₹1.5 lakh a year**, anchored between the ₹50,000–2 lakh packaged compliance offers and ₹6–40 lakh consulting engagements found in research |
| Auditor | an audit firm or consultancy | **₹40,000 a year per client, five clients minimum** |
| Shield | an NBFC adopting AI | add-on, priced later (doc 62) |

**Cost to serve:**
- Readiness runs on the customer's machine and uses no AI model, so infrastructure and inference cost is near zero.
- The real costs are onboarding (a first session together), upkeep of the map when RBI changes the text, and support.
- Gross margin is therefore high once onboarding is short. The risk is founder time, not cloud bills.
- There is no unlimited AI anywhere in this offer.

**Twelve months after the first paid customer** (hypotheses, not forecasts):

| | NBFCs | Audit firms (5 clients each) | Yearly revenue |
|---|---|---|---|
| Conservative | 3 | 1 | ₹6.5 lakh |
| Base | 10 | 3 | ₹21 lakh |
| Optimistic | 25 | 6 | ₹49.5 lakh |

- **The minimum paid offer:** one NBFC, one chapter, the board pack, the recurring duties, and support.
- **The upgrade path:**
  1. evidence attachments and a second-person sign-off;
  2. CSCRF and other directions;
  3. Shield when the NBFC adopts AI.

## 4. The plan, ranked

Scores use the weights customer value 25%, commercial 25%, differentiation 15%, feasibility 15%, retention 10% and risk
reduction 10%. A security failure blocks an item whatever its score.

| Pri | Item | Score | Effort | Acceptance |
|---|---|---|---|---|
| **P0** | Remove employer and role hints from the public repo | gate | S | Done: no job-description references remain |
| **P0** | One price table for the business product | gate | S | Done: this doc; 09, 96 and 97 point here |
| **P0** | Decide the legal and employment position before any paid pilot (owner) | gate | — | Written yes from the owner, in private |
| **P1** | Readiness: customer-side assessment of the 2026 directions, by chapter | 4.5 | M | **Done**: `./securax readiness`, 7 tests, board pack checked at desktop and phone width |
| **P1** | The landing page for NBFCs and auditors, with a sample board pack | 4.2 | S | **Done**: `website/nbfc/`; homepage banner links to it |
| **P1** | A browser screen for marking (most buyers will not use a terminal) | 4.4 | M | A CISO marks 10 items in the browser in under 10 minutes; same files as the CLI |
| **P1** | Evidence attachments and a second-person sign-off | 4.0 | M | Each mark can hold files (hashed); a "met" can require a checker |
| **P1** | Import a consultant's workbook (they already have one) | 3.9 | M | A gap-assessment xlsx fills the marks, row by row, with a report of what did not match |
| **P2** | CSCRF readiness on the same engine | 3.6 | M | Same commands for SEBI entities, by category |
| **P2** | Multi-client view for auditors (one page, all clients) | 3.5 | S | `readiness list` as a page |
| **P2** | A trust page and a security questionnaire pack | 3.4 | S | Answers grounded in tests; nothing claimed without evidence |
| **P2** | One product name per buyer; retire names a buyer never sees | 3.2 | S | The site and docs use Readiness, Shield and Community only |
| **P3** | The SOC and AI-SOC roadmap (SIEM connectors) | 2.6 | L | After the beachhead pays |

## 5. What was built in this change

- **`./securax readiness`** (`governance/readiness.py`):
  - one NBFC's own assessment, by chapter, from the existing paragraph map;
  - marks with evidence and provenance; a "met" without evidence is refused;
  - the vital few, the recurring duties, a board pack (HTML, prints to PDF) and an auditor's sheet (CSV);
  - a sample that runs in seconds (`readiness demo`);
  - private by design: files are readable by you only and never committed.
- **The landing page** `website/nbfc/` and a sample board pack made from fake data.
- **Clean-up:** job-description references removed; CI moved to Node 22; the Dependabot round recorded in the queue.

**Verified:**
- the readiness tests (7);
- the full test suite;
- the board pack and the landing page rendered in Chromium at 1,280 px and 390 px with no page errors and no sideways scroll;
- the CLI run end to end on the sample.

**Not yet verified:**
- whether any NBFC or auditor will use or pay for it (section 7);
- the unverified market figures marked above;
- accessibility beyond contrast-safe design tokens: a keyboard and screen-reader pass is still due.

## 6. The scorecard

There is no baseline yet: there are no customers and no site traffic (the site is not live), and the product runs offline with
no telemetry by design. The first numbers come from pilots. These are the targets to set once measured:

| Stage | Measure | How it is measured |
|---|---|---|
| Acquisition | Qualified conversations a week | the owner's log |
| Activation | Time from install to a first board pack on real data | timed in the pilot session |
| Activation | Share of in-scope items assessed after two weeks | the assessment file (`assessed_pct`) |
| Retention | Recurring duties recorded on time; a second board pack a quarter later | the assessment file |
| Value | Hours saved against the customer's last cycle; gaps with owner and date | asked in the pilot review |
| Economics | Pilot to paid; onboarding hours per customer | the owner's log |

## 7. The first 30 days: prove or kill it

| Week | Do | Done when |
|---|---|---|
| 1 | Write the list of 30 NBFC heads (IT, risk, compliance) and 15 IS audit firms from your own network, kept private. Settle the employment and conflict-of-interest question in writing first | Both lists; the written answer |
| 1–2 | 15 discovery calls (no pitch): how did you answer the Directions; what did it cost; what is still open; who owns the next audit | 15 calls logged with pains and current spend |
| 2 | Show the sample board pack in each call. Test two leads: "readiness" against "AI firewall" | Which lead gets the follow-up question, by count |
| 3 | Ask for a pilot: free for 90 days, one session together, their real assessment | 3 NBFC pilots and 1 auditor pilot agreed |
| 3–4 | Run the first pilot session; time it; note every point of confusion | Time to first board pack measured; the top 3 frictions fixed |
| 4 | The price test: present ₹1.5 lakh a year (and ₹40,000 a client to auditors) as the after-pilot price; record the reaction | 5 or more price reactions recorded |

**Kill or change course if:**
- fewer than 3 of 15 calls name the Directions as a top-three problem;
- or no pilot is agreed by day 30.

Then test the auditor channel alone, or the CSCRF lead.

## 8. Sources

Read on 2026-10-22; paraphrased:
- RBI NBFC cybersecurity directions 2026: [rbi.org.in](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13592)
- RBI Report on Trend and Progress (NBFC layers): [rbi.org.in](https://rbi.org.in/SCRIPTS/PublicationsView.aspx?id=23641)
- Packaged CSCRF compliance offers: [Infosek](https://www.infosek.in/sebi-compliance), [GetCSCRF](https://getcscrf.com/)
- AI-security consolidation: [Palo Alto 10-K](https://www.sec.gov/Archives/edgar/data/1327567/000132756725000027/panw-20250731.htm),
  [CSO Online on Check Point and Lakera](https://www.csoonline.com/article/4058653/check-point-acquires-lakera-to-build-a-unified-ai-security-stack.html)
- NSE Market SOC: [NSE circular](https://nsearchives.nseindia.com/content/circulars/INSP67808.pdf)
