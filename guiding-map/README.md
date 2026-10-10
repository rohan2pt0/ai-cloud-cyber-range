# Guiding Map — your local-first home screen

The one screen you actually use every day. Tasks, your local AI, money, OPSEC, continuity —
all in a single installable app. **Your data lives only on your device** (browser storage);
nothing is sent anywhere unless you tap a cloud action.

## Use it
It starts automatically with the estate:
```bash
./securax up && ./securax open      # Mac/Linux
# Windows: double-click START-HERE-Windows.bat
```
Then open **http://localhost:8088** and tap **Install** (or "Add to Home Screen") to use it
like a native app — it works offline too.

## What's inside
- **Today** — your top tasks by Eisenhower quadrant + a 10-minute shutdown ritual.
- **Ask** — your local AI (via the guardrail gateway); Red data stays on your machine.
- **Launch** — one tap to chat, private docs, automations, the visual tour.
- **Money** — a private FIRE (financial independence) calculator, Indian context.
- **Guard** — on-device footprint scan + an OPSEC checklist.
- **Vault** — continuity notes, with one-tap **Export** backup (3-2-1 your data).

## Make it yours
It's one file (`index.html`) with no build step. Edit the `LAUNCH`, `SHUT`, or `OPSEC`
arrays near the bottom to change the quick-links and checklists. Bump `CACHE` in `sw.js`
after edits so the offline copy refreshes. That's the whole maintenance story.
