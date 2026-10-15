# 49 · Career compass: choose the next job without betting the house

Guiding Map → **💼 Career**. It is one screen for a job decision, worked out from your own numbers on your own device. It shows:

- your floor (never go backwards) and your target (+30%);
- what financial independence (FI) actually needs from your pay;
- every offer, run through must-have gates and then good-to-haves;
- the worst cases;
- the career ladder, worked backwards from the top;
- a dated plan that shows up in **Today → Due now**.

While a decision is live (offers entered, or a notice date set), Career joins the Calm-mode tab row. Otherwise it waits under **More**.

Nothing personal ships in the app: all defaults are zero, and the ladder is the generic BFSI security ladder. You bring your numbers in two ways:
- type them in **step 4**, or
- tap **Load my career file** and pick a JSON file you keep yourself (`{cur, house, cfg, offers}`).

Either way they stay on the device and in your backups.

## The rules it applies (the 20% that decides 80%)

| Rule | What it means | Computed or tapped |
|---|---|---|
| **Never go backwards** | **Today's real value** = payslip net, plus rent and cash-like perks your employer pays, plus employer and own retirement contributions. An offer's real value is its in-hand after tax, minus the health cover you would now buy yourself, plus its PF. The **floor** is today's real value plus your own health and term cover: the minimum in-hand at a job that gives none of them. | computed |
| **Honest CTC** | The baseline for "+30%". It is cash gross, plus rent, plus perks, plus yearly benefits you actually receive. It leaves out what HR brochures add: loan subsidies you are not using, gratuity you have not vested (under 5 years), amortised one-off allowances, and double-counted leave. | computed |
| **Break-even CTC per offer** | The CTC needed, with this offer's own structure, to match today and to beat it by 30%. "Structure" means its variable share, PF, gratuity, cover and tax mode. This is the number to negotiate to. | computed |
| **A rung up** | The title or scope moves you up the ladder, or clearly sets up the next rung. | tapped |
| **Survive it ending early** | The emergency fund ÷ (expenses + EMIs − spouse income) must be ≥ 12 months for a contract role and ≥ 6 for a permanent one. | computed |
| **Regulated field** | Keeps you in regulated BFSI or critical infrastructure, with board or regulator exposure. | tapped |
| **Commute** | 75 minutes door to door or less, or hybrid. | tapped |
| **In writing** | CTC breakdown, reporting line and notice terms; for a contract, also tenure and renewal. | tapped |

Any ✗ rejects the offer. Any **?** means "not decidable yet", and the screen lists exactly what to find out. Offers that pass every gate are compared on weighted good-to-haves:

- next-move value ×3;
- stability ×2;
- team and budget ×2;
- AI-security mandate ×2;
- learning, benefits and flexibility ×1 each.

## Tax model

New regime, FY 2026-27. Budget 2026 left it unchanged.

- **Slabs:** nil up to ₹4L, then 5, 10, 15, 20 and 25% bands up to ₹24L, then 30%.
- **Rebate:** income up to ₹12L is tax-free, with marginal relief just above it.
- **Standard deduction** for salary: ₹75,000.
- **Surcharge:** 10% above ₹50L, 15% above ₹1Cr, 25% above ₹2Cr. There is no marginal relief at those lines, so the estimate is slightly high near them.
- **Cess:** 4%.

The test checks this against a real payslip's figure: tax on ₹18,39,400 is ₹1,74,595.

**Fee income** (a contract paid as a professional fee) is taxed in full by default. Tick **44ADA** only after a CA confirms the work is a notified profession. 44ADA taxes 50% of receipts on a presumptive basis up to ₹75L. GST may apply above ₹20L of fees.

## FI arithmetic

```
corpus = monthly expenses × 12 × (1 + inflation)^years ÷ safe-withdrawal rate
SIP    = (corpus − today's investments grown) × r ÷ ((1 + r)^months − 1)
needed in-hand = expenses + EMIs + SIP − spouse income
```

The defaults are all editable: 6% inflation, 10% return, 3.5% withdrawal, FI at 50.

When FI needs more than the floor, the screen says so. Your real walk-away number is then the higher of the two.

## The 30-month rhythm

A 30% step every 30 months is about 11% a year compounded. That is roughly 2 points a year above the 2026 India Inc average increment (about 9%, per Aon and Mercer) and well above about 6% inflation.

Each offer shows its projected CTC at 45 and 50 if the rhythm holds. Each offer also has a **first-move hike**. A title such as CISO usually earns a bigger next step than a lateral contract does, and that is how title value enters the comparison.

The plan opens the move window at month 24 and decides at month 30. Switch only for a rung up or 30%+; otherwise renegotiate.

## The ladder, worked backwards

| Rung | Role | Rough fixed pay, ₹ lakh (Mumbai, Oct 2026) |
|---|---|---|
| 1 | Senior Manager / head of one security function | 30-45 |
| 2 | CISO of a smaller regulated entity, or Deputy CISO of a large bank | 45-75 |
| 3 | CISO of a mid-size bank, insurer, large NBFC or payments company | 75-120 |
| 4 | CISO of a large bank or a BFSI group | 120-250 |
| 5 | Work optional: board, advisory, own practice | — |

Each rung lists the proof a hiring panel checks: team and budget, board reporting, private-sector delivery, a title held 24+ months, and so on.

The bands are estimates. Sources:
- a public Group CISO contract advert with pay up to ₹2.5Cr;
- aggregator tables giving ₹55-150L for Deputy CISO / CISO.

Check them with two or three executive-search firms before relying on them.

## Worst cases on the screen

- No job for 6 months after your last day.
- A contract ends at month 12, followed by a 6-month search.
- A ₹5L medical bill with no group cover.

All three are measured against the emergency fund, after counting spouse income.

The **one-way door**: leaving a government or PSU post is usually final. The only undo is withdrawing the resignation before you are relieved, if your service rules allow it, so the screen names that date.

## The plan (shows in Due now)

Dated from your notice start, your last day and your joining day:

1. Offers in writing.
2. HR asks: leave encashment, NPS shift, staff-loan closure, accommodation hand-over.
3. The decision.
4. Health and term cover while still salaried.
5. Relieving papers.
6. Keep the same NPS account (PRAN).
7. A 12-month fund if the new role is a contract.
8. The 90-day outcomes.
9. Month 12, 18, 24 and 30 career actions.

## Proof

- `guiding-map/tests/test19.js` (29 checks): tax against a real payslip figure, the rebate and marginal relief; floor, honest CTC, target, FI; gates and verdicts; break-even CTC; survival failing a contract on 10.9 months of runway; plan items in Due now; remove asks first; the empty state; the section is visible.
- `guiding-map/tests/ui_audit.py` (journey `guiding_map_full_use`) now loads a dummy career profile in a real browser and checks the visible screen in both themes for contrast. It caught the screen rendering hidden before release.
- Decision aid, not financial or legal advice.
