#!/usr/bin/env python3
"""Set up your environment so the right thing happens by default — then forget it (doc 112).

    ./securax environment                 every set-and-forget change, the one best choice each, with the one-time steps
    ./securax environment focus money      only the changes for the struggles you name (focus, phone, money, bills, debt,
                                            routine, social, reading)
    ./securax environment --json           the catalog as JSON (for the Life OS one-tap screen)

The principle (governance/principles.json: shape-environment, best-default, worst-day): we do not tell you "use your phone
less" or "spend less". We change the SETTING, once, so the good path is automatic and the harmful one is effort. Each entry
below reverses one common struggle into a single obvious change you make one time; the environment then enforces it for you.
Nothing here needs willpower, and nothing leaves your devices. Standard library only.
"""
from __future__ import annotations

import json
import sys

# Each trick: reverse a struggle into the ONE best change (best-default), set once, enforced by the environment, not by willpower.
CATALOG = [
    {"id": "focus", "struggle": "Can't focus; the phone pulls you in, especially at night",
     "change": "The phone goes grey and quiet at night, by itself",
     "why": "A grey, silent screen is boring, so you put it down. No decision, no willpower — the phone just stops being a slot machine after bedtime.",
     "set_once": {
         "iPhone": "Settings → Accessibility → Per-App / Display → Color Filters on; add it to a Sleep Focus that turns on at your bedtime (Settings → Focus → Sleep).",
         "Android": "Settings → Digital Wellbeing → Bedtime mode → schedule it; turn on Grayscale and Do Not Disturb inside Bedtime mode."}},
    {"id": "phone", "struggle": "Doomscrolling; hours vanish into a few apps",
     "change": "The time-wasting apps are time-boxed and off the home screen",
     "why": "If an app is three taps away and locks itself after 20 minutes, you open it on purpose, not by reflex. The default becomes 'not now'.",
     "set_once": {
         "iPhone": "Settings → Screen Time → App Limits → 20 min on the two worst apps; move them off page 1 into a folder.",
         "Android": "Digital Wellbeing → App timers → 20 min on the two worst; long-press each icon → remove from home screen."}},
    {"id": "money", "struggle": "Money disappears; nothing gets saved",
     "change": "You pay yourself first, on salary day, automatically",
     "why": "If savings leave the account the day the salary lands, you never see the money to spend it. Saving stops being a monthly decision you lose.",
     "set_once": {
         "Any bank": "Set a standing instruction / auto-debit SIP for a fixed amount on your salary date, into a separate account or fund you do not carry a card for.",
         "Tip": "Keep only the week's spending money in the account whose card is in your wallet; the rest is one transfer away, not one tap."}},
    {"id": "bills", "struggle": "Late fees; bills and renewals slip",
     "change": "Every bill and premium is on autopay before its due date",
     "why": "A missed due date is a fee and a credit-score ding for nothing. Autopay removes the memory step entirely — the one thing memory is worst at.",
     "set_once": {
         "Cards & utilities": "Turn on autopay (full amount) in each bank/card/biller app, dated a day or two before the due date.",
         "Life OS": "Scan each policy/bill into the Inbox; the lens reads the due date and the estate alarms you well before, as a backstop."}},
    {"id": "debt", "struggle": "Debt that never shrinks",
     "change": "Autopay at least the minimum everywhere; attack the costliest one",
     "why": "Autopay the minimum kills late fees and protects your score; then every spare rupee goes to the highest-interest debt, where it saves the most. One rule, no spreadsheet.",
     "set_once": {
         "Each loan/card": "Autopay the minimum on the due date for all of them, so none ever goes late.",
         "Then": "Point one fixed extra amount at the single highest-interest debt until it is gone, then roll that amount to the next (the avalanche)."}},
    {"id": "routine", "struggle": "No routine; good habits never stick",
     "change": "One keystone habit, anchored to something you already do, with an alarm",
     "why": "A habit stuck onto an existing one (after coffee, after brushing teeth) needs no new slot in your day. The floor is two minutes, so a bad day still counts — never miss twice.",
     "set_once": {
         "Life OS": "Pick ONE keystone habit; the estate schedules it at a fixed time and the calendar alarm fires — you do not set the reminder.",
         "Anchor": "Say when: 'right after my morning coffee'. The old habit becomes the trigger for the new one."}},
    {"id": "social", "struggle": "Drifting from people; weak at keeping in touch",
     "change": "A standing cadence to reach the few people who matter",
     "why": "Relationships fail from neglect, not malice. A gentle recurring nudge to message one person turns 'I should call them' into a two-minute action that actually happens.",
     "set_once": {
         "Life OS": "List the handful of people who matter; the estate surfaces one to reach out to each week, and puts their birthdays and anniversaries in the calendar.",
         "Tip": "A one-line message beats a perfect call you never make."}},
    {"id": "reading", "struggle": "Hard to read or concentrate on text (dyslexia, ADHD, tired eyes)",
     "change": "The estate reads to you, in big calm type, and reads your documents for you",
     "why": "If the system does the reading and the typing, a learning difference stops being a barrier to running your life. Scan a paper and it is read, classed and dated for you.",
     "set_once": {
         "Life OS": "Scan documents instead of typing (📷 on the Inbox); turn on larger text in the app's settings.",
         "Phone": "iPhone: Settings → Accessibility → Spoken Content → Speak Screen. Android: Settings → Accessibility → Select to Speak / TalkBack."}},
]

TAGS = [c["id"] for c in CATALOG]


def for_struggles(tags):
    """The best changes for the struggles named; unknown tags are ignored, an empty list means 'all'."""
    want = [t.lower() for t in tags if t and not t.startswith("-")]
    if not want:
        return list(CATALOG)
    return [c for c in CATALOG if c["id"] in want]


def _print(entries):
    if not entries:
        print("No match. Known struggles: " + ", ".join(TAGS))
        return
    for c in entries:
        print(f"\n■ {c['struggle']}")
        print(f"  → {c['change']}")
        print(f"    {c['why']}")
        print("    Set it once:")
        for where, how in c["set_once"].items():
            print(f"      · {where}: {how}")
    print("\nThat is the whole point: set each one once, then forget it. The environment keeps you on the good path.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--json" in argv:
        print(json.dumps({"about": "Set-and-forget environment changes (doc 112).", "catalog": CATALOG}, ensure_ascii=False, indent=1))
        return 0
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    _print(for_struggles(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
