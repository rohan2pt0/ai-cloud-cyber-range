# The Life OS as a superapp, without the bloat

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** A plan, not a build (2026-11-25): the evidence, what exists, and the six small additions that make the Life OS one app without bloat. Each turns the light as its slice ships. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

The owner asked (2026-11-25) whether the Life OS can be the one app for productivity and personal finance, and what to add without making it heavy. This page is the answer: what the evidence says, what we already have, and the few things worth adding.

## What the evidence says

Most of it is vendor research, so read it as direction, not proof.

- **People use several apps because one is missing a feature, not because they like many.** A 2025 survey of 1,500+ users in the UK and Europe found 60% add a second finance app for a missing feature, 91% would consolidate if one app did it all, and over 80% are at least sometimes unsure where their information lives. [DECTA: Wallet Fatigue](https://www.decta.com/company/media/digital-wallet-and-financial-app-user-experience-2025), [The Paypers](https://thepaypers.com/payments/news/dectas-new-study-finds-forced-fragmentation-in-digital-banking).
- **Ease beats extras.** A 2026 UK survey puts an easy interface ahead of security as the most wanted trait in a finance app. [Apadmi Finance App Report 2026](https://www.apadmi.com/insights/resources/finance-app-report-2026/).
- **The tipping points for deleting an app are friction, not missing features:** pop-ups, crashes, tiny text and unclear privacy settings. [TechRadar, citing Amplitude](https://www.techradar.com/pro/ready-set-gone-why-popups-app-freezing-and-small-texts-are-causing-millions-of-app-users-to-jump-ship-and-abandon-businesses).
- **Wealth tools win on two things:** one consolidated view across entities and assets, and a vault for the papers behind it (policies, wills, tax slips). [Masttro](https://masttro.com/insights/family-office-app), [Wealthica](https://www.investmentexecutive.com/news/wealthica-offers-consolidated-reporting-for-family-offices/).
- **In India, bank data can reach an app by consent** through the RBI's Account Aggregator rails, but an app joins them as a regulated data user or through a partner. It is not a weekend job. [Sahamati](https://sahamati.org.in/), [HyperVerge guide](https://hyperverge.co/blog/account-aggregator-framework-rbi/).

## What we already have (so we do not add it twice)

Goals and the wheel, the money tab with runway and the waterfall, property and landlord, career, kids and family, the Inbox, life papers read for you, scan a document, the Coming up list, the calendar registry, the calls journal, the lock, sync and move-to-another-phone, money health (insurance, cash, debt, allocation) and fixes for every flagged issue. The gap is not more features. It is the **spine** that makes them feel like one app.

## The few things worth adding (80/20, in this order)

1. **Find anything.** One search box, offline, across goals, papers, policies, deadlines, properties and notes. It answers "where is X?", the confusion more than 80% of people report. Built on what is already on the device; nothing new is stored.
2. **Everything that falls due, in one list.** Policy premiums and maturity dates from the Money health register, loan EMIs, rent, tax and renewals all feed the one Coming up timeline, which already reaches the calendar. No second reminders screen.
3. **One add button.** One tap from any screen: a note, an expense, a task or a photo of a paper. Code routes it to the right place, with an undo. Builds on the Inbox.
4. **Numbers arrive by themselves.** The least-effort path first: read a statement or message the person pastes or shares, on the device (the Inbox already reads papers). The consent-based bank route comes later, through a partner, because it needs regulatory standing.
5. **Use it or fold it (the bloat guard).** The app counts, on the device only, which sections a person opens. A section unused for 60 days folds under "More", with one tap to bring it back. A new module must replace or fold something, and the home screen keeps one open action. A test holds the number of things open on the first screen.
6. **Show only what fits the person** (queue `fits-the-person`, `essentials-first`): a student, a salaried person, a business owner and a retiree each see their own few sections first.

## What we will not add

A feed, a points game, ads, a second login, a marketplace, or any screen that needs a manual. Each fails the human-first rule and the evidence above.

## Order of work

Find anything, then the due-list feed, then the add button, then use-it-or-fold-it. Each is one small slice with its own test. The store apps (queue `store-submission`) follow once the spine is in.
