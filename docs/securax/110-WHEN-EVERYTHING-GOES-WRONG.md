# 110. When everything goes wrong at once: names, IP and the crisis plan

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: four more monthly guards (name cleared and filed, domain paid ahead, liability cover, bundled licences reviewed), a stricter claims list, a licence register every compose image must appear in, a trade mark policy, and an everything-at-once tabletop; from Satyam, Fair & Lovely, Maggi, Vimal, CCI and Reliance ADA cases. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Docs 107 to 109 asked how the business could fail slowly. This one asks how it could fail on one bad day, when several
things go wrong together:
- a letter about the name;
- a dispute over who owns the code;
- a complaint about a claim on the website;
- a security flaw in the product;
- the domain about to lapse;
- a regulator asking questions.

It reads seven Indian cases and a few court rulings, then sets the safeguards that limit the damage. Four of them are new
monthly guards (section 5).

This is not legal advice. One session with an IP lawyer and a chartered accountant, with the real papers, settles the
details. The owner's own position stays private, as in doc 106.

## 1. What the cases teach

| Case | What happened | The lesson | What SecuRAX does |
|---|---|---|---|
| **Satyam (2009)** | The founder confessed to years of inflated cash and profits. A CBI court convicted him and others in 2015, as reported, with appeals since. In 2018 SEBI barred the auditor's firm from certifying listed companies for two years, saying a network's brand is no shield. The Satyam name did not survive: the company was bought and merged into another. | Books checked by someone other than the founder. And a product name kept apart from the company, so one can be dropped without losing the other. | Guards `revenue-proof` and `independent-review` (doc 108). Every name lives in `brand.env`, so a rename is one file. |
| **Satyam Infoway v Sifynet (Supreme Court, 2004)** | The Court held that a domain name is a business identifier, protected like a trade mark. "Sify" and "Siffy" were too close, and adding "net" did not help. | A domain can infringe a name. A near-miss spelling is no defence. | The name clearance covers domains and spellings that look or sound alike. |
| **Fair & Lovely (2020)** | Society moved and the name became a liability, so the owner renamed it. A rival had already launched "Glow & Handsome", a week before the announcement, and the dispute went to the Bombay High Court. The owner won interim relief; we found no final ruling. | A rename is a launch. Clear and file the new name **before** anyone hears it, and keep a spare. | Guard `brand-cleared`: an attorney's search and a filing come before any public rename. |
| **Maggi (2015)** | FSSAI banned the product over lead and MSG labelling. It was withdrawn and returned about five months later. The government claimed Rs 640 crore before the NCDRC, which dismissed the claim in April 2024, per Nestlé's filings. | Being proved right nine years later does not bring back the lost months. Evidence must exist **before** the test, and the first answer comes in hours. | `SECURITY.md` for flaws; tests, signed releases and an SBOM as standing evidence; an advisory within a day; guard `insurance`. |
| **Vimal pan masala (2025–26)** | A consumer commission summoned the brand and three film stars over a "saffron in every grain" claim (March 2025). A state FDA sent show-cause notices over surrogate promotion (August 2026). Both are at notice stage. The CCPA can fine a maker **or an endorser** up to Rs 10 lakh, and Rs 50 lakh for a repeat (Consumer Protection Act 2019, s.21). | Whoever says a claim is liable for it. Partners and endorsers may repeat only what we can prove, and no claim may imply an approval nobody gave. | Guard `claims` now also fails "RBI approved", "fully compliant", "zero risk" and similar words. |
| **CCI: Google (2022), Amazon–Future (2021)** | The CCI fined Google Rs 1,337.76 crore over Android, largely upheld by the NCLAT in 2023, and Rs 936.44 crore over Play Store terms. In 2021 it suspended an approval it found was obtained on incomplete facts. | Competition law reaches firms of every size, and a regulator punishes a half-told story more than the act itself. | Never agree prices with a competitor, and never fix a partner's resale price (doc 106 partner programme). Tell a regulator the whole story the first time. |
| **Anil Ambani, Reliance ADA group** | A UK court in 2020 held him to a personal guarantee of about $717 million, which he disputed. SBI sought personal insolvency over a Rs 1,200 crore guarantee. SEBI barred him for five years in 2024 over money diverted through Reliance Home Finance, an order he disputes. Banks classed the telecom company's loans as fraud in 2025; it is in insolvency. Both brothers kept the Reliance name after the 2005 split. | A personal guarantee turns a company's failure into the founder's. Money moved between related companies becomes the case against you. And a shared name carries the other side's trouble. | Guards `debt` and `related-party` (doc 109). The rule below: **no personal guarantee, ever**. One company owns the names. |

And the court rulings behind the safeguards:
- **S. Syed Mohideen v P. Sulochana Bai (Supreme Court, 2016):** a prior user's rights rank above a later registration
  (Trade Marks Act s.27(2) and s.34). Filing a mark first does not beat someone who has used it longer.
