# 48 · The Guiding Map, freeze-ready: a quarterly system you will actually run

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** UI audit with 30 days of realistic data. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Written from the owner's own screenshots and requests (15 Oct 2026). The aim: freeze the app and use it, not research it further.

## First: the phone was running an old copy

The screenshots showed **V13.0.2** and the old 15-tab layout. Current SecuRAX shows **v0.1.0** and opens on Calm mode (doc 47).
An installed web app keeps the copy from the address it was installed from, so the phone was not getting any of these changes.
Your data lives with that old copy. To move it:

1. In the **old** app: Ops → System health → **Export one now** (a dated `.json` file lands in Downloads).
2. On the phone, open the **estate** address (the one `./securax open` prints; from a phone that is your estate's address over Tailscale, doc 14), and install it (Add to home screen).
3. In the new app: Ops → System health → **Restore from file**, pick the `.json`.
4. Check that Today shows your name and history, then remove the old icon.

## What changed

| You said | Now |
|---|---|
| Quarterly OKRs too complicated (sliders, typing) | **Quarterly check-in**, about 5 minutes, all taps: grade last quarter (one tap per result: Not started / A little / Half / Most / Done), rate the 8 areas of life (1 to 10), pick up to 3 goals **suggested from your lowest scores**, each with two measurable results already written. Progress once a month: one tap per result. |
| Wheel of life: same problem | It is step 2 of the same check-in: 8 taps, last quarter's score shown. |
| Make it "a system" in my calendar | **Add the rhythm to my calendar** writes one `.ics` with 5 repeating events, each with what to do written inside and a 30-minute reminder: quarterly check-in (1st Saturday of Jan/Apr/Jul/Oct), monthly review (1st Sunday: money + After-Action Review), Sunday Pulse, April tax lock-in, August overhaul. Already added them by hand? Skip it. |
| After-Action Review: never knew when | It is now a **monthly ritual**: from the 24th it shows in Today → Due now, and the monthly calendar event names it. Four questions, one cause, one change. |
| Child development | Add a child right on the Kids tab (name and date of birth). Each child gets **this quarter's three actions** for their age (tick them) and the **monthly SIP** that funds their education (assumptions stated: 10% education inflation, 12% equity return; cost editable). |
| Undo: what does it do, and it never goes away | It said "14948 min ago": it kept a 10-day-old snapshot, and tapping it would have **wiped ten days of entries**. Now it is offered for 30 minutes only, says "Undo puts everything back as it was before that", has a ×, and an old one can never roll anything back. |
| "When it goes wrong" buttons cannot be reverted | Pausing now **asks first**; while paused, Ops says until when and offers **End it now**. |
| Ops: many things I do not understand (cues, WOOP card, NIST CSF score) | Ops opens with **Quarterly check-in** and **Add to calendar**, then System health. Everything else is folded: *The rhythm*, *When it goes wrong*, *Connections* (sync, Microsoft 365, phone reminders, all optional, explained in one line), *Advanced tools* (WOOP card, cue check, NIST CSF self-score, and the rest: nothing there is needed day to day), *Glossary*. |
| Integrations: are these the right parameters? | They were **copy-in boxes labelled as automatic** ("Auto-fills", "Pulls on refresh"). A web app on a phone cannot read your bank, health or fund apps. They now say so, use Indian/Android sources (Health Connect / Google Fit / Fitbit; your bank or a Sahamati-registered Account Aggregator app; CAMS / KFintech CAS or MF Central), and say how often (weekly or monthly). Optional: skip them and nothing breaks. |
| Dark mode: blurred, unreadable text | A contrast checker measured every visible text on every tab in both themes with realistic data: **439 failures**. The worst was navy text on navy cards in dark mode. Now **0** (WCAG AA). |
| (found) Runway "274219.5m" | A "lakh" field typed in rupees. Values over 10,000 in lakh fields are now read as rupees; runway caps at "120m+". |

## Proof

* `guiding-map/tests/test18.js`: 28 checks (the check-in flow, the 3-goal limit, progress taps, the calendar file format, the AAR ritual, the folded Ops, the Undo expiry, the pause question, kids add and tick, integration wording, runway).
* `guiding-map/tests/ui_audit.py`, run by the sandbox journey **`guiding_map_full_use`**: a real browser does what a person does with realistic data, then visits every tab in dark and light mode. It passes only with 0 failed checks, 0 page errors and 0 text below contrast minimum. It found the stale Undo still offered in System health, the dark-mode navy-on-navy text and a light-mode gold-on-navy regression of my own; all fixed before shipping.
* All earlier Guiding Map suites pass.

## Not changed on purpose

Nothing was deleted: every advanced tool still works, it is folded. The app's own rule stands: use it for a month before adding anything.
