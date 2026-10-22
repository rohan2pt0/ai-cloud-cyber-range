# 106 · Who SecuRAX is for, and how it sells

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Decided from an audit of the code, sourced market research and the owner's call: SecuRAX is for any organisation that handles other people's data; industry pages are ways in, NBFCs the first. Built and tested: ./securax readiness for any mapped regulation, the homepage's two pillars and the NBFC page. Not yet proven: that any segment will pay; the 30-day plan tests every segment in parallel. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** turn SecuRAX into a product that security teams understand, trust, adopt, pay for and renew. The owner's decision,
after a first draft that led with a single segment: **do not limit the audience.** SecuRAX is for any organisation that handles
other people's data. Industry pages are ways in, not walls.

**How this was decided:** an audit of the code, not the docs (2026-10-22), market research with a source for every fact, and a
look at how the strongest compliance platforms position themselves. Anything not verified is marked. No customer, price or
result below is invented; a number that is a hypothesis says so.

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
| 2 | No enterprise plumbing: tenancy, licensing, an admin console, SCIM; gateway sign-in is off by default on a laptop | High for enterprises, low for a first pilot | High |
| 3 | No connectors to customer tools (SIEM, ticketing, scanners) | High for a SOC product, low for Readiness | High |
| 4 | Too many names, three price tables that disagree (docs 09, 96, 97), personal tools next to business ones | Medium: confuses buyers | Low |
| 5 | Looks like a one-person project: a public repo under a personal name, v0.2.0, no references | High for regulated buyers | Partners and time |

**The five strongest assets**

| # | Asset | Why it matters |
|---|---|---|
| 1 | Paragraph-level maps of six regulations (RBI NBFC 2026, SEBI CSCRF, UK CAF, NIST AI 600-1, MIT AI risk, post-quantum), with chapter or category applicability | The core of Readiness; deep India coverage few tools have |
| 2 | The regulator incident clock (RBI, SEBI, CERT-In, DPDP, IRDAI as data) | The six-hour duty, with drafts and a tamper-evident log |
| 3 | Proof-native engineering: every claim tied to a test | Matches what an auditor wants to see |
| 4 | Runs offline, open source (MIT) | Fits the Directions' vendor clauses: right to audit, source code available |
| 5 | The India-aware AI gateway | A second product for when NBFCs adopt AI (RBI FREE-AI) |

**Fixed in this change:** a public repository must carry no employer or role hints. Several files still referred to the job
descriptions they were first built against. Those references are removed.

## 2. The audience: everyone who handles other people's data

