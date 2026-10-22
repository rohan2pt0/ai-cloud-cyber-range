# 97 · Built for one, ready for many: the suite

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: governance/suite.json declares every component's edition and the shared platform services it uses; ./securax suite shows how ready each edition is to sell and the gaps that unlock the most; suite sheet writes an honest datasheet; fitness enterprise-declared fails an undeclared feature, a built claim without its files, or a broken open core. Community is ready; the paid editions wait on audit, roles, tenancy, licensing, hosting and support, each dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

> **Prices for the business product are now set in [doc 106](106-THE-BEACHHEAD-NBFC-READINESS.md)** (a hypothesis to test with design partners). The tables below are kept as history.

**The ask:** make it part of how every component is built that it can grow into an enterprise ecosystem, sold to everyone the way one productivity suite is sold to homes, small businesses and large enterprises, with a few core things kept open source.

**The answer:**
- **One shared platform:** identity, roles, audit, tenancy, policy, metering, export, residency, continuity and updates are each built once. Every component stands on them.
- **One declaration per component** in `governance/suite.json`: the edition it starts in, the platform services it uses, and what its enterprise version adds.
- **A fitness check that fails** any feature that is not declared, and any service claimed as built without the files that prove it.
- **`./securax suite`** shows how ready each edition is to sell, and which gap unlocks the most.

## 1. The pattern we are copying

The large productivity suites follow one pattern:
- **The same apps, every size of customer:** the person at home, the 50-person firm and the bank all use the same mail, documents and chat.
- **Editions differ by the platform around the apps:** identity and single sign-on, administration, device management, security, compliance and audit. Not by different apps.
- **One identity and compliance platform under everything:** each new app plugs into it and inherits it, so the hundredth app costs far less than the first.
- **Per-seat pricing in clear tiers,** with add-ons for specialist needs.
- **A free or low-cost entry point** that builds familiarity before anyone pays.

What we take from it: **build every component for a person first, on the shared platform, never with a private copy of a platform service.** The step from one person to an organisation is then a platform upgrade, not a rewrite of every component.

## 2. The rule for every component

1. **Build it for one person first.** It must make someone visibly better off (the north star, AGENTS.md section 0).
2. **Use the shared platform.** Sign-in comes from identity, records go to audit, and data stays inside its tenant. If a service falls short, improve the shared one, never a local copy.
3. **Declare it** in `governance/suite.json`:
   - the edition it starts in;
   - the services it uses;
   - one sentence on what the enterprise version adds.
4. **Keep the open core open.** The rules are in section 4.
5. **Claim only what is proven.** A service is built only when its evidence files exist. A datasheet lists as included only what is built.

## 3. Editions and add-ons

| Edition | For | Price (a hypothesis to test) |
|---|---|---|
| **Community** | anyone: a person, a family, a student, a small team that self-hosts | Free, open source |
| **Pro** | one professional: a CISO, a founder, a data protection officer | Rs 999 a user a month |
| **Business** | an organisation of 10 to 300 people | Rs 399 a user a month |
| **Enterprise** | a regulated or large organisation, or a group of companies | Rs 1,299 a user a month |

Add-ons:
- **Concierge** (doc 96), for HNIs and family offices.
- **Range training**, for security teams.
- **Govern advisory**, for boards and CISOs.

Pro costs more per seat than Business because one person carries the whole cost of hosting, support and every edition. Business spreads the platform over many seats.

**For scale only:** Indian resellers list one global productivity suite (October 2026, excluding GST) at about:

| Plan | Price a user a month |
|---|---|
| Business entry | Rs 125-145 |
| Business standard | Rs 660-770 |
| Business premium | Rs 1,500-1,830 |
| Enterprise E3 | Rs 1,900-2,700 |
| Enterprise E5 | Rs 3,100-3,700 |

The quotes differ by up to half between resellers ([itforsme](https://itforsme.in/pricing/microsoft-365-india), [ogma](https://ogma.in/solutions/microsoft-365-price-india), [cloudfy](https://cloudfysystems.com/blog/microsoft-365-renewal-pricing-india)). They show what Indian organisations already pay per seat for a suite. They are not a price for this one.

## 4. The open-core line

| Always open (this public repository) | Commercial (a separate private repository; only its interfaces are here) |
|---|---|
| Every component | The tenant admin centre: users, seats, policies, audit and bills in one console |
| Identity with SSO and MFA: **no SSO tax** | SCIM: joiners, movers and leavers synced from the customer's identity provider |
| Export of your own data, in every edition | Licensing and billing: entitlements, licence keys, invoices with GST |
| Data residency, backups, recovery and drills | Managed hosting of nodes and tenant cells in India regions |
| Roles, audit, tenancy, policy, metering and the APIs | A support desk with an SLA |
| Security fixes, which reach every edition at once | Human services: Concierge, facilitated range exercises, advisory |

Why the line sits here:
- A person, a family or a single organisation can be fully safe with the open core alone.
- What is sold is what running many people and many organisations takes: administration, automation, hosting and humans.
- Charging extra for single sign-on is widely criticised as an "SSO tax" (see [this playbook on enterprise SSO](https://guptadeepak.com/ebooks/b2b-saas-security-playbook/enterprise-sso/)). Gating it is also bad security, because it pushes small customers to shared passwords.
- The check enforces the line:
  - identity and export must be open and in the first edition;
  - the free edition may stand only on open services;
  - a commercial service may have no code in this public repository.

The code is MIT licensed, so what is already public stays usable by anyone. The moat is the platform's quality, the service, the trust and the brand, so register the name as a trademark.

## 5. How it is enforced

| Where | What it does |
|---|---|
| `governance/suite.json` | The editions, the shared services (open or commercial, built, partial or planned, with evidence or a gap and a date), and every component's declaration |
| Fitness `enterprise-declared` | Fails CI when a feature is undeclared, a built claim lacks its files, the editions do not nest, or the open core is broken |
| `AGENTS.md`, sections 0 and 3 | Tells every builder (person, Claude or the open models) to use the shared platform and declare the component |
| `./securax suite sheet EDITION` | A datasheet that lists as included only what is built, and puts everything else under "on the way" with its date |

## 6. What to build next, and why in this order

Run `./securax suite` for the live order. It ranks gaps by how many components and editions each one blocks. Today the top of the list is:
- **audit:** one estate-wide, tamper-evident stream that a customer can send to their SIEM;
- **roles:** across the sync, the kit apps and the registers;
- **licensing:** entitlements and keys;
- **tenancy:** a tenant id that runs through the laptop and VPS path, not only the cluster.

Audit, roles and tenancy together unlock most of the Business edition, and they are open. So the community gains first, and the paid editions become possible on top. That is the 80/20, and it is also dual use (doc 96).

## 7. Proof

`governance/tests/test_suite.py` checks that:
- the suite is sound and every feature is declared;
- an undeclared feature fails, and so does a claim without its files;
- an SSO tax fails, and so does commercial code in the public repository;
- the editions must nest, and every gap needs a date;
- readiness follows what is built;
- a datasheet sells only what is built.

The fitness check `enterprise-declared` runs `suite check` on every change.
