# Release readiness — the go/no-go gates for the public launch and the paid edition

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Audited 15 November 2026: NO-GO for the public launch and for the paid edition. The gates are built and run on every change (./securax release ready; fitness release-gates; a 1.0.0 tag is refused while a public-launch gate is NO-GO). It turns green when both verdicts are GO. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The verdict on 15 November 2026: NO-GO for both.** Nothing found is a leaked secret or a live breach. What blocks is
smaller and fixable: the hosted apps share a browser address with other projects, there is no privacy notice, no
disclaimer, no line that says money guidance is education, and four parts that strangers will reach have no threat model.

This page is the audit. The live verdict is one command, worked out from the repository each time it runs:

```bash
./securax release ready          # the verdict, and what blocks each launch
./securax release ready --all    # the same, with the gates that already pass
```

Three people wrote it together: a security chief (sections 3, 4 and 8), a privacy counsel (sections 5 to 7) and a release
manager (sections 2 and 10). The legal sections are an engineer's careful reading, written so a lawyer can check them
fast. They are not a legal opinion, and two gates wait for one.

## 1. First, three things

1. **Do not call it open source yet.** The licence is the Functional Source License (FSL-1.1-MIT). It lets anyone read,
   run and change the code, but not sell a competing product, and each version becomes MIT after two years. The Open Source
   Initiative does not count that as open source, and the FSL's own authors call it "Fair Source". Say **"free to use,
   source available, MIT after two years"**. One line on the site said "open-source edition"; it is fixed, and gate
   `licence-named-truthfully` keeps it fixed. If the launch must be truly open source, that is a licence change: the
   owner's decision, with the lawyer (queue `licence-review`).
2. **The hosted apps must move before strangers use them.** On the current static host every project of one account
   shares one browser origin, and the host sends none of our security headers. A page in any other project there could
   read what the Life OS stored. That host's terms also do not allow running a paid service. The threat model already
   accepts this risk, with a review date of **20 November 2026**. The day after, the fitness check `threat-modelled`
   turns red on every pull request until the apps have their own origin (queue `own-origin-hosting`) or the owner
   re-accepts the risk with a new date.
3. **Charging money for planning on a person's own numbers needs a securities lawyer first.** Section 6 says why, and
   what to send them.

## 2. How the gates work

- Two launches are judged. **open** is the public launch of the free core. **paid** is charging for an edition.
- A gate is a **probe** or an **attest**. A probe is a small function in
  [`governance/release_gates.py`](../../governance/release_gates.py) that reads the repository. Nobody types its state in:
  it is GO when the thing is there. An attest is something only the owner can confirm, such as a repository setting or a
  lawyer's letter. It is GO once it carries a date and where the evidence is kept.
- The gates live in [`governance/release-gates.json`](../../governance/release-gates.json): what each is, why it
  matters, which launch it blocks, the fix, its queue item and its due date.
- **A gate cannot fail quietly.** The fitness check `release-gates` runs on every change. It fails when a probe goes red
  without a record (since when, the fix, a live queue item, a date), and when a record is left on a gate that now passes.
  So a gate that was GO cannot slip to NO-GO in a pull request unnoticed.
- **A launch tag is held.** The release workflow runs the gates. A `0.x` tag prints the verdict and goes on. A tag of
  `1.0.0` or later is the public launch, and it is refused while any open gate is NO-GO.
- Dates do not break the build. A gate's due date shows in the verdict, and its queue item shows late in
  `./securax backlog`; neither turns main red. One date does: a threat-model acceptance past its review date fails
  the fitness check `threat-modelled`, as it did before this audit.

## 3. The gates

State is as found on 15 November 2026. The command above is the truth after that.

### Secrets

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `secrets-scanned-in-ci` | open, paid | GO | Every push and pull request is scanned over the whole history; the same scan runs before a commit. |
| `no-secret-files-tracked` | open, paid | GO | No key file, environment file or vault content is tracked. The only matches for key shapes are the documented fake keys in test fixtures. |
| `secrets-history-and-push-protection` | open | owner | A setting cannot be read from code. The owner turns on secret scanning with push protection and runs one full-history scan. |

