#!/usr/bin/env python3
"""Set up your environment so the right thing happens by default — then forget it (doc 112).

    ./securax environment                 every set-and-forget change, the one best choice each, with the one-time steps
    ./securax environment focus money      only the changes for the struggles you name (focus, phone, money, bills, debt,
                                            routine, social, reading, move, career, space, rest)
    ./securax environment --json           the catalog as JSON (for the Life OS one-tap screen)

The principle (governance/principles.json: shape-environment, best-default, worst-day): we do not tell you "use your phone
less" or "spend less". We change the SETTING, once, so the good path is automatic and the harmful one is effort. Each entry
reverses one common struggle (mapped to a Wheel-of-Life area) into a single obvious change you make one time; the environment
then enforces it for you. Each also carries an IF-THEN plan — the single best-evidenced behaviour lever (Gollwitzer: an
if-then plan roughly doubles follow-through over a bare goal) — and, where it is a habit, a START-SMALL floor (the two-minute
rule / deliberate-practice edge: begin tiny, grow at the edge). Nothing needs willpower, nothing leaves your devices.
Standard library only.
"""
from __future__ import annotations

import json
import sys

# Each trick: reverse a struggle into the ONE best change (best-default), set once, enforced by the environment, not willpower.
# domain = its Wheel-of-Life area. if_then = the implementation intention you rehearse. start_small = the deliberate-practice floor.
CATALOG = [
    {"id": "focus", "domain": "Health · sleep", "struggle": "Can't focus; the phone pulls you in, especially at night",
     "change": "The phone goes grey and quiet at night, by itself",
     "why": "A grey, silent screen is boring, so you put it down. No decision, no willpower — the phone just stops being a slot machine after bedtime. Consistent sleep is the master keystone: it lifts mood, focus, weight and money decisions together.",
     "if_then": "If it is my bedtime, then the phone has already gone grey and silent, and I read or sleep.",
     "set_once": {
         "iPhone": "Settings → Accessibility → Per-App / Display → Color Filters on; add it to a Sleep Focus that turns on at your bedtime (Settings → Focus → Sleep).",
         "Android": "Settings → Digital Wellbeing → Bedtime mode → schedule it; turn on Grayscale and Do Not Disturb inside Bedtime mode.",
         "Keystone": "Set a FIXED wake alarm (same time daily) and get morning light — the single biggest lever on your body clock."}},
    {"id": "phone", "domain": "Personal growth", "struggle": "Doomscrolling; hours vanish into a few apps",
     "change": "The time-wasting apps are time-boxed and off the home screen; a learning app takes their place",
     "why": "If an app is three taps away and locks itself after 20 minutes, you open it on purpose, not by reflex. Swapping the cue — a book or learning app where the time-waster sat — turns the reflex toward growth.",
     "if_then": "If I reach where the time-waster used to be, then I find a learning app instead; the old one is a tap away in a folder and locks in 20 minutes.",
     "set_once": {
         "iPhone": "Settings → Screen Time → App Limits → 20 min on the two worst apps; move them off page 1 into a folder; put a learning/reading app on page 1.",
         "Android": "Digital Wellbeing → App timers → 20 min on the two worst; long-press each icon → remove from home screen; add a learning app to the home screen."}},
    {"id": "money", "domain": "Finances", "struggle": "Money disappears; nothing gets saved",
     "change": "You pay yourself first, on salary day, automatically",
     "why": "If savings leave the account the day the salary lands, you never see the money to spend it. Auto-transfer on payday is the strongest nudge there is (the same mechanism as pension auto-enrolment): it works WITH inertia instead of against it.",
     "if_then": "If my salary lands, then savings have already moved out to a separate account, before I can spend them.",
     "set_once": {
         "Any bank": "Set a standing instruction / auto-debit SIP for a fixed amount on your salary date, into a separate account or fund you do not carry a card for.",
         "Tip": "Keep only the week's spending money in the account whose card is in your wallet; the rest is one transfer away, not one tap."}},
    {"id": "bills", "domain": "Finances", "struggle": "Late fees; bills and renewals slip",
     "change": "Every bill and premium is on autopay before its due date",
     "why": "A missed due date is a fee and a credit-score ding for nothing. Autopay removes the memory step entirely — the one thing memory is worst at.",
     "if_then": "If a bill is due, then it is already paid on autopay — I never touch it.",
     "set_once": {
         "Cards & utilities": "Turn on autopay (full amount) in each bank/card/biller app, dated a day or two before the due date.",
         "Life OS": "Scan each policy/bill into the Inbox; the lens reads the due date and the estate alarms you well before, as a backstop."}},
    {"id": "debt", "domain": "Finances", "struggle": "Debt that never shrinks",
     "change": "Autopay at least the minimum everywhere; attack the costliest one",
     "why": "Autopay the minimum kills late fees and protects your score; then every spare rupee goes to the highest-interest debt, where it saves the most. One rule, no spreadsheet.",
     "if_then": "If I have a spare rupee, then it goes to the single highest-interest debt.",
     "set_once": {
         "Each loan/card": "Autopay the minimum on the due date for all of them, so none ever goes late.",
         "Then": "Point one fixed extra amount at the single highest-interest debt until it is gone, then roll that amount to the next (the avalanche)."}},
    {"id": "move", "domain": "Health · body", "struggle": "Sedentary; 'I'll start the gym' never happens",
     "change": "A daily walk, anchored to something you already do",
     "why": "The daily walk is the habit people most often wish they'd started sooner. Anchored to an existing cue, with a 'to the gate and back' floor, it needs no willpower and compounds into the biggest single health return.",
     "if_then": "If I finish lunch, then I walk — even if only to the gate and back.",
     "start_small": "Start with 'put shoes on and step outside'; the walk grows itself. Add a little at the edge once it is automatic.",
     "set_once": {
         "Life OS": "The estate schedules a daily walk at a fixed time and alarms it; a short loop counts.",
         "Anchor": "'After lunch, I walk.' Park farther away and take the stairs — make the active option the default.",
         "Phone": "Turn on daily move/step reminders (iPhone Fitness / Android Health) as a backstop."}},
    {"id": "routine", "domain": "Health", "struggle": "No routine; good habits never stick",
     "change": "One keystone habit, anchored to something you already do, with an alarm",
     "why": "A habit stuck onto an existing one (after coffee, after brushing teeth) needs no new slot in your day. The floor is two minutes, so a bad day still counts — never miss twice.",
     "if_then": "If I finish my morning coffee, then I do my two-minute keystone habit.",
     "start_small": "Two minutes is the whole habit at first; grow it at the edge once it is automatic, never before.",
     "set_once": {
         "Life OS": "Pick ONE keystone habit; the estate schedules it at a fixed time and the calendar alarm fires — you do not set the reminder.",
         "Anchor": "Say when: 'right after my morning coffee'. The old habit becomes the trigger for the new one."}},
    {"id": "career", "domain": "Career", "struggle": "Sunday dread; work goes nowhere, no visible wins",
     "change": "A protected weekly block: one skill, one reach-out, one visible win",
     "why": "Careers move on a few deliberate reps, not busywork. One guarded hour a week — learn one thing, contact one person, ship one visible result — compounds where grinding does not. Focus on the process rep you control, not the outcome.",
     "if_then": "If it is my weekly career hour, then I do exactly one: a skill rep, a reach-out, or a shipped win.",
     "start_small": "One 25-minute block to begin; grow it as it sticks.",
     "set_once": {
         "Life OS": "Block a fixed weekly hour the estate protects and alarms; the career compass names the one next move.",
         "Calendar": "Make it recurring and marked 'busy', so meetings cannot eat it."}},
    {"id": "social", "domain": "Relationships", "struggle": "Drifting from people; weak at keeping in touch",
     "change": "A standing cadence to reach the few people who matter",
     "why": "Relationships are the strongest long-run predictor of health and happiness (Harvard's 85-year study), and they fail from neglect, not malice. A gentle recurring nudge turns 'I should call them' into a two-minute message that actually happens.",
     "if_then": "If it is my weekly nudge, then I send one person a one-line message.",
     "set_once": {
         "Life OS": "List the handful of people who matter; the estate surfaces one to reach out to each week, and puts their birthdays and anniversaries in the calendar.",
         "Tip": "A one-line message beats a perfect call you never make."}},
    {"id": "space", "domain": "Environment", "struggle": "Clutter and mess pile up; the place feels out of control",
     "change": "A 10-minute daily reset, anchored to a cue",
     "why": "Order is kept by a small daily reset, not a heroic weekend clean. Anchored to an existing cue with a two-minute floor, a tidy space stops being a project and the whole place feels under control.",
     "if_then": "If I put the kettle on, then I reset one surface until it boils.",
     "start_small": "One surface, two minutes, on a bad day; never miss twice.",
     "set_once": {
         "Life OS": "The estate schedules a short daily reset and alarms it; two minutes counts.",
         "Anchor": "'While the kettle boils / coffee brews, I clear one surface.'"}},
    {"id": "rest", "domain": "Fun & recovery", "struggle": "Burnout; rest and fun never get scheduled, so they never happen",
     "change": "Protected recovery blocks on the calendar — recovery is training, not a reward",
     "why": "Elite athletes periodize: they plan recovery into every cycle, because gains happen DURING recovery, not only under load. A protected rest/fun block, and a planned light week, prevent the burnout that erases months of progress.",
     "if_then": "If it is my protected rest block, then I do the restful thing — I do not catch up on work.",
     "set_once": {
         "Calendar": "Put a weekly recovery/fun block in as 'busy' and protect it like a meeting; plan one small thing to look forward to.",
         "Life OS": "Mark a lighter 'deload' week every 4–6 weeks; a habit missed in it is planned rest, not failure."}},
    {"id": "reading", "domain": "Personal growth", "struggle": "Hard to read or concentrate on text (dyslexia, ADHD, tired eyes)",
     "change": "The estate reads to you, in big calm type, and reads your documents for you",
     "why": "If the system does the reading and the typing, a learning difference stops being a barrier to running your life. Scan a paper and it is read, classed and dated for you.",
     "if_then": "If I need to take in a document, then I scan it or have it read aloud — I do not type it out.",
     "set_once": {
         "Life OS": "Scan documents instead of typing (📷 on the Inbox); turn on larger text in the app's settings.",
         "Phone": "iPhone: Settings → Accessibility → Spoken Content → Speak Screen. Android: Settings → Accessibility → Select to Speak / TalkBack."}},
]

TAGS = [c["id"] for c in CATALOG]


def for_struggles(tags):
    """The best changes for the struggles named by id or Wheel-of-Life domain word; empty means 'all', unknown matches nothing."""
    want = [t.lower() for t in tags if t and not t.startswith("-")]
    if not want:
        return list(CATALOG)
    return [c for c in CATALOG if c["id"] in want or any(w in c["domain"].lower() for w in want)]


def _print(entries):
    if not entries:
        print("No match. Known struggles: " + ", ".join(TAGS))
        return
    for c in entries:
        print(f"\n■ [{c['domain']}] {c['struggle']}")
        print(f"  → {c['change']}")
        print(f"    {c['why']}")
        print(f"    If-then: {c['if_then']}")
        if c.get("start_small"):
            print(f"    Start small: {c['start_small']}")
        print("    Set it once:")
        for where, how in c["set_once"].items():
            print(f"      · {where}: {how}")
    print("\nThat is the whole point: set each one once, then forget it. The environment keeps you on the good path.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--json" in argv:
        print(json.dumps({"about": "Set-and-forget environment changes mapped to the Wheel of Life (doc 112).", "catalog": CATALOG}, ensure_ascii=False, indent=1))
        return 0
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    _print(for_struggles(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
