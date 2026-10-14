# 34 · CCSP-aligned coverage (step 5)

You are preparing for CCSP within a year. This turns the estate into a **map against ISC2's six CCSP domains**, so the lab and the study plan point at each other, and it ships in the audit pack.

```
./securax ccsp                 weighted coverage, per domain, biggest gaps
./securax ccsp --domain 5      sub-topic detail with evidence
./securax ccsp --json          machine-readable
./securax ccsp --verify        consistency only (also runs in ./securax verify, ./securax fitness and CI)
./securax evidence             the pack now includes ccsp-coverage.md / .json (checksummed in SHA256SUMS)
```

## What is real here
- Titles and weights (17/20/17/16/17/13 %, 38 sub-topics) are ISC2's published outline, read 2026-10-14 (page header date 2026-08-01). Check the effective date before you rely on it.
- **Status is our own assessment** and is made hard to fudge (`governance/ccsp.py`):
  - every evidence reference (`file:`, `cmd:`, `journey:`, `test:`) must exist, or the map is stale and the check fails;
  - **covered** needs a journey or test as proof; documentation alone earns only **partial** (the checker caught my own first overclaim on 4.2);
  - a **gap** cites no evidence; every non-gap cites some.
- Score: covered = 1, partial = 0.5, gap = 0, weighted by domain weight. First run: **58.6 %**. Biggest gaps: 2.6 IRM, 3.2 secure data centre, 6.5 outsourcing/contract design — the last two are exactly what the burrow and a real vendor contract will teach you.

## Limits
- A practice map of a lab. **Not exam content, not study material, not a pass prediction.** CCSP also needs the required work experience.
- The percentage measures what is *demonstrated and testable here*, not what you know.
- Nothing is applied to a real cloud; "covered" means the mechanism is proven in the sandbox/twin.
