# Selftest: prove every command works before you need it

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and a CI gate: ./securax selftest proves every command the CLI advertises is wired (no 'unknown command'), that every Python module behind it loads (a syntax error, bad import or missing file is caught), and that the read-only commands (status/check/--json/list/help) actually run without throwing — all with no side effects (nothing that changes state is executed; a missing service dependency is reported, not failed). test_selftest.py runs it on every change, so a command that stops loading fails the build. Extending the probes to subcommands and a weekly report are queued (selftest-subcommands). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

A system you can't trust to run is worse than no system. `./securax selftest` is the honest answer to "do all these
commands actually work?" — it exercises the whole command surface and tells you, plainly, what is wired, what loads, and
what runs, with **no side effects**.

## What it checks

For every command the CLI lists in `./securax help`:

1. **Wired** — the command has a dispatch branch, so it can never print `unknown command` for something in its own menu.
2. **Loads** — every Python module the command runs is imported (its top level is executed), so a **syntax error, a bad
   import, or a missing file is caught here** instead of when you type the command in anger.
3. **Runs (the read-only ones)** — commands with a safe read-only form (`status` / `check` / `--json` / `list` / `help`)
   are **actually executed**, and must finish **without throwing** — a Python traceback or a shell error is a failure,
   a clean "nothing set up yet" is not.

It never runs anything that changes state: no `up`/`down`/`backup`/`restore`/`update`/`ship`/`send`. A command whose
code needs a service dependency this machine hasn't installed (for example the gateway's web framework) is reported as
**"needs a dependency"**, not a failure — that is an environment fact, not broken code.

## Use it

```
./securax selftest              the full report: each command, its modules, and its read-only probe
./securax selftest --quiet      just the summary line and anything that failed
./securax selftest --json       machine-readable, for CI and the cockpit
./securax selftest --no-probes  wiring + module load only (runs nothing at all)
```

It exits `0` only when **every** command is wired, **every** module loads, and **every** read-only probe ran clean — so
it is a gate, not just a report. The test `test_selftest.py` runs it on every change in CI, so a command that stops
loading (a typo, a bad import, a renamed module) **fails the build** before it can ever reach you.

## Why this exists

Because the opposite happened: a command could break — or the estate could fail to even start — and nothing caught it
until a person hit it live. This closes that gap for the command surface: the machine checks its own commands, every
change, so "it doesn't work" is found by a test, not by you at the worst moment.

## Where this is going

Queued in `governance/queue.json` (`selftest-subcommands`): extend the probes to the common **subcommands** (not just the
top-level command), and add a weekly `selftest` routine that reports a green/red line to `./securax progress`, so the
command surface is proved on a schedule as well as on every change.
