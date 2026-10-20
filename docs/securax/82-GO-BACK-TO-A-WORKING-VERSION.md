# 82 · Go back to a working version, at any time: first restore, then diagnose

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: every healthy start is recorded and pinned in git; ./securax rollback goes back in one command (edits stashed, data backed up, the version left pinned, automatic return if the old one does not start), --with-data, --latest, a weekly --check routine and a sandbox journey on every pull request. Release tags and a safe-mode start are dated in the doc. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The fear:** the estate has grown fast. One bad change could stop everything. And the code may be too large to debug under pressure.

**The answer:** you never have to debug in a crisis. Go back to the last version that worked, in one command, and diagnose afterwards, calmly. Fixing forward is optional, never urgent.

## 1. The break-glass card

| Situation | Command |
|---|---|
| Something broke after an update or a change | `./securax rollback` |
| See every version that worked on this machine | `./securax rollback --list` |
| Go back further | `./securax rollback 3` (the number from `--list`), or `./securax rollback v0.1.0`, or a commit id |
| The data is damaged too | `./securax rollback 3 --with-data` (also restores the backup taken while that version ran) |
| Where am I? | `./securax rollback --status` |
| Fixed: come forward again | `./securax rollback --latest` |
| Is the estate answering? | `./securax ready` (prints READY or NOT READY) |

`rollback` asks before it changes anything. Scripts add `--yes`.

## 2. How a "working version" is known

A version counts as working only when the estate really came up healthy on **this** machine, never because the code merely exists.

- **When one is recorded:** every time `./securax up` or `./securax update` ends with the readiness check passing.
- **What the record holds:** the commit, the version number, the time, and the newest data backup at that moment.
- **Where it lives:** `~/.securax/known-good.jsonl`, outside the repository, so no change to the code can damage it.
- **How long it is kept:** the newest 50 versions. The same version is recorded again at most every 6 hours. Bounded, like everything else (doc 80).
- **Pinned in git:** each version also gets a git reference (`refs/securax/good/…`). Its code cannot be lost even if the published history changes.

## 3. Why going back is safe

**Before** it moves anything, `rollback`:

1. **Keeps your unsaved edits:** puts them aside as a named git stash (`securax-rollback-…`). `git stash pop` brings them back.
2. **Backs up your data:** takes a backup of the running estate.
3. **Pins where you are:** the version you leave gets `refs/securax/before-rollback/…`, so `--latest` (or that commit) always brings you forward again.

**After** the move, the estate restarts and must pass its health check. If it does not, you are returned to where you started, automatically (exit code 3). A rollback can never leave you worse off than before it.

**It stays put.** The nightly update runs only on the main branch, so it never silently undoes a rollback. `--latest` returns you to main and updates again.

## 4. Code and data are separate, on purpose

- **Code:** `rollback` moves only the code. Your data (chats, workflows, registers, the vault) stays as it is, because newer data is usually what you want to keep.
- **Data too:** add `--with-data` when the data is damaged as well. It restores the backup recorded with that version, after taking a fresh backup of the current data first. If that backup file is gone, it says so and moves only the code.
- **Images:** each version pins its own container images. Going back to a version whose images were never on this machine needs the network once. Images SecuRAX builds itself, such as the range's gamebox, are rebuilt from that version's code.

## 5. It is checked, not just written

| Check | When | What it proves |
|---|---|---|
| Unit tests (`governance/tests/test_recovery.py`) | Every push | Recording, pinning, the bound, choosing the target, stash and backup before the switch, automatic return when an old version does not start, data restore |
| Sandbox journey `rollback_anytime` | Every pull request, on a real estate | `up` records a version; a newer commit is recorded; `rollback` returns to the first one, backs up first and pins the one it left; the estate is healthy there; `--check` passes; `--latest` returns to main |
| Routine `rollback-check` | Every Monday at 06:35 | Every recorded version still has its code and its backup file. Changes nothing. A failure is the signal to take a fresh backup (`./securax backup`) |
| `update`'s own safety net (doc 37) | Every update | A backup first, then a health check; a failed update rolls back by itself |

## 6. After going back: diagnose calmly

Once you are back on a working version, find out what broke:

1. **What changed:** `git log --oneline <working>..<broken>` lists the changes between the two versions. `--list` and `--status` show both ids.
2. **What stopped:** `./securax why` and `./securax doctor` name the service, and the reason.
3. **What a change can touch:** `./securax impact` shows the blast radius of each changed file.
4. **Fix it on a branch,** let CI and the sandbox prove it, then `./securax rollback --latest`.

The estate also limits how much can break at once: one CLI, small modules with their own tests, the impact map, and the sandbox journeys on every pull request (AGENTS.md).

## 7. Next steps (dated)

| By | Step |
|---|---|
| 2026-11-15 | Tag a release (`vX.Y.Z`) on every merge to main. Only `v0.1.0` is tagged today, so "go back to v0.2.0" needs the commit id or the `--list` number |
| 2026-12-15 | A "safe mode" start: only the gateway and the Command Center, for when even a working version is short of resources |
| 2027-01-31 | Copy the known-good record into the encrypted off-machine backup (doc 72), so a new laptop knows which versions worked |
