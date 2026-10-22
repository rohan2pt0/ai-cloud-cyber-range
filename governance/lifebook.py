#!/usr/bin/env python3
"""Your life workbooks, read for you: every open issue becomes one Life OS action with a date, the vital few first (doc 104).

    ./securax lifeos import workbook [FILE ...]   one or more .xlsx (no file: the newest ones in vault/life/, Downloads, Documents, Desktop)
    ./securax lifeos import workbook --dry-run    show what would arrive, write nothing

Sheets are recognised by their column headers, not their names, so a renamed or reordered sheet still works:
  register      Item / Document + Nominee Set? + Expiry      nominee missing, password-manager entry missing, a PIN or password
                                                             written in the sheet, an expiry or renewal within 90 days or passed
  nominations   Nominee Name + Needs Update?                 no nominee, or marked as needing an update
  checklist     Included? (Y/N)                              each item not yet in the emergency binder
  credentials   Service / Portal + Password Manager Entry?   logins outside the password manager, no 2FA backup-codes location (grouped)
  people        Full Name + Aadhar + PAN                     each household member (self, spouse, children, parents) without an
                                                             Aadhaar or PAN on record; NA counts as missing (numbers are never read out)
  goals         Goal or Certification + Status + Target      each goal not done; one past its target is late
  roadmap       TASK TITLE + PCT OF TASK COMPLETE            each task under 100%
  banking       Account Type + Action Items                  each action item that is not "None"
  gaps          Gaps + Action Items                          each action item
  insurance     Cover type + Gap to close                    each cover with a gap
  renewals      Certification Name + Expiry Date             a certification expiring within 120 days or expired

80/20: every item gets a score (impact of its area x urgency of its date); the top fifth is marked vital, and the Life OS shows
those first. Outputs, all on this machine and never in git:
  portal/inbox-import.json     the Life OS merges it into the Inbox by itself; an issue fixed in the workbook since the last
                               import is listed as resolved, so the Life OS ticks it off
  vault/life/alarms.ics        a calendar file: each dated vital item with alarms 7 days and 1 day before (open it once on the phone)
  vault/life/ledger.json       what was read, per sheet, and the ids imported last time

Secrets are never copied: a PIN or password found in a sheet becomes an action to remove it, without the value; ID and account
numbers are never read into any output. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "portal" / "inbox-import.json"
LIFE = ROOT / "vault" / "life"
SOURCE = "workbook"
IMPACT = {"Identity": 3, "Insurance": 3, "Nominees": 3, "Security": 3, "Health": 3, "Family": 2.5, "Banking": 2, "Investments": 2,
          "Property": 2, "Finance": 2, "Career": 1.5, "Learning": 1.5, "Documents": 1.5, "Vehicle": 1.5, "Growth": 1}


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------------------------------------------- cell helpers
def text(v) -> str:
    return re.sub(r"\s+", " ", str(v)).strip() if v not in (None, "") else ""


def yes(v) -> bool:
    return text(v).upper() in ("Y", "YES")


def no(v) -> bool:
    return text(v).upper() in ("N", "NO")


def as_date(v) -> dt.date | None:
    """A date from an .xlsx cell: Excel's day number, or an ISO / Indian dd-mm-yyyy / dd/mm/yyyy string."""
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = text(v)
    if re.fullmatch(r"\d{4,5}(\.\d+)?", s) and 20000 < float(s) < 80000:
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(float(s)))
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d-%b-%Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(s[:19], fmt).date()
        except ValueError:
            continue
    return None


def pct(v) -> float | None:
    s = text(v).rstrip("%")
    try:
        f = float(s)
    except ValueError:
        return None
    return f * 100 if f <= 1 else f


def header_row(rows: list[list], need: tuple[str, ...], scan: int = 8) -> int | None:
    """The first row (of the first few) whose cells start with every needed header (case-insensitive)."""
    for i, r in enumerate(rows[:scan]):
        cells = [text(c).lower() for c in r]
        if all(any(c.startswith(n.lower()) for c in cells) for n in need):
            return i
    return None


