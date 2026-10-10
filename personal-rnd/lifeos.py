"""LifeOS planning helper — structure goals -> projects -> next-actions.

Pure, offline scaffolding you can push into Notion/Todoist/Calendar via the Claude app
connectors. It only renders structure; it stores nothing and sends nothing itself.
"""
from __future__ import annotations
import argparse, json

HORIZONS = ["Life vision (3-5y)", "Yearly goals", "Quarterly rocks", "Weekly focus", "Daily next-actions"]
AREAS = ["Career/AI-security", "Health", "Family", "Finances/FIRE", "Learning/Certs", "Security/OPSEC"]

def weekly_review_template() -> dict:
    return {
        "horizons": HORIZONS,
        "life_areas": AREAS,
        "weekly_review": [
            "Inbox zero: email, Todoist, notes captured",
            "Did this week's actions move a quarterly rock?",
            "Health/family check-in (not just work)",
            "Finances: spend vs plan, one FIRE action",
            "Security: one OPSEC gap closed (run self_opsec.py)",
            "Certs/learning: one block done (CKS/AWS-Sec/42001)",
            "Plan next week's 3 focus items",
        ],
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true", help="Print the weekly-review template")
    a = ap.parse_args()
    print(json.dumps(weekly_review_template() if a.review else
                     {"areas": AREAS, "horizons": HORIZONS}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
