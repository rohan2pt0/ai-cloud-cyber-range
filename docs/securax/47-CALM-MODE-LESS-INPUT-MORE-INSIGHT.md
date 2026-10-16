# 47 · Calm mode: less input, more insight (the Guiding Map, reviewed as a user)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built into the Guiding Map and tested. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

The complaint was right: the app asked for too much and gave back too little time to act on what it said.
This is what a review from the user's chair found, and what changed.

## What the review found (measured on a 412 px phone screen, first open)

| Finding | Before |
|---|---|
| First thing you can tap on Today | about 700 px down, under three banners, a header, ten numbers and a stage card |
| Same habits asked twice | the Daily Three (Move, Mind, Family) and again a five-habit list with anchors and science text |
| Checklists shown when not needed | the full Quarterly Review and Red-Team lists, every day of the month they are due |
| Insight overload | nine "Live Insights" cards, most of them "set this up" reminders |
| Setup | a 20-field form, and the Life Map then asked for income and net worth again (two data models, same numbers) |
| Navigation | 21 tabs |
| Example data trap | invented spouse, child, parent and a ₹30 lakh example home loan kept steering insights until every field was overwritten |
| Today page length | 3,675 px |

## What changed: Calm mode (the default; one tap "Show everything" brings the full app back)

Today is now, top to bottom:

1. **Four quick questions, once** (age, take-home, spending, savings + investments), one per screen, each skippable. Each answer is written into
   **both** data models. When you finish, example-only values (people, loans) are removed so they stop steering your insights.
2. **Check in with taps**: the Daily Three, the other habits as one-tap chips, an optional energy tap (1 to 5), an optional one-line note. No form.
3. **Your one open action** (unchanged: the stack still decides what is next).
4. **Due now**: one line per ritual that is actually due, with Open and Done. The checklist only unfolds when you open it.
5. **This week, worked out for you**: computed on the device from your taps (check-in rate against last week, strongest habit, the one slipping, average energy).
   **"Review my week with my estate AI"** sends that summary to *your* SecuRAX gateway (guardrails on) and shows a three-part review: what worked,
   what slipped, one smaller change. Notes containing ID numbers are never sent. If the gateway is not reachable, it says so; the on-device summary stays.
6. **From your estate**: up to four lines SecuRAX already knows (cockpit red items with their fix, the certification you are on and its exam-by date,
   backup age and encryption). Nothing to type.

Tabs: Today, Ask, Life Map, Money Map, Ops, and **More** for the rest. The help, stage and gamification banners and the duplicate header numbers are folded away; the vitals bar stays.

Measured after: Today is **1,603 px** (was 3,675), the first tap is at **220 px** (was about 700), and **0 typed fields** are needed on a normal day.

## Honesty fixes found while testing as a new user

* **Day-one scolding (an older bug):** on its first run, habit strength looked back 60 days and counted every day *before you installed the app* as a miss,
  so a new user read "budget used, floor is mandatory". It now starts from your first check-in.
* **The week counts only days since you started** ("Check-ins over your first 2 days: 60%"), and nothing is called "slipping" before 3 days of data.
* **Saving rate from your two answers:** with no savings split entered yet, it is (take-home minus spending) ÷ take-home instead of a blank. Runway stays "—" until you give an emergency fund figure: it is not guessed.

## The estate side: `./securax lifefeed`

```bash
./securax lifefeed --print     # writes portal/estate-feed.json; served at /portal/estate-feed.json next to the cockpit
```
It runs automatically after every cockpit refresh, so after `./securax up`. It contains no amounts, names or keys, and it never repeats something the cockpit already said.

## Proof and limits

* `guiding-map/tests/test17.js` (28 checks in a real DOM): Calm mode is the default; banners, the duplicate list and the insight wall are hidden; 5 tabs plus More;
  energy is one tap; the quick setup writes both models, converts net worth to lakh, clears example markers and removes example people and loans; a skipped question changes nothing;
  the week summary comes from taps; Show everything and back; the AI review goes only to the estate gateway and never sends an ID number; an unreachable gateway is said plainly.
* `governance/tests/test_lifefeed.py` (7): urgent first, no duplicates, nothing personal, atomic write, corrupt sources never crash it.
* Every earlier Guiding Map suite still passes, including habit strength, which a first version of this change broke (the strength score only updated while its bars were drawn). The test caught it.
* **Not measured:** whether a month of daily use actually feels lighter. That is the README's own rule ("a month of daily use demonstrating the gap"). Use it for a month and tell me which tap you skip.
