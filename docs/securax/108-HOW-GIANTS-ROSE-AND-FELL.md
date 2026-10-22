# 108 · How the giants rose, how they fell, and the guards SecuRAX runs

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: ./securax venture guards checks runway, burn multiple, product and customer concentration, revenue proof, the independent review, unprovable claims, stop tests and platform shifts every month, from sourced case studies of NVIDIA, Microsoft, Google, Meta, Anthropic, IBM, Tesla, RIM, Nokia, Kodak, Byju's, Unacademy, Dunzo, GoMechanic, Builder.ai, Paytm Payments Bank and others; its first run caught and removed an unprovable claim from the site. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** build SecuRAX as if it were the next NVIDIA, Microsoft, Alphabet, Meta, Anthropic, IBM or Tesla. Learn what took
them to the top. Learn from those who fell (RIM, Nokia, Kodak) and from Indian failures (Unacademy, Byju's and others). Then put
the lessons into the estate, not only into a document.

**What was built:** `./securax venture guards`, a monthly check that turns the failure patterns into numbers with a line each
(section 4). It found a real case on its first run: the site promised "Your private superintelligence", a claim nothing in the
code proves. That is Builder.ai's failure in miniature, and the copy was changed the same day.

Facts are from public reporting read on 2026-10-22 (section 6). Where sources disagree, or a fact is secondary reporting, it says
so.

## 1. What took them to the top

| Company | The decisive move | What SecuRAX does with it |
|---|---|---|
| **NVIDIA** | CUDA (2006) given away free for years, before it paid off with deep learning in 2012; the free platform pulled the paid chips | The open-source Community edition is the platform. Measure active installs and outside contributors, and keep the docs and tools excellent while revenue is small |
| **Microsoft** | Nadella (2014) stopped defending Windows: cloud first, open source, GitHub (2018); Azure grew about 100% a year for two years | Never defend a product against a better shift. The shift register (`governance/shifts.json`) names what could replace each SecuRAX product |
| **Google** | Did not invent paid search; did it better (AdWords, 2000) with a revenue engine it could measure | One path from a free check to a paid pilot to a subscription, measured at each step (doc 106 scorecard) |
| **Meta** | Admitted its mobile miss after the 2012 IPO and fixed it within a year; open model weights (2023) to catch up | Say the miss out loud, early. Every failure becomes a lesson, a test and a drill (LESSONS.md) |
| **Anthropic** | Safety and reliability sold as the enterprise feature; a large share of enterprise use by 2025 (investor-reported) | Trust *is* the product in security: every claim tested, open code, a public "what we do not claim" page |
| **IBM** | Gerstner (1993) kept IBM whole and sold integration: "in every industry, there's an integrator" | Sell an outcome across products ("ready for your regulator, with proof"), not eight separate tools |
| **Tesla** | Software updates after the sale (2012), when cars needed dealer visits | Signed, offline-capable updates on a fixed cadence (`./securax update`, releases, doc 21); measure installs on the current release |

## 2. How the giants fell

| Company | What happened | The one-line cause | The lesson for SecuRAX |
|---|---|---|---|
| **BlackBerry** | Share fell from 41% (2007) to under 4% (2012) | Trusted enterprise loyalty over a platform shift | Current buyers will not warn you of the shift: review it every quarter |
| **Nokia** | "Burning platform" memo, 2011: lost "market share, mind share and time" | Its own platform too late | Act before the memo has to be written |
| **Kodak** | Invented the digital camera (1975); bankrupt in 2012 | Protected film margins | Replace your own best product before a rival does |
| **Yahoo** | Haggled over Google (2002) and Facebook (2006); sold for $4.8B in 2016 | No focus, no conviction | Know the one core and fund it |
| **Intel** | Turned down the iPhone chip on a volume forecast far too low | Priced a new market on the old model | Do not price a new market on today's volumes |
| **Theranos** | Fraud conviction, 2022 | Claims nobody checked independently | Every claim needs a test someone else can repeat |
| **FTX** | 25 years for the founder, 2024; customers lost about $8B | Customer money mixed with the founder's firm | Customer data and keys never leave the customer; independent checks |
| **WeWork** | $47B valuation (2019); bankrupt in 2023 | Negative unit economics, founder control | Valuation is not margin |
| **Quibi** | Raised $1.75B; shut down six months after launch (2020) | Capital before product-market fit | Prove pull with a few customers before spending to scale |

## 3. Indian failures, studied closely

| Company | What happened | The cause | The lesson, for a security-software founder |
|---|---|---|---|
| **Byju's** | About $3B of acquisitions; FY21 accounts 18 months late, with the loss up twentyfold after the auditor changed the revenue basis; Deloitte resigned (2023); insolvency admitted (2024) | Growth bought with debt and acquisitions; revenue ahead of cash; a board that did not check | Book revenue on contract and delivery; never let the audit slip; no acquisition while small |
| **Unacademy** | Valued at $3.44B (2021); repeated layoffs; sold to upGrad for about $206M (2026), roughly 94% below the peak | Costs sized for the pandemic peak | Grow costs with recurring revenue, not with a valuation |
| **Dunzo** | Salaries unpaid; vendors' notices over unpaid dues; offline in 2025 | A cash-burning race with no runway buffer | Payroll and vendors first; stop scaling while 12 months of runway remain |
| **GoMechanic** | Founder admitted "grave errors" in financial reporting (2023); 70% of staff cut | Metrics nobody verified, under pressure to raise | Every reported number traces to an invoice and a bank entry |
| **Zilingo** | CEO suspended after due-diligence discrepancies (2022), then liquidation (she denies wrongdoing) | Governance found wanting under diligence | Assume every investor's diligence will be forensic, and be ready all the time |
| **BluSmart / Gensol** | SEBI interim order (2025): loans for EVs partly diverted, including to a luxury flat; shares fell about 90% | The founders' entities and the company's money mixed | No related-party payment without a second signature and disclosure |
| **Builder.ai** | Revenue restated from about $220M to about $55M; bankrupt (2025); its "AI" reportedly fronted human engineers (secondary reporting) | Overclaimed AI and revenue | For an AI security company, the most direct lesson: every AI capability demonstrable and tested; the human share disclosed |
| **Paytm Payments Bank** | RBI fine (2023); new deposits barred for "persistent non-compliances" (January 2024); licence cancelled (2026) | Audit findings left open | Close every audit finding on time. A compliance vendor gets no slack here |
| **Housing.com** | Board removed the CEO after public attacks on investors (2015) | Founder conduct | Behaviour is a business risk; have a written way to settle disputes |
| **Ola Electric** | Over 10,000 consumer complaints investigated (2024); sales fell sharply in 2025 | Sold past its service capacity | Support backlog is a leading signal; never sell more than you can support |
| **Hike** | One law (the 2025 ban on real-money gaming) ended its business in weeks | All revenue on one regulatory bet | Watch every regulation that could stop a product, with a plan B |

Context: Tracxn counted 11,223 Indian startup shutdowns in 2025, up 30% on 2024, 2,785 of them in SaaS.

## 4. The guards SecuRAX runs every month

`./securax venture guards` reads your own private numbers (`vault/venture.json`), the product catalogue, the shift register and
the website. Each guard shows PASS, WATCH, FAIL or NOT YET. NOT YET means there is not enough data to judge, and it never counts
as a pass. The lines live in `governance/guards.json`; tighten them there, and never loosen one to turn a red month green.

| Guard | Line | Learned from |
|---|---|---|
| Cash runway | 12 months or more | Dunzo, Byju's, Quibi |
| Burn multiple (net burn ÷ new revenue) | 2 or less | WeWork, Dunzo |
| Largest product's share of revenue | 50% or less | Nokia, RIM, Kodak |
| Largest customer's share of revenue | 30% or less | small B2B firms that lost their one customer |
| Revenue backed by money received (`--ref` invoice or UTR on every line) | every line | Byju's, GoMechanic, Builder.ai |
| Independent review of the books | yearly, from ₹20 lakh of revenue | Byju's, Zilingo, BluSmart |
| Claims the code cannot prove (words such as "superintelligence", "unhackable", "world's best") | none | Builder.ai, Theranos |
| Stop tests past their date (`kill_if` in `products.json`) | none | Yahoo, Quibi |
| Platform shifts reviewed (`governance/shifts.json`) | within 92 days | Nokia, RIM, Kodak, Intel, Hike |

How to feed it:
- `./securax venture log revenue 150000 "first year" --product readiness --customer "client code" --ref INV-001`
- `./securax venture plan cash=500000`
- `./securax venture plan last_independent_review=2027-04-01`

## 5. The owner's rules the guards cannot check

| Rule | From |
|---|---|
| Every audit or VAPT finding against SecuRAX itself closed within its deadline; criticals within 30 days | Paytm Payments Bank |
| No payment to a related party without a second signature and a written disclosure | BluSmart/Gensol, FTX |
| An independent adviser before the first outside money; accounts closed by the 15th of the next month | Byju's, WeWork, Housing.com |
| No acquisition until the last thing bought is paying its way | Byju's |
| Each year, name the SecuRAX product you would kill if a rival did it better, and build its replacement | Kodak, Microsoft |
| Never sell more pilots than you can support in person | Ola Electric |
| Disclose where people, not software, do the work (for example a human reviewer in Concierge) | Builder.ai |

## 6. Sources

Read on 2026-10-22. Most are news and secondary reporting; the RBI and US Department of Justice releases are primary.
- NVIDIA and CUDA: [Motley Fool](https://www.fool.com/terms/c/cuda-programming/), [btw.media](https://btw.media/en/jensen-huangs-long-cuda-bet-turned-the-gpu-into-a-computing-platform)
- Microsoft under Nadella: [Microsoft WPC 2014](https://news.microsoft.com/speeches/satya-nadella-wpc-2014-keynote/), [TechCrunch on GitHub](https://techcrunch.com/2018/06/04/microsoft-has-acquired-github-for-7-5b-in-microsoft-stock/)
- Google AdWords: [Search Engine Land](https://searchengineland.com/2000-in-review-adwords-launches-yahoo-partners-with-google-34831)
- Meta's mobile turn: [MIT Technology Review](https://www.technologyreview.com/2013/03/06/179555/how-facebook-slew-the-mobile-monster/)
- Anthropic's enterprise share (investor-reported): [TechCrunch](https://techcrunch.com/2025/07/31/enterprises-prefer-anthropics-ai-models-over-anyone-elses-including-openai)
- IBM under Gerstner: [Wharton](https://knowledge.wharton.upenn.edu/podcast/knowledge-at-wharton-podcast/lou-gerstners-turnaround-tales-at-ibm/)
- Tesla's updates: [Green Car Reports](https://www.greencarreports.com/news/1092515_tesla-model-s-electric-car-software-updates-since-2012)
- BlackBerry: [Washington Times/AP](https://www.washingtontimes.com/news/2012/jul/10/rim-seeks-patience-until-blackberry-10-ready/)
- Nokia: [Engadget](https://www.engadget.com/2011/02/08/nokia-ceo-stephen-elop-rallies-troops-in-brutally-honest-burnin/)
- Kodak: [BGR](https://www.bgr.com/2246470/kodak-invention-digital-camera-explained/)
- Yahoo: [iTechPost](https://www.itechpost.com/articles/22831/20160726/yahoo-sale-inevitable-failing-compete-google-purchase-facebook.htm)
- Intel: [Engadget](https://www.engadget.com/2013-05-17-outgoing-intel-ceo-regrets-not-getting-intel-cpu-in-iphone.html)
- Theranos: [NBC](https://www.nbcbayarea.com/news/business/money-report/former-theranos-ceo-elizabeth-holmes-sentenced-to-more-than-11-years-in-prison/3082761/)
- FTX: [US DoJ SDNY](https://www.justice.gov/usao-sdny/pr/samuel-bankman-fried-sentenced-25-years-prison)
- WeWork: [Bloomberg Law](https://news.bloomberglaw.com/bankruptcy-law/wework-goes-bankrupt-capping-co-working-companys-downfall)
- Quibi: [PBS](https://www.pbs.org/newshour/arts/short-video-app-quibi-shutting-down-just-months-after-launch)
- Byju's:
  - [Deccan Herald on the FY21 accounts](https://www.deccanherald.com/business/business-news/byjus-losses-widen-to-rs-4588-crore-in-fy21-1145093.html)
  - [The Wire on Deloitte](https://thewire.in/business/deloitte-resigns-as-auditor-for-byjus)
  - [The Wire on insolvency](https://m.thewire.in/article/business/nlct-initiates-insolvency-proceedings-against-byjus-in-pettition-filed-by-bcci)
- Unacademy:
  - [TechCrunch on the valuation](https://techcrunch.com/2025/12/10/unacademys-founder-says-startup-is-now-worth-less-than-500m-confirms-ma-talks)
  - [TechCrunch on the sale](https://techcrunch.com/2026/09/01/indias-unacademy-sells-to-rival-upgrad-for-206m-about-94-less-than-its-peak-valuation/)
- Dunzo: [YourStory](https://yourstory.com/2025/01/dunzo-goes-offline-investors-co-founder-departs), [Rest of World](https://restofworld.org/2025/dunzo-shutdown-india-quick-commerce/)
- GoMechanic: [TechCrunch](https://techcrunch.com/2023/01/18/sequoia-india-backed-gomechanic-faces-severe-trouble/amp/)
- Zilingo: [The News Minute](https://www.thenewsminute.com/article/zilingo-sacks-ceo-ankiti-bose-over-complaints-financial-irregularities-164183)
- BluSmart and Gensol: [Value Research](https://www.valueresearchonline.com/stories/223978/sebi-bars-gensol-founders-over-ev-loan-diversion-tied-to-blusmart/)
- Builder.ai: [Silicon UK](https://www.silicon.co.uk/cloud/ai/builder-ai-sales-collapse-615436), [ACS](https://ia.acs.org.au/article/2025/the-company-whose--ai--was-actually-700-humans-in-india.html)
- Paytm Payments Bank:
  - [RBI press release](https://rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=57224)
  - [Outlook Business on the licence](https://www.outlookbusiness.com/corporate/rbi-cancels-paytm-payments-bank-licence-what-happens-to-your-account)
- Housing.com: [Fortune](https://fortune.com/2015/07/23/rahul-yadav-fired)
- Ola Electric: [BW Disrupt](https://bwdisrupt.com/article/ola-electric-faces-ccpa-show-cause-notice-amid-rising-consumer-complaints-535623)
- Hike: [TechCrunch](https://techcrunch.com/2025/09/13/hike-once-a-unicorn-shuts-down-as-india-cracks-down-on-real-money-gaming)
- Indian startup shutdowns: [Channel IAM on Tracxn](https://en.channeliam.com/2025/10/25/india-startup-closures-tracxn-report/)
