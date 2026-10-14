#!/usr/bin/env python3
"""Regulatory incident clock — who must be told what, by when, and proof that you did.

When a cyber incident is detected the clock starts for EVERY regulator that applies to the entity at once: RBI (DAKSH, 6 h), SEBI
(6 h e-mail + 24 h portal + quarterly report), CERT-In (6 h), and any other you add. This tool opens a case, computes every deadline,
shows what is due and overdue, drafts each notification with the case's facts filled in (and the gaps called out), records each
filing, keeps a tamper-evident log, and seals the evidence.

    ./securax incident regulators                                   what is loaded, and whether each rule was verified against primary text
    ./securax incident open "title" --regulators rbi-nbfc,sebi-cscrf,cert-in [--detected "2026-10-14T09:30+05:30"] [--severity high]
    ./securax incident status [ID] [--json]
    ./securax incident due [--within 2]        exit 2 if anything is overdue, 1 if something falls due within N hours (default 1), else 0
    ./securax incident set ID key=value ...    record facts (systems_affected, impact, data_affected, actions_taken, contact, entity_name, ...)
    ./securax incident draft ID --regulator ID [--obligation ID]    notification text; missing facts are marked <<MISSING: ...>>
    ./securax incident file ID --regulator ID --obligation ID --reference REF [--at TIME]    you filed it: records it and whether it was on time
    ./securax incident note ID "text"          ./securax incident close ID          ./securax incident verify ID
    ./securax incident seal ID --evidence FILE... [--out DIR]       hash and copy the logs/screenshots you are preserving
    ./securax incident rollup --regulator sebi-cscrf --period 2026Q3    the periodic report's inputs and due date

Regulators are DATA (governance/regulators/*.json): adding another regulator or another jurisdiction needs no code. A rule marked
`verified: false` was taken from secondary sources; it is shown with a warning every time and must be confirmed against the primary text.
Times are stored in UTC and shown in the entity's time zone (SECURAX_TZ, default Asia/Kolkata). The clock runs continuously (no
business-hours relief). The case log is hash-chained: editing or deleting an entry is detected by `verify`.
This is a clock and a drafting aid, NOT legal advice and not a filing: you file with the regulator. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REG_DIR = HERE / "regulators"
UTC = timezone.utc


def tz():
    name = os.environ.get("SECURAX_TZ", "Asia/Kolkata")
    try:
        return ZoneInfo(name) if ZoneInfo else timezone(timedelta(hours=5, minutes=30))
    except Exception:  # noqa: BLE001
        return timezone(timedelta(hours=5, minutes=30))


def home() -> pathlib.Path:
    base = pathlib.Path(os.environ.get("SECURAX_INCIDENT_DIR") or (pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax") / "incidents"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def parse_time(s: str | None, now: datetime | None = None) -> datetime:
    if not s or s == "now":
        return now or datetime.now(UTC)
    t = datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T"))
    return (t if t.tzinfo else t.replace(tzinfo=tz())).astimezone(UTC)


def iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(t: datetime) -> str:
    return t.astimezone(tz()).strftime("%d %b %Y %H:%M %Z")


# ---------------------------------------------------------------------------------------------------------------- regulators
def load_regulators(extra_dir: pathlib.Path | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    dirs = [REG_DIR] + ([extra_dir] if extra_dir else []) + ([pathlib.Path(os.environ["SECURAX_REGULATORS_DIR"])] if os.environ.get("SECURAX_REGULATORS_DIR") else [])
    for d in dirs:
        for f in sorted(d.glob("*.json")):
            if f.name.endswith(".example.json"):
                continue
            r = json.loads(f.read_text("utf-8"))
            out[r["id"]] = r
    return out


def regulator_problems(r: dict) -> list[str]:
    out = []
    for k in ("id", "name", "obligations", "verified"):
        if k not in r:
            out.append(f"{r.get('id', '?')}: missing '{k}'")
    ids = [o.get("id") for o in r.get("obligations", [])]
    for o in r.get("obligations", []):
        for k in ("id", "label", "from", "within_hours", "channel"):
            if k not in o:
                out.append(f"{r.get('id')}/{o.get('id', '?')}: missing '{k}'")
        src = o.get("from", "")
        if src != "detection" and not (src.startswith("after:") and src[6:] in ids):
            out.append(f"{r.get('id')}/{o.get('id')}: 'from' must be 'detection' or 'after:<obligation id>'")
        if not isinstance(o.get("within_hours"), (int, float)) or o.get("within_hours") < 0:
            out.append(f"{r.get('id')}/{o.get('id')}: within_hours must be a non-negative number")
    if r.get("verified") and not r.get("verified_on"):
        out.append(f"{r.get('id')}: verified without a date")
    return out


# ------------------------------------------------------------------------------------------------------------------ case log
def _hash(prev: str, body: dict) -> str:
    return hashlib.sha256((prev + json.dumps(body, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()


class Case:
    def __init__(self, path: pathlib.Path):
        self.path = path

    @property
    def id(self) -> str:
        return self.path.stem

    def events(self) -> list[dict]:
        return [json.loads(ln) for ln in self.path.read_text("utf-8").splitlines() if ln.strip()] if self.path.exists() else []

    def append(self, kind: str, data: dict, actor: str = "", at: datetime | None = None) -> dict:
        ev = self.events()
        prev = ev[-1]["hash"] if ev else "0" * 64
        body = {"seq": len(ev) + 1, "ts": iso(at or datetime.now(UTC)), "actor": actor or os.environ.get("USER", "unknown"), "kind": kind, "data": data}
        rec = {**body, "prev": prev, "hash": _hash(prev, body)}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        os.chmod(self.path, 0o600)
        return rec

    def verify(self) -> list[str]:
        prev, problems = "0" * 64, []
        for i, e in enumerate(self.events(), 1):
            body = {k: e[k] for k in ("seq", "ts", "actor", "kind", "data")}
            if e.get("seq") != i:
                problems.append(f"entry {i}: sequence broken (an entry was removed or reordered)")
            if e.get("prev") != prev:
                problems.append(f"entry {i}: does not follow the previous entry")
            if e.get("hash") != _hash(e.get("prev", ""), body):
                problems.append(f"entry {i}: content was altered")
            prev = e.get("hash", "")
        return problems

    def state(self) -> dict:
        st: dict = {"id": self.id, "facts": {}, "filings": [], "notes": [], "evidence": [], "closed": False, "regulators": []}
        for e in self.events():
            d = e["data"]
            if e["kind"] == "open":
                st.update(title=d["title"], detected_at=d["detected_at"], severity=d.get("severity", ""), regulators=d["regulators"], opened_at=e["ts"],
                          rules=d.get("rules", {}), entity_roles=d.get("entity_roles", []))
            elif e["kind"] == "set":
                st["facts"].update(d)
            elif e["kind"] == "file":
                st["filings"].append({**d, "ts": e["ts"]})
            elif e["kind"] == "note":
                st["notes"].append({"ts": e["ts"], "text": d["text"]})
            elif e["kind"] == "evidence_sealed":
                st["evidence"].append(d)
            elif e["kind"] == "close":
                st["closed"], st["closed_at"] = True, e["ts"]
        return st


def deadlines(st: dict, regs: dict[str, dict], now: datetime) -> list[dict]:
    """Every obligation of every regulator on the case, with due time, status and (if filed) whether it was on time."""
    out = []
    detected = parse_time(st["detected_at"])
    filed = {(f["regulator"], f["obligation"]): parse_time(f.get("filed_at") or f["ts"]) for f in st["filings"]}
    for rid in st["regulators"]:
        r = st.get("rules", {}).get(rid) or regs.get(rid)   # the rule in force when the incident was opened
        if not r:
            out.append({"regulator": rid, "obligation": "?", "label": "regulator definition not found", "due": None, "status": "unknown", "verified": False})
            continue
        for o in r["obligations"]:
            if o.get("applies_to_roles") and not (set(o["applies_to_roles"]) & set(st.get("entity_roles", []))):
                continue                                   # e.g. only stock brokers / depository participants report to the exchange
            if o.get("conditional") and st["facts"].get(f"applies:{rid}/{o['id']}") != "yes":
                out.append({"regulator": rid, "obligation": o["id"], "label": o["label"], "channel": o["channel"], "due": None, "status": "conditional",
                            "verified": bool(r.get("verified")), "remaining_s": None, "condition": o["conditional"]})
                continue
            base = detected
            if o["from"].startswith("after:"):
                prev = filed.get((rid, o["from"][6:]))
                base = prev
            due = base + timedelta(hours=o["within_hours"]) if base else None
            f = filed.get((rid, o["id"]))
            if f:
                status = "on_time" if due and f <= due else "late"
            elif due is None:
                status = "waiting"
            else:
                status = "overdue" if now > due else "open"
            out.append({"regulator": rid, "obligation": o["id"], "label": o["label"], "channel": o["channel"], "due": iso(due) if due else None,
                        "status": status, "filed_at": iso(f) if f else None, "verified": bool(r.get("verified")),
                        "remaining_s": int((due - now).total_seconds()) if due and not f else None})
    return out


def fmt_remaining(s: int | None) -> str:
    if s is None:
        return ""
    sign = "-" if s < 0 else ""
    s = abs(s)
    return f"{sign}{s // 3600}h {s % 3600 // 60:02d}m"


# --------------------------------------------------------------------------------------------------------------------- draft
def draft(st: dict, r: dict, o: dict) -> str:
    facts = {**st["facts"], "id": st["id"], "detected_at": local(parse_time(st["detected_at"])), "title": st["title"]}
    if not facts.get("entity_name") and os.environ.get("SECURAX_ENTITY_NAME"):
        facts["entity_name"] = os.environ["SECURAX_ENTITY_NAME"]
    lines = [f"To: {o['channel']}", f"Re: {r['name']} — {o['label']}", f"Incident: {st['id']}  Severity: {st.get('severity') or '<<MISSING: severity>>'}", ""]
    missing = []
    for f in o.get("fields", []):
        v = facts.get(f["key"]) or facts.get(f.get("from", ""))
        if not v:
            missing.append(f["label"])
        lines.append(f"{f['label']}: {v or '<<MISSING: ' + f['label'] + '>>'}")
    due = next((d for d in deadlines(st, {r["id"]: r}, datetime.now(UTC)) if d["obligation"] == o["id"]), None)
    if due and due["due"]:
        lines += ["", f"Due: {local(parse_time(due['due']))}  ({due['status']})"]
    if o.get("notes"):
        lines += ["", "Note: " + o["notes"]]
    if not r.get("verified"):
        lines += ["", "!! This regulator's rule is UNVERIFIED against the primary text. Confirm the period and channel before relying on it."]
    if missing:
        lines += ["", f"!! {len(missing)} item(s) still missing: set them with  ./securax incident set {st['id']} key=value"]
    lines += ["", "(Draft prepared by SecuRAX. You file it; filing is your responsibility.)"]
    return "\n".join(lines)


def quarter_bounds(period: str) -> tuple[datetime, datetime]:
    y, q = int(period[:4]), int(period[-1])
    start = datetime(y, 3 * (q - 1) + 1, 1, tzinfo=tz())
    end = datetime(y + (q == 4), (3 * q) % 12 + 1, 1, tzinfo=tz())
    return start.astimezone(UTC), end.astimezone(UTC)


# --------------------------------------------------------------------------------------------------------------------- CLI
def cases() -> list[Case]:
    return [Case(p) for p in sorted(home().glob("INC-*.jsonl"))]


def get_case(cid: str) -> Case:
    p = home() / f"{cid}.jsonl"
    if not p.exists():
        raise SystemExit(f"no such case {cid}")
    return Case(p)


def warn_unverified(regs: dict, ids: list[str]) -> None:
    for i in ids:
        if i in regs and not regs[i].get("verified"):
            print(f"  ⚠ {i}: rule NOT verified against the primary text ({regs[i]['source']['title']}) — confirm before relying on its deadlines")


def cmd_open(a, now: datetime) -> int:
    regs = load_regulators()
    ids = [x for x in a.regulators.split(",") if x]
    unknown = [i for i in ids if i not in regs]
    if unknown or not ids:
        print(f"unknown regulator(s) {unknown or '(none given)'}; loaded: {', '.join(regs)}")
        return 2
    detected = parse_time(a.detected, now)
    n = 1 + sum(1 for c in cases() if c.id.startswith(f"INC-{now:%Y%m%d}"))
    c = Case(home() / f"INC-{now:%Y%m%d}-{n:03d}.jsonl")
    c.append("open", {"title": a.title, "detected_at": iso(detected), "severity": a.severity, "regulators": ids,
                      "entity_roles": [x for x in a.roles.split(",") if x], "rules": {i: regs[i] for i in ids}})
    print(f"Opened {c.id}: detected {local(detected)}  — the clock is running for: {', '.join(ids)}")
    warn_unverified(regs, ids)
    return show(c, now)


def show(c: Case, now: datetime, as_json: bool = False) -> int:
    st = c.state()
    regs = load_regulators()
    dl = deadlines(st, regs, now)
    if as_json:
        print(json.dumps({"case": st["id"], "title": st["title"], "detected_at": st["detected_at"], "closed": st["closed"], "deadlines": dl}, indent=2))
        return 0
    print(f"\n{st['id']}  {st['title']}  [{'closed' if st['closed'] else 'OPEN'}]  detected {local(parse_time(st['detected_at']))}")
    for d in sorted(dl, key=lambda x: x["due"] or "9"):
        mark = {"overdue": "🔴 OVERDUE", "open": "🟡 due", "on_time": "✅ filed on time", "late": "🟠 filed LATE", "waiting": "⏳ waits for earlier filing", "unknown": "?", "conditional": "◻ if applicable"}[d["status"]]
        due = local(parse_time(d["due"])) if d["due"] else "—"
        if d["status"] == "conditional":
            print(f"  {mark:<26} {d['regulator']}/{d['obligation']:<12} only if: {d['condition']}  (confirm with: incident set {st['id']} applies:{d['regulator']}/{d['obligation']}=yes)")
            continue
        rem = f"  ({fmt_remaining(d['remaining_s'])} left)" if d["remaining_s"] is not None and d["remaining_s"] >= 0 else (f"  ({fmt_remaining(d['remaining_s'])})" if d["remaining_s"] is not None else "")
        print(f"  {mark:<26} {d['regulator']}/{d['obligation']:<12} by {due}{rem}  → {d.get('channel', '')}" + ("" if d["verified"] else "  ⚠ unverified rule"))
    return 0


def cmd_status(a, now: datetime) -> int:
    cs = [get_case(a.id)] if a.id else [c for c in cases() if not c.state()["closed"]]
    if not cs:
        print("no open incidents")
        return 0
    for c in cs:
        show(c, now, a.json)
    return 0


def cmd_due(a, now: datetime) -> int:
    regs, worst = load_regulators(), 0
    for c in cases():
        st = c.state()
        if st["closed"]:
            continue
        for d in deadlines(st, regs, now):
            if d["status"] == "overdue":
                print(f"OVERDUE  {st['id']} {d['regulator']}/{d['obligation']} was due {local(parse_time(d['due']))}")
                worst = 2
            elif d["status"] == "open" and d["remaining_s"] is not None and d["remaining_s"] <= a.within * 3600:
                print(f"DUE SOON {st['id']} {d['regulator']}/{d['obligation']} in {fmt_remaining(d['remaining_s'])}")
                worst = max(worst, 1)
    if worst == 0:
        print("nothing due")
    return worst


def main(argv: list[str] | None = None, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("regulators")
    o = sub.add_parser("open")
    o.add_argument("title")
    o.add_argument("--regulators", default="")
    o.add_argument("--detected", default="now")
    o.add_argument("--severity", default="")
    o.add_argument("--roles", default="", help="the entity's roles where a rule is role-specific, e.g. stock-broker,depository-participant")
    s = sub.add_parser("status")
    s.add_argument("id", nargs="?")
    s.add_argument("--json", action="store_true")
    d = sub.add_parser("due")
    d.add_argument("--within", type=float, default=1.0)
    st = sub.add_parser("set")
    st.add_argument("id")
    st.add_argument("pairs", nargs="+")
    dr = sub.add_parser("draft")
    dr.add_argument("id")
    dr.add_argument("--regulator", required=True)
    dr.add_argument("--obligation", default="")
    fi = sub.add_parser("file")
    fi.add_argument("id")
    fi.add_argument("--regulator", required=True)
    fi.add_argument("--obligation", required=True)
    fi.add_argument("--reference", required=True)
    fi.add_argument("--at", default="now")
    nt = sub.add_parser("note")
    nt.add_argument("id")
    nt.add_argument("text")
    cl = sub.add_parser("close")
    cl.add_argument("id")
    vf = sub.add_parser("verify")
    vf.add_argument("id")
    se = sub.add_parser("seal")
    se.add_argument("id")
    se.add_argument("--evidence", nargs="+", required=True)
    se.add_argument("--out", default="")
    ro = sub.add_parser("rollup")
    ro.add_argument("--regulator", required=True)
    ro.add_argument("--period", required=True, help="e.g. 2026Q3")
    a = ap.parse_args(argv)

    if a.cmd == "regulators":
        for r in load_regulators().values():
            probs = regulator_problems(r)
            print(f"{r['id']:<12} {('verified ' + r['verified_on']) if r['verified'] else 'UNVERIFIED       '}  {r['name']}" + (f"   ✗ {probs}" if probs else ""))
            for ob in r["obligations"]:
                print(f"{'':<14}{ob['label']}: {ob['within_hours']} h from {ob['from']} → {ob['channel']}")
            for p in r.get("periodic", []):
                print(f"{'':<14}{p['label']}: {p['frequency']}, {p['due_days_after_period_end']} days after period end")
        return 0
    if a.cmd == "open":
        return cmd_open(a, now)
    if a.cmd == "status":
        return cmd_status(a, now)
    if a.cmd == "due":
        return cmd_due(a, now)
    if a.cmd == "rollup":
        regs = load_regulators()
        r = regs.get(a.regulator)
        per = next((p for p in (r or {}).get("periodic", []) if p["frequency"] == "quarterly"), None)
        if not per:
            print(f"{a.regulator} has no quarterly report defined")
            return 2
        start, end = quarter_bounds(a.period)
        due = end + timedelta(days=per["due_days_after_period_end"]) - timedelta(seconds=1)
        mine = [c.state() for c in cases() if a.regulator in c.state()["regulators"] and start <= parse_time(c.state()["detected_at"]) < end]
        print(f"{r['name']} — {per['label']} for {a.period} ({local(start)} to {local(end - timedelta(seconds=1))})\nDue {local(due)} → {per['channel']}   {per.get('notes', '')}")
        if not r.get("verified"):
            print("  ⚠ rule NOT verified against the primary text")
        print(f"Incidents detected in the period: {len(mine)}")
        for s in mine:
            late = any(x["status"] == "late" for x in deadlines(s, regs, now))
            print(f"  {s['id']}  {s['severity'] or '-':<8} {s['title']}  [{'closed' if s['closed'] else 'open'}]" + ("  (a filing was late)" if late else ""))
        return 0

    c = get_case(a.id)
    if a.cmd == "set":
        facts = dict(p.split("=", 1) for p in a.pairs if "=" in p)
        c.append("set", facts)
        print(f"recorded {', '.join(facts)}")
    elif a.cmd == "note":
        c.append("note", {"text": a.text})
        print("noted")
    elif a.cmd == "file":
        filed_at = parse_time(a.at, now)
        c.append("file", {"regulator": a.regulator, "obligation": a.obligation, "reference": a.reference, "filed_at": iso(filed_at)}, at=now)
        d = next((x for x in deadlines(c.state(), load_regulators(), now) if x["regulator"] == a.regulator and x["obligation"] == a.obligation), None)
        print(f"recorded: {a.regulator}/{a.obligation} filed {local(filed_at)} ref {a.reference} — {'ON TIME' if d and d['status'] == 'on_time' else 'LATE (record why with: incident note)' if d else 'unknown obligation'}")
    elif a.cmd == "close":
        c.append("close", {})
        print(f"{c.id} closed")
    elif a.cmd == "verify":
        probs = c.verify()
        print("log intact: every entry chains to the one before" if not probs else "TAMPERING DETECTED:\n  " + "\n  ".join(probs))
        return 1 if probs else 0
    elif a.cmd == "draft":
        stt = c.state()
        r = stt.get("rules", {}).get(a.regulator) or load_regulators().get(a.regulator)
        if not r:
            print(f"unknown regulator {a.regulator}")
            return 2
        obs = [x for x in r["obligations"] if not a.obligation or x["id"] == a.obligation]
        if not obs:
            print(f"{a.regulator} has no obligation {a.obligation!r}; choose from {[x['id'] for x in r['obligations']]}")
            return 2
        for ob in obs:
            print(draft(stt, r, ob) + "\n" + "-" * 70)
    elif a.cmd == "seal":
        out = pathlib.Path(a.out or (home() / f"{c.id}-evidence"))
        out.mkdir(parents=True, exist_ok=True)
        manifest = []
        for f in a.evidence:
            src = pathlib.Path(f)
            if not src.is_file():
                print(f"not a file: {f}")
                return 2
            dst = out / src.name
            shutil.copy2(src, dst)
            manifest.append({"file": src.name, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(), "bytes": dst.stat().st_size})
        (out / "MANIFEST.json").write_text(json.dumps({"case": c.id, "sealed_at": iso(now), "files": manifest}, indent=1), "utf-8")
        c.append("evidence_sealed", {"dir": str(out), "files": manifest})
        print(f"sealed {len(manifest)} file(s) into {out} — hashes are in the case log; copy the folder to write-once media")
    return 0


if __name__ == "__main__":
    sys.exit(main())