### Supply chain

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `release-signed-with-sbom` | open, paid | GO | A release carries a list of its parts (SBOM), checksums and signed build provenance, and is published only after every file is attached. |
| `actions-pinned-by-commit` | open | NO-GO | Most build steps written by others follow a movable tag (the command lists them). Two of them run in the job that publishes a release. A hijacked tag would ship a tampered build with a valid signature. |
| `workflows-safe-for-strangers` | open, paid | GO | No workflow gives a stranger write access, secrets or a shell. The build agent starts only on the owner's own issue, and its task reaches the script as data. |
| `third-party-notices` | open, paid | NO-GO | The Life OS bundles a text reader and its language data with no licence text beside them. The SBOM lists the gateway image only, not the apps. |
| `dependencies-watched` | open, paid | GO | Python, JavaScript, containers and build steps are watched weekly. |
| `download-verification-documented` | open, paid | GO | Doc 21 shows the checksum and the attestation check. |
| `repository-hardened` | open | owner | Protect main, use a passkey or hardware key, make releases immutable, turn on private vulnerability reports, and name a second person who can act. Today one account is the only way a build reaches everyone. |
| `contributions-signed-off` | open | NO-GO | Nothing checks that a stranger's contribution is theirs to give. Code of unknown origin cannot be sold, and cannot become MIT later. |

### Threat models

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `threat-models-hold` | open, paid | GO | Every model is complete. Two acceptances expire on 20 November (see section 1). |
| `hosted-apps-own-origin` | open | NO-GO | The shared origin and the missing headers are accepted risks today. They must be closed, not re-dated, before strangers store data there. |
| `launch-surfaces-modelled` | open | NO-GO | No model yet for the AI gateway, the sync hub, the installer and update channel, or the release pipeline with its build agent. |
| `paid-surfaces-modelled` | paid | NO-GO | Payments and the paid entitlement need a model before any payment code is written. |

### Data that leaves the device

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `guest-sends-nothing` | open, paid | GO | New test: the Life OS is opened as a guest, with a profile, and as the hosted copy; every screen is visited; nothing leaves its own origin. |
| `no-trackers-no-foreign-code` | open, paid | GO | Fixed in this audit: the Command Center's visual tour loaded its typefaces from another company on every open. No page names a tracker. |
| `every-outbound-flow-declared` | open, paid | GO | The flows are declared (section 4). Every outside address in the apps' code belongs to one. |

### Privacy

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `privacy-notice-published` | open, paid | NO-GO | There is no privacy notice. |
| `export-and-erase-work` | open, paid | GO | A person can take all their data out and erase all of it on the device, without us, and a test holds both. |
| `dpdp-map-verified` | paid | NO-GO | The DPDP map covers only the breach clock and is marked unverified. |
| `responsible-entity-named` | paid | owner | A notice, an invoice and a licence each need a named legal person and a grievance contact that is answered. |
| `gdpr-scope-decided` | paid | owner | Decide whether the paid edition is offered in the EU or UK, and act on the answer. |

### Investment advice

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `no-securities-recommendation` | open, paid | GO | No screen names a security, tells a person to trade, promises a market return or picks products. Three phrases were reviewed and kept, each with its reason in the registry. |
| `no-live-prices` | open, paid | GO | No app reads a market price feed. |
| `no-referral-income` | open, paid | GO | No link to a financial product carries a referral tag. |
| `education-line-shown` | open, paid | NO-GO | Rules of thumb show beside the person's own numbers with no line that says what they are. |
| `ai-personas-bounded` | open, paid | NO-GO | The Ask screen tells its AI to act as a "personal-finance advisor" and an "insurance advisor" and to give an opinion on the person's case. |
| `securities-counsel-opinion` | paid | owner | Only counsel can clear paid planning (section 6). |

### Disclaimers and terms

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `licence-named-truthfully` | open, paid | GO | Fixed in this audit (section 1). |
| `disclaimer-published` | open, paid | NO-GO | The limits are said in several places, or nowhere. One page must hold them. |
| `paid-terms-published` | paid | NO-GO | No terms for a paid edition exist. |
| `trademark-cleared` | paid | owner | A name that must change after launch costs every user their trust in which copy is real. |

### Abuse

