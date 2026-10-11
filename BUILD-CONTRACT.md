# SecuRAX BUILD CONTRACT

> This file is the operating contract for ANY model building SecuRAX — a local coder, DeepSeek,
> Gemini, or Claude. It exists because **rigor comes from the process, not only the model.** A
> smaller/cheaper model that follows this contract, backed by SecuRAX's test + CI gates, produces
> reliable changes. `./securax build` feeds this file to the agent on every run.

## Prime directive
Make the **smallest correct change** that satisfies the task, prove it with the repo's own gates,
and never weaken security to get green.

## The loop (do this every task — do not skip steps)
1. **Restate** the task in one sentence. If it's ambiguous or touches >3 files, STOP and ask.
2. **Locate** the exact files/functions involved. Read them before editing. Do not guess paths.
3. **Plan** the change in 2–5 bullets. Prefer editing existing code over adding new code.
4. **Tests first.** Add or update a test that fails for the current behavior and will pass when done.
5. **Implement** the minimal diff. Match the surrounding code's style, naming, and comment density.
6. **Run the gates** (see below). Read the output. Fix until ALL are green.
7. **Re-read your own diff adversarially**: what input makes this crash or bypass a rail? Fix it.
8. **Summarize** what changed and why, in 2–3 lines, and stop. One validated change beats three.

## The gates — the quality floor (run these, they are your safety net)
```bash
ruff check .                                   # lint/format
python -m pytest -q                            # all unit tests (161+)
cd guiding-map && node build.js && cd ..       # rebuild the PWA shell (if you touched ops.js)
cd local/compose && python3 gen_litellm_config.py --baseline --write && cd ../..  # if catalog changed
docker compose -f local/compose/docker-compose.yml --profile ai config -q   # compose still valid
```
CI additionally runs gitleaks (no secrets in the diff), Semgrep/Trivy (SAST), and a build-drift
check. **A change is not done until `ruff` + `pytest` are green locally.**

## Hard rules — never violate (these are the "security must be an enabler" guarantees)
- **Never** skip, disable, delete, or `xfail` a test to get green. Fix the code instead.
- **Never** weaken the guardrail rails, loosen `FAIL_MODE`, or widen network egress to pass a task.
- **Never** commit a secret or a real key. Keys live only in git-ignored `.env`. No inline comments
  after `KEY=` lines (gitleaks reads them as values).
- **Never** hardcode a model ID where the catalog + `<ID>_MODEL` override belongs.
- **Keep the estate's invariants:** the gateway is the only front door for model traffic; local data
  stays local; every cloud provider is reached through the gateway's rails.

## When to escalate to a stronger model (Claude Opus / Sonnet)
Escalate ONLY for: a new security-sensitive design, a cross-cutting refactor, a bug you've failed to
fix after 3 honest attempts, or a change where you cannot write a test that proves correctness.
Everything else — tests, docs, config, single-file features, lint fixes, dependency bumps — stays on
the cheap/local tier. Escalation is the exception, not the default.

## Style
Terse, direct, BFSI/security context. No emoji in code or commits. Reference code as `path:line`.
Commit messages: imperative subject, a short body of what/why, and the project's attribution footer.
