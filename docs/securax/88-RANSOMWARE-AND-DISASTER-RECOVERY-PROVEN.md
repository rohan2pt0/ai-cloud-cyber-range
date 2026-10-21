# 88 · Ransomware and disaster recovery, proven before shipping

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and proved on three levels (unit tests, the real CLI, the real containers in CI): encrypted data is caught before it can replace a clean backup, retention keeps weeks and months, restore latest and the drill take the newest clean copy, the restore twin opens it as working data, a drill with nothing to restore fails, and three tabletop exercises check what the machine can prove. Sync history and a write-once off-site bucket are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

## 1. The ask, made precise

The request was broad: regression testing, several kaizen rounds, a digital twin, every BCP and DR scenario, tabletop exercises, and a ransomware recovery drill above all. To get the best return on the effort, it was turned into one brief:

| Part | What it says |
|---|---|
| **Objective** | Before anything ships, prove that the estate comes back from the worst day: ransomware, a lost machine, a compromise. Proof means a test that runs, not a document that says so. |
| **Assume** | Ransomware runs as you, on your laptop. It reaches every folder you can reach, the synced OneDrive folder included. It can wait days before it strikes. Nobody notices for a week. |
| **Method** | (1) Run the regression baseline. (2) Read the backup, restore and drill code as an attacker would. (3) Fix what fails. (4) Prove each fix on three levels: a unit test, the real CLI and the real containers. (5) Re-review, and repeat until a round finds nothing new. |
| **Constraints** | No new dependency. No network call. Nothing that weakens a rail. It must work for someone who is not an expert. |
| **Done when** | A ransomware night is played end to end on the real estate in CI: the attack is caught, the clean copy survives, the restore brings back the same account, and the tabletop exercise passes on what the machine can prove. |

## 2. What the kaizen rounds found

**Regression baseline (main, before any change):** `ruff` clean, 993 unit tests passed, the Life OS tests passed.

**Round 1** read the backup chain as an attacker would. It found the flaws below. Rows 1 to 4 would each have defeated a recovery on their own.

