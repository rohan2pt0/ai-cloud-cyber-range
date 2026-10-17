#!/usr/bin/env python3
"""The risk register: vulnerability / threat / risk (V/T/R) registers and risk treatment plans in one place, linked to the
BFSI control library, the navigator heat map, the cockpit and postmortems.

    ./securax risks import [FILE.xlsx]    (no path: finds registers in Downloads/Documents) read a V/T/R register (risk-wise, asset-wise, observations) or a risk assessment +
                                          treatment plan workbook into vault/risks/register.json (private, never committed)
    ./securax risks list [--open]         every risk, worst inherent score first, with its linked controls
    ./securax risks overdue               open treatments past their due date (exit 1 when there is one, for a routine)
    ./securax risks cii                   NCIIPC CII self-check: do your functions meet the guideline's national-impact tests?

Columns are found by their HEADER NAMES (not positions), so a re-ordered or extended workbook still imports. Scores follow the
workbooks' own scale: inherent = likelihood (1-5) x impact (1-5); 20-25 critical, 12-19 high, 6-11 medium, 1-5 low.
Each risk is linked to library controls by what it is about (access, patch, vendor, backup ...), so the navigator can rank
the controls that would treat your highest open risks first. Standard library only.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "vault" / "risks" / "register.json"
CLOSED = re.compile(r"\b(closed|completed|done|resolved|accepted)\b", re.I)
_spec = importlib.util.spec_from_file_location("controls", ROOT / "governance" / "controls.py")
controls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(controls)

# what a risk is about -> the library controls that treat it (first match wins per theme; several themes can apply)
LINKS = [
    (r"anti.?virus|malware|ransomware|virus", ["EP-003", "EP-001", "BCP-006"]), (r"patch|end.?of.?life|eol|unsupported|outdated", ["VM-002", "AM-002", "EP-006"]),
    (r"vulnerab|va scan|pen(etration)? test|vapt", ["VM-001", "VM-003"]), (r"privileg|admin", ["IAM-001", "IAM-012"]),
    (r"access|authenticat|password|credential|identity|tailgat|unauthori[sz]ed", ["IAM-005", "IAM-002", "IAM-003"]),
    (r"vendor|third.?party|supply.?chain|outsourc|backdoor", ["TP-005", "TP-008", "AS-006"]), (r"backup|restore|snapshot", ["BCP-003", "BCP-010"]),
    (r"continuity|disaster|\bdr\b|fallback|availability|outage", ["BCP-001", "BCP-002"]), (r"phishing|social engineering|awareness|human error", ["AW-002", "AW-001"]),
    (r"fire|smoke|water|power|ups|environment", ["PS-003"]), (r"physical|cctv|premises", ["PS-001", "PS-005"]),
    (r"encrypt|crypto|key management|certificate", ["DP-006", "DP-007", "DP-009"]), (r"log|monitor|siem|visibility|soc\b", ["SOC-004", "SOC-001"]),
    (r"leak|exfiltrat|dlp|data protection|privacy|personal data", ["DP-002", "DP-004"]), (r"network|firewall|perimeter|segment|exposure", ["NS-001", "NS-003"]),
    (r"cloud|saas", ["CL-002", "CL-003"]), (r"api|web application|injection|sql|xss", ["AS-002", "AS-011"]), (r"mobile|byod", ["EP-007", "AM-006"]),
    (r"configur|hardening|misconfig", ["EP-008", "NS-011"]), (r"change management|change control", ["AS-101"]), (r"insider|disgruntled", ["HR-004"]),
    (r"incident|breach|cert-in", ["IR-001", "IR-005"]), (r"swift", ["NS-009"]), (r"atm", ["EP-002"]), (r"upi|aeps|fraud", ["ET-004", "SOC-010"]),
    (r"ai\b|genai|model|llm", ["ET-001", "ET-010"]), (r"governance|policy|oversight", ["GOV-001", "GOV-009"]), (r"regulat|compliance|legal", ["GOV-014"]),
]
# header name (lower-case, spaces squeezed) -> field; the first alias found in a sheet wins
ALIASES = {
    "id": ["risk id", "reference #", "ref. no.", "sr. no.", "sn"], "perspective": ["risk perspective", "department", "area"],
    "asset": ["asset/process", "asset name", "associated assets", "business process name", "sub area"],
    "category": ["risk category", "asset category"], "threat": ["risk description (threat)", "risk description", "observations", "threat"],
    "vulnerability": ["associated vulnerability", "vulnerability"], "likelihood": ["likelihood score", "probability of threat"],
    "impact": ["impact value", "overall impact"], "inherent": ["ir score (likelihood x impact)", "ir score", "inherent risk score"],
    "residual": ["residual risk score"], "treatment": ["residual risk treatment", "treatment type"],
    "plan": ["recommended control", "recommendation", "treatment plan"], "owner": ["risk owner", "person responsible", "spoc"],
    "due": ["target date", "implementation timeline", "planned end date"], "done": ["actual end date"],
    "status": ["current risk status", "risk status", "status"], "severity": ["severity"], "ref": ["reference doc"],
    "treatment_ref": ["risk treatment #"],
}


def _norm(h) -> str:
    return re.sub(r"\s+", " ", str(h or "").replace("\n", " ")).strip().lower()


def _date(v) -> str:
    if v in (None, ""):
        return ""
    if isinstance(v, (int, float)) or re.fullmatch(r"\d{4,5}(\.\d+)?", str(v)):
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(float(v)))).isoformat()        # Excel serial date
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", str(v).strip().split("\n")[0])
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y", "%B %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _header(rows: list[list]) -> tuple[int, dict[int, str]] | None:
    """The header (merging a two-row header) with the most known names among the first 8 rows: (last header row, {col: name})."""
    known = {a for al in ALIASES.values() for a in al}
    best = None
    for i in range(min(8, len(rows))):
        names = {}
        for j in range(max(len(rows[i]), len(rows[i + 1]) if i + 1 < len(rows) else 0)):
            lo = _norm(rows[i + 1][j]) if i + 1 < len(rows) and j < len(rows[i + 1]) else ""
            hi = _norm(rows[i][j]) if j < len(rows[i]) else ""
            names[j] = lo if lo in known or not hi else hi
        two = sum(1 for n in names.values() if n in known)
        one = sum(1 for j, v in enumerate(rows[i]) if _norm(v) in known)
        # a one-row header wins a tie: otherwise the first data row under it would be read as a second header row and lost
        for score, last, nm in ((one, i, {j: _norm(v) for j, v in enumerate(rows[i])}), (two, i + 1, names)):
            if score >= 4 and (best is None or score > best[0]):
                best = (score, last, nm)
    return (best[1], best[2]) if best else None


def link(text: str) -> list[str]:
    out = []
    for pat, ids in LINKS:
        if re.search(pat, text, re.I):
            out += [i for i in ids if i not in out]
    return out[:5]


def rating(score) -> str:
    if score is None:
        return ""
    return "critical" if score >= 20 else "high" if score >= 12 else "medium" if score >= 6 else "low"


def import_file(path: pathlib.Path) -> list[dict]:
    risks, plans = [], {}
    for sheet, rows in controls.read_xlsx(path).items():
        h = _header(rows)
        if not h:
            continue
        last, names = h
        col = {}
        for field, al in ALIASES.items():
            for a in al:
                hit = next((j for j, n in names.items() if n == a), None)
                if hit is not None:
                    col[field] = hit
                    break
        if "threat" not in col:
            if {"id", "plan", "status"} <= set(col):          # a separate treatment-plan sheet, joined to risks by its reference
                for r in rows[last + 1:]:
                    g = lambda f: (r[col[f]] if f in col and col[f] < len(r) else None)
                    if g("id"):
                        plans[str(g("id")).strip()] = {"treatment": str(g("treatment") or "").strip(), "plan": str(g("plan") or "").strip()[:400],
                                                      "status": str(g("status") or "").strip(), "owner": str(g("owner") or "").strip(),
                                                      "due": _date(g("due")), "done": _date(g("done"))}
            continue
        for k, r in enumerate(rows[last + 1:], 1):
            get = lambda f: (r[col[f]] if f in col and col[f] < len(r) else None)
            threat = str(get("threat") or "").strip()
            if not threat or threat == "0":
                continue
            lk, im = _num(get("likelihood")), _num(get("impact"))
            inh = _num(get("inherent")) or (lk * im if lk and im else None)
            res = _num(get("residual"))
            about = " ".join(str(get(f) or "") for f in ("category", "threat", "vulnerability", "asset"))
            risks.append({
                "id": str(get("id") or f"{sheet[:12]}-{k}").strip(), "source": f"{path.name} / {sheet}",
                "perspective": str(get("perspective") or "").strip(), "asset": str(get("asset") or "").strip(),
                "category": str(get("category") or "").strip(), "threat": threat[:400], "vulnerability": str(get("vulnerability") or "").strip()[:300],
                "likelihood": lk, "impact": im, "inherent": inh, "inherent_rating": rating(inh), "residual": res, "residual_rating": rating(res),
                "treatment": str(get("treatment") or "").strip(), "plan": str(get("plan") or "").strip()[:400],
                "owner": str(get("owner") or "").strip(), "due": _date(get("due")), "done": _date(get("done")),
                "status": str(get("status") or "").strip(), "severity": str(get("severity") or "").strip(), "ref": str(get("ref") or "").strip(),
                "controls": link(about), "treatment_ref": str(get("treatment_ref") or "").strip(),
            })
    for r in risks:                                            # fill each risk from its treatment-plan row, where one exists
        for ref in re.split(r"[,;/\s]+", r.get("treatment_ref") or ""):
            p = plans.get(ref)
            if p:
                r.update({k: v for k, v in p.items() if v and not (k == "plan" and r.get("plan"))})
    return risks


def load(path: pathlib.Path | None = None) -> list[dict]:
    try:
        return json.loads((path or REG).read_text("utf-8"))["risks"]
    except (OSError, ValueError, KeyError):
        return []


def is_open(r: dict) -> bool:
    return not (r.get("done") or CLOSED.search(r.get("status") or ""))


def overdue(risks: list[dict], today: dt.date | None = None) -> list[dict]:
    today = (today or dt.date.today()).isoformat()
    return [r for r in risks if is_open(r) and r.get("due") and r["due"] < today]


def control_pressure(risks: list[dict]) -> dict[str, float]:
    """{control id: the highest inherent score among the OPEN risks it would treat}: what the navigator ranks by."""
    out: dict[str, float] = {}
    for r in risks:
        if is_open(r) and r.get("inherent"):
            for c in r["controls"]:
                out[c] = max(out.get(c, 0), r["inherent"])
    return out


CII_TESTS = [
    ("customers", "Would losing these ICT systems hit customers, business or government at NATIONAL scale (transaction value or count per day, connected devices, customers)?"),
    ("timeframe", "Would the impact become very significant within HOURS of the systems being unavailable?"),
    ("geography", "Would it spread beyond one city or district: a state, a region, the nation, or across borders?"),
    ("dependency", "Would its failure cascade into other critical sectors, or do essential services depend on it?"),
]


def cii_verdict(answers: dict[str, bool]) -> str:
    """NCIIPC CII identification guidelines (v1.0, para 7-8): the four impact parameters. A self-check only: designation is the
    Government's (s.70 IT Act) on NCIIPC's advice."""
    yes = [k for k, _ in CII_TESTS if answers.get(k)]
    if len(yes) >= 2 or "customers" in yes and "dependency" in yes:
        return ("LIKELY CII: treat these systems as High-risk infrastructure (every NSCS audit marker mandatory) and engage NCIIPC "
                "through your sector regulator for identification. Tests met: " + ", ".join(yes))
    if yes:
        return "POSSIBLY CII: one national-impact test met (" + yes[0] + "). Document the assessment and re-check yearly; use the Medium-risk NSCS profile."
    return "UNLIKELY CII on these answers: use the NSCS Medium or Low risk profile, as your risk assessment decides."


def find_registers(dirs: list[pathlib.Path] | None = None) -> list[pathlib.Path]:
    """Workbooks in the usual folders that read as a risk register (the control-library workbook excluded)."""
    out = []
    for f in controls.find_xlsx(dirs):
        if controls.is_library_workbook(f):
            continue
        try:
            if import_file(f):
                out.append(f)
        except (SystemExit, Exception):     # not a register, or not readable: skip it, never stop the search
            continue
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "help"
    if cmd == "import" and len(argv) <= 2:
        paths = [pathlib.Path(argv[1]).expanduser()] if len(argv) == 2 else controls.confirm(find_registers(), "risk register(s)")
        if not paths:
            return 1
        for path in paths:
            new = import_file(path)
            keep = [r for r in load() if not r["source"].startswith(path.name + " /")]   # re-import replaces that file only
            REG.parent.mkdir(parents=True, exist_ok=True)
            REG.write_text(json.dumps({"imported": dt.date.today().isoformat(), "risks": keep + new}, indent=1, ensure_ascii=False), "utf-8")
            try:
                REG.chmod(0o600)
            except OSError:
                pass
            linked = sum(1 for r in new if r["controls"])
            print(f"✔ {len(new)} risks from {path.name} ({linked} linked to library controls); register now holds {len(keep) + len(new)} (private: {REG.relative_to(ROOT)})")
        data = controls.load()
        if data:
            controls.write_navigator(data)
            print("✔ navigator refreshed: the heat map and the vital few now use these risks")
        return 0
    if cmd == "list":
        rs = sorted((r for r in load() if not ("--open" in argv and not is_open(r))), key=lambda r: -(r.get("inherent") or 0))
        for r in rs:
            print(f"{r['id'][:14]:<14} {r['inherent_rating'] or '-':<8} {(r['inherent'] or 0):>4g}  {r['threat'][:70]:<70}  → {', '.join(r['controls']) or '-'}")
        if not rs:
            print("no risks yet:  ./securax risks import FILE.xlsx")
        return 0
    if cmd == "overdue":
        od = overdue(load())
        for r in od:
            print(f"✗ {r['id']:<14} due {r['due']}  {r['threat'][:80]}  (owner: {r['owner'] or 'none'})")
        print(f"{len(od)} overdue treatment(s)" if od else "no overdue treatments")
        return 1 if od else 0
    if cmd == "cii":
        ans = {}
        for key, q in CII_TESTS:
            try:
                ans[key] = input(q + " [y/N]: ").strip().lower().startswith("y")
            except EOFError:
                ans[key] = False
        print("\n" + cii_verdict(ans))
        out = ROOT / "vault" / "risks" / "cii.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"date": dt.date.today().isoformat(), "answers": ans, "verdict": cii_verdict(ans)}, indent=1), "utf-8")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