**Decision (the owner's): horizontal.** SecuRAX sells to any organisation, of any size and industry, that must protect other
people's data, prove it to someone (a regulator, an auditor, a client, a Board), and use AI without leaking it.

**Why horizontal is sound here (research, 2026-10-22):**
- **It is how the leaders in this space position.** Sprinto, founded in Bangalore, describes itself as a trust platform across
  200+ frameworks, and is reported to serve 3,000+ customers in 75 countries. Vanta claims 35+ frameworks and 400+ integrations.
  Neither limits its audience; both use framework and industry pages as entry points.
- **The product is already horizontal.** The Readiness engine reads any mapped regulation. Shield guards any AI use.
  Only the map and the message change between buyers.
- **Different buyers share one job:** "show where we stand, close the gaps, and prove it". Only the regulation differs.

**What horizontal costs, and how we pay for it:**

| Risk of going broad | How SecuRAX handles it |
|---|---|
| A vague message ("compliance for everyone") | The homepage names the outcome; each industry page names the regulation in the buyer's own words |
| Competing with well-funded horizontal tools | Lead where they are thin: India-specific depth (RBI chapters, SEBI categories, Aadhaar/PAN-aware AI rails), offline and open source, "unknown is never met" |
| Limited founder time | One product and one engine for all; industry pages are copy, not code. Discovery runs across segments in parallel (section 8), and effort follows the segment that answers first |

**Who it serves, and the way in for each:**

| Audience | What they must prove | The way in | Built today |
|---|---|---|---|
| NBFCs | RBI cyber directions 2026, by chapter (in force since 31 July 2026) | Industry page `website/nbfc/`; `readiness --layer III/IV/V` | ✅ |
| Brokers, depository participants, AMCs, other SEBI entities | SEBI CSCRF, by category | `readiness --map cscrf --category ...`; an industry page is next | ✅ engine, page next |
| Any firm under DPDP (hospitals, insurers, law and accounting firms, SaaS) | DPDP duties; core obligations apply from 13 May 2027 | Shield (PII redaction, residency); a DPDP map is next | 🟡 |
| Any firm using AI | NIST AI 600-1, AI risk, and soon RBI FREE-AI and ISO 42001 | Shield, and `readiness --map nist-ai-600-1` | ✅ |
| UK and global firms | NCSC CAF 4 | `readiness --map caf` | ✅ |
| Auditors and consultants (a channel to all of the above) | Many clients, one method | One assessment per client, the auditor's sheet | ✅ |
| Individuals and families | Their own papers and digital safety | SecuRAX Personal and the Life OS | ✅ |

**The two pillars, one estate:**
1. **Shield:** let people use any AI and keep the data out of it (the existing homepage message, kept).
2. **Readiness:** know where you stand on any regulation, with evidence, and show it to your Board and auditor.

Both run on the customer's own machine, both are open source, and both feed one audit trail.

## 3. Positioning

- **Statement:** SecuRAX lets any organisation that handles other people's data use AI safely and prove where it stands on its
  regulations. Every claim carries its evidence, and everything runs on the organisation's own machines.
- **Headline (kept):** "Let your people use AI. Keep your data out of it." **Second line, for Readiness:** "Know where you stand
  on every regulation. Show the proof."
- **The problem:**
  - Staff already paste customer data into AI tools.
  - Every regulator now asks for evidence, not assurances.
  - The answer to "where do we stand?" lives in a consultant's spreadsheet that dates in a week.
- **Three value propositions:**
  1. AI without the leak: PII and secrets removed before any model sees them, confidential work kept local, every request
     audited.
  2. Readiness for any regulation: only the requirements that apply to you, each with evidence, owner and date, with a board
     pack in one command.
  3. Yours to verify: open source, offline, tested; an "unknown" is never reported as met.
- **Three use cases:**
  1. A firm adopts AI and keeps customer data out of it (Shield).
  2. A regulated entity prepares for its audit (Readiness).
  3. An auditor runs one method across many clients.
- **Why it is different:**
  - India-specific depth inside a horizontal product;
  - offline and open source;
  - proof-native: every status tied to a test.
- **How a buyer verifies it:**
  - the free AI-risk check;
  - the sample board pack;
  - their own pilot;
  - the tests in this repository.
- **"Why not our existing tools?":** GRC suites track controls but do not guard AI use. AI firewalls guard prompts but do not
  show regulatory readiness. Consultants deliver a snapshot. SecuRAX does all three jobs on the customer's own machine and
  keeps the evidence current.

## 4. The business model (a hypothesis)

This section replaces the three earlier price tables (docs 09, 96 and 97) for the business product. Those stay as history.
Prices are per organisation, whatever its industry. Every product SecuRAX sells is listed here, generated from `products.json`.

<!-- products:start -->
Generated from [`products.json`](../../products.json) by `tools/features_sync.py`: edit that file to change a product or a price. Community (the open-source core) stays free.

| Product | For | What it is | Price (hypothesis) | Set against | Status |
|---|---|---|---|---|---|
| **Shield** (AI security) | Any organisation whose people use AI tools or build on models | Use any AI. Keep your data out of it. | ₹399 a user a month, 10 users minimum | AI firewalls are quote-only; third-party sites report US$20,000–80,000 a year for one vendor's enterprise plan (unverified) | 🟡 Partly built |
| **Readiness** (Compliance) | Regulated entities and their auditors: RBI, SEBI, UK and AI frameworks | Know where you stand on every regulation. Show the proof. | ₹1.5 lakh a year for one regulation; ₹50,000 each further one | Packaged compliance offers in India sell for ₹50,000–2 lakh a year; consulting engagements ₹6–40 lakh | 🟡 Partly built |
| **Compliance recipes** (Templates) | CISOs, compliance heads and consultants who should not start from a blank page | Ready-made policies, plans and packs, mapped to the rules. | ₹50,000 a year for the full template library and its updates | An international ISO 27001 documentation toolkit lists at US$799–897 | 🟡 Partly built |
| **CISO OS** (Leadership) | CISOs and heads of security, from a one-person function to a large team | Run the security function, not the spreadsheet. | ₹4,999 a month per CISO | No direct comparable found; priced as a fraction of one consulting day a month (hypothesis) | 🟡 Partly built |
| **Cyber Range** (Training) | SOC teams, CERTs, training institutes and anyone running a cyber drill | Practise against a live red team before the real one arrives. | ₹1,000 a participant a month, or ₹2.5 lakh per hosted exercise | One public cyber range lists US$9–15 a user a month; enterprise range licences run £80,000 and up a year | 🟡 Partly built |
| **Quantum-safe** (Post-quantum) | Banks, insurers, government suppliers and anyone with data that must stay secret past 2030 | Find the cryptography that will not survive, and fix it in order. | ₹75,000 for an assessment and migration plan; ₹40,000 a year to keep it current | CBOM and PQC tools are quote-only and the market is early (ABI Research) | 🟡 Partly built |
| **Respond** (Incidents) | Anyone with a regulator's incident clock: RBI, SEBI, CERT-In, DPDP, IRDAI | Six hours goes fast. Start the clock, not the panic. | ₹1 lakh a year | Usually bought as incident-response retainers from consultancies (no public India price found) | 🟡 Partly built |
| **Personal** (For you) | Individuals and families | Your private superintelligence, and your papers in order. | ₹999 a month | Set against consumer productivity and password-manager subscriptions (hypothesis) | 🟡 Partly built |
<!-- products:end -->

Auditors and consultants buy per client: ₹40,000 a year a client, five clients minimum. The whole estate, for an enterprise: priced per deal.

**What the price points are anchored on:**
- Packaged compliance offers in India sell for ₹50,000–2 lakh a year.
- Consulting engagements run ₹6–40 lakh.
- Global GRC SaaS runs US$6,000–30,000 a year.

**Cost to serve:**
- Readiness runs on the customer's machine and uses no AI model, so its infrastructure and inference cost is near zero.
- Shield's model costs are the customer's own keys or local models, capped per caller by the allowance.
- The real costs are onboarding, upkeep of the maps when regulators change them, and support.
- There is no unlimited AI anywhere.

**Twelve months after the first paid customer** (hypotheses, not forecasts):

| | Readiness customers | Shield users | Audit firms | Yearly revenue (approx.) |
|---|---|---|---|---|
| Conservative | 4 | 20 | 1 | ₹9.0 lakh |
| Base | 12 | 80 | 3 | ₹27.8 lakh |
| Optimistic | 30 | 250 | 6 | ₹69.0 lakh |

Each Readiness customer is counted at one regulation (₹1.5 lakh). Shield is counted at ₹399 a user a month (₹4,788 a user a year). Audit firms are counted at five clients each (₹2 lakh). Example, base case: 12 × ₹1.5 lakh + 80 × ₹4,788 + 3 × ₹2 lakh = ₹27.8 lakh.

**The upgrade path:**
1. A second regulation.
2. Shield for AI use.
3. Sign-off and evidence files.
4. Enterprise: SSO admin, SLA, hosting.

## 5. The plan, ranked

Scores use the weights customer value 25%, commercial 25%, differentiation 15%, feasibility 15%, retention 10% and risk
reduction 10%. A security failure blocks an item whatever its score.

| Pri | Item | Score | Effort | Acceptance |
|---|---|---|---|---|
| **P0** | Remove employer and role hints from the public repo | gate | S | Done |
| **P0** | One price table for the business product | gate | S | Done: this doc; 09, 96 and 97 point here |
| **P0** | Settle the employment and conflict-of-interest position before any paid pilot (owner) | gate | — | A written answer, kept private |
| **P1** | Readiness for any mapped regulation | 4.5 | M | **Done**: `./securax readiness`, 8 tests |
| **P1** | Homepage carries both pillars for every audience; the first industry page | 4.2 | S | **Done**: homepage Readiness section; `website/nbfc/` |
| **P1** | Readiness in the browser (most buyers will not use a terminal) | 4.4 | M | Mark 10 items in the browser in under 10 minutes; the same files as the CLI |
| **P1** | Industry pages for SEBI entities and DPDP-bound firms | 4.0 | S | Each names the regulation in the buyer's words and links a sample |
| **P1** | A DPDP map, so Readiness serves every Indian firm | 4.1 | M | Requirement-level, with sources, in `comply` and `readiness` |
| **P1** | Evidence attachments and a second-person sign-off | 4.0 | M | Each mark can hold files (hashed); a "met" can require a checker |
| **P2** | Import a consultant's workbook into an assessment | 3.9 | M | Row-by-row report of what matched |
| **P2** | RBI FREE-AI and ISO 42001 maps (doc 105, G12) | 3.7 | M | In `comply` and `readiness` |
| **P2** | A trust page and a security questionnaire pack | 3.4 | S | Every answer grounded in a test |
| **P2** | One name per buyer-facing product: Shield, Readiness, Personal, Community | 3.2 | S | Site and docs use only these |
| **P3** | SOC connectors (SIEM, ticketing) | 2.6 | L | After the first revenue |

## 6. What was built in this change

**The catalogue stays current by itself.** To add or change a product, a price or a screenshot:
1. Edit `products.json`.
2. Run `python3 tools/screenshots.py ID` in a clean checkout. It uses sample data only and refuses where `vault/` holds private files.
3. Run `python3 tools/features_sync.py`. The homepage section and the table above are rewritten from the file.

CI's `features-current` check fails if any product names a feature or command that does not exist, or if a screenshot is
missing. A product's status light is the weakest light of the features it is made of.


- **`./securax readiness`** (`governance/readiness.py`):
  - an organisation's own assessment of any mapped regulation, by chapter or category;
  - marks with evidence and provenance; a "met" without evidence is refused;
  - the vital few, the recurring duties, a board pack (HTML, prints to PDF) and an auditor's sheet (CSV);
  - a sample that runs in seconds (`readiness demo`);
  - private by design: files are readable by you only and never committed.
- **The website:** the homepage carries both pillars (Shield and Readiness) for every audience; `website/nbfc/` is the first industry page, with a sample board pack made from fake data.
- **Clean-up:** job-description references removed; CI moved to Node 22; the Dependabot round recorded in the queue.

**Verified:**
- the readiness tests (7);
- the full test suite;
- the board pack and the landing page rendered in Chromium at 1,280 px and 390 px with no page errors and no sideways scroll;
- the CLI run end to end on the sample.

**Not yet verified:**
- whether any organisation, in any segment, will use or pay for it (section 8);
- the unverified market figures marked above;
- accessibility beyond contrast-safe design tokens: a keyboard and screen-reader pass is still due.

## 7. The scorecard

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

## 8. The first 30 days: prove it across segments, follow the pull

| Week | Do | Done when |
|---|---|---|
| 1 | Settle the employment and conflict-of-interest question in writing. Write a private list of 45 contacts from your own network: 15 regulated finance (NBFC, SEBI entities), 15 other DPDP-bound firms (healthcare, SaaS, professional services), 15 auditors and consultants | The written answer; the three lists |
| 1–2 | 5 discovery calls per group (no pitch): what must you prove, to whom, how do you do it today, what does it cost, how are you using AI | 15 calls logged with pains and current spend |
| 2 | In each call, show both pillars: the AI-risk check (Shield) and the sample board pack (Readiness). Record which one gets the follow-up question | A count per group and per pillar |
| 3 | Ask for pilots: free for 90 days, one session together | At least 3 pilots across any groups |
| 3–4 | Run the first sessions; time them; note every confusion | Time to first value measured; the top 3 frictions fixed |
| 4 | The price test: present the section 4 prices; record each reaction | 5 or more price reactions |

**Follow the pull.** Effort goes where pilots and follow-ups come from: more industry pages, maps and calls for that group. The
audience stays open to everyone; only the order of the work changes.

**Change course if:** no group yields a pilot by day 30. Then revisit the offer (price, pilot length, Shield first or Readiness
first), not the audience.

## 9. Sources

Read on 2026-10-22; paraphrased:
- RBI NBFC cybersecurity directions 2026: [rbi.org.in](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13592)
- RBI Report on Trend and Progress (NBFC layers): [rbi.org.in](https://rbi.org.in/SCRIPTS/PublicationsView.aspx?id=23641)
- Packaged CSCRF compliance offers: [Infosek](https://www.infosek.in/sebi-compliance), [GetCSCRF](https://getcscrf.com/)
- AI-security consolidation: [Palo Alto 10-K](https://www.sec.gov/Archives/edgar/data/1327567/000132756725000027/panw-20250731.htm),
  [CSO Online on Check Point and Lakera](https://www.csoonline.com/article/4058653/check-point-acquires-lakera-to-build-a-unified-ai-security-stack.html)
- NSE Market SOC: [NSE circular](https://nsearchives.nseindia.com/content/circulars/INSP67808.pdf)