| # | Finding | Why it mattered | Fix (proved) |
|---|---|---|---|
| 1 | **Backups were kept by count only:** the newest 7 here and 12 off-site, one a night | A week of encryption nobody noticed left only encrypted copies. The rotation deleted the last clean one by itself | One a week for 4 weeks and one a month for 3 months are kept as well (6 months off-site). Suspect copies never count as clean. Tests: a 100-day history still holds a copy from months back; 8 suspect nights delete no clean copy |
| 2 | **Nothing checked that the data was still readable** before backing it up and sending it off-site | Ransomware's output was saved, synced to OneDrive and rotated in as if it were good | Every backup first runs the guard. **Canary files** (fixed text in `vault/` and `~/.securax`) and a **format check** of the vault: text must read as text, workbooks must be zip files, PDFs must start with `%PDF`. Ransom-note names and ransomware file endings only back up other evidence, never decide alone. If the data looks encrypted, the backup is still written but named `-SUSPECT`. Nothing is deleted, nothing goes off-site, an alert is sent, and it exits 3 |
| 3 | **The restore drill passed when there was no off-site folder** (exit 0 with nothing proved) | A false green: the continuity plan recorded the ransomware scenario as drilled and within target | With no off-site folder, the drill proves the local copy and says so. With no clean backup at all, it **fails** |
| 4 | **The drill checked checksums only** | A backup of encrypted data matches its checksums perfectly | The drill now builds a **restore twin**. Every volume and the vault are unpacked in a scratch folder. Every database passes SQLite's own integrity check, the vault's files must open, the canary must be intact, and `.env` must be there. Live data is never touched |
| 5 | **A restore needed you to pick the right file, under stress** | On the worst day, picking the newest file picks the encrypted one | `./securax restore latest` picks the newest copy that is not suspect: local first, then off-site |
| 6 | **No copy was ever disconnected** (the 3-2-1-1-0 rule's "1 offline") | The OneDrive folder is a folder the ransomware can write to | `./securax backup offline` copies the newest clean encrypted backup to a USB stick and checks it byte for byte. The tabletop exercise checks its age. On Microsoft 365 plans, OneDrive can also roll a whole folder back 30 days. That fallback is now in the plan |
| 7 | **Rollback with data, the recovery point, and the status screen counted suspect copies** | "Backup from last night" looked fine when it held encrypted data | All three skip `-SUSPECT` files. `go` shows `RANSOMWARE SUSPECTED` |
| 8 | **No tabletop exercise, and no drill at all for a compromise** | People and decisions were never tested. Only files were | `./securax continuity tabletop` (section 4) |

**Round 2** reviewed round 1's own code and found four more problems:
- The suspect check used a `||` pattern that `set -e` would have turned into an aborted backup whenever the check itself failed. The same trap is already in LESSONS.
- An Excel lock file (`~$Book.xlsx`) would have counted as a damaged workbook.
- An OneDrive path with spaces would have been split in two by `restore latest`.
- The drill said "decrypts" for a plain backup.

All four are fixed and tested.

**Round 3** was an independent, adversarial review of rounds 1 and 2. Its brief: find what would lose data, give a false green, or crash. It found six more problems, all fixed and tested:

| # | Finding | Fix |
|---|---|---|
| 9 | **A name alone raised the alarm.** `postmortem new "Tabletop ransomware"`, which the after-action report itself suggests, or an imported advisory about ransomware, made every later backup suspect, for good | A ransom-note name or a ransomware ending now counts only next to content that really changed. Many files renamed to such an ending still count alone |
| 10 | **A canary that went missing for an ordinary reason was suspect forever.** That covered a moved checkout, a deleted folder, or a restore from before this change | Canaries are found by place, not by remembered path. A missing one is planted again. Only one whose text changed is evidence. After a false alarm you have checked yourself: `./securax backup clear-alarm` |
| 11 | **Suspect backups were never trimmed.** One false alarm would have added a full backup every night until the disk filled | A suspect run trims old suspect copies to the newest 3. It never touches a clean one |
| 12 | **The restore twin failed on a link inside a volume**, which a real restore handles fine | Links are skipped. Only regular files are opened, and nothing can be written outside the twin |
| 13 | **The twin needed about three times the backup's size on disk.** A large model volume would have filled it, a false red | The archives are read as a stream, which still proves they are whole. Only databases are written out, one volume at a time, beside the unpacked backup |
| 14 | Small ones | The status line now looks at the newest backup only. A scrambled offline log no longer crashes the tabletop. A stick formatted FAT32 is named as the reason when a backup over 4 GB does not fit |

**Text files Windows writes** also no longer look encrypted: a UTF-8 byte-order mark, UTF-16, and Excel's default code page all read as text. Encrypted bytes read as none of these.

**Round 4** played the whole night against the real containers (section 3): 20 of 20 checks passed.

**Regression after the change:** the full unit suite, the Life OS tests, `ruff`, fitness, `mkdocs --strict`, and the privacy and config checks.

## 3. The digital twin, in three sizes

A full copy of the estate on the laptop, kept just for drills, would cost memory and attention every day. So the twin comes in three sizes, each run where it is cheap:

| Level | Where it runs | What it proves | When |
|---|---|---|---|
| **1. Checksums** | Any machine | The copy decrypts and nothing in it changed | Every backup, and in every drill |
| **2. Restore twin** | Any machine (`./securax backup drill`, `continuity drill data-lost`) | The newest **clean** copy opens as working data: databases integrity-checked, vault readable, canary intact | Quarterly by the `offsite-restore-drill` routine, and any time you ask |
| **3. Estate twin** | CI, on the real containers (sandbox journey `ransomware_recovery`) | The whole ransomware night, end to end (below) | Every change that touches the estate, backups or governance |

The estate twin plays the night in this order:
1. An account and a vault exist. A clean, encrypted backup is taken and copied off-site.
2. The vault and its canary are encrypted, and a ransom note is left.
3. The next backup is marked `-SUSPECT`. It deletes nothing, sends nothing off-site and alerts you, and the alert carries no keys or data.
4. The drill proves the clean off-site copy in a restore twin, with Open WebUI's database passing its integrity check.
5. The data volume is destroyed.
6. `restore latest` brings back the same account and a readable vault, with the encrypted vault kept aside as evidence.
7. The tabletop exercise passes on what the machine can prove.

The cluster has its own drill: `./securax gameday` restores an etcd snapshot on the burrow twin (doc 33).

## 4. Tabletop exercises

```bash
./securax continuity tabletop               # the exercises
./securax continuity tabletop ransomware    # play one: about 10 minutes
```

An exercise is a story told in injects: the time, what happens, and the question it puts to you.
- **Where the machine can prove the answer, it checks for itself, and its answer wins over yours.** That covers whether alerts reach your phone, backups a week and a month old, an encrypted key, a fresh off-site copy and a recent offline one, a drill passed this quarter, working versions recorded, other nodes, and the code mirror. Saying "yes" cannot pass an inject the machine knows is false.
- **Where it cannot, you answer y or n.**

Each run writes an **after-action report**: what held, each gap with the command that fixes it, and a line to turn the gaps into tracked actions with `postmortem`. The newest 20 reports are kept. `./securax continuity` shows when each exercise was last run and how many gaps it left.

| Exercise | Story | Injects |
|---|---|---|
| `ransomware` | A file opened on Friday waits, then encrypts the laptop on Tuesday night | 10: detect, protect, contain, sync, the key, off-site and offline copies, restore, key rotation, whose clocks start, postmortem |
| `compromise` | A provider reports your key used abroad; an unknown device joins your private network | 6: spend cap, where the key lives, who may sign in, known-good code, audit trail, postmortem |
| `node-lost` | The VPS provider deletes your server | 4: a second machine at the same address, synced data, rebuild from backup, code without GitHub |

## 5. The drill calendar

| How often | What | How |
|---|---|---|
| Every night | Backup, guarded | routine `daily-backup` |
| Every day | Code mirror | routine `code-mirror` |
| Monthly | Offline copy on a USB stick | `./securax backup offline` (needs your hands) |
| Monthly | A continuity drill | routine `continuity-drill` |
| Quarterly | Restore twin from the off-site copy | routine `offsite-restore-drill` |
| Twice a year | Tabletop: `ransomware` | `./securax continuity tabletop ransomware` |
| Yearly | Tabletops: `compromise`, `node-lost` | the same command |
| Every change | Estate twin | CI sandbox |

## 6. Mapped to the standards

The references are cited and paraphrased.

| Standard | What it asks | Where it is met |
|---|---|---|
| NIST CSF 2.0 PR.DS-11 | Backups are created, protected, maintained and tested | Guarded nightly backups, encryption, retention by weeks and months, quarterly restore twin |
| NIST CSF 2.0 RC.RP-03 | Check the integrity of a backup before restoring from it | `restore latest` and the drill skip suspect copies; the twin opens the copy first |
| NIST CSF 2.0 RC.RP-05 | Check that restored assets work | The estate twin signs in with the same account; the guard re-checks the restored data |
| NIST CSF 2.0 ID.IM-02 | Improve from tests and exercises | After-action reports, with gaps turned into postmortem actions |
| CISA #StopRansomware guide | Offline, encrypted backups, tested regularly; exercise the response plan | `backup offline`, `protect`, the drills, the ransomware tabletop |
| NIST SP 800-84 | Tabletop and functional exercises, then an after-action report | `continuity tabletop` (tabletop), `continuity drill` (functional), the sandbox (full scale) |
| NIST SP 800-61 | Detect, contain, eradicate, recover, learn | The phases of each exercise's injects |
| ISO 22301 (exercise programme) | A planned programme of exercises, with results reviewed | Section 5, and `./securax continuity` showing each exercise's last run |
| Industry 3-2-1-1-0 | 3 copies, 2 media, 1 off-site, 1 offline, 0 errors on a restore test | Local, OneDrive, USB stick; the restore twin is the zero-errors test |

## 7. Accepted for now, with dates

| Risk | Why it stays | What limits it | By |
|---|---|---|---|
| Sync keeps the latest value of each item, with no history: a thief with a sync token could overwrite Life OS items on every node | History needs storage and a design for deletes | Every node's nightly backup holds its sync data; the plan removes a hit node from the others | 2026-12-31: per-item history (the last 5 versions) in the sync service |
| The off-site folder is writable from the laptop | It is what makes off-site copies need no setup | Encryption; retention by weeks and months; OneDrive's 30-day rollback (Microsoft 365); the monthly offline copy | 2027-01-31: an optional write-once bucket (object lock) for those who want one |
| Canaries can be found and skipped by a careful attacker | A canary is a cheap tripwire, not a wall | The vault's own format check is the second signal | Review yearly |
| The restore twin on your machine does not start the services | Starting them needs the full estate's memory | CI's estate twin starts them on every change | Ongoing |
