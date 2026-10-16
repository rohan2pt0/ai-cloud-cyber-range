# 46 · Certification path: the hardest offensive and AI certifications, on 30 hours a week and ₹5 lakh a year

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🔴 Not built yet.** A plan; no certification has been started. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

`./securax certs` turns "clear every serious offensive and AI certification" into a dated, costed plan that re-dates itself as you pass.
Written 14 Oct 2026 for: starting from zero, 30 h/week, ₹5 lakh/year, paid personally, goal = credibility for every future role.

```bash
./securax certs plan                    # the whole plan (defaults: 30 h/week, ₹5,00,000/year, start today)
./securax certs next                    # this week: what, why, how to split your hours, where to practise
./securax certs mark cpts passed        # progress (also: studying | booked | failed); the plan moves on
./securax certs plan --pace 1.3         # you were slower than the estimate: everything re-dates
./securax certs plan --with-optional    # also CWES, eJPT, GIAC
```

## The strategy (80/20)

**Three skill engines, not twenty exams.** Every certification sits on one of three engines; studying the engine counts towards all its exams.

| Engine | Path (in order) | Where to practise |
|---|---|---|
| Network + Active Directory | CPTS → CRTP → OSCP+ → CRTO → CRTE → CRTM → OSEP → OSED | Vendor labs; `./securax range` (MINILAB, 8 GB) for repetition |
| Web + code review | BSCP → OSWE | PortSwigger Web Security Academy (free), Burp Suite Professional |
| AI | COAE → OSAI | `./securax purple` and `./securax demo` against your own gateway; HTB AI Red Teamer path |

Choices that save the most time and money:
1. **CPTS before OSCP+.** It is broader on Active Directory and reporting, costs a fraction, and its Academy path doubles as your foundations. OSCP+ then becomes exam practice, not new learning.
2. **CRTP and BSCP early.** They are the cheapest credible proofs of AD depth and web skill, and both feed the expert exams.
3. **AI early (COAE in year 1).** It is your differentiator in BFSI, and you already own the lab.
4. **The OffSec 300-level certs in ONE Learn Unlimited year.** OSAI, OSWE, OSEP and OSED cost about ₹3 lakh each as single courses, but about ₹7.1 lakh together in a [Learn Unlimited](https://offsec.com/pricing) year with unlimited attempts. The planner saves unspent budget for it.
   With your numbers that is **12 certifications in about 3 years for about ₹12.7 lakh**, against about 3.6 years and ₹16.8 lakh course by course. The planner prints both.
5. **Skipped by default:** eJPT (CPTS covers it) and GIAC (about [$999 per attempt](https://unihackers.com/certifications/gcih); take one when a role asks for it).

**The weekly 80/20 split** (`certs next` prints it): 60% hands-on in the labs, 20% notes plus one practice report section (OffSec and HTB exams grade the report),
20% redoing yesterday's failures from memory. Do not binge videos.

## How the planner works

* Data: [`learning/certs.json`](../../learning/certs.json). Each cert has its hours (planning estimate for a beginner), price with a source link, prerequisites, engine and exam format.
* Order: strategic order, never before a prerequisite. When the next cert does not fit this year's money, a cheaper ready one is pulled forward. If nothing fits, the wait is shown as a **practice block** (free machines, retake buffer), never hidden.
* Money: each plan-year may spend 85% of the budget; **15% is kept for one retake**. Unspent money carries forward (`--no-carry-over` turns that off). Subscriptions (HTB Academy, Burp Pro, Learn Unlimited) are charged in each plan-year that uses them.
* Rupees: price × ₹96.5/USD × 1.21 (an assumption: 18% GST where a foreign vendor charges it, plus about 3% card forex markup). Paid personally, so there is no deduction against salary. Your invoice decides; edit the file.
* Time: hours ÷ (hours/week × 0.85 efficiency).

## Honest limits

* **Prices are a 14 Oct 2026 snapshot**, several from third parties that disagree (HTB changed its prices on 12 Oct; OffSec bundle prices vary by source). Check the vendor before paying and update `certs.json`.
* **Hours are estimates**, not promises. Re-plan with `--pace` after your first exam; that number will be the most accurate one in this file.
* Exam formats change (CRTO changed in 2025); check each exam's current rules before booking.
* Practise only on vendor labs and your own isolated range. Never on systems you are not authorised to test.
