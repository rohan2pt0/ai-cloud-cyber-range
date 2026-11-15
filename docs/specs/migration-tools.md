# Spec: migration-tools

Queue item `migration-tools` in `governance/queue.json` · due 2026-12-15 · added 2026-10-27.

**The ask, as the queue holds it:** Three connective tools (doc 120) that remove the last friction of moving off Claude Code Pro, all opencode-tier so they build on the user's own models: (A) ./securax keys - a read-only secret inventory that scans local/compose/.env and ~/.securax/ for KEY/SECRET/TOKEN/PASSWORD/PRIVATE patterns and lists each one's …

## Outcome for the person

A person moving to their own models knows where every key is, has their documents ready for questions, and one tool list.

## Data

A read-only inventory of secret names and locations (never values), documents handed to the private workspace, one MCP configuration.

## Screen (one action)

`./securax keys`: one table and one line, the one key that needs attention (duplicate or unprotected).

## Test that proves it

Tests: values are never printed, fake keys in fixtures are low entropy, the scan is read-only.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** Three small CLI tools on one machine.
- **Enterprise, when conditions call for it:** A secrets inventory across nodes with a `--to-vault` move and rotation reminders.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
