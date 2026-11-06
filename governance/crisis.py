#!/usr/bin/env python3
"""`./securax crisis` — coordinate a multi-agency cyber-crisis response, and hit every agency deadline (doc 125).

A real cyber crisis is lost not in the attack but in the scramble afterwards: a regulator, a CERT and the police each
send a requisition with a short deadline, and each item needs a specific record from a specific team. This turns that
scramble into a tracked, templated workflow — open a requisition from a ready template, every item already assigned to
its owning team, see what is done / pending / overdue against the clock, and generate the response pack to hand over.

  ./securax crisis start <scenario> [--agency "<who>"] [--ref "<ref>"] [--title "<t>"]   one command: stand up the scenario's requisitions + the next steps (clock, checklist, first messages)
  ./securax crisis next [<id>]                            the single most urgent action right now — zero thinking required
  ./securax crisis comms [<id>|--audience .. --medium .. --scenario ..]   ready, legally-defensible messages (SITREP, staff, customers, public, partners) per medium (SMS/WhatsApp/email/letter/call)
  ./securax crisis templates                              the requisition library (law-enforcement, CERT forensics, regulator) and the ready documents
  ./securax crisis doc <name>                             print a ready document (forensic-tool-exception, chain-of-custody, forensic-collection-sop, agency-cover-letter, duty-roster)
  ./securax crisis new <template> --agency "<who>" --ref "<their ref>" [--due 72h|<ISO>] [--title "<t>"]
  ./securax crisis list                                   your open requisitions
  ./securax crisis status [<id>] [--json]                 progress by team, what is overdue, time left on the clock
  ./securax crisis assign <id> <section|item> --to "<team / person>"
  ./securax crisis set <id> <item> [--done|--na|--pending] [--owner "<who>"] [--evidence "<ref>"] [--note "<text>"]
  ./securax crisis pack <id>                              write the response register (Markdown + CSV) and a filled cover letter

Runs are stored in vault/crisis-runs/ (private, in your backups, never in git). The templates are DATA
(governance/crisis.json and governance/crisis-templates/) — deliberately generic; add your own agencies and items.
Pair it with ./securax incident (the exact regulator deadline clock) and ./securax playbook (the response checklist).
Standard library only. This is a coordination aid, not legal advice: your legal and compliance teams own the response.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = HERE / "crisis.json"
COMMS = HERE / "crisis-comms.json"
DOCS = HERE / "crisis-templates"
UTC = dt.timezone.utc


def runs_dir() -> pathlib.Path:
    base = pathlib.Path(os.environ.get("SECURAX_CRISIS_DIR") or (ROOT / "vault" / "crisis-runs"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def tz() -> dt.timezone:
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(os.environ.get("SECURAX_TZ", "Asia/Kolkata"))
    except Exception:  # noqa: BLE001
        return dt.timezone(dt.timedelta(hours=5, minutes=30))


def iso(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(s: str) -> str:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(tz()).strftime("%d %b %Y %H:%M %Z")


def lib() -> dict:
    return json.loads(LIB.read_text("utf-8"))


def fmt_left(seconds: float) -> str:
    sign = "-" if seconds < 0 else ""
    s = int(abs(seconds))
    h, m = s // 3600, (s % 3600) // 60
    return f"{sign}{h}h {m:02d}m" if h or sign else f"{m}m"


def parse_due(s: str | None, default_hours: int, now: dt.datetime) -> str:
    if not s:
        return iso(now + dt.timedelta(hours=default_hours))
    s = s.strip()
    m = re.fullmatch(r"(\d+)\s*([hd])", s, re.I)
    if m:
        n = int(m.group(1))
        return iso(now + dt.timedelta(hours=n if m.group(2).lower() == "h" else n * 24))
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return iso(d if d.tzinfo else d.replace(tzinfo=tz()))
    except ValueError as e:
        raise SystemExit(f"bad --due {s!r}: use e.g. 72h, 3d, or 2026-11-10T17:00") from e


def run_path(cid: str) -> pathlib.Path:
    return runs_dir() / f"{cid}.json"


def load_run(cid: str) -> dict:
    p = run_path(cid)
    if not p.exists():
        raise SystemExit(f"no such requisition {cid} (see: ./securax crisis list)")
    return json.loads(p.read_text("utf-8"))


def save_run(run: dict) -> None:
    p = run_path(run["id"])
    p.write_text(json.dumps(run, indent=1) + "\n", "utf-8")
    os.chmod(p, 0o600)


def runs() -> list[dict]:
    return sorted((json.loads(p.read_text("utf-8")) for p in runs_dir().glob("CRISIS-*.json")), key=lambda r: r["id"])


def _build(template: str, agency: str, ref: str, title: str, due: str, now: dt.datetime) -> dict:
    t = lib()["requisitions"][template]
    n = 1 + sum(1 for r in runs() if r["id"].startswith(f"CRISIS-{now:%Y%m%d}"))
    cid = f"CRISIS-{now:%Y%m%d}-{n:03d}"
    sections = [{"id": s["id"], "title": s["title"], "owner": s["owner"], "spoc": "",
                 "items": [{"id": it["id"], "q": it["q"], "record": it["record"], "owner": s["owner"],
                            "status": "pending", "note": "", "evidence": "", "updated_at": ""} for it in s["items"]]}
                for s in t["sections"]]
    run = {"id": cid, "template": template, "name": t["name"], "tier": t["tier"], "agency": agency, "ref": ref,
           "title": title or t["name"], "opened_at": iso(now), "due_at": parse_due(due, t.get("default_due_hours", 72), now),
           "sections": sections}
    save_run(run)
    return run


def cmd_new(a, now: dt.datetime) -> int:
    if a.template not in lib()["requisitions"]:
        print(f"unknown template {a.template!r}; known: {', '.join(lib()['requisitions'])}")
        return 2
    run = _build(a.template, a.agency, a.ref, a.title, a.due, now)
    n_items = sum(len(s["items"]) for s in run["sections"])
    print(f"Opened {run['id']}: {run['name']} for {a.agency} (ref {a.ref}).")
    print(f"  {len(run['sections'])} sections, {n_items} items; due {local(run['due_at'])}.")
    print(f"  Start the regulator clock too:  ./securax incident open \"{run['title']}\"")
    print(f"  Next action:  {next_action(run, now)}")
    return 0


def next_action(run: dict, now: dt.datetime) -> str:
    """The single most useful thing to do on this requisition right now — zero thinking required."""
    owners = lib()["owners"]
    items = [i for s in run["sections"] for i in s["items"]]
    _, _, pend = _counts(items)
    if pend == 0:
        return f"all items resolved — generate the pack:  ./securax crisis pack {run['id']}"
    left = (dt.datetime.fromisoformat(run["due_at"].replace("Z", "+00:00")) - now).total_seconds()
    s = max(run["sections"], key=lambda x: _counts(x["items"])[2])
    p = _counts(s["items"])[2]
    who = s.get("spoc") or owners.get(s["owner"], s["owner"])
    head = f"OVERDUE by {fmt_left(left)} — escalate and close" if left < 0 else f"{fmt_left(left)} to deadline — work"
    return f"{head}: '{s['title']}' ({p} items) → {who}   (./securax crisis assign {run['id']} {s['id']} --to \"<SPOC>\")"


def cmd_next(a, now: dt.datetime) -> int:
    rs = [load_run(a.id)] if a.id else runs()
    open_rs = [r for r in rs if _counts([i for s in r["sections"] for i in s["items"]])[2] > 0]
    if not open_rs:
        print("No open requisition needs you. If a crisis is unfolding, stand it up in one step:")
        print("  ./securax crisis start <scenario>        (scenarios: " + ", ".join(lib()["scenarios"]) + ")")
        return 0
    open_rs.sort(key=lambda r: r["due_at"])     # nearest deadline first
    r = open_rs[0]
    print(f"▶ {r['id']}  {r['name']} — {r['agency']} (ref {r['ref']})")
    print(f"  {next_action(r, now)}")
    print("  Also: regulator deadlines →  ./securax incident due    ·    first messages →  ./securax crisis comms")
    if len(open_rs) > 1:
        print(f"  ({len(open_rs) - 1} other open requisition(s); see ./securax crisis status)")
    return 0


def _comms() -> dict:
    return json.loads(COMMS.read_text("utf-8"))


def cmd_comms(a, now: dt.datetime) -> int:
    data = _comms()
    drafts = data["drafts"]
    if a.id:
        d = next((x for x in drafts if x["id"] == a.id), None)
        if not d:
            print(f"no draft {a.id!r}. See: ./securax crisis comms")
            return 2
        sel = [d]
    else:
        sel = [d for d in drafts
               if (not a.audience or a.audience.lower() in d["audience"].lower())
               and (not a.medium or a.medium.lower() in d["medium"].lower())
               and (not a.scenario or d["scenario"] in (a.scenario, "any"))]
    if not a.id and not (a.audience or a.medium or a.scenario):
        print("Crisis-communication drafts (./securax crisis comms <id>, or --audience/--medium/--scenario):")
        for d in drafts:
            print(f"  {d['id']:<24} [{d['medium']:<26}] {d['audience']}  ·  {d['scenario']}")
        print("\nRules (every draft obeys these):")
        for r in data["rules"]:
            print(f"  - {r}")
        print(f"\n{data['severity_note']}")
        return 0
    for d in sel:
        print(f"\n===== {d['id']}  ·  {d['audience']}  ·  {d['medium']}  ·  scenario: {d['scenario']} =====")
        if d.get("subject"):
            print(f"Subject: {d['subject']}")
        print(d["body"])
        if d.get("notes"):
            print(f"\n[guidance] {d['notes']}")
    print("\nFill the <…> placeholders; legal / compliance / comms approve before it goes out. One source of truth across channels.")
    return 0 if sel else 2


def cmd_start(a, now: dt.datetime) -> int:
    scen = lib()["scenarios"]
    if a.scenario not in scen:
        print(f"unknown scenario {a.scenario!r}; known: {', '.join(scen)}")
        return 2
    sc = scen[a.scenario]
    title = a.title or f"{a.scenario} incident"
    print(f"Standing up the crisis for: {title}\n")
    opened = []
    for tmpl in sc["requisitions"]:
        run = _build(tmpl, a.agency or "<fill: agency>", a.ref or "<fill: ref>", title, "", now)
        opened.append(run)
        print(f"  ✔ requisition {run['id']}: {run['name']}  (due {local(run['due_at'])})")
    print("\nNow, in order:")
    kind = f" --kind {sc['incident_kind']}" if sc.get("incident_kind") else ""
    print(f"  1. Start the regulator clock:   ./securax incident open \"{title}\"{kind}")
    pb = sc.get("playbook")
    print(f"  2. Open the response checklist:  ./securax playbook start {pb} \"{title}\"" if pb else
          "  2. Open the response checklist:  ./securax playbook list   (pick the closest scenario)")
    print("  3. First messages to send:       ./securax crisis comms exec-sitrep   &&   ./securax crisis comms staff-alert-sms")
    print("  4. What to do right now:         ./securax crisis next")
    if not a.agency:
        print("\n  Set each agency and reference as the notices arrive:  ./securax crisis status   then edit, or re-open with --agency/--ref.")
    return 0


def _counts(items: list[dict]) -> tuple[int, int, int]:
    done = sum(1 for i in items if i["status"] == "done")
    na = sum(1 for i in items if i["status"] == "na")
    return done, na, len(items) - done - na


def cmd_status(a, now: dt.datetime) -> int:
    rs = [load_run(a.id)] if a.id else [r for r in runs()]
    if not rs:
        print("no open requisitions. Open one:  ./securax crisis new <template> --agency \"…\" --ref \"…\"")
        return 0
    if a.json:
        print(json.dumps(rs, indent=2))
        return 0
    owners = lib()["owners"]
    worst = 0
    for run in rs:
        items = [i for s in run["sections"] for i in s["items"]]
        done, na, pend = _counts(items)
        left = (dt.datetime.fromisoformat(run["due_at"].replace("Z", "+00:00")) - now).total_seconds()
        clock = "🔴 OVERDUE by " + fmt_left(left) if left < 0 else ("🟡 " + fmt_left(left) + " left")
        if left < 0 and pend:
            worst = 2
        elif pend and left < 12 * 3600:
            worst = max(worst, 1)
        print(f"\n{run['id']}  {run['name']}  — {run['agency']} (ref {run['ref']})")
        print(f"  due {local(run['due_at'])}   {clock}    {done}/{len(items)} done, {pend} pending, {na} n/a")
        for s in run["sections"]:
            d, nn, p = _counts(s["items"])
            who = s.get("spoc") or owners.get(s["owner"], s["owner"])
            bar = "✅" if p == 0 else ("🟡" if d or nn else "⬜")
            print(f"    {bar} {s['title']:<44} {who:<26} {d}/{len(s['items'])}" + (f"  · {p} pending" if p else ""))
        overdue_pending = [i for i in items if i["status"] == "pending"] if left < 0 else []
        if overdue_pending:
            print(f"  ⚠ {len(overdue_pending)} item(s) still open past the deadline — escalate or request an extension.")
        if pend:
            print(f"  ▶ next: {next_action(run, now)}")
    return worst


def _find(run: dict, target: str):
    for s in run["sections"]:
        if s["id"] == target:
            return s, None
        for i in s["items"]:
            if i["id"] == target:
                return s, i
    return None, None


def cmd_assign(a, now: dt.datetime) -> int:
    run = load_run(a.id)
    s, i = _find(run, a.target)
    if not s:
        print(f"no section or item {a.target!r} in {a.id}")
        return 2
    if i is None:
        s["spoc"] = a.to
        for it in s["items"]:
            it["owner"] = a.to
        print(f"{a.id}: section {s['id']} ({s['title']}) assigned to {a.to}")
    else:
        i["owner"] = a.to
        print(f"{a.id}: item {i['id']} assigned to {a.to}")
    save_run(run)
    return 0


def cmd_set(a, now: dt.datetime) -> int:
    run = load_run(a.id)
    _, i = _find(run, a.item)
    if i is None:
        print(f"no item {a.item!r} in {a.id}")
        return 2
    if a.done:
        i["status"] = "done"
    elif a.na:
        i["status"] = "na"
    elif a.pending:
        i["status"] = "pending"
    if a.owner:
        i["owner"] = a.owner
    if a.evidence is not None:
        i["evidence"] = a.evidence
    if a.note is not None:
        i["note"] = a.note
    i["updated_at"] = iso(now)
    save_run(run)
    print(f"{a.id}: {i['id']} → {i['status']}" + (f"  evidence: {i['evidence']}" if i["evidence"] else ""))
    return 0


def cmd_pack(a, now: dt.datetime) -> int:
    run = load_run(a.id)
    owners = lib()["owners"]
    out = runs_dir() / run["id"] / "pack"
    out.mkdir(parents=True, exist_ok=True)
    # response register (Markdown)
    md = [f"# Response register (Annexure R) — {run['id']}", "",
          f"**To:** {run['agency']}  ·  **Their ref:** {run['ref']}  ·  **Due:** {local(run['due_at'])}",
          f"**From:** `<ORGANISATION>`  ·  **Prepared:** {local(iso(now))}", "",
          "| Item | Question | Record to attach | Owner | Status | Evidence ref |",
          "|---|---|---|---|---|---|"]
    rows = []
    for s in run["sections"]:
        md.append(f"| **{s['title']}** | | | | | |")
        for i in s["items"]:
            who = i.get("owner") or owners.get(s["owner"], s["owner"])
            st = {"done": "provided", "na": "not applicable", "pending": "in progress"}[i["status"]]
            md.append(f"| {i['id']} | {i['q']} | {i['record']} | {who} | {st} | {i.get('evidence', '')} |")
            rows.append([i["id"], s["title"], i["q"], i["record"], who, st, i.get("evidence", "")])
    (out / "response-register.md").write_text("\n".join(md) + "\n", "utf-8")
    with open(out / "response-register.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "section", "question", "record", "owner", "status", "evidence"])
        w.writerows(rows)
    # cover letter from the template, with the agency/ref filled in
    cover = (DOCS / "agency-cover-letter.md").read_text("utf-8")
    cover = cover.replace("`<AGENCY / OFFICE>`", run["agency"]).replace("`<NOTICE / REQUISITION REF>`", run["ref"])
    (out / "cover-letter.md").write_text(cover, "utf-8")
    done, na, pend = _counts([i for s in run["sections"] for i in s["items"]])
    print(f"Wrote the response pack for {run['id']} ({done} provided, {pend} in progress, {na} n/a):")
    for name in ("cover-letter.md", "response-register.md", "response-register.csv"):
        print(f"  {out / name}")
    print("  Fill the evidence references, attach each record, and have legal sign the cover letter before it goes out.")
    return 0


def cmd_doc(a, now: dt.datetime) -> int:
    p = DOCS / f"{a.name}.md"
    if not p.exists():
        avail = ", ".join(sorted(x.stem for x in DOCS.glob("*.md")))
        print(f"no document {a.name!r}. Available: {avail}")
        return 2
    print(p.read_text("utf-8"))
    return 0


def cmd_templates(a, now: dt.datetime) -> int:
    data = lib()
    print("Requisition templates (./securax crisis new <id> …):")
    for tid, t in data["requisitions"].items():
        n = sum(len(s["items"]) for s in t["sections"])
        print(f"  [{t['tier']:<8}] {tid:<26} {t['name']}  ({len(t['sections'])} sections, {n} items)")
    print("\nReady documents (./securax crisis doc <name>):")
    for p in sorted(DOCS.glob("*.md")):
        print(f"  {p.stem}")
    return 0


def cmd_list(a, now: dt.datetime) -> int:
    rs = runs()
    if not rs:
        print("no requisitions yet. Open one:  ./securax crisis new <template> --agency \"…\" --ref \"…\"")
        return 0
    for r in rs:
        items = [i for s in r["sections"] for i in s["items"]]
        done, na, pend = _counts(items)
        print(f"  {r['id']}  {r['name']:<42} {r['agency']:<22} due {local(r['due_at'])}  {done}/{len(items)} done")
    return 0


def main(argv: list[str] | None = None, now: dt.datetime | None = None) -> int:
    now = now or dt.datetime.now(UTC)
    ap = argparse.ArgumentParser(prog="crisis", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("templates")
    sub.add_parser("list")
    nx = sub.add_parser("next")
    nx.add_argument("id", nargs="?")
    cm = sub.add_parser("comms")
    cm.add_argument("id", nargs="?")
    cm.add_argument("--audience", default="")
    cm.add_argument("--medium", default="")
    cm.add_argument("--scenario", default="")
    sr = sub.add_parser("start")
    sr.add_argument("scenario")
    sr.add_argument("--agency", default="")
    sr.add_argument("--ref", default="")
    sr.add_argument("--title", default="")
    d = sub.add_parser("doc")
    d.add_argument("name")
    nw = sub.add_parser("new")
    nw.add_argument("template")
    nw.add_argument("--agency", required=True)
    nw.add_argument("--ref", required=True)
    nw.add_argument("--due", default="")
    nw.add_argument("--title", default="")
    st = sub.add_parser("status")
    st.add_argument("id", nargs="?")
    st.add_argument("--json", action="store_true")
    asg = sub.add_parser("assign")
    asg.add_argument("id")
    asg.add_argument("target")
    asg.add_argument("--to", required=True)
    se = sub.add_parser("set")
    se.add_argument("id")
    se.add_argument("item")
    se.add_argument("--done", action="store_true")
    se.add_argument("--na", action="store_true")
    se.add_argument("--pending", action="store_true")
    se.add_argument("--owner", default="")
    se.add_argument("--evidence", default=None)
    se.add_argument("--note", default=None)
    pk = sub.add_parser("pack")
    pk.add_argument("id")
    a = ap.parse_args(argv)
    fn = {"templates": cmd_templates, "list": cmd_list, "doc": cmd_doc, "new": cmd_new, "status": cmd_status,
          "assign": cmd_assign, "set": cmd_set, "pack": cmd_pack, "next": cmd_next, "comms": cmd_comms, "start": cmd_start}[a.cmd]
    return fn(a, now)


if __name__ == "__main__":
    sys.exit(main())