def table(rows: list[list], need: tuple[str, ...]):
    """(column index by header prefix, body rows) for the first header row that has every needed header, else None."""
    h = header_row(rows, need)
    if h is None:
        return None
    hdr = [text(c).lower() for c in rows[h]]

    def col(prefix: str) -> int | None:
        p = prefix.lower()
        return next((i for i, c in enumerate(hdr) if c.startswith(p)), None)
    body = [r for r in rows[h + 1:] if any(text(c) for c in r)]
    return col, body


def cell(r: list, i: int | None):
    return r[i] if i is not None and i < len(r) else None


# ------------------------------------------------------------------------------------------------------ the readers
def _id(*parts: str) -> str:
    return "lw-" + hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _item(src: str, key: str, title: str, area: str, kind: str = "action", due: dt.date | None = None, nxt: str = "") -> dict:
    return {"id": _id(src, key, title), "t": title[:200], "kind": kind, "area": area, "due": due.isoformat() if due else "",
            "next": nxt[:200], "from": SOURCE, "src": src[:60]}


def _area(category: str) -> str:
    c = category.lower()
    for k, a in (("identity", "Identity"), ("insur", "Insurance"), ("bank", "Banking"), ("invest", "Investments"), ("property", "Property"),
                 ("vehicle", "Vehicle"), ("medical", "Health"), ("health", "Health"), ("career", "Career"), ("education", "Learning"),
                 ("device", "Security"), ("credential", "Security")):
        if k in c:
            return a
    return "Documents"


def read_register(rows, sheet, today):
    t = table(rows, ("Item / Document", "Nominee Set"))
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        item, owner = text(cell(r, col("item / document"))), text(cell(r, col("owner")))
        if not item:
            continue
        label = f"{item}" + (f" ({owner})" if owner else "")
        area = _area(text(cell(r, col("category"))))
        if no(cell(r, col("nominee set"))):
            out.append(_item(sheet, item + owner, f"Set a nominee: {label}", "Nominees", "issue", today + dt.timedelta(days=14),
                             "ask the institution for its nomination form, or do it in its app"))
        if no(cell(r, col("password manager"))):
            out.append(_item(sheet, item + owner + "pm", f"Put the login for {label} in the password manager", "Security", "issue",
                             today + dt.timedelta(days=7), "add it to Vaultwarden (./securax start pass), then mark the sheet Y"))
        secret = text(cell(r, col("mpin")))
        if secret and secret.upper() not in ("N/A", "NA", "-", "NONE"):
            out.append(_item(sheet, item + owner + "secret", f"Remove the PIN or password written in the workbook for {label}",
                             "Security", "issue", today, "move it into the password manager, then clear that cell"))
        exp = as_date(cell(r, col("expiry")))
        if exp and (exp - today).days <= 90:
            late = exp < today
            out.append(_item(sheet, item + owner + "exp" + exp.isoformat(),
                             (f"Expired on {exp.isoformat()}: renew " if late else f"Renew before {exp.isoformat()}: ") + label,
                             area, "issue", today if late else max(today, exp - dt.timedelta(days=21)), "start the renewal now"))
    return out


def read_nominations(rows, sheet, today):
    t = table(rows, ("Nominee Name", "Needs Update"))
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        asset = text(cell(r, col("asset"))) or text(cell(r, col("institution")))
        if not asset:
            continue
        if not text(cell(r, col("nominee name"))):
            out.append(_item(sheet, asset, f"No nominee recorded: {asset}", "Nominees", "issue", today + dt.timedelta(days=14),
                             "register a nominee, then record who and the share"))
        elif yes(cell(r, col("needs update"))):
            out.append(_item(sheet, asset + "upd", f"Update the nominee: {asset}", "Nominees", "issue", today + dt.timedelta(days=21),
                             "file the change with the institution"))
    return out


