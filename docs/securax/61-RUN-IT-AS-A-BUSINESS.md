# 61 · Run SecuRAX as a business, with a low profile

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The clean-publish script and the site are built; the entity, payments and the organisation move are your steps. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

You sell **SecuRAX Shield** (the AI firewall for regulated companies) under the **CyberBaba** brand. The open-source core
stays free and is the funnel. This page covers the identity, legal and payment set-up, so the brand is what customers see.

!!! warning "Low profile, not invisible"
    A regulated payment provider must know who you are (KYC), and India's company registry lists directors and partners
    publicly. What you *can* do is make the brand, not your name, the thing customers, code and search results show.

## 1. Keep your name off the product

| Layer | Do this | Status |
|---|---|---|
| **Code** | Create the GitHub organisation `cyberbaba`. Publish a fresh copy with no history: `tools/publish-clean.sh cyberbaba securax` refuses to publish while any personal identifier remains. Then make the old repository **private**. | 🟢 script built and dry-run clean |
| **Commits from now on** | In the new clone: `git config user.name "CyberBaba"` and `git config user.email "<id>+<user>@users.noreply.github.com"` (GitHub → Settings → Emails → keep my address private). Set your org membership to **private**. | you |
| **Domain** | Namecheap → Domain List → cyberbaba.org → **WHOIS privacy on** (free). | you |
| **E-mail** | Cloudflare Email Routing: `hello@cyberbaba.org` → your Gmail. To *send* as the brand, use a separate mailbox (for example Zoho Mail's free plan) instead of your personal Gmail. | you |
| **Website** | No founder name, photo or employer anywhere. The site says "built to banking security habits", not who built it. | 🟢 done |
| **Social** | Brand accounts only (LinkedIn page, X, YouTube). Never cross-post from personal accounts. | you |
| **Devices** | Never work on SecuRAX from an employer laptop, network or e-mail. | you |

## 2. Stay clear of conflicts

- **Do not sell to, or partner with, entities your employer supervises or funds**, such as regional rural banks and
  co-operative banks. The site deliberately targets NBFCs, brokers, AMCs, fintechs and any DPDP-regulated firm instead.
- Never use non-public information from your job.
- Keep your employer's written terms, which you have confirmed allow outside business, in your records.

## 3. The entity (decide with a CA)

| Form | What customers and the public see | Note |
|---|---|---|
| Sole proprietorship | **Your legal name** on GST records and invoices | fastest, least private |
| **One Person Company (OPC) or LLP** | the company name on invoices and the payment page; your name in the public MCA filings as director or partner | recommended balance |
| Private limited company | as above; needs two directors | when you raise money or hire |

Register for **GST**. Exports of services can be zero-rated under a **Letter of Undertaking (LUT)**. Open a **separate
current account** in the company's name, and never take business payments into a personal account.

## 4. Taking payments

| Where buyers are | Use | Why |
|---|---|---|
| India | **Razorpay**: Payment Pages, Payment Links or Subscriptions; settles to the company's current account | no code needed; activate international cards separately |
| Global | a **merchant of record** (for example Paddle or Lemon Squeezy) | the merchant of record is the legal seller and handles VAT and GST worldwide, and the buyer's invoice shows them. Confirm they onboard India-based sellers before you rely on one |
| Not now | Stripe | new Indian businesses are invite-only |

**Wiring it to the site:** create a Razorpay Payment Page (for example "Shield, founding licence"), then replace the
`mailto:` link of the pricing button in `website/index.html` with the page's URL. Until the entity and account exist,
the site deliberately sells **design-partner places** by e-mail, not card payments.

## 5. The first 90 days

1. Set up the entity, GST and the current account (CA).
2. Publish the clean repository under `cyberbaba` and make the old one private.
3. Five design partners from your network's *non-supervised* firms: deploy Shield, measure what it catches, collect two quotes.
4. Set the price from what they say they would pay, then switch the button to the Razorpay page.
