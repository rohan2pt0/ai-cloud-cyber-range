# 76 · Findings, repairs, restore, shortcuts: the best of four mature tools

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Built and tested: the findings register (SARIF, CSV and VAPT workbooks, SLA dates, KEV, time-boxed acceptance, a cockpit reading), Repairs, restore while installing with the vault now in every backup, and the Life OS shortcuts and CSV export. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The method.** Look at the mature open-source tools nearest to each part of SecuRAX. Take the one idea from each that removes the most work, and build only that. Some of their best ideas were already here:

- Loop's habit strength is like the Life OS's 20-day weighted average.
- Home Assistant's backup checks are like the restore drill.
- Mattermost's support packet is now here too (doc 75).

These four were the gaps.

| Borrowed from | The idea | What SecuRAX now does |
|---|---|---|
| **DefectDojo** (OWASP) | One findings register, duplicates merged, a fix-by date set by the severity, time-boxed risk acceptance | `./securax findings` |
| **Home Assistant** | A Repairs page: every problem in one list, each with its fix, and a count in the menu | `./securax repairs`, and a count on the Command Center |
| **Home Assistant** | Restore a backup while setting up a new machine | `bash install.sh --restore BACKUP`; backups now include `vault/` |
| **Loop Habit Tracker** | Tick a habit from the home screen; export to a spreadsheet | Long-press the Life OS icon; Ops → Export for Excel (CSV) |

## The findings register

**Why:** RBI and SEBI auditors ask two things about vulnerabilities. When was each one found, and was it fixed in time? Scan reports alone cannot answer, because each scan repeats the last one.

**What it does:**

- **One record per problem.** The same rule on the same asset and location is one finding, however many scans report it.
- **Fix-by dates from severity:**

  | Severity | Days to fix |
  |---|---|
  | Critical | 7 |
  | High | 30 |
  | Medium | 90 |
  | Low | 180 |

  Change them in `vault/findings/sla.json`, for example `{"high": 15}`. A CVE on CISA's known-exploited list counts as critical, whatever the scanner said (run `./securax offline sync kev` once first).
- **Re-scans close and reopen.** When a new scan from the same tool stops reporting a finding, it is marked fixed. If it comes back, it reopens with a new date.
- **Risk acceptance always ends.** It needs a reason, a person and an end date at most a year away. On that date the finding is open again.
- **It feeds what you already watch:** a cockpit reading (red when something is overdue), the phone alert, and Repairs.

**How:**

```bash
./securax scan                       # the image scan now fills the register by itself
./securax findings import            # a VAPT report (.xlsx or .csv) or any SARIF file; no file name: it looks in Downloads
./securax findings                   # what is open, overdue first
./securax findings accept F-1a2b3c --reason "isolated lab, no customer data" --until 2027-03-31 --by "CISO"
./securax findings fixed F-1a2b3c
./securax findings report            # the audit view: open by severity, % fixed in time, median days to fix
```

**What a VAPT workbook needs:** a header row naming a title column and a severity column. "Observation" and "Risk Rating" work, and so do most other names. Columns for the host, CVE and due date are picked up when present. Informational items are skipped, because they have nothing to fix by a date.

**Re-scans:** each file name is its own source. To have a re-test close the first test's findings, import both with the same `--source`, for example `--source vapt-portal`.

**Why not run DefectDojo itself?** It is a full web application with a database and workers, made for teams. One person needs the register and the dates, not the platform. If a team adopts SecuRAX, DefectDojo can read the same SARIF files.

## Repairs

`./securax repairs` puts these in one list, the most urgent first:

- every red or amber cockpit reading
- every overdue finding, and every risk acceptance ending within 14 days
- every overdue risk treatment
- every routine that needs a decision

Each line says what is wrong, why it matters, and the command that fixes it. The Command Center shows the count and the first item. The list runs nothing slow: health readings come from the last cockpit snapshot, and their age is shown. Setup steps you have not done are not repairs; they stay in `./securax finish`.

## Restore while installing

On a new or replacement machine, one command installs SecuRAX and brings your data back:

```bash
bash install.sh --restore ~/securax-20261101-0230.tar.gz     # add --keyfile PATH for an encrypted backup
```

- **Before anything is installed:** the installer checks that the backup exists and can be read.
- **The restore itself** checks every file against its checksum, then starts the estate.
- **Without Docker running:** it installs the code and prints the exact restore command for later.

**Fixed along the way:** backups did not include `vault/` (your controls, risk register, findings and setup marks). A new machine would have started blank. Every backup now carries it. A restore keeps the vault already on the machine aside as `vault.pre-restore-<time>`, never overwriting it.

## Life OS: shortcuts and a spreadsheet

- **Shortcuts:** long-press the installed app's icon (Android, and Windows or macOS with Chrome or Edge) for **Move**, **Mind**, **Family** or **Note**. A shortcut only ever ticks, never unticks, so a second tap cannot undo the day. The address drops the shortcut afterwards, so a reload does not repeat it. iPhones do not offer shortcuts for web apps.
- **Spreadsheet:** Ops → **Export for Excel (CSV)** gives one row per day for the last year: the daily three, energy and the note. Days with nothing recorded are left out.

## Sources and tests

- [DefectDojo findings](https://docs.defectdojo.com/asset_modelling/engagements_tests/os__findings/) · [OWASP DefectDojo](https://owasp.org/www-project-defectdojo/) · [Home Assistant Repairs](https://www.home-assistant.io/integrations/repairs) · [Home Assistant: restore during onboarding](https://home-assistant.io/common-tasks/general) · [Loop Habit Tracker](https://github.com/iSoron/uhabits)
- Tests:
  - `governance/tests/test_findings.py` (8)
  - `governance/tests/test_repairs.py` (2)
  - `governance/tests/test_installers.py` (the restore path)
  - `guiding-map/tests/test27.js` (8)