def read_checklist(rows, sheet, today):
    t = table(rows, ("Item", "Included?"))
    if not t:
        return None
    col, body = t
    return [_item(sheet, text(cell(r, col("item"))), f"Add to the emergency binder: {text(cell(r, col('item')))}", "Family", "action",
                  today + dt.timedelta(days=30), "put a copy in the binder, then mark it Y")
            for r in body if text(cell(r, col("item"))) and no(cell(r, col("included?")))]


def read_credentials(rows, sheet, today):
    t = table(rows, ("Service / Portal", "Password Manager"))
    if not t:
        return None
    col, body = t
    named = [r for r in body if text(cell(r, col("service")))]
    outside = sum(1 for r in named if no(cell(r, col("password manager"))))
    no2fa = sum(1 for r in named if not text(cell(r, col("2fa"))))
    out = []
    if outside:
        out.append(_item(sheet, "pm-group", f"Move {outside} login(s) into the password manager", "Security", "issue",
                         today + dt.timedelta(days=7), "five a day in Vaultwarden (./securax start pass); the vital ones (bank, email, tax) first"))
    if no2fa:
        out.append(_item(sheet, "2fa-group", f"Record where the 2FA backup codes are kept ({no2fa} service(s))", "Security", "issue",
                         today + dt.timedelta(days=14), "store the codes in the password manager, one note per service"))
    return out


HOUSEHOLD = {"self", "wife", "husband", "spouse", "son", "daughter", "father", "mother", "child", "kid"}
EMPTY = {"", "na", "n/a", "nil", "none", "-", "pending", "not available", "tbd"}


def read_people(rows, sheet, today):
    """Only the household (self, spouse, children, parents): the people whose papers the owner keeps. A contact list of the wider
    family is for birthdays, not for an Aadhaar check. NA / NIL / - count as missing."""
    t = table(rows, ("Full Name", "Aadhar"))
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        name = text(cell(r, col("full name")))
        rels = {text(cell(r, col("relation"))).lower(), text(cell(r, col("relationship"))).lower()}
        if not name or not rels & HOUSEHOLD:
            continue
        who = next((x for x in (text(cell(r, col("relationship"))), text(cell(r, col("relation")))) if x and x.upper() != "NA"), "a family member")
        for doc, prefix in (("Aadhaar", "aadhar"), ("PAN", "pan card")):
            if text(cell(r, col(prefix))).lower() in EMPTY:
                out.append(_item(sheet, name + doc, f"{doc} not on record for {who}", "Identity", "issue", today + dt.timedelta(days=30),
                                 f"get or find the {doc}, then record it (in the Master Register, not in a chat)"))
    return out


_DONE = ("done", "completed", "complete", "achieved", "passed", "closed", "certified")


def read_goals(rows, sheet, today):
    t = None
    for need in (("Goal", "Status"), ("Certification", "Current Status"), ("Certification", "Status")):
        t = table(rows, need)
        if t:
            break
    if not t:
        return None
    col, body = t
    out = []
    area = "Learning" if "cert" in sheet.lower() or col("certification") is not None else (
        "Family" if "child" in sheet.lower() else "Health" if "health" in sheet.lower() else
        "Finance" if "financ" in sheet.lower() else "Career" if "profession" in sheet.lower() else "Growth")
    for r in body:
        goal = text(cell(r, col("goal"))) or text(cell(r, col("certification")))
        status = text(cell(r, col("current status")) or cell(r, col("status")))
        done = pct(cell(r, col("% complete")))
        if not goal or len(goal) < 3 or goal.lower() in ("goal", "certification") or status.lower().startswith(_DONE) or (done or 0) >= 100:
            continue
        target = as_date(cell(r, col("target date")))
        late = bool(target and target < today)
        if not (status or target):        # a heading or an idea with no status and no date: one note, not a task
            continue
        title = (f"Late since {target.isoformat()}: " if late else "") + goal
        out.append(_item(sheet, goal, title, area, "action", today if late else target,
                         "decide: a new date, a smaller first step, or drop it" if late else f"next step towards it ({status or 'not started'})"))
    return out


