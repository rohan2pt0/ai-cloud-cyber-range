# Fable autopilot

One short prompt, pasted unchanged into a new Fable session each time. Each session takes the first task marked
**next**, does only that, marks it done, marks the following task **next**, pushes and opens one PR. The owner never has
to come back to a navigator between runs.

The prompt to paste (Fable, Medium effort, a new session each time):

> Read docs/specs/fable-autopilot.md from branch claude/queue-calm-and-real-zero-setup-3jgb9b (git show; if it is on
> main, read it there). Do the one task marked next, following the Rules in that file exactly. Then edit that file on
> your new branch: mark the task done with your PR number, mark the following task next. Push, open one PR, and end
> with: what you did in five lines, what you did not run, and "Paste the same prompt again for the next task."

## Rules (every task)

- **Files, not chat:** specs, content as data (`guiding-map/levers/*.json`, with `verified`, `review`, `confirm`,
  `where`), and short test-first briefs an open model can finish in 20 minutes. Never change app code
  (`guiding-map/*.html`, `ops.js`, `apps/`).
- **A new branch from main.** Read the content of open PR branches with `git show` when you need it; never merge them.
  Commit and push after each file, so a stop loses nothing.
- **Verify before you write a fact:** web-search scheme rules, laws, amounts and numbers; cite sources; mark anything
  unverified with a `confirm` line. India first, a Global note where it differs.
- **Privacy:** no real names, places, employers or personal figures; fake examples only. `./securax privacy check`
  before the last push.
- **Gates:** `ruff check .`, then `git add -A`, then `python3 -m lifecycle.fitness`. A CHANGELOG line under
  [Unreleased]; `python3 tools/readme_sync.py`. Say what you could not run.
- **Budget:** stay under 60% of context. If told "stop", push what you have and open the PR at once.
- **No merging, no PR subscriptions.**

## Tasks, in order (highest value per token first)

1. **done (PR #311).** **Life systems, content.** Write `guiding-map/levers/life-systems.json` and `docs/specs/life-systems.md`
   (max 4 pages). Cover health (check-ups by age and sex, with rough costs and where to get them; vaccinations; the
   family health calendar), family (children's milestones, parents' care, the partner's weekly time), career (the
   ladder, offers, renewals), learning (one skill a quarter), home (a monthly reset, seasonal maintenance). Each one is
   a loop (cue, smallest step, visible reward, environment, review, its one constraint) with persona cases (the
   distracted, the ADHD, the novice, the expert). Add 6 briefs to `docs/specs/life-systems-briefs.md`.
2. **next.** **Profession packs, archetypes 5 to 10.** Extend `guiding-map/levers/professions.json` (same shape as the first
   four): founders and business owners; investors and finance; aviation, defence and intelligence; volatile short
   careers (athletes, actors, media, authors); research and academia; technical specialists. Verify each licence or
   renewal rule; mark the rest confirm.
3. **More savings levers.** Extend `guiding-map/levers/levers.json`: the 10 largest states' own schemes (energy,
   transport, health, education, women, seniors), scholarships, insurance cost cuts, energy tariffs, and a Global set
   (no country assumed). Same fields as the existing levers; cite every source.
4. **Growth templates for income.** `guiding-map/levers/growth.json` and `docs/specs/growth.md`: a personal-brand
   system (LinkedIn cadence and post templates, a one-page site found by search, outreach scripts, a weekly loop), a
   side-income ladder that respects employment and conduct rules, and drafts a local model writes but never sends
   without a tap.
5. **Contradiction guard and the remaining validation.** `docs/specs/contradiction-guard.md` with one rule table
   (each conflict, the question asked, the two buttons) and every remaining field's rule (money cards, Kids, Commit,
   OKR key results, Inbox amounts, Life Map flow fields) as test-first briefs.
6. **Review sweep.** Read the open PRs' diffs (`gh` is not available: use `git show`/`git diff` on their branches) as
   a senior reviewer. Write `docs/specs/review-sweep.md`: per PR, merge / fix first / hold, the risks, and a merge
   order. Change nothing else.
7. **Threat models for what ships next.** For the native apps, the updater, hosted sync at scale and the scheme watch's
   auto-draft: one model each in `governance/threat-models.json` (all six STRIDE ways, evidence or a dated acceptance).

When the list is done, the session writes the next seven tasks itself, ranked the same way from
`governance/queue.json`, and marks the first **next**.
