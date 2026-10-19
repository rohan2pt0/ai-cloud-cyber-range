# 74 · Pattern interrupt: in a heavy week, the Life OS subtracts

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested (test25, 13 checks): the heavy-week check, the one-card interrupt, the recovery-mode planning lock and AI guard, and the repeat-question notice. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The loop it breaks.** In a saturated week the reflex is to ask for a new system, build it for a week or two, and drop it. The new system is itself a symptom, so a planning tool that says "yes, here is a better plan" makes the week worse. The fix is to write down your failure modes rather than your aspirations, and to have the tool hold itself back at the right moment.

## What the app does

1. **It notices the signs, on the device only.** Over the last 7 days it counts:
   - daily notes and questions to the AI that use heavy-week words, such as "overwhelmed", "exhausted", "can't sleep", "a mess" or "fix everything"
   - days you tapped energy 1 or 2

   You can edit the words in Ops → When it goes wrong. Nothing is sent anywhere for this check.
2. **At 3 signs, Today opens with one card and nothing to plan:**
   - **One question:** for example, "Which of this week's commitments could wait a fortnight without real harm?"
   - **One small thing:** for example, "Walk for 20 minutes today, phone left at home."
   - **Book 3 hours of rest:** a calendar file for Saturday 14:00–17:00.
   - **Pause everything but the daily three for 7 days**, or **Not now**, which hides the card for 3 days.
3. **In recovery mode, new plans wait:**
   - **New goals:** adding a goal, a key result or a quarterly check-in shows a short note instead of opening the form. Your existing goals stay where they are.
   - **The AI:** it is told not to give a plan, framework, KPI, OKR or checklist.
   - **The guard is code, not only a prompt:** an answer that still contains one, or runs past 160 words, is replaced with one question and one small action. A prompt alone is not a control.
4. **"You have asked this before."** When a question to the AI closely matches an earlier one, the answer starts with a line saying so, with the dates:
   - **The check:** word overlap of half or more.
   - **The history:** the last 80 questions, kept on the device and in your encrypted sync.

## What it does not do

- **It does not diagnose anything.** It counts words and taps. If sleep problems, chest pain or anxiety keep coming back, see a doctor that week.
- **It never stops the daily three, and never deletes a goal.**

## Where the idea came from

- **The source:** a personal Life OS design, shared privately, built around a "pattern interrupt" agent. On 3 heavy-week signs in 7 days it pauses the planning agents and returns only one question, one recovery action and one rest block, with a code-level guard against planning words.
- **What was taken:** the pattern only, written for this app. No personal data from that design is in this repository.
- **The test:** `guiding-map/tests/test25.js` (13 checks).
