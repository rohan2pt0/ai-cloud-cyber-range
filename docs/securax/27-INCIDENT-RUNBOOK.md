# 27 · Incident runbook — what to do, in order

Three situations, one page. Everything is a command; nothing needs thinking at 2 a.m.

## A. An API key was exposed (pasted in chat/screenshot/git, or a provider emailed you)
1. **Revoke it at the provider first** (the key is dead the moment you do):
   Gemini https://aistudio.google.com/apikey · Groq https://console.groq.com/keys · OpenRouter https://openrouter.ai/keys · OpenAI https://platform.openai.com/api-keys · others: provider console → API keys.
2. Make a new key there, then in Ubuntu: `cd ~/securax && ./securax keys` (or `./securax providers add`) and paste it (typing is hidden).
3. Check for misuse in the provider's usage page for the exposure window.
4. If it was in a git commit: rotation (step 1) is the fix; rewriting history does not un-leak a key.
5. Prevention already in place: keys are typed silently, `.env` is owner-only and git-ignored, gitleaks runs in CI.

## B. "Everything is blocked" / chat returns an error
1. `./securax doctor` — it names the broken layer (router, gateway, detector, model).
2. `./securax up` — repairs the usual causes (stale Llama Guard, missing config, dead container) and waits for READY.
3. Still broken: paste the whole `doctor` output to your build agent / to me. Do not rebuild anything.

## C. Suspected data exposure or misuse of the AI plane
1. Contain: `./securax down` (stops everything; nothing is reachable).
2. Preserve: `./securax backup` (keeps the data) and copy `watch.log` + the gateway audit log (`docker compose logs gateway > gateway-audit.txt` from `local/compose`).
3. Rotate every key (A) and the sync token (`./securax setup` regenerates `SYNC_TOKENS`).
4. Assess against your obligations (for a regulated entity: CERT-In 6-hour reporting, RBI/SEBI notification, DPDP breach intimation) with your compliance/legal team — SecuRAX provides the evidence trail, not the legal determination.
5. Recover: restore from a known-good backup (`./securax restore <file>`), then `./securax up`.
