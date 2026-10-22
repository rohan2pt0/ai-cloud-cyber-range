# Contributing to SecuRAX

Thanks for taking the time to look — this project exists partly *to be pressure-tested by the
community*. Whether you break it, extend it, or just fix a typo, you're welcome here.

> **TL;DR:** fork → branch → make the change → `python3 -m pytest -q` stays green → open a PR.
> Everything is open-source, vendor-agnostic, and documented so you can learn by reading it.

## Ways to contribute (all valued)
- 🐞 **Break it.** Find a prompt-injection, PII-leak, or guardrail bypass the test corpus misses.
  Open an issue (or a PR adding the case to `redteam/run_attacks.py`). Adversarial findings are
  the most valuable contribution — the design is meant to get *stronger* from them.
- 🧰 **Add a capability or tool.** Follow the "plug contract" in
  [`docs/securax/06-EXTENDING.md`](docs/securax/06-EXTENDING.md): new work connects to the shared
  spine through open interfaces; you add a plug, you don't rewire the base.
- 📖 **Improve the docs.** If a file can't teach what it does and why, that's a bug.
- 🌍 **Map another framework/region.** Extend `docs/securax/04-COMPLIANCE-MAP.md`.

## Ground rules
1. **Keep it green.** `python3 -m pytest -q` must pass from the repo root (23+ tests). If you add
   code, add at least a smoke test.
2. **Keep it vendor-agnostic.** Program to the open interface, not a product. If you add a tool,
   add it to `docs/securax/03-CAPABILITY-CATALOG.md` with at least one swappable alternative.
3. **Keep it teachable.** Comments and full-forms on first use; a newcomer should learn by browsing.
4. **No secrets, ever.** `.env` is git-ignored; never commit keys, tokens, customer data, or real
   PII. Run `gitleaks detect` before pushing if you're unsure.
5. **Security/offensive content stays in the authorized-use lane** — defensive testing, CTFs,
   research, and your own systems only.

## Development setup
```bash
git clone https://github.com/rohan2pt0/ai-cloud-cyber-range
cd ai-cloud-cyber-range
pip install -r apps/llm-gateway/requirements-dev.txt pyyaml
python3 -m pytest -q                 # all tests
python3 redteam/run_attacks.py       # adversarial-ML scorecard
# optional: ./local/scripts/bootstrap-laptop.sh  (needs Docker)
```

## Pull request checklist
- [ ] Tests pass locally (`python3 -m pytest -q`).
- [ ] New code has a test; new tool is in the capability catalog with an alternative.
- [ ] Docs updated (and the portal data in `portal/securax.data.js` if you added a capability).
- [ ] No secrets, no real customer/PII data.
- [ ] `ruff check .` passes and `CHANGELOG.md` has an entry under **[Unreleased]** for user-visible changes.
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org)
      (`feat:`, `fix:`, `docs:`, …); one logical change per PR.

See [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md) for
versioning/release policy, [`GOVERNANCE.md`](GOVERNANCE.md) for how decisions are made, and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community expectations.

## Reporting a security issue
For a vulnerability in *this project's* code, please open a **private** security advisory on
GitHub (Security → Report a vulnerability) rather than a public issue, so it can be fixed before
disclosure.

## License
By contributing, you agree your contributions are licensed under the repository's
terms of the version it goes into: FSL-1.1-MIT from v0.4.0 on, becoming MIT two years after
each release ([LICENSING.md](LICENSING.md)).