- **Toyota v Prius Auto (Supreme Court, 2017):** what counts is a reputation in India. A name used only abroad weighs less here.
- **Ferid Allani (Delhi High Court, 2019) and the 2025 guidelines for computer-related inventions:** software that produces a
  technical effect can be patented in India; "a computer program per se" cannot.
- **ANI v OpenAI (Delhi High Court, July 2026, at the interim stage):** training on published text was held, prima facie, to be fair
  dealing. The case continues on its merits.
- **Copyright Act s.17:** an employer owns work made under a contract of service in the course of the job. What counts is
  whose time, whose tools and whose job it was.

## 2. The intellectual property, angle by angle

| Angle | The risk | The safeguard |
|---|---|---|
| **Copyright in the code** | A claim that the code belongs to someone else (an employer, a contributor, a copied source). | Own time, own machine, own accounts, with git history as a dated record. Contributions come in under the terms of the version they join (`CONTRIBUTING.md`). From v0.4.0 the code is FSL-1.1-MIT: free to use, no competing resale, each release MIT after two years (`LICENSING.md`). No copied regulator text (AGENTS.md, section 4). AI-assisted code is reviewed and directed by a person, and the record says so (`./securax ai share`). |
| **The names** | Another firm used a similar name first, in a nearby trade. The code licence is read as licensing the name. A fork trades on it. | An attorney's clearance search in India (and abroad before selling there), covering spellings and domains. A filing in the company's name for software (class 9) and IT services (class 42), plus training (class 41) for the range. `TRADEMARKS.md`: the code is free, the names are not. Search results stay private: a public note about another firm's name helps nobody. |
| **Domains** | A lapsed card hands the domain to a stranger. A look-alike domain phishes customers. | Paid years ahead, with auto-renew, a registrar lock and 2FA. Guard `domain-renewal`. Common misspellings registered once revenue justifies it. |
| **Patents** | Ours: publishing first kills novelty, and India has no general grace period. Theirs: someone patents an idea we published. | We do not chase patents. The public repository is dated prior art against others' patents. An idea worth patenting is filed **before** it is pushed. |
| **Bundled licences** | A fair-code or branding clause forbids what a reseller assumes "open source" allows. | `governance/licences.json` lists every image and model, with what selling it needs; a test fails a new image that is not listed. Guard `licence-terms`. Today: n8n may not be hosted for paying customers without its licence; Open WebUI keeps its branding above 50 users; AGPL parts publish any change we make. |
| **Others' marks** | Using RBI, SEBI, NIST or another project's name in a way that implies an endorsement. | The names only describe what a map covers. No logos, and no "approved" words (guard `claims`). Vaultwarden is never called Bitwarden. |
| **Trade secrets and data** | A customer's evidence or our private plans leak. | `vault/` is never committed; files are mode 0600; privacy and PII checks run in CI. |

## 3. The rules that limit the damage

1. **A company, not the person.** Sell only through a company (doc 106 and the private founder note), so liability stops at
   the company.
2. **No personal guarantee, ever.** Not for a loan, a lease or a customer contract (Anil Ambani).
3. **Contracts cap the downside.** Liability capped at twelve months' fees; no liability for indirect loss; the community
   edition "as is"; the customer keeps its own regulatory duties.
4. **Cover before the first contract.** Professional indemnity and cyber cover, sized to the contracts' cap. Guard `insurance`.
5. **A cleared, filed name before the first invoice,** and a spare cleared name kept ready (Fair & Lovely). Guard `brand-cleared`.
6. **Only provable claims,** from us and from every partner (Vimal, Builder.ai). Guard `claims`.
7. **Books checked outside the founder** once revenue is material (Satyam). Guard `independent-review`.
8. **One owner for the names:** the company, never a relative or a side firm (Reliance).
9. **Evidence kept before it is asked for:** tests, signed releases, SBOM, audit chains (Maggi).

## 4. The day everything goes wrong

A tabletop for the owner, once a year: `./securax continuity tabletop everything-at-once` asks each question below and
checks what this machine can prove. In one week:
- a lawyer's letter says the name is too close to a firm that used it first;
- a customer blames SecuRAX for a breach;
- a consumer complaint cites a claim on the website;
- a researcher publishes a flaw;
- the domain shows 20 days to expiry.

**The first 24 hours**
1. Nobody answers on social media. One person speaks for the company.
2. Preserve everything: logs, the audit chain, the release that ran, the page as it stood (git history holds the site).
3. The flaw: confirm it, ship the fix or a safe setting, and publish an advisory (`SECURITY.md`).
4. Renew the domain. Check the registrar lock.
5. Send the lawyer's letter, the complaint and the contract to the lawyer, and tell the insurer within the policy's window.

**The first week**
1. **The name.** If the other side used it first, do not fight a prior user (S. Syed Mohideen). Move to the spare cleared
   name: change `brand.env`, run `./securax config check`, and redirect the old domain for a set period. Reply through the lawyer.
