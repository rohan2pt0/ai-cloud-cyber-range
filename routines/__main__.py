"""CLI for SecuRAX Routines (sovereign scheduled estate tasks).

  ./securax routines list            # show configured jobs
  ./securax routines due             # what WOULD run right now (no execution)
  ./securax routines run             # run everything due now (call this from a 1-min cron)
  ./securax routines prune           # which routines earn their place: failing, found nothing, duplicate, never ran
  ./securax routines off ID | on ID  # switch one off or back on, on this machine only

Install the single cron line that drives it (Linux/macOS):
  * * * * * cd /path/to/estate && ./securax routines run >> routines/.log 2>&1
"""
from __future__ import annotations

import json
import sys
import time

from .scheduler import due_jobs, load_jobs, run_due, set_off


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "list"
    try:
        jobs = load_jobs()
    except Exception as exc:  # noqa: BLE001
        print(f"routines config error: {exc}", file=sys.stderr)
        return 2

    if cmd == "list":
        for j in jobs:
            flag = "on " if j.enabled else "off"
            print(f"  [{flag}] {j.id:<22} {j.kind:<6} {j.cron:<16} {' '.join(j.command)}")
            if j.description:
                print(f"         {j.description}")
        if not jobs:
            print("  (no jobs — add some to routines/jobs.json; see routines/examples/jobs.json)")
        return 0

    if cmd == "due":
        now = time.localtime()
        d = due_jobs(jobs, now)
        print(f"At {time.strftime('%Y-%m-%d %H:%M', now)}, {len(d)} job(s) due:")
        for j in d:
            print(f"  • {j.id}  ({' '.join(j.command)})")
        return 0

    if cmd == "run":
        results = run_due()
        print(json.dumps(results, indent=2))
        # non-zero if any job failed OR a config error was surfaced (entries without exit_code)
        return 0 if all(r.get("exit_code", 1) == 0 for r in results) else 1

    if cmd == "prune":
        from .prune import main as prune_main
        return prune_main(argv[1:])

    if cmd in ("off", "on") and len(argv) == 2:
        if argv[1] not in {j.id for j in jobs}:
            print("routines: " + ", ".join(j.id for j in jobs), file=sys.stderr)
            return 2
        set_off(argv[1], cmd == "off")
        print(f"✔ {argv[1]} switched {cmd} on this machine" + ("  (./securax routines on " + argv[1] + " brings it back)" if cmd == "off" else ""))
        return 0

    print(f"unknown command '{cmd}'. Use: list | due | run | prune | off ID | on ID", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
