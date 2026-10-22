#!/usr/bin/env python3
"""BACKLOG: one queue of everything started or promised and not finished, so no ask is lost when a session ends.

    ./securax backlog                 what is not finished, most urgent first (local; asks GitHub when it can)
    ./securax backlog --offline       only what this machine knows (the cockpit uses this)
    ./securax backlog --markdown      the same as the body of the weekly "Backlog" issue
    ./securax backlog --json

Where unfinished work hides, and how each source is read:
  queue      governance/queue.json: an ask that was deferred, in our own words, with a due date (agents add to it)
  promise    a dated row in a docs table ("Next, with dates") that is due within 14 days or past its date
  pr         a pull request still open on GitHub (a Dependabot bump nobody handled counts too)
  branch     a branch on GitHub with commits main does not have and no open pull request
  unpushed   commits or edits on this machine that are not on GitHub yet (they vanish with a cloud session)
  worktree   an agent's scratch copy with changes that were never brought back

A session can end at any time (a usage limit, a restart). Everything here survives it: the queue and the docs are in git,
and the weekly backlog workflow rebuilds the issue on GitHub's machines with no session at all. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE = ROOT / "governance" / "queue.json"
SOON_DAYS, PR_STALE_DAYS = 14, 7
DATE = re.compile(r"(?<![\d-])(\d{4}-\d{2}-\d{2})(?![\d-])")
RANK = {"queue": 0, "promise": 1, "unpushed": 2, "worktree": 3, "branch": 4, "pr": 5}


def _item(kind: str, title: str, where: str, days: int | None = None, overdue: bool = False, next_step: str = "") -> dict:
    return {"kind": kind, "title": title, "where": where, "days": days, "overdue": overdue, "next": next_step}


# ------------------------------------------------------------------------------------------------- what the repo knows
def queue_items(today: dt.date, path: pathlib.Path = QUEUE) -> list[dict]:
    try:
        q = json.loads(path.read_text("utf-8")).get("items", [])
    except (OSError, ValueError):
        return []
    out = []
    for it in q:
        if it.get("state") == "done":
            continue
        due = dt.date.fromisoformat(it["due"]) if it.get("due") else None
        days = (due - today).days if due else None
        out.append(_item("queue", it.get("ask", "?"), it.get("id", ""), days, bool(due and due < today), it.get("next", "")))
    return out


def promises(today: dt.date, docs: pathlib.Path = ROOT / "docs" / "securax") -> list[dict]:
    """Dated rows in docs tables that are due soon or late. A struck row (~~…~~) or one that says done is finished; a row
    whose first cell is a date is a ledger entry (something that happened), not a promise."""
    out = []
    for f in sorted(docs.glob("*.md")):
        for n, ln in enumerate(f.read_text("utf-8").splitlines(), 1):
            if not ln.startswith("|") or set(ln) <= set("|-: "):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) < 2 or "~~" in cells[0] or re.search(r"\bdone\b", ln, re.I) or DATE.match(cells[0].strip("*")):
                continue
            dates = [dt.date.fromisoformat(d) for c in cells[1:] if "~~" not in c for d in DATE.findall(c)]
            if not dates:
                continue
            days = (max(dates) - today).days
            if days <= SOON_DAYS:
                out.append(_item("promise", re.sub(r"[*`]", "", cells[0])[:120], f"docs/securax/{f.name}:{n}", days, days < 0))
    return out


def _git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def local_work() -> list[dict]:
    out = []
    ahead = _git("rev-list", "--count", "@{upstream}..HEAD")
    if ahead and ahead != "0":
        out.append(_item("unpushed", f"{ahead} commit(s) on {_git('branch', '--show-current')} not on GitHub", "git push",
                         next_step="push them: a cloud session's container is reclaimed when it ends"))
    if _git("status", "--porcelain", "--untracked-files=no"):
        out.append(_item("unpushed", "edits on this machine that are not committed", "git status",
                         next_step="commit and push, or they are lost with the session"))
    for w in sorted((ROOT / ".claude" / "worktrees").glob("*")) if (ROOT / ".claude" / "worktrees").is_dir() else []:
        r = subprocess.run(["git", "-C", str(w), "status", "--porcelain"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            out.append(_item("worktree", f"an agent's scratch copy with {len(r.stdout.splitlines())} changed file(s)", str(w.relative_to(ROOT)),
                             next_step="bring it back (git diff there, apply here) or remove it"))
    return out


# ---------------------------------------------------------------------------------------------- what GitHub knows
def _slug() -> str:
    try:
        m = re.search(r"(?m)^REPO_SLUG=(.*)$", (ROOT / "brand.env").read_text("utf-8"))
        return m.group(1).strip() if m else ""
    except OSError:
        return ""


def _api(path: str, opener=urllib.request.urlopen):
    h = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    with opener(urllib.request.Request(f"https://api.github.com{path}", headers=h), timeout=15) as r:
        return json.loads(r.read())


def github_work(today: dt.date, slug: str = "", api=_api) -> tuple[list[dict], str]:
    """(items, note). The note says why GitHub was not asked, so a quiet list is never mistaken for an empty one."""
    slug = slug or _slug()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", slug or ""):
        return [], "no repository named in brand.env (REPO_SLUG)"
    try:
        prs = api(f"/repos/{slug}/pulls?state=open&per_page=100")
        branches = api(f"/repos/{slug}/branches?per_page=100")
    except Exception as e:  # noqa: BLE001 - offline or rate-limited: say so
        return [], f"GitHub could not be asked ({type(e).__name__}); pull requests and branches are not listed"
    out, with_pr = [], set()
    for p in prs:
        with_pr.add(p["head"]["ref"])
        age = (today - dt.date.fromisoformat(p["created_at"][:10])).days
        bot = p.get("user", {}).get("login", "").startswith("dependabot")
        out.append(_item("pr", f"#{p['number']} {p['title']}", p.get("html_url", ""), -age, age > PR_STALE_DAYS,
                         "check, then merge or close with a reason" if bot else "drive it to green and merge"))
    for b in branches:
        name = b["name"]
        if name in with_pr or name == "main":
            continue
        try:
            ahead = api(f"/repos/{slug}/compare/main...{name}").get("ahead_by", 0)
        except Exception:  # noqa: BLE001 - one branch that cannot be compared is skipped, not fatal
            continue
        if ahead:
            out.append(_item("branch", f"branch {name}: {ahead} commit(s) not on main, no pull request", name,
                             next_step="open a PR for it, or delete it if its work is already elsewhere"))
    return out, ""


# ------------------------------------------------------------------------------------------------------ the queue
def build(today: dt.date | None = None, offline: bool = False, github=github_work) -> dict:
    today = today or dt.date.today()
    items = queue_items(today) + promises(today) + local_work()
    note = "offline: only what this machine knows"
    if not offline:
        gh, note = github(today)
        items += gh
    items.sort(key=lambda i: (not i["overdue"], RANK[i["kind"]], i["days"] if i["days"] is not None else 999))
    return {"date": today.isoformat(), "items": items, "note": note,
            "counts": {k: sum(i["kind"] == k for i in items) for k in RANK}, "overdue": sum(i["overdue"] for i in items)}


def when(i: dict) -> str:
    d = i["days"]
    if d is None:
        return ""
    if i["kind"] == "pr":
        return f"open {-d} day(s)"
    return f"{-d} day(s) late" if d < 0 else ("due today" if d == 0 else f"due in {d} day(s)")


def markdown(b: dict) -> str:
    names = {"queue": "Deferred asks", "promise": "Dated promises due or late", "unpushed": "Not on GitHub yet",
             "worktree": "Agent scratch copies", "branch": "Branches with no pull request", "pr": "Pull requests waiting"}
    lines = [f"What is not finished, as of {b['date']}. Rebuilt every week by the `backlog` workflow; "
             "the same list on any machine: `./securax backlog`.", ""]
    if b["note"]:
        lines += [f"_{b['note']}_", ""]
    if not b["items"]:
        lines.append("Nothing is waiting.")
    for kind, title in names.items():
        rows = [i for i in b["items"] if i["kind"] == kind]
        if rows:
            lines += [f"### {title} ({len(rows)})", ""]
            lines += [f"- [ ] {'**late** ' if i['overdue'] else ''}{i['title']} · {when(i)} · `{i['where']}`"
                      + (f" → {i['next']}" if i["next"] else "") for i in rows]
            lines.append("")
    return "\n".join(lines).replace(" ·  ·", " ·")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax backlog", description=__doc__.split("\n\n")[0])
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    b = build(offline=a.offline)
    if a.json:
        print(json.dumps(b, indent=1))
    elif a.markdown:
        print(markdown(b))
    else:
        print(f"Not finished: {len(b['items'])} item(s), {b['overdue']} late." + (f"  ({b['note']})" if b["note"] else ""))
        for i in b["items"][:25]:
            print(f"  {'!' if i['overdue'] else '·'} [{i['kind']}] {i['title']}  {when(i)}")
            if i["next"]:
                print(f"      → {i['next']}")
        if len(b["items"]) > 25:
            print(f"  … and {len(b['items']) - 25} more: ./securax backlog --markdown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
