# LESSONS.md: what went wrong before, so it does not again

One line each: what happened → what to do instead. Newest last. Add with `./securax lessons add "…"`;
autobuild adds one by itself when a red attempt turns green. Keep lines short: every agent reads this file.

<!-- lessons:start -->
- 2026-10-17 fitness: a new file passed locally but failed the impact-map check in CI because it was untracked → `git add -A` before `python3 -m lifecycle.fitness`.
- 2026-10-17 cockpit: a loop variable named `c` shadowed render()'s config and crashed the page → never reuse a short outer name inside a loop; the cockpit_page journey catches it.
- 2026-10-17 pwa: build.json was fetched under file:// and badge checks expected exact text → fetch only over http(s); assert on stable parts (release, commit), not whole strings.
- 2026-10-18 readme: the README block regex did not match an empty block → test generators on the empty case too.
- 2026-10-19 pwa: a 60 s setInterval kept the jsdom test (which waits for the event loop) alive forever → arm timers only when the feature is on.
- 2026-10-19 pii: an all-zero GUID in a test matched the card-number rule → use non-numeric fake ids in fixtures.
- 2026-10-19 pwa: goals created by the quarterly check-in had no timestamp, so "idle" read as since 1970 → stamp every creation path, and treat a missing time as now.
- 2026-10-19 ux: the cockpit hint printed `./securax controls import FILE.xlsx`; users typed it as is and got a traceback → never print a placeholder without a fallback that finds the file.
- 2026-10-19 ux: gold text on the light theme's grey failed contrast (2.0:1) → run ui_audit.py after every PWA style change; use dark text plus a gold mark in light mode.
- 2026-10-19 site: adding a header item pushed the button off a 390 px screen → check scrollWidth at phone width after any header change.
- 2026-10-19 ci: each push to an open PR restarts the 40-minute sandbox → batch commits, and push once per round.
- 2026-10-19 cockpit: the setup card printed https:// step links and failed cockpit_page (the page must name no external URL) → strip the scheme in anything rendered into the cockpit
- 2026-10-19 sandbox: adding a sixth compliance map broke comply_evidence, which counted exactly five → when adding a map, update the count in sandbox/run.py
<!-- lessons:end -->