| Gate | Blocks | State | What the audit found |
|---|---|---|---|
| `fake-copy-report-route` | open, paid | GO | Added in this audit: SECURITY.md now says where the real SecuRAX lives, how to check a copy, what we never ask for, and how to report a fake or misuse. |
| `coercive-setup-modelled` | open | NO-GO | Reading bank messages and a mailbox is also what stalkerware does. Neither model considers a set-up on someone else. |
| `gateway-abuse-rails` | open, paid | GO | The AI gateway has a tested allowance per person, refuses foreign origins, and keeps a human in command. |

## 4. Data that leaves the device

The promise is simple: **nothing leaves until the person connects something, and then only to their own account or
their own machine.** It is now a test (`guiding-map/tests/test120.js`), not a sentence.

| Flow | What leaves | When | To whom | Protection |
|---|---|---|---|---|
| OneDrive backup | A sealed copy of the person's data | After they tap to connect | Their own Microsoft account. We never receive it. | Sealed on the device; the key stays there |
| Bank alerts from Outlook | Nothing goes out; mails are read in | After they tap to read alerts | The device | Read-only, one switch off |
| Estate sync | The person's data | On a device they paired | A machine the person runs | The estate's own names over TLS |
| Web push | A push address and short alert texts | After they allow notifications | Their estate, then the browser maker's push service | Encrypted for the device |
| Ask | The question typed | When they ask | The gateway on their own estate | Rails, identity, allowance, audit chain |
| Site visit | The device's address and the page asked for; an e-mail if they write | On opening the site or hosted app | The static host; our mailbox | No cookies, no analytics, no scripts from elsewhere |

Two limits, said plainly. The egress test runs in a simulated browser, so it proves what our code asks for, not what an
injected script could do; the hosted app has no script policy until it has its own origin. And Vantage and the Command
Center were checked by reading their code, not by opening every screen.

## 5. Privacy: India's DPDP Act and the GDPR

**Who answers for what.** A person who keeps their own and their family's facts in the Life OS, on their own device, is
acting for a personal or domestic purpose. Both laws leave that alone (DPDP Act section 3; GDPR article 2). SecuRAX
answers only for the personal data *it* decides how to use: site and host logs, mail people send, support packets, and
later billing. That is a small list, and it should stay small. Every new flow in section 4 that ends at us makes it longer.

**Dates.** The DPDP Rules were notified in mid-November 2025. The Data Protection Board's rules applied at once, the
consent-manager rules a year later, and the main duties (notice, safeguards, breach reports, children, rights,
retention) eighteen months later, about 13 May 2027. Sources differ by a day, so confirm against the gazette (gate
`dpdp-map-verified`). A paid edition that launches before then should be built to the full duties anyway.

**What a paid edition owes, in short.**

| Duty | DPDP Act | GDPR | State |
|---|---|---|---|
| A clear, itemised notice | section 5 | articles 13 and 14 | missing (`privacy-notice-published`) |
| Consent that is specific and can be withdrawn as easily as given | section 6 | articles 6 and 7 | each connection is one tap, with one switch off |
| Access, correction, erasure, taking data out | sections 11 to 13 | articles 15 to 20 | on the device, without us (`export-and-erase-work`) |
| A grievance contact that answers; then the Board | sections 8 and 13 | articles 12 and 77 | missing (`responsible-entity-named`) |
| Reasonable safeguards | section 8 | article 32 | the threat models, the lock, the sealed backup |
| Tell the Board and each person of a breach | section 8; the Rules give 72 hours for the full report | article 33 | the incident clock exists; the map is unverified |
| Children: a parent's verifiable consent; no tracking, no targeted ads | section 9 | article 8 | no trackers at all; children's facts stay on the device |
| Erase when the purpose is done, unless a law says keep | section 8 | article 5 | to state in the notice (billing records are kept as tax law requires) |
| Sending data abroad | section 16 | chapter V | nothing reaches us today; billing and mail processors will |
| A representative in the Union, if offered there | not applicable | article 27 | to decide (`gdpr-scope-decided`) |

**The privacy notice.** `PRIVACY.md` must have these seven parts, by these names, written from the flows in section 4:
**Who is responsible** (the named person and a contact). **What we collect** (itemised, each with its purpose; and what
we never collect). **What leaves your device** (the table above). **Your rights** (and that most need no request,
because the data is on your device). **How to complain** (to us first; then the Data Protection Board of India, or your
own authority in the EU or UK). **Children** (their facts stay on the device; nothing is tracked). **How long we keep**
(each item, and why). The owner and counsel approve the wording. The DPDP Act also asks that a notice can be read in
English or any language of the Constitution's Eighth Schedule; the app's Hindi and Marathi catalogs are the start.

