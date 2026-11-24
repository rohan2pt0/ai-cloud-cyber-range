# Queue plan, 2026-11

The owner approved a re-plan of `governance/queue.json` on 2026-11-24. Dates had been set one at a time and never checked against what the builders can merge (about 8 to 10 changes a day). Now every open ask has a score, a place and a date that fits.

**How it works.** Score = risk x reach / effort, each 1 to 5, stored as `rre`. Hard gates (no single point of failure, security, recoverability, legal before launch) come first whatever the score (`gate`). Builders get 8 slices of work a day (effort + 1 slices per item). Asks only the owner can finish carry `needs: owner`, with a soft date. Everything else has a `horizon` and `due` set to that period's last day.

**Counts.** 208 open before, 33 merged away, 175 open now: 58 Now (28 gates + top 30), 55 in 2027-Q1, 55 in 2027-Q2, 7 later. 24 need the owner.

## Now, in order (2026-11-25 to 2026-12-20)

No single point of failure and 24x7 (gates, first):

1. `routine-repo-attach` 11-25: the daily build routine never starts blind.
2. `second-static-host` 11-25: the site and apps stay up if one host fails.
3. `ci-download-resilience` 11-25: a GitHub download error no longer turns CI red.
4. `delegate-reliability` 11-26: delegated builds finish, with less Claude.
5. `chat-history-shared` 11-26: a chat survives the machine it began on.
6. `autobuild-ci-key` 11-28 (owner): builds keep running after a session ends.
7. `open-model-second-provider` 11-30 (owner): one builder outage no longer stops work.
8. `gitlab-mirror` 12-02 (owner): the code has a second home.
9. `builder-no-money-spof` 12-04 (owner): builders stay up when one plan or credit runs out.
10. `always-on-real-vps` 12-06 (owner): sync and access work with the laptop off.
11. `off-paid-claude` 12-08 (owner): building does not depend on paid Claude.

Security and recoverability (gates):

12. `ai-gap-g14` 11-27: the audit trail survives restarts, anchored daily.
13. `app-lock` 11-27: private details stay behind the lock.
14. `pin-actions-by-commit` 11-28: build steps cannot be swapped under us.
15. `ai-gap-g9` 11-28: provider keys leave plain text.
16. `soc-auth-refusal-alerts` 11-29: a forged key or refused caller raises an alert.
17. `own-origin-hosting` 11-29: apps get proper security headers.
18. `ref-bar-supply-chain` 11-30: signed releases with an SBOM.
19. `threat-models-by-risk` 12-01: the riskiest parts are threat-modelled.
20. `golive-first-run` 12-10 (owner): the go-live runbook proven on real machines.

Legal before launch (gates):

21. `third-party-notices` 12-01: bundled software is credited properly.
22. `privacy-notice` 12-02: a published privacy notice, disclaimers and the education line.
23. `abuse-coercive-setup` 12-02: the apps cannot easily be used to spy on someone.
24. `launch-owner-attests` 12-12 (owner): the two launch confirmations only the owner can give.
25. `name-clearance` 12-14 (owner): the name and trademark are clear to use.
26. `liability-cover` 12-16 (owner): indemnity cover and capped contract liability.
27. `licence-review` 12-18 (owner): what is sold matches each licence.
28. `paid-terms` 12-20 (owner): published terms, GDPR scope and the paid-advice line before anyone pays.

Top 30 by score:

29. `build-freeze-live-first` 12-03: time to live with the apps, not only build.
30. `github-api-backoff` 12-03: busy rounds stop tripping GitHub limits.
31. `dependabot-round` 12-03: waiting security updates are handled.
32. `open-model-budget` 12-04: the monthly builder cap is not spent in a day.
33. `audit-round-1` 12-04: safety, correctness and real-day audits, one ask.
34. `owner-frictions-goals-ask` 12-05: Goals and Ask stop annoying.
35. `one-open-action-2` 12-05: one clear next step on every screen.
36. `validation-rest` 12-06: impossible numbers are refused everywhere.
37. `contradiction-guard` 12-06: contradictory answers are caught.
38. `essentials-first` 12-07: the person knows the few values that matter.
39. `keys-in-command-center` 12-07: no terminal to add AI keys.
40. `wsl-user-without-opening-ubuntu` 12-08: Windows install needs no Ubuntu step.
41. `explainer-own-fonts` 12-08: the tour works offline.
42. `calendar-subscribe` 12-08: deadlines reach the calendar by themselves.
43. `spend-guard` 12-09: rupee caps on AI cost.
44. `estate-gap-gates` 12-09: the remaining gap classes get a gate.
45. `setup-one-command` 12-10: one command to set up a machine.
46. `deterministic-backbone` 12-11: code decides, AI proposes.
47. `delivery-four-keys` 12-11: delivery measured in `progress`.
48. `ip-contributor-terms` 12-12: outside work is licensed cleanly.
49. `codex-builder-trial` 12-12: a trial of one more builder.
50. `life-papers-first-import` 12-13: private papers read into the Life OS.
51. `enterprise-sweep-components` 12-14: the five-lens review of every component.
52. `life-papers-upload` 12-15: upload papers from the phone.
53. `ai-gap-g15` 12-15: retrieval respects document owner and class.
54. `ai-gap-g3` 12-16: tool calls wait for approval.
55. `pr-321-review` 12-16: a stuck review ledger slice settled.
56. `trust-pack` 12-17: a trust page and questionnaire pack.
57. `ai-install` 12-17: install by pasting one sentence.
58. `calm-and-real` 12-18: calmer, truer lock-screen visuals.

## Owner actions

Gates above with `(owner)`, plus these 12 later asks: `commercial-lead`, `owner-github-settings`, `one-door-primary-identity`, `door-access-bypass`, `licence-holder-company`, `discovery-30-days`, `cloud-seedbank-first-apply`, `signed-official-content`, `multilingual-review`, `real-phone-check`, `site-on-own-domain`, `store-submission`. Builders prepare the rail and the exact step first, then the owner does the account, money or legal part. Dates on these are soft.

## Merges (survivor, then the asks folded into it)

- `design-premium-review`: luxury-standard, maison-finish, world-class-pass, visual-standard-v2, lux-real-polish
- `audit-round-1`: audit-round-2, audit-round-3, 360-audit-rounds, test-campaign-2, kaizen-2
- `ai-gap-g6`: ai-gap-g7; `spend-guard`: ai-gap-g16
- `one-door-accounts-panel`: one-door-aws-federation, one-door-drive-consent
- `privacy-notice`: disclaimers, sebi-education-line; `paid-terms`: gdpr-scope, sebi-paid-opinion
- `multilingual`: launch-languages, i18n-quality; `multilingual-review`: language-pro-review; `global-ready-rail`: rtl-ready
- `name-clearance`: ip-trademark; `threat-models-by-risk`: paid-threat-model
- `easy-start`: start-simple-2; `wheel-systems`: life-systems, systems-not-theory, instructions-to-systems
- `felt-vs-measured`: measured-not-scored; `expert-council`: profession-packs
- `calendar-subscribe`: deadlines-in-calendar; `model-trust-routing`: open-weight-lab; `nature-atlas`: nature-elements-2

## Later

| Horizon | Open asks | Due field |
|---|---|---|
| 2027-Q1 | 55 | 2027-03-31 |
| 2027-Q2 | 55 | 2027-06-30 |
| later | 7 | 2027-12-31 |

Rule for the next session: take the top of Now; when it is empty, pull the highest-scoring 2027-Q1 asks forward. Re-run this plan monthly.