def read_roadmap(rows, sheet, today):
    t = table(rows, ("TASK TITLE", "PCT OF TASK"))
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        task = text(cell(r, col("task title")))
        p = pct(cell(r, col("pct of task")))
        if task and p is not None and p < 100:
            due = as_date(cell(r, col("due date")))
            out.append(_item(sheet, task, f"{task} ({int(p)}% done)", "Growth", "action", due, "the next 30-minute step"))
    return out


def read_actions(rows, sheet, today, need: tuple[str, ...], area: str):
    t = table(rows, need)
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        act = text(cell(r, col("action items")))
        if act and act.lower() not in ("none", "n/a", "na", "-", "nil"):
            what = text(cell(r, col(need[0]))) or text(cell(r, col("category")))
            out.append(_item(sheet, what + act, f"{act}" + (f" ({what})" if what else ""), area, "action", today + dt.timedelta(days=30)))
    return out


def read_insurance(rows, sheet, today):
    t = table(rows, ("Cover type", "Gap to close"))
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        cover, gap = text(cell(r, col("cover type"))), text(cell(r, col("gap to close")))
        if cover and gap and gap not in ("0", "0.0", "-", "N/A", "None"):
            out.append(_item(sheet, cover, f"Close the insurance gap: {cover}", "Insurance", "issue", today + dt.timedelta(days=30),
                             "get two quotes; decide on the cover the plan recommends"))
    return out


def read_renewals(rows, sheet, today):
    t = table(rows, ("Certification Name", "Expiry Date"))
    if not t:
        return None
    col, body = t
    out = []
    for r in body:
        name, exp = text(cell(r, col("certification name"))), as_date(cell(r, col("expiry date")))
        if name and exp and (exp - today).days <= 120:
            late = exp < today
            out.append(_item(sheet, name + exp.isoformat(), (f"Expired on {exp.isoformat()}: " if late else f"Renew before {exp.isoformat()}: ") + name,
                             "Career", "issue", today if late else max(today, exp - dt.timedelta(days=30)), "log the CPEs and pay the fee"))
    return out


READERS = (read_register, read_nominations, read_checklist, read_credentials, read_people, read_goals, read_roadmap,
           lambda rows, s, d: read_actions(rows, s, d, ("Account Type", "Action Items"), "Banking"),
           lambda rows, s, d: read_actions(rows, s, d, ("Category", "Gaps", "Action Items"), "Career"),
           read_insurance, read_renewals)


def read_book(path: pathlib.Path, today: dt.date) -> tuple[list[dict], dict]:
    sheets = _load("securax_controls_x", "governance/controls.py").read_xlsx(path)
    items, seen = [], {}
    for name, rows in sheets.items():
        for reader in READERS:
            got = reader(rows, name, today)
            if got is not None:
                items += got
                seen[name] = len(got)
                break
    return items, seen


# ------------------------------------------------------------------------------------------------------------ 80/20
def score(items: list[dict], today: dt.date) -> list[dict]:
    for it in items:
        days = (dt.date.fromisoformat(it["due"]) - today).days if it["due"] else 999
        urgency = 3 if days <= 0 else 2.5 if days <= 15 else 2 if days <= 60 else 1
        it["score"] = round(IMPACT.get(it["area"], 1) * urgency * (1.2 if it["kind"] == "issue" else 1), 2)
    items.sort(key=lambda i: (-i["score"], i["due"] or "9999"))
    vital = max(1, round(len(items) * 0.2)) if items else 0
    for n, it in enumerate(items):
        it["vital"] = n < vital
    return items


# ------------------------------------------------------------------------------------------------------------ outputs
def _ics_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    out, b = [], line.encode("utf-8")
    while len(b) > 75:
        cut = 75
        while (b[cut] & 0xC0) == 0x80:      # never split a character
            cut -= 1
        out.append(b[:cut].decode("utf-8"))
        b = b" " + b[cut:]
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)