## 6. Investment advice: staying on the education side of SEBI's line

**The rule, paraphrased.** Under SEBI's investment-adviser regulations, a person who gives investment advice *for
consideration* must be registered. Advice covers buying, selling or dealing in securities and investment products, and
advice on a portfolio, and it includes financial planning. Advice through media open to the public is treated
differently, and research on named securities falls under the research-analyst rules. SEBI's 2025 rules on unregistered
"finfluencers" allow education only when it gives no recommendation and makes no claim about returns, and its 2026
circular lets education use only price data that is at least 30 days old.

**Where SecuRAX stands.** The free Life OS shows general rules (keep six months of costs, a share in equity that falls
with age, pay costly debt first) beside the person's own numbers. No screen names a security, a fund, an insurer or a
policy. There are no prices, no orders, no commissions. Free, general and unpaid is the safe side. Three things move it
toward the line:

1. **Money for it.** A paid edition that does planning maths on a person's own numbers is the fact pattern the rules
   were written for. The argument that it is software, not advice, is reasonable. It is counsel's to confirm.
2. **An AI told to advise.** The Ask personas are instructed to act as advisers and give an opinion on the person's case.
3. **What is planned.** Reading holdings from a broker is education. Placing an order, or telling a person what to
   rebalance into, is not.

**The line we hold** (each is a gate): name no product; never say buy, sell or hold; promise no return; read no live
prices; take no commission; place no order; charge for software at one price, never a share of wealth; and show the
line below wherever money guidance appears.

> Education and tools, not advice for you. SecuRAX is not a SEBI-registered investment adviser or research analyst. It
> names no product and takes no commission. Check with a registered professional before you act.

In the Global edition the second sentence reads "is not a registered investment adviser in any country". The same care
applies to insurance (a cover range is education; naming an insurer is selling) and to tax and law (the screens already
say "not tax or legal advice" in their notes; the line must be on screen).

**What to send counsel** (gate `securities-counsel-opinion`): this section; screenshots of the Stack, the money
screens, Vantage and Ask; the price list; and four questions. Is paid planning maths on a person's own numbers
"investment advice"? Does an AI answer change that? Does the public-media carve-out help a signed-in app? If the answer
is no, is the better route registration or a registered partner?

## 7. Disclaimers and terms

**`DISCLAIMER.md`** has six parts, by these names:

- **Security.** SecuRAX lowers risk; it cannot promise safety. If you lose your device and your recovery phrase, nobody,
  including us, can recover your data.
- **Compliance.** The regulator maps are working aids with linked evidence. They are not a certificate, an audit or
  legal advice, and SecuRAX has not been independently audited.
- **Money and tax.** The line in section 6. Amounts and rules change every year; each lever shows when it was checked.
- **Health.** Check-up reminders and health notes are for learning. They are not a diagnosis. In an emergency, call one.
- **AI answers.** An AI can be wrong and can sound sure. Treat an answer as a first draft.
- **Authorised use.** The red-team tools, the range and the hunt packs are for systems you own or are authorised in
  writing to test.

**`TERMS.md`**, before anyone pays, has four parts: **Price and renewal** (the full price up front, a notice before each
renewal, no auto-renew by surprise). **Cancelling and refunds** (as easy as signing up; the refund rule in one
sentence). **Liability** (the limits, in plain words). **Governing law** (and where disputes go). India's e-commerce
consumer rules and the 2023 guidelines against dark patterns apply here; the `human-first` principle already forbids
what they forbid. Tax invoices, GST and the payment provider's contract were **not** audited: that is for the
accountant and counsel.

## 8. If it becomes a massive hit: the abuse cases

