#!/usr/bin/env python3
"""The findings register: every vulnerability from every source, once, with a fix-by date.

    ./securax findings import [FILE]       SARIF (Trivy, Semgrep, Gitleaks, CodeQL, Bandit...), CSV, or a VAPT report as .xlsx
                                           (no file: it looks in Downloads and Documents for one)
    ./securax findings add "title" --severity high [--asset X] [--cve CVE-YYYY-NNNN]
    ./securax findings                     the open ones, overdue first
    ./securax findings overdue             only those past their fix-by date (exit 1 when there is one, for a routine)
    ./securax findings accept ID --reason "why" --until YYYY-MM-DD [--by NAME]
    ./securax findings fixed ID
    ./securax findings report              the audit view: open by severity, SLA met, days to fix, acceptances ending soon

Modelled on DefectDojo, kept to what an auditor asks for:

- **One record per problem.** The same rule on the same asset and location is one finding, however many scans report it.
- **A fix-by date from the severity.** Critical 7 days, high 30, medium 90, low 180. Change them in vault/findings/sla.json.
  A CVE on CISA's known-exploited list is treated as critical, whatever the scanner said (needs `./securax offline sync kev`).
  One with an EPSS score of 50% or more (FIRST's estimate that it is exploited within 30 days) is at least high
  (`./securax offline sync epss`).
- **Re-importing closes what is gone.** When a new scan from the same tool no longer reports a finding, it is marked fixed.
  If it comes back, it reopens with a new fix-by date.
- **Risk acceptance is time-boxed.** It needs a reason, a person and an end date at most a year away. When the date passes,
  the finding is open again.

Kept in vault/findings/register.json (private, never committed; included in `./securax backup`). Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "vault" / "findings" / "register.json"
SLA_FILE = REG.parent / "sla.json"
SLA = {"critical": 7, "high": 30, "medium": 90, "low": 180}
ORDER = ["critical", "high", "medium", "low"]
MAX_ACCEPT_DAYS = 365
CVE = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)
HEAD = {   # header words that name each column in a CSV or workbook (first match wins)
    "title": r"title|finding|vulnerabilit|observation|issue|name",
    "severity": r"severity|risk rating|rating|risk|priority|criticality",
    "asset": r"asset|host|ip|url|application|system|component|target",
    "location": r"location|path|port|endpoint|parameter",
    "cve": r"cve",
    "due": r"due|target date|closure date",
}


def today() -> dt.date:
    return dt.date.today()


def sla(path: pathlib.Path | None = None) -> dict[str, int]:
    try:
        return {**SLA, **{k: int(v) for k, v in json.loads((path or SLA_FILE).read_text("utf-8")).items() if k in SLA}}
    except (OSError, ValueError):
        return dict(SLA)


def severity(raw) -> str | None:
    """'Critical', 'HIGH', 'Moderate', 'error', '9.8' -> critical/high/medium/low; informational -> None (no fix-by date)."""
    s = str(raw or "").strip().lower()
    try:
        n = float(s)
        return "critical" if n >= 9 else "high" if n >= 7 else "medium" if n >= 4 else "low" if n > 0 else None
    except ValueError:
        pass
    for word, sev in (("crit", "critical"), ("high", "high"), ("error", "high"), ("med", "medium"), ("moderate", "medium"),
                      ("warn", "medium"), ("low", "low"), ("note", "low")):
        if word in s:
            return sev
    return None


def key(source: str, rule: str, asset: str, location: str) -> str:
    return hashlib.sha256("|".join(x.strip().lower() for x in (source, rule, asset, location)).encode()).hexdigest()[:10]


EPSS_HIGH = 0.5          # a 50% chance of exploitation within 30 days is treated as at least high


def _intel(name: str) -> dict:
    try:
        sys.path.insert(0, str(ROOT / "ai-soc"))
        from soc import enrich
        return (enrich._load(name) or {}).get("by_cve", {})
    except Exception:  # noqa: BLE001 - no snapshot yet: scanner severities stand
        return {}
    finally:
        if sys.path and sys.path[0] == str(ROOT / "ai-soc"):
            sys.path.pop(0)


def kev_cves() -> set[str]:
    return set(_intel("kev"))


def epss_scores() -> dict[str, float]:
    return {k: (v[0] if isinstance(v, list) else v) for k, v in _intel("epss").items()}


def raise_for(sev: str, cve: str, kev: set, epss: dict) -> str:
    """The severity after threat intelligence: known-exploited -> critical; EPSS >= 50% -> at least high."""
    if cve and cve in kev:
        return "critical"
    if cve and epss.get(cve, 0) >= EPSS_HIGH and ORDER.index(sev) > ORDER.index("high"):
        return "high"
    return sev


# -- reading scans --------------------------------------------------------------------------------------------------------
def from_sarif(doc: dict) -> list[dict]:
    out = []
    for run in doc.get("runs", []):
        driver = (run.get("tool") or {}).get("driver") or {}
        rules = {r.get("id"): r for r in driver.get("rules") or []}
        for res in run.get("results") or []:
            rule = rules.get(res.get("ruleId"), {})
            props = {**(rule.get("properties") or {}), **(res.get("properties") or {})}
            loc = ((res.get("locations") or [{}])[0].get("physicalLocation") or {})
            uri = (loc.get("artifactLocation") or {}).get("uri", "")
            line = (loc.get("region") or {}).get("startLine")
            text = ((res.get("message") or {}).get("text") or (rule.get("shortDescription") or {}).get("text") or res.get("ruleId") or "")
            out.append({"source": driver.get("name") or "sarif", "rule": res.get("ruleId") or text[:60],
                        "title": text.strip().splitlines()[0][:160] if text.strip() else res.get("ruleId", "finding"),
                        "severity": severity(props.get("security-severity")) or severity(res.get("level") or rule.get("defaultConfiguration", {}).get("level")),
                        "asset": uri.split("/")[0] if "/" in uri else uri, "location": f"{uri}:{line}" if line else uri,
                        "cve": (CVE.search(str(res.get("ruleId")) + " " + text) or [""])[0].upper()})
    return out


def from_rows(rows: list[list], source: str) -> list[dict]:
    """A table whose header row names the columns (any order, any extra columns): CSV or a workbook sheet."""
    for hi, row in enumerate(rows[:15]):                                  # the header is the first row naming a title column
        names = [str(c or "").strip().lower() for c in row]
        col = {}
        for field, rx in HEAD.items():
            for i, n in enumerate(names):
                if n and re.search(rx, n) and i not in col.values():
                    col[field] = i
                    break
        if "title" in col and "severity" in col:
            break
    else:
        return []
    out = []
    for row in rows[hi + 1:]:
        get = lambda f: str(row[col[f]]).strip() if f in col and col[f] < len(row) and row[col[f]] is not None else ""  # noqa: E731
        title = get("title")
        if not title:
            continue
        out.append({"source": source, "rule": title[:80], "title": title[:160], "severity": severity(get("severity")),
                    "asset": get("asset"), "location": get("location"), "cve": (CVE.search(get("cve") + " " + title) or [""])[0].upper(),
                    "due": get("due")[:10] if re.match(r"\d{4}-\d{2}-\d{2}", get("due")) else ""})
    return out


def read(path: pathlib.Path, source: str = "") -> list[dict]:
    name = path.name.lower()
    if name.endswith((".sarif", ".sarif.json")) or (name.endswith(".json") and '"runs"' in path.read_text("utf-8", "ignore")[:4000]):
        found = from_sarif(json.loads(path.read_text("utf-8")))
        return [dict(f, source=source or f["source"]) for f in found]
    if name.endswith(".csv"):
        with path.open(newline="", encoding="utf-8-sig") as fh:
            return from_rows(list(csv.reader(fh)), source or path.stem)
    if name.endswith(".xlsx"):
        out = []
        for _sheet, rows in _controls().read_xlsx(path).items():
            out += from_rows(rows, source or path.stem)
        return out
    raise ValueError(f"{path.name}: use a .sarif, .csv or .xlsx file (most scanners can write SARIF: trivy --format sarif)")


def _controls():
    s = importlib.util.spec_from_file_location("controls", ROOT / "governance" / "controls.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# -- the register ---------------------------------------------------------------------------------------------------------
def load(path: pathlib.Path | None = None) -> dict:
    try:
        return json.loads((path or REG).read_text("utf-8"))
    except (OSError, ValueError):
        return {"findings": {}}


def save(reg: dict, path: pathlib.Path | None = None) -> None:
    p = path or REG
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=1, ensure_ascii=False), "utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)


def _due(sev: str, start: dt.date, days: dict) -> str:
    return (start + dt.timedelta(days=days[sev])).isoformat()


def merge(reg: dict, found: list[dict], on: dt.date | None = None, days: dict | None = None, kev: set | None = None,
          close_missing: bool = True, epss: dict | None = None) -> dict:
    """Add what is new, refresh what is known, reopen what came back and (per source) close what is gone. Returns counts."""
    on, days, kev = on or today(), days or sla(), kev if kev is not None else kev_cves()
    epss = epss if epss is not None else epss_scores()
    fs = reg.setdefault("findings", {})
    n = {"new": 0, "seen": 0, "reopened": 0, "fixed": 0, "skipped": 0}
    seen_now: dict[str, set] = {}
    for f in found:
        sev = f.get("severity")
        if sev:
            sev = raise_for(sev, f.get("cve", ""), kev, epss)
        if not sev:
            n["skipped"] += 1                                             # informational: nothing to fix by a date
            continue
        k = key(f["source"], f["rule"], f.get("asset", ""), f.get("location", ""))
        seen_now.setdefault(f["source"], set()).add(k)
        old = fs.get(k)
        if old is None:
            fs[k] = {"id": "F-" + k[:6], "title": f["title"], "severity": sev, "source": f["source"], "asset": f.get("asset", ""),
                     "location": f.get("location", ""), "cve": f.get("cve", ""), "kev": bool(f.get("cve") and f["cve"] in kev),
                     "epss": epss.get(f.get("cve", "")),
                     "first_seen": on.isoformat(), "last_seen": on.isoformat(), "status": "open",
                     "due": f.get("due") or _due(sev, on, days)}
            n["new"] += 1
            continue
        old["last_seen"] = on.isoformat()
        if f.get("cve") in epss:
            old["epss"] = epss[f["cve"]]                                 # the chance changes daily: keep the latest
        if old["status"] == "fixed":                                     # it came back: a regression, with a fresh clock
            old.update(status="open", reopened=old.get("reopened", 0) + 1, due=_due(sev, on, days))
            old.pop("fixed_on", None)
            n["reopened"] += 1
        else:
            n["seen"] += 1
        if ORDER.index(sev) < ORDER.index(old["severity"]):              # it got worse (e.g. now on the KEV list): the tighter date wins
            old["severity"], old["due"] = sev, min(old["due"], _due(sev, dt.date.fromisoformat(old["first_seen"]), days))
            old["kev"] = old.get("kev") or bool(f.get("cve") and f["cve"] in kev)
    if close_missing:
        for src, keys in seen_now.items():
            for k, f in fs.items():
                if f["source"] == src and f["status"] == "open" and k not in keys:
                    f.update(status="fixed", fixed_on=on.isoformat(), fixed_by="no longer reported by " + src)
                    n["fixed"] += 1
    return n


def status(f: dict, on: dt.date | None = None) -> str:
    """open / overdue / accepted / fixed, with an expired acceptance counting as open again."""
    on = (on or today()).isoformat()
    st = f["status"]
    if st == "accepted" and (f.get("accepted") or {}).get("until", "") < on:
        st = "open"
    if st == "open" and f.get("due", "9999") < on:
        return "overdue"
    return st


def find(reg: dict, ident: str) -> dict:
    ident = ident.strip().upper()
    hits = [f for f in reg.get("findings", {}).values() if f["id"].upper() == ident or f["id"].upper() == "F-" + ident]
    if not hits:
        raise KeyError(f"No finding {ident}. See them with:  ./securax findings")
    return hits[0]


def accept(reg: dict, ident: str, reason: str, until: str, by: str, on: dt.date | None = None) -> dict:
    on = on or today()
    end = dt.date.fromisoformat(until)
    if not reason.strip():
        raise ValueError("A risk acceptance needs a reason: --reason \"why it is safe to wait\"")
    if end <= on or (end - on).days > MAX_ACCEPT_DAYS:
        raise ValueError(f"--until must be after today and at most {MAX_ACCEPT_DAYS} days away (then decide again)")
    f = find(reg, ident)
    f.update(status="accepted", accepted={"reason": reason.strip(), "until": until, "by": by or "estate owner", "on": on.isoformat()})
    return f


def fixed(reg: dict, ident: str, on: dt.date | None = None) -> dict:
    f = find(reg, ident)
    f.update(status="fixed", fixed_on=(on or today()).isoformat(), fixed_by="marked fixed")
    f.pop("accepted", None)
    return f


def overdue(reg: dict, on: dt.date | None = None) -> list[dict]:
    return sorted((f for f in reg.get("findings", {}).values() if status(f, on) == "overdue"), key=lambda f: (f["due"], ORDER.index(f["severity"])))


def expiring(reg: dict, on: dt.date | None = None, within: int = 14) -> list[dict]:
    on = on or today()
    lim = (on + dt.timedelta(days=within)).isoformat()
    return [f for f in reg.get("findings", {}).values() if status(f, on) == "accepted" and f["accepted"]["until"] <= lim]


def summary(reg: dict, on: dt.date | None = None) -> dict:
    on = on or today()
    fs = list(reg.get("findings", {}).values())
    open_ = [f for f in fs if status(f, on) in ("open", "overdue")]
    done = [f for f in fs if f["status"] == "fixed" and f.get("fixed_on")]
    took = sorted((dt.date.fromisoformat(f["fixed_on"]) - dt.date.fromisoformat(f["first_seen"])).days for f in done)
    in_sla = sum(1 for f in done if f["fixed_on"] <= f["due"])
    return {"open": {s: sum(1 for f in open_ if f["severity"] == s) for s in ORDER}, "overdue": len(overdue(reg, on)),
            "accepted": sum(1 for f in fs if status(f, on) == "accepted"), "expiring": len(expiring(reg, on)),
            "fixed": len(done), "sla_met": round(100 * in_sla / len(done)) if done else None,
            "median_days_to_fix": took[len(took) // 2] if took else None, "kev_open": sum(1 for f in open_ if f.get("kev")),
            "likely_open": sum(1 for f in open_ if (f.get("epss") or 0) >= EPSS_HIGH)}


# -- the command line -----------------------------------------------------------------------------------------------------
def _line(f: dict, on: dt.date) -> str:
    st = status(f, on)
    when = f"due {f['due']}" if st in ("open", "overdue") else (f"accepted until {f['accepted']['until']}" if st == "accepted" else f"fixed {f.get('fixed_on', '')}")
    tag = {"overdue": "✗ OVERDUE", "open": "○ open", "accepted": "◐ accepted", "fixed": "✔ fixed"}[st]
    return (f"  {f['id']}  {tag:<11} {f['severity']:<8} {when:<26} {f['title'][:70]}" + (f"  [{f['asset']}]" if f.get("asset") else "")
            + ("  KEV" if f.get("kev") else "") + (f"  EPSS {f['epss']:.0%}" if f.get("epss") else ""))


def find_reports() -> list[pathlib.Path]:
    out = []
    for d in _controls().search_dirs():
        for pat in ("*.sarif", "*.sarif.json", "*VAPT*.xlsx", "*vapt*.xlsx", "*finding*.xlsx", "*finding*.csv"):
            out += [p for p in d.glob(pat) if p.is_file()]
    return sorted(set(out), key=lambda p: p.stat().st_mtime, reverse=True)[:5]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="./securax findings", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("import")
    p.add_argument("file", nargs="?")
    p.add_argument("--source", default="")
    p = sub.add_parser("add")
    p.add_argument("title")
    p.add_argument("--severity", required=True)
    p.add_argument("--asset", default="")
    p.add_argument("--cve", default="")
    p = sub.add_parser("list")
    p.add_argument("--all", action="store_true")
    sub.add_parser("overdue")
    p = sub.add_parser("accept")
    p.add_argument("id")
    p.add_argument("--reason", required=True)
    p.add_argument("--until", required=True)
    p.add_argument("--by", default="")
    p = sub.add_parser("fixed")
    p.add_argument("id")
    sub.add_parser("report")
    a = ap.parse_args(argv or ["list"])
    reg, on = load(), today()
    try:
        if a.cmd == "import":
            paths = [pathlib.Path(a.file).expanduser()] if a.file else find_reports()
            if not paths:
                print("No scan or VAPT report found in Downloads or Documents.\n"
                      "  Save one there (.sarif, .csv or .xlsx) and run this again, or name it:  ./securax findings import PATH")
                return 1
            if not paths[0].is_file():
                print(f"Not a file: {paths[0]}   (a .sarif, .csv or .xlsx scan or VAPT report)")
                return 1
            path = paths[0]
            got = read(path, a.source)
            if not got:
                print(f"{path.name}: no findings read. A CSV or workbook needs a header row with a title and a severity column.")
                return 1
            n = merge(reg, got, on)
            save(reg)
            print(f"✔ {path.name}: {n['new']} new, {n['seen']} already known, {n['reopened']} back again, {n['fixed']} gone (marked fixed)"
                  + (f", {n['skipped']} informational skipped" if n["skipped"] else ""))
            late = overdue(reg, on)
            print(f"  {len(late)} overdue. See them:  ./securax findings overdue" if late else "  Nothing overdue.")
            return 0
        if a.cmd == "add":
            sev = severity(a.severity)
            if not sev:
                print("--severity must be critical, high, medium or low")
                return 2
            n = merge(reg, [{"source": "manual", "rule": a.title, "title": a.title, "severity": sev, "asset": a.asset,
                             "location": "", "cve": a.cve.upper()}], on, close_missing=False)
            save(reg)
            f = reg["findings"][key("manual", a.title, a.asset, "")]
            print(f"✔ {f['id']} {f['severity']}, fix by {f['due']}" if n["new"] else f"Already in the register as {f['id']}.")
            return 0
        if a.cmd == "accept":
            f = accept(reg, a.id, a.reason, a.until, a.by, on)
            save(reg)
            print(f"✔ {f['id']} accepted until {a.until} by {f['accepted']['by']}. It reopens by itself on that date.")
            return 0
        if a.cmd == "fixed":
            f = fixed(reg, a.id, on)
            save(reg)
            print(f"✔ {f['id']} marked fixed. A later scan that still reports it will reopen it.")
            return 0
        if a.cmd == "overdue":
            late = overdue(reg, on)
            print(f"{len(late)} finding(s) past their fix-by date:" if late else "Nothing overdue.")
            for f in late:
                print(_line(f, on))
            return 1 if late else 0
        if a.cmd == "report":
            s = summary(reg, on)
            print(f"Findings register on {on.isoformat()} (SLA days: " + ", ".join(f"{k} {v}" for k, v in sla().items()) + ")")
            print("  Open:      " + ", ".join(f"{s['open'][k]} {k}" for k in ORDER) + (f"  ({s['kev_open']} known-exploited)" if s["kev_open"] else "")
                  + (f"  ({s['likely_open']} with EPSS 50%+)" if s["likely_open"] else ""))
            print(f"  Overdue:   {s['overdue']}")
            print(f"  Accepted:  {s['accepted']}" + (f" ({s['expiring']} ending within 14 days)" if s["expiring"] else ""))
            print(f"  Fixed:     {s['fixed']}" + (f", {s['sla_met']}% within the SLA, median {s['median_days_to_fix']} days to fix" if s["fixed"] else ""))
            for f in expiring(reg, on):
                print(f"  ◐ {f['id']} acceptance ends {f['accepted']['until']}: decide again (accept, or fix)  {f['title'][:60]}")
            return 0
        fs = sorted(reg.get("findings", {}).values(), key=lambda f: ({"overdue": 0, "open": 1, "accepted": 2, "fixed": 3}[status(f, on)], f["due"]))
        shown = [f for f in fs if a.all or status(f, on) != "fixed"]
        if not shown:
            print("No open findings." + ("" if fs else "  Import a scan or VAPT report:  ./securax findings import"))
            return 0
        for f in shown:
            print(_line(f, on))
        return 0
    except (KeyError, ValueError) as e:
        print(str(e).strip("'\""))
        return 1


if __name__ == "__main__":
    sys.exit(main())
