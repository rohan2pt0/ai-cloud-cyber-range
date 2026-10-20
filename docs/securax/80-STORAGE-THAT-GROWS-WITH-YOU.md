# 80 · Storage that grows with you: bounded by design, tiered, and run by itself

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: every growth source bounded, storage --auto on a 6-hourly routine (exercise compaction, superseded own images, safe clean-ups, phone alert only when still short), verified on a real disk. The SeaweedFS cold tier and cloud tiering are next (dated in the doc). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** as the estate grows, storage must never become the reason something stops. It should be scalable and flexible, without a fixed ceiling, and run with as little human work as possible.

**The honest answer** has three parts:

1. **Nothing grows without a bound.** Every source of growth either has a limit or is cleaned automatically.
2. **Data moves to the cheapest tier that is still safe.** Hot data stays on the fast local disk; bulky, rarely read data moves to another disk or to object storage.
3. **Object storage is the tier without a ceiling.** You add disks or machines to it, or let a cloud bucket take the overflow and pay per gigabyte. "No caps" really means "no fixed ceiling, at a known price per GB".

**A note on the 800 MB.** The "800 MB left" during the exercise-range build was the disk of the temporary cloud container the AI assistant works in. It is a fixed allowance per session, discarded afterwards. It was never your laptop or SecuRAX. The work below makes sure the estate itself never hits the same wall.

## 1. Every source of growth, and what bounds it

| Grows | Bound | Automatic? |
|---|---|---|
| Container logs | Rotate at 10 MB × 3 per container (compose file) | Yes, always |
| Backups | The newest `BACKUP_KEEP` (7) are kept; encrypted copies go off the machine (doc 72) | Yes |
| Old versions of images SecuRAX builds itself (such as the exercise range's gamebox) | `storage --auto` removes every version no container uses | **Yes, new** |
| Dangling images, build cache older than 7 days | `storage --auto` cleans them when free space is below 20%, or more than 3 GB can be reclaimed | **Yes, new** |
| Exercise check results (about 25 rows a minute in the lite range) | `storage --auto` folds all but the newest 1,440 rounds (24 hours) into per-check totals. Scores, reports and the after-action report do not change | **Yes, new** |
| Local AI models (often the largest) | You choose them. `storage` names a volume over 5 GB and how to remove a model | Advice only, on purpose: deleting a model is your call |
| Packet captures | Rotate them (`tcpdump -C 100 -W 20` keeps at most 2 GB) | Rule in doc 79. The earlier exercise timetable wrote one capture file without a limit, which is exactly how a disk fills mid-exercise |

## 2. What runs by itself now

The `storage-guard` routine runs `./securax storage --auto` every 6 hours (at minute 40). It does four things:

- **Folds old exercise data** into totals.
- **Removes old builds:** old versions of images SecuRAX built itself, but never one a container still uses, and never anything when it cannot tell which version is current.
- **Cleans up safely when space is tight:** dangling images and build cache older than 7 days.
- **Alerts only if needed:** if free space is still below 10% after all that, it sends one alert to your phone (`./securax notify setup` once). The alert names what to move.

**It never deletes:** a volume, a backup, a pinned third-party image or a model.

**It was run for real during this build:**
- It removed the superseded gamebox image and nothing else.
- It raised the alert correctly: the build machine's disk really was 99% full.

## 3. The tiers

| Tier | What goes there | Where | How it scales |
|---|---|---|---|
| **Hot** | Databases, chats, workflows, the models you use, the running range | The fast local disk (Docker volumes) | **Vertical:** a bigger disk, or move Docker's data folder to one (below) |
| **Warm** | Backups, finished exercises, offline threat data | A second disk or a NAS: `SECURAX_BACKUP_DIR` | **Vertical:** a bigger or second disk |
| **Cold** | Encrypted backups, archived exercises, evidence packs | **Object storage:** SeaweedFS (S3 API), already in the estate's `sprout` stage, and/or a cloud bucket | **Horizontal:** add SeaweedFS volume servers on more disks or machines (the `burrow` stage joins them). **Elastic:** SeaweedFS can tier rarely read data to a cloud bucket |

**Off-site copies already work.** Every encrypted backup is copied to a cloud-synced folder, such as OneDrive (doc 72), and `./securax backup drill` proves that copy restores. Nothing unencrypted leaves the machine.

**Data residency still applies** (doc 36):
- **Non-Indian buckets:** only encrypted backups may go to a bucket outside India.
- **Regulated data:** anything that must stay in India goes to an India region, such as Amazon S3 in Mumbai.

## 4. Getting more room on the laptop today (Windows)

- **Docker Desktop:** Settings → Resources → Advanced → **Disk image location**. Point it at a bigger drive. Docker moves its whole disk there, models and volumes included.
- **Backups:** set `SECURAX_BACKUP_DIR` in `local/compose/.env` to a folder on the bigger drive.
- **Models:** keep only the one or two local models you use. `./securax bench` tells you which model fits.

## 5. Indicative prices for the cold tier (October 2026)

These come from third-party sites, not the providers' own pages. Confirm on the provider's page before you choose.

| Option | Storage | Getting data out | Notes |
|---|---|---|---|
| Backblaze B2 | about $6.95 per TB a month | Free up to 3× what you store, then $0.01/GB | Published rates are for the US West region |
| Cloudflare R2 | about $0.015 per GB a month (≈ $15/TB) | No egress fee | 10 GB free each month; per-request fees apply |
| Amazon S3 Standard, Mumbai | about ₹2.10 per GB a month (≈ ₹2,100/TB) | First 100 GB a month free, then about ₹8–9/GB | The India-region choice for data that must stay in India; Glacier Deep Archive is about ₹0.16/GB |
| SeaweedFS on your own disks | The disks | Free | Already in the estate; scales by adding disks or machines |

Sources: [Backblaze B2 pricing explained (Upstash, Oct 2026)](https://upstash.com/blog/backblaze-b2-pricing-explained-2026.md) · [EgressCost B2](https://egresscost.com/backblaze-b2) · [Cloudflare R2 egress (Spendbase)](https://www.spendbase.co/?p=35561) · [AWS India pricing guide (reseller)](https://precisiontech.in/cloud/amazon-aws-cloud/aws-pricing/aws-pricing-in-bangalore/)

## 6. Next, with target dates (each needs your merge)

| Item | Target | Needs |
|---|---|---|
| `./securax storage tier setup`: wake SeaweedFS, move finished exercises and old backups to it automatically, keep N recent ones local | 2026-11-05 | — |
| SeaweedFS cloud tier for cold objects, with a residency check per bucket | 2026-11-20 | A bucket and key (B2, R2, or S3 Mumbai for regulated data) |
| A second SeaweedFS volume server on a `burrow` machine (horizontal growth, and no single disk as a point of failure) | With the first extra machine | The machine |

## Tests

- **`governance/tests/test_storage_auto.py`:**
  - only unused old versions of SecuRAX's own images are removed
  - nothing at all is removed when the current version is unknown
  - exercise data is folded into totals
  - the phone alert is sent only when space is still short
- **`exercise/tests/test_engine.py`:** compaction leaves the after-action report and the score log unchanged.