| What goes wrong at scale | Who is hurt | What holds today | Gate |
|---|---|---|---|
| Fake copies: a look-alike site or app collects people's money facts | New users | Signed releases; the report route | `fake-copy-report-route`, `trademark-cleared` |
| One bad change reaches everyone at once: a stolen owner account, a hijacked build step, a hostile pull request | Every user | Checks on every change; a build agent only the owner can start | `repository-hardened`, `actions-pinned-by-commit`, `contributions-signed-off` |
| Another page on the shared address reads stored data | Hosted users | Nothing; it is an accepted risk | `hosted-apps-own-origin` |
| A partner, parent or employer sets message-reading up on someone else | The person watched | It needs that person's own sign-in | `coercive-setup-modelled` |
| "SecuRAX told me to invest": screens quoted as advice, or sold as advice by others | Users; the owner | No product is named | section 6 gates |
| The free AI door is drained or steered into harm | The owner's bill; others | Allowance, origin check, kill switch | `gateway-abuse-rails`, `paid-surfaces-modelled` |
| The testing tools are aimed at someone else's systems | Third parties | The authorised-use line in SECURITY.md; where the tools point by default was not checked | `disclaimer-published` |
| A firm tells its regulator SecuRAX "certified" it | The firm; the owner | The site says it is not certified | `disclaimer-published` |
| Lost phones and lost recovery phrases, by the thousand | Users; support | Export, backup phrase, restore drill | `disclaimer-published` |
| One maintainer, many users: reports and fixes queue up | Every user | SECURITY.md targets | `repository-hardened` |
| Someone hosts a paid copy | The owner | The licence forbids it | `licence-named-truthfully`, `trademark-cleared` |

## 9. What was not tested

- **The full git history.** The clone here was shallow. CI's scanner does read the whole history on every push.
- **Repository settings.** Branch protection, push protection and immutable releases cannot be seen from code. They are
  owner attests.
- **A real release.** No published file was downloaded and verified.
- **A real browser.** The egress test runs in a simulated one. The device and theme audits were not rerun; one page
  (the visual tour) now uses the system's typefaces until its own are bundled (queue `explainer-own-fonts`).
- **The 40-minute sandbox.** CI runs it on the pull request.
- **Tax, payments, export rules and employment law.** Out of scope.
- **The law itself.** Sections 5 to 7 are for counsel to confirm.

## 10. The order of work

Ranked by risk times reach, over effort.

1. **This week:** `own-origin-hosting` (it also unblocks the fitness check on the 21st); the owner's two attests
   (`launch-owner-attests`).
2. **By 29 November:** `pin-actions-by-commit`, `third-party-notices`, `privacy-notice`, `disclaimers`,
   `sebi-education-line`. The first, second and last are small build tasks for the open models.
3. **By 5 December:** the four threat models (`threat-models-by-risk`), `abuse-coercive-setup`, and the sign-off check
   (`ip-contributor-terms`).
4. **Before any price is charged:** the lawyer's letter (`sebi-paid-opinion`), the named legal person
   (`licence-holder-company`), `gdpr-scope`, `paid-terms`, `paid-threat-model`, `dpdp-map` and the trademark.

Then cut `1.0.0`. The workflow will let it through.

## Sources read for this audit

Cited by reference and paraphrased; the regulators' own texts decide.

- The Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025 (India); commentary
  on the phased dates from [SCC Online](https://www.scconline.com/blog/post/2025/12/26/digital-personal-data-protection-rules-2025-key-highlights/)
  and [Lawrbit](https://www.lawrbit.com/article/digital-personal-data-protection-rules-2025).
- Regulation (EU) 2016/679 (the GDPR), articles 2, 3, 13, 27, 28, 32 and 33.
- SEBI (Investment Advisers) Regulations, 2013 and SEBI (Research Analysts) Regulations, 2014; SEBI's FAQs on the
  adviser regulations ([a copy](https://icmai.in/upload/pd/FAQs-Investment-Advisers-Regulations.pdf)).
- SEBI's January 2025 circular on unregistered persons and education, and its May 2026 revision of the price-data lag
  ([Outlook Money](https://www.outlookmoney.com/invest/sebi-revises-norms-for-sharing-and-usage-of-price-data-for-educational-purposes),
  [Business Standard](https://www.business-standard.com/markets/news/sebi-finfluencer-circular-live-stock-data-market-education-rules-125013000571_1.html)).
- The Functional Source License: [fsl.software](https://fsl.software/).
- The Consumer Protection (E-Commerce) Rules, 2020 and the Guidelines for Prevention and Regulation of Dark Patterns, 2023 (India).
