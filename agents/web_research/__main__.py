"""CLI for the autonomous web-research agent.

  # read-only research, confined to an allowlist, local model via the gateway:
  GATEWAY_URL=http://localhost:8080 \
    python -m agents.web_research "best term insurance for a 35yo in India 2026" \
      --allow policybazaar.com --allow irdai.gov.in --allow livemint.com

  # open browsing (deny-list only) — use deliberately:
  python -m agents.web_research "..." --open --deny facebook.com

Nothing that changes state is ever executed; such steps are printed under
"PENDING ACTIONS (need your approval)".
"""
from __future__ import annotations

import argparse
import json
import sys

from .researcher import ddg_search, gateway_llm, http_fetch, research


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agents.web_research",
                                 description="Autonomous, read-only, injection-safe web research (sovereign).")
    ap.add_argument("task", help="what to research, in plain English")
    ap.add_argument("--allow", action="append", default=[], help="allowed domain (repeatable)")
    ap.add_argument("--deny", action="append", default=[], help="denied domain (repeatable)")
    ap.add_argument("--open", action="store_true", help="open browsing (deny-list only) — use with care")
    ap.add_argument("--max-pages", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--no-llm", action="store_true", help="collect+cite sources without model synthesis")
    ap.add_argument("--json", action="store_true", help="emit the full result as JSON")
    args = ap.parse_args(argv)

    allow = ["*"] if args.open else args.allow
    if not allow:
        print("Refusing to browse with no allowlist. Pass --allow <domain> (repeatable), "
              "or --open for deny-list-only browsing.", file=sys.stderr)
        return 2

    res = research(
        args.task,
        allow=allow, deny=args.deny,
        search=ddg_search, fetch=http_fetch, robots_fetch=http_fetch,
        llm=None if args.no_llm else gateway_llm,
        max_pages=args.max_pages, max_steps=args.max_steps,
    )

    if args.json:
        print(json.dumps({
            "task": res.task, "report": res.report,
            "sources": [vars(s) for s in res.sources],
            "pending_actions": [vars(a) for a in res.pending_actions],
            "skipped": res.skipped, "steps_used": res.steps_used,
        }, indent=2, ensure_ascii=False))
        return 0

    print("=" * 70 + f"\nTASK: {res.task}\n" + "=" * 70)
    print(res.report + "\n")
    if res.sources:
        print("SOURCES:")
        for i, s in enumerate(res.sources):
            print(f"  [{i+1}] {s.title[:80]} — {s.url}")
    if res.pending_actions:
        print("\nPENDING ACTIONS (need your approval — NOT taken):")
        for a in res.pending_actions:
            print(f"  • {a.method} {a.url}  ({a.reason})")
    if res.skipped:
        print(f"\nSkipped {len(res.skipped)} link(s) by the safety rails"
              + (" — e.g. " + res.skipped[0] if res.skipped else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