def ics(items: list[dict], stamp: str) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//SecuRAX//Life OS alarms//EN", "CALSCALE:GREGORIAN"]
    for it in items:
        if not (it["due"] and it["vital"]):
            continue
        d = it["due"].replace("-", "")
        lines += ["BEGIN:VEVENT", f"UID:{it['id']}@securax", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{d}",
                  f"SUMMARY:{_ics_text(it['t'])}", f"DESCRIPTION:{_ics_text(it.get('next') or '')}"]
        for trig in ("-P7D", "-P1D"):
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_text(it['t'])}", f"TRIGGER:{trig}", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(x) for x in lines) + "\r\n"


def _private_write(path: pathlib.Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(data)


def merge(new: list[dict], out: pathlib.Path = OUT, source: str = SOURCE) -> dict:
    """Keep other sources' items (Keep, documents); replace this source's; ids of this source that are gone are resolved."""
    try:
        cur = json.loads(out.read_text("utf-8"))
    except (OSError, ValueError):
        cur = {}
    old = cur.get("items", [])
    gone = {x["id"] for x in old if x.get("from") == source} - {x["id"] for x in new}
    resolved = sorted(set(cur.get("resolved", [])) - {x["id"] for x in new} | gone)
    return {"items": [x for x in old if x.get("from") != source] + new, "resolved": resolved}


def find_books(dirs: list[pathlib.Path] | None = None) -> list[pathlib.Path]:
    """The newest workbook of each kind in vault/life, Downloads, Documents, Desktop (and the Windows ones on WSL)."""
    ctl = _load("securax_controls_f", "governance/controls.py")
    dirs = dirs if dirs is not None else [LIFE] + ctl.search_dirs()
    found = sorted((f for d in dirs if d.is_dir() for f in d.glob("*.xlsx") if not f.name.startswith("~$")),
                   key=lambda f: f.stat().st_mtime, reverse=True)
    picked, kinds = [], set()
    for f in found:
        k = "guiding" if "guiding" in f.name.lower() else "agap" if ("agap" in f.name.lower() or "achievement" in f.name.lower()) else ""
        if k and k not in kinds:
            kinds.add(k)
            picked.append(f)
    return picked


def run(paths: list[pathlib.Path], today: dt.date | None = None, dry: bool = False, out: pathlib.Path = OUT,
        life: pathlib.Path = LIFE) -> dict:
    today = today or dt.date.today()
    items, read = [], {}
    for p in paths:
        got, seen = read_book(p, today)
        items += got
        read[p.name] = seen
    uniq = {i["id"]: i for i in items}
    items = score(list(uniq.values()), today)
    merged = merge(items, out)
    if not dry:
        _private_write(out, json.dumps(merged, indent=1, ensure_ascii=False))
        _private_write(life / "alarms.ics", ics(items, dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
        _private_write(life / "ledger.json", json.dumps({"date": today.isoformat(), "read": read, "ids": [i["id"] for i in items]}, indent=1))
    return {"items": items, "read": read, "resolved": merged["resolved"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax lifeos import workbook", description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    paths = [pathlib.Path(f) for f in a.files] or find_books()
    if not paths:
        print("No life workbook found. Put the .xlsx in vault/life/ (or Downloads), or name it:  ./securax lifeos import workbook FILE.xlsx")
        return 1
    missing = [p for p in paths if not p.is_file()]
    if missing:
        print(f"Not found: {', '.join(map(str, missing))}")
        return 1
    res = run(paths, dry=a.dry_run)
    if a.json:
        print(json.dumps({k: v for k, v in res.items()}, indent=1, ensure_ascii=False))
        return 0
    items = res["items"]
    print(f"Read {len(paths)} workbook(s): {sum(len(s) for s in res['read'].values())} sheets understood, {len(items)} open item(s)"
          + (f", {len(res['resolved'])} fixed since last time" if res["resolved"] else "") + ".")
    vital = [i for i in items if i["vital"]]
    print(f"The vital few ({len(vital)}), first:")
    for i in vital[:12]:
        print(f"  ! {i['t']}  (by {i['due'] or 'no date'})")
    if not a.dry_run:
        print("They are in the Life OS Inbox the next time it opens. Calendar alarms: vault/life/alarms.ics (open it once on your phone).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