2. **The claim.** Remove or correct the words the same day. Keep the evidence for what stays.
3. **The breach.** Answer on facts: what ran, which setting, what the logs show. The contract's cap and the customer's own
   duties apply.

**The first month**
1. Write a lesson for each failure (`./securax lessons add`), a test and a drill (AGENTS.md, section 0: antifragility).
2. Tighten the guard line that should have caught it. Never loosen one.

## 5. The four new guards

`./securax venture guards` now checks sixteen things a month. The new four read private plan settings in `vault/venture.json`:

| Guard | Passes when | Before revenue | After revenue |
|---|---|---|---|
| `brand-cleared` | `name_cleared` (the search date) and `trademark_filed` (the application) are both set | WATCH | FAIL |
| `domain-renewal` | `domain_expires` is 180 days or more away | NOT YET if unset | WATCH under 180 days, FAIL under 30 |
| `insurance` | `insured_until` is in the future | NOT YET | FAIL |
| `licence-terms` | `licence_review` is within a year | WATCH | FAIL |

The `claims` guard gained the approval and compliance words in section 1.

Set them with, for example: `./securax venture plan name_cleared=2026-11-15 domain_expires=2028-02-06`.

## Sources

- Satyam: [the scandal](https://en.wikipedia.org/wiki/Satyam_scandal), [SEBI's 2018 order on the auditor](https://www.moneylife.in/article/pricewaterhousecoopers-banned-for-2-years-by-sebi-in-satyam-scam/52739.html)
- [Satyam Infoway v Sifynet (2004)](https://en.wikipedia.org/wiki/Satyam_Infoway_Ltd._v._Sifynet_Solutions_Pvt._Ltd.)
- Fair & Lovely and Glow & Handsome: [The Week](https://www.theweek.in/news/biz-tech/2020/07/03/emami-hul-spar-over-glow-and-handsome-brand-name-both-claim-trademark-rights.html), [Bar & Bench](https://barandbench.com/news/litigation/hul-ad-interim-interim-relief-bombay-hc-trademark-tussle-for-glow-and-handsome-with-emami), [LiveLaw](https://www.livelaw.in/amp/news-updates/glow-handsome-trademark-dispute-bombay-hc-dismisses-emamis-appeal-against-interim-relief-to-hul-160027)
- Maggi: [Supreme Court, 2019](https://www.businesstoday.in/amp/latest/economy-politics/story/nestle-welcomes-sc-order-on-government-maggi-case-at-ncdrc-158313-2019-01-03), [NCDRC dismissal](https://www.outlookbusiness.com/amp/story/news/ncdrc-dismisses-govt-petition-seeking-damages-from-nestle-in-maggi-case)
- Vimal: [consumer commission, 2025](https://www.businesstoday.in/amp/india/story/consumer-disputes-forum-issues-notices-to-shah-rukh-khan-ajay-devgan-tiger-shroff-for-vimal-pan-masala-ad-467211-2025-03-08), [FDA notices, 2026](https://www.theweek.in/news/india/2026/08/16/vimal-elaichi-ad-indirect-promo-for-pan-masala-shah-rukh-khan-ajay-devgan-tiger-shroff-gets-fda-show-cause-notice.html); CCPA penalties: [Rajya Sabha reply](https://rsdebate.nic.in/bitstream/123456789/752503/1/PQ_266_17122024_U2439_p151_p152.pdf)
- CCI and Google: [NCLAT, 2023](https://www.businesstoday.in/technology/news/story/nclat-upholds-ccis-rs-1337-cr-penalty-on-google-375285-2023-03-29)
- Anil Ambani: [UK guarantee ruling](https://www.theweek.in/news/biz-tech/2020/05/22/anil-ambani-ordered-to-pay-717-million-to-chinese-banks-by-uk-court.html), [SBI personal insolvency](https://www.livelaw.in/amp/corporate/nclt-initiates-insolvency-process-against-anil-ambani-over-rs-1200-crores-personal-guarantee-to-sbi-161813), [fraud classification](https://theprint.in/judiciary/why-bombay-high-court-upheld-sbi-decision-to-report-anil-ambani-to-rbi-for-fraud-in-rcom-case/2760205/), [the 2005 split](https://gulfnews.com/world/asia/india/ambani-brothers-dance-and-pray-1.958790)
- Prior use: [Bar & Bench on registered and unregistered marks](https://www.barandbench.com/columns/registered-mark-v-unregistered-mark-who-wins)
- Software patents: [the 2025 CRI guidelines](https://www.aippi.org/news/decoding-cri-guidelines-2025/)
- [ANI v OpenAI, July 2026](https://www.livelaw.in/amp/high-court/delhi-high-court/delhi-high-court-rejects-ani-copyright-suit-open-ai-chatgpt-542736)
- Licences: [n8n Sustainable Use License](https://docs.n8n.io/faircode-license), [Open WebUI License](https://docs.openwebui.com/license/)
