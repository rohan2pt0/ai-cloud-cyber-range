#!/usr/bin/env python3
"""Read your own documents on this laptop, and put the dates and gaps that matter into the Life OS Inbox (doc 84).

    ./securax lifeos docs [FOLDER]            read every PDF, JPG or PNG in FOLDER (default vault/life/docs/, subfolders too)
    ./securax lifeos docs [FOLDER] --dry-run  show what it would add; write nothing
    ./securax lifeos docs [FOLDER] --json     the same, as JSON (numbers masked)
    ./securax lifeos papers                   the guided list: which papers to drop in, where to get each, which are in

No spreadsheet to fill: the papers are the input. Drop in your Form 16, the AIS or Form 26AS, the CDSL or NSDL consolidated
account statement (CAS), a year of bank statements, your EPF and NPS statements, policies and ID scans (PDF, scan, photo,
Excel, Word, CSV or text). Each is recognised by what it says, not by its name, and its key figures are read: income and
tax from Form 16, money in and out from a statement, the portfolio value from the CAS. The Life OS shows them as "Your
papers" (what is in, what is still missing, and the figures), so the first numbers fill themselves.

Drop insurance policies, bank statements, scanned ID cards and the like into the folder. Each one is read here, on this
machine: pdftotext for a PDF with text, tesseract for a scan or a photo. Nothing goes on the network, and no cloud model
sees it. Install the readers once: sudo apt install poppler-utils tesseract-ocr.

What it finds becomes one Inbox item each:
  - an expiry, renewal or premium due within 60 days: renew it, 15 days before the date;
  - a date already passed: LAPSED?, due today;
  - no nominee on a policy, an account or an investment: add one;
  - a file it could not read: a note that says why.

It writes portal/inbox-import.json (the Guiding Map picks the items up; other sources' items stay), vault/life/docs-register.json
(one row per document) and vault/life/docs-alarms.ics (a calendar file, two reminders per date). Numbers are kept masked
(XXXX1234), and names are never kept. All of it stays on this machine (git-ignored, readable by you only). Standard library only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIFE = ROOT / "vault" / "life"
DOCS = LIFE / "docs"
OUT = ROOT / "portal" / "inbox-import.json"
SOURCE = "docs"
WINDOW = 60                       # days ahead that count as "soon"
LEAD = 15                         # days before the date the item falls due
MIN_TEXT = 40                     # fewer characters from pdftotext means a scan
RESOLVED_KEEP = 500               # resolved ids kept in the import file
PDF = {".pdf"}
IMAGES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
TEXT = {".txt", ".csv", ".tsv", ".md"}
SHEETS = {".xlsx", ".xlsm"}
WORDDOC = {".docx"}
READABLE = PDF | IMAGES | TEXT | SHEETS | WORDDOC
INSTALL = "could not read: install poppler-utils / tesseract-ocr (sudo apt install poppler-utils tesseract-ocr)"

KINDS = [  # (kind, keywords); the kind with most hits wins, ties go to the earlier one
    ("form16", ["form no. 16", "form no.16", "form 16", "section 192", "tds certificate", "gross salary", "salary as per provisions",
                "deductor", "employer", "tan of the deductor"]),
    ("taxstatement", ["annual information statement", "form 26as", "26as", "taxpayer information summary", "tax deducted at source",
                      "traces", "assessment year"]),
    ("cas", ["consolidated account statement", "cdsl", "nsdl", "central depository", "national securities depository",
             "portfolio value", "isin", "demat account"]),
    ("epf", ["employees' provident fund", "employees provident fund", "epfo", "uan", "member passbook", "provident fund"]),
    ("nps", ["national pension system", "pran", "tier i", "tier 1", "pension fund", "cra"]),
    ("insurance", ["insurance", "policy", "premium", "sum assured", "sum insured", "insured", "nominee", "policyholder"]),
    ("bank", ["statement of account", "account statement", "opening balance", "closing balance", "ifsc", "savings account"]),
    ("identity", ["aadhaar", "uidai", "permanent account number", "income tax department", "passport", "republic of india",
                  "driving licence", "driving license", "date of birth"]),
    ("loan", ["loan account", "emi", "outstanding principal", "sanction letter", "rate of interest", "repayment schedule"]),
    ("investment", ["folio", "nav", "demat", "mutual fund", "units allotted", "depository", "holding statement"]),
    ("property", ["sale deed", "property tax", "khata", "registration of property", "encumbrance", "plot no", "flat no"]),
    ("vehicle", ["registration certificate", "puc", "pollution under control", "chassis", "engine no", "vehicle"]),
]
AREA = {"form16": "Money", "taxstatement": "Money", "cas": "Investments", "epf": "Investments", "nps": "Investments",
        "insurance": "Insurance", "bank": "Banking", "loan": "Banking", "identity": "Identity", "investment": "Investments",
        "property": "Property", "vehicle": "Vehicle", "other": "Documents"}
WORD = {"form16": "Form 16", "taxstatement": "tax statement", "cas": "consolidated account statement", "epf": "EPF passbook",
        "nps": "NPS statement", "insurance": "insurance policy", "bank": "bank account", "loan": "loan", "identity": "ID document",
        "investment": "investment", "property": "property paper", "vehicle": "vehicle paper", "other": "document"}
IMPACT = {"insurance": 3, "identity": 3, "bank": 2, "loan": 2, "investment": 2}
NOMINEE_KINDS = {"insurance", "investment", "bank", "cas", "epf", "nps"}

# The guided list (doc 104): what to drop in, why, and where to get it. Paraphrased, no links: the steps work offline.
CATALOG = [  # (key, kinds that count, name, why, where)
    ("form16", {"form16"}, "Form 16 (latest year)", "your annual income and the tax already paid",
     "from your employer (HR or the payroll portal), each June"),
    ("tax", {"taxstatement"}, "AIS or Form 26AS", "every income the tax department sees: interest, dividends, sales",
     "income-tax e-filing portal: Annual Information Statement, download as PDF"),
    ("cas", {"cas", "investment"}, "CDSL or NSDL consolidated account statement (CAS)", "all your shares and mutual funds in one place",
     "the CDSL or NSDL CAS page: ask for it by e-mail with your PAN; it comes as a PDF"),
    ("bank", {"bank"}, "Bank statements, last 12 months, each account", "what comes in and goes out: your real spending",
     "net banking: Statements, choose 12 months, download PDF or Excel"),
    ("epf", {"epf"}, "EPF passbook", "your provident fund balance and the nominee",
     "the EPFO member passbook page, signed in with your UAN"),
    ("nps", {"nps"}, "NPS statement (if you have NPS)", "your pension balance and the nominee",
     "your NPS record-keeper's site: transaction statement"),
    ("insurance", {"insurance"}, "Every insurance policy (health, life, vehicle)", "renewal dates, cover and nominees",
     "the insurer's app or e-mail: the policy schedule PDF"),
    ("identity", {"identity"}, "Aadhaar and PAN for each family member", "who in the household is missing an ID",
     "a scan or photo of each card, or the e-Aadhaar PDF"),
    ("loan", {"loan"}, "Loan statements (if any)", "what you owe and the EMI dates",
     "the lender's app: statement of account or repayment schedule"),
]
AMOUNT = r"(?:rs\.?|inr|₹)?\s*(?P<v>\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?|\d{4,}(?:\.\d{1,2})?)"
FIGURES = {  # kind: [(figure, label pattern)]; the first amount within 80 characters after the label
    "form16": [("gross_income", r"gross\s+(?:total\s+)?(?:salary|income)"), ("taxable_income", r"(?:total|net)\s+taxable\s+income|total\s+income"),
               ("tax_paid", r"(?:total\s+)?tax\s+deducted|net\s+tax\s+payable|tax\s+payable")],
    "taxstatement": [("tds_total", r"total\s+tax\s+deducted|tds\s+total|total\s+tds")],
    "cas": [("portfolio_value", r"(?:total\s+)?portfolio\s+value|grand\s+total|total\s+value|net\s+worth")],
    "investment": [("portfolio_value", r"(?:total\s+)?portfolio\s+value|market\s+value|current\s+value")],
    "bank": [("money_in", r"total\s+credits?|credits?\s+total|total\s+deposits?"), ("money_out", r"total\s+debits?|debits?\s+total|total\s+withdrawals?"),
             ("closing_balance", r"closing\s+balance")],
    "epf": [("epf_balance", r"(?:total|closing|net)\s+balance|grand\s+total")],
    "nps": [("nps_balance", r"(?:total\s+)?(?:holding|current)\s+value|total\s+value")],
    "loan": [("loan_outstanding", r"(?:principal\s+)?outstanding(?:\s+principal)?|balance\s+outstanding")],
}

_MON = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_MONRE = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATE = re.compile(
    r"(?<!\d)(?:"
    r"(?P<iy>\d{4})-(?P<im>\d{1,2})-(?P<id>\d{1,2})"                                       # 2026-11-21
    r"|(?P<nd>\d{1,2})\s*[/.\-]\s*(?P<nm>\d{1,2})\s*[/.\-]\s*(?P<ny>\d{4}|\d{2})"             # 21/11/2026, 21-11-26
    r"|(?P<td>\d{1,2})(?:st|nd|rd|th)?[\s\-/.]*(?P<tm>" + _MONRE + r")\.?[\s\-/.,]*(?P<ty>\d{4}|\d{2})"  # 21 Nov 2026, 21-Nov-26
    r"|(?P<sm>" + _MONRE + r")\.?\s+(?P<sd>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<sy>\d{4})"        # Nov 21, 2026
    r")(?!\d)", re.I)
LABELS = [  # (role, label); the date nearest after the label belongs to it
    ("premium", r"next\s+premium\s+due(?:\s+date)?|premium\s+due(?:\s+date)?|payment\s+due(?:\s+date)?|due\s+date"),
    ("maturity", r"(?:date\s+of\s+)?maturity(?:\s+date)?"),
    ("expiry", r"date\s+of\s+expiry|expiry\s+date|expiry|expires?(?:\s+on)?|valid\s+(?:till|upto|up\s+to|until|thru|through)"
               r"|renewal(?:\s+due)?(?:\s+date)?|policy\s+(?:end|expiry)(?:\s+date)?|end\s+date|date\s+of\s+renewal"),
]
LABEL = re.compile(r"\b(?:" + "|".join(f"(?P<{r}>{p})" for r, p in LABELS) + r")\b", re.I)
NUMBER = re.compile(
    r"\b(?:(?:policy|account|a/c|acct|folio|passport|licen[cs]e|dl|registration|regn|certificate|loan|member|customer|uan|pran|card)"
    r"\s*(?:no\.?|number|num|id|#)|pan|aadhaar|folio)\b\s*[:.\-#]?\s*(?P<v>[A-Z0-9][A-Z0-9/\- ]{3,30})", re.I)
BARE = [re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")]    # PAN, Aadhaar
COVER = re.compile(r"\b(?:sum\s+(?:assured|insured)|cover(?:age)?\s+amount|cover|basic\s+sum)\b[^\d\n]{0,25}?(?P<v>\d[\d,]*(?:\.\d+)?)", re.I)
NOMINEE = re.compile(r"\bnominee(?:\s*(?:name|details|registered))?\s*[:\-–]?[ \t]*(?P<v>[^\n]{0,40})", re.I)
NO_NOMINEE = re.compile(r"^\s*(?:[-–—]+|n\.?a\.?|n/a|nil|none|no\b|not\s+(?:registered|available|provided|updated|given|nominated)"
                        r"|unregistered|\(?blank\)?)\s*(?:$|[\s.,;:|])", re.I)


def today() -> dt.date:
    return dt.date.today()


# -- reading ---------------------------------------------------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int, run=None) -> str | None:
    """The command's stdout, or None when it is missing, fails or runs too long."""
    run = run or subprocess.run
    try:
        p = run(cmd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if getattr(p, "returncode", 1) != 0:
        return None
    out = p.stdout
    return out.decode("utf-8", "replace") if isinstance(out, bytes) else (out or "")


def extract(path: pathlib.Path, run=None, which=None) -> tuple[str, str]:
    """(text, "") when read, or ("", why it could not be)."""
    which = which or shutil.which
    ext = path.suffix.lower()
    if ext in TEXT:
        try:
            return path.read_text("utf-8", "replace"), ""
        except OSError:
            return "", "could not read: the file cannot be opened"
    if ext in SHEETS | WORDDOC:
        try:
            return (_sheet_text(path) if ext in SHEETS else _docx_text(path)), ""
        except (OSError, zipfile.BadZipFile, KeyError, ValueError):
            return "", "could not read: the file is damaged or locked with a password (save an unlocked copy)"
    if ext in PDF:
        text = ""
        if which("pdftotext"):
            text = _run(["pdftotext", "-layout", str(path), "-"], 60, run) or ""
        if len(text.strip()) >= MIN_TEXT:
            return text, ""
        if not (which("pdftoppm") and which("tesseract")):
            return "", INSTALL
        with tempfile.TemporaryDirectory(prefix="lifedocs-") as tmp:
            if _run(["pdftoppm", "-r", "200", "-png", "-f", "1", "-l", "10", str(path), os.path.join(tmp, "p")], 120, run) is None:
                return "", "could not read: the PDF would not open (damaged, or locked with a password)"
            pages = sorted(pathlib.Path(tmp).glob("p*.png"))
            text = "\n".join(_run(["tesseract", str(p), "-", "-l", "eng"], 120, run) or "" for p in pages)
    elif ext in IMAGES:
        if not which("tesseract"):
            return "", INSTALL
        text = _run(["tesseract", str(path), "-", "-l", "eng"], 120, run) or ""
    else:
        return "", "could not read: not a PDF, scan, photo, Excel, Word or text file"
    if len(text.strip()) < MIN_TEXT:
        return "", "could not read: no text found (a blank or very faint scan; scan it again at 300 dpi)"
    return text, ""


def _sheet_text(path: pathlib.Path) -> str:
    """Every sheet as tab-separated lines, by the estate's own reader (no new dependency)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_controls_ld", ROOT / "governance" / "controls.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return "\n".join("\t".join("" if v is None else str(v) for v in row) for rows in mod.read_xlsx(path).values() for row in rows)


def _docx_text(path: pathlib.Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>|<w:br/>|<w:tab/>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


# -- understanding ---------------------------------------------------------------------------------------------------------------

def classify(text: str) -> str:
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    best, hits = "other", 0
    for kind, words in KINDS:
        n = sum(1 for w in words if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low))
        if n > hits:
            best, hits = kind, n
    return best


def parse_date(s: str) -> dt.date | None:
    m = DATE.search(s or "")
    return _date(m) if m else None


def _date(m: re.Match) -> dt.date | None:
    g = m.groupdict()
    try:
        if g["iy"]:
            y, mo, d = int(g["iy"]), int(g["im"]), int(g["id"])
        elif g["ny"]:
            y, mo, d = int(g["ny"]), int(g["nm"]), int(g["nd"])
        elif g["ty"]:
            y, mo, d = int(g["ty"]), _MON[g["tm"][:3].lower()], int(g["td"])
        else:
            y, mo, d = int(g["sy"]), _MON[g["sm"][:3].lower()], int(g["sd"])
        if y < 100:
            y += 2000 if y < 70 else 1900
        return dt.date(y, mo, d)
    except (ValueError, KeyError, TypeError):
        return None


def find_dates(text: str) -> list[tuple[str, dt.date]]:
    """(role, date) for each labelled date: the first date after the label, on its line or the next."""
    found = []
    for m in LABEL.finditer(text):
        role = next(r for r, _ in LABELS if m.group(r))
        rest = text[m.end():m.end() + 120]
        rest = "\n".join(rest.split("\n")[:2])
        for d in DATE.finditer(rest):
            day = _date(d)
            if day:
                if (role, day) not in found:
                    found.append((role, day))
                break
    return found


def mask(value: str) -> str:
    """XXXX and the last four letters or digits; never the whole thing."""
    s = re.sub(r"[^A-Za-z0-9]", "", value or "")
    return "XXXX" + s[-4:].upper() if len(s) >= 4 else ("XXXX" if s else "")


def find_number(text: str) -> str:
    """The policy, account or ID number, masked."""
    for m in NUMBER.finditer(text):
        v = re.split(r"\s{2,}|\s+(?=[A-Za-z]{3,})", m.group("v").strip())[0]
        if re.search(r"\d", v) and not DATE.fullmatch(v.strip()):
            return mask(v)
    for rx in BARE:
        m = rx.search(text)
        if m:
            return mask(m.group(0))
    return ""


def find_figures(kind: str, text: str) -> dict:
    """{figure: rupees} for the kind's key figures. Totals only, never an account or ID number."""
    out = {}
    for name, label in FIGURES.get(kind, []):
        m = re.search(r"\b(?:" + label + r")\b[^\n\d]{0,60}?" + AMOUNT, text, re.I)
        if m:
            v = float(m.group("v").replace(",", ""))
            if 0 < v < 1e10:
                out[name] = round(v)
    return out


def find_cover(text: str) -> int | None:
    m = COVER.search(text)
    if not m:
        return None
    try:
        return int(float(m.group("v").replace(",", "")))
    except ValueError:
        return None


def nominee_state(text: str) -> str:
    """present, absent or unknown. The name itself is never kept."""
    states = []
    for m in NOMINEE.finditer(text):
        v = m.group("v").strip()
        if NO_NOMINEE.match(v) or re.search(r"(?i)\bno\s*$", text[max(0, m.start() - 4):m.start()]):
            states.append("absent")
        elif re.match(r"(?i)(?:yes|y|registered)\b", v):
            states.append("present")
        elif re.match(r"[A-Za-z][A-Za-z.'\s]{1,}[A-Za-z]", v) and not re.match(r"(?i)(?:details|name|relationship|share)\s*$", v):
            states.append("present")
    if re.search(r"(?i)\bno\s+nominee\b", text):
        states.append("absent")
    if "present" in states:
        return "present"
    return "absent" if "absent" in states else "unknown"


def _clean_stem(stem: str) -> str:
    """The file's name, with any long number in it masked."""
    return re.sub(r"[A-Za-z0-9]*\d{4,}[A-Za-z0-9]*", lambda m: mask(m.group(0)) if len(m.group(0)) >= 6 else m.group(0), stem)[:60]


def _id(rel: str, rule: str) -> str:
    return "ld-" + hashlib.sha256((rel + "\x1f" + rule).encode()).hexdigest()[:12]


def _fmt(d: dt.date) -> str:
    return f"{d.day} {d.strftime('%b')} {d.year}"


# -- turning documents into items ------------------------------------------------------------------------------------------------

def read_doc(path: pathlib.Path, folder: pathlib.Path, run=None, which=None) -> tuple[dict, str]:
    """(register row, text). The text is used here and dropped; it is never written."""
    rel = path.relative_to(folder).as_posix()
    text, why = extract(path, run, which)
    if why:
        return {"file": rel, "kind": "unknown", "dates": [], "number": "", "nominee": "unknown", "readable": False, "why": why}, ""
    row = {"file": rel, "kind": classify(text), "dates": [{"role": r, "date": d.isoformat()} for r, d in find_dates(text)],
           "number": find_number(text), "nominee": nominee_state(text), "readable": True}
    figs = find_figures(row["kind"], text)
    if figs:
        row["figures"] = figs
    cover = find_cover(text)
    if cover is not None and row["kind"] in ("insurance", "loan", "investment"):
        row["cover"] = cover
    return row, text


def _urgency(days: int | None) -> float:
    if days is None:
        return 1.0
    if days < 0:
        return 3.0
    return 2.5 if days <= 15 else 2.0 if days <= WINDOW else 1.0


def items_for(row: dict, now: dt.date) -> list[dict]:
    rel, kind = row["file"], row["kind"]
    stem = _clean_stem(pathlib.PurePosixPath(rel).stem)
    if not row["readable"]:
        return [{"id": _id(rel, "unreadable"), "t": f"Could not read {stem}: {row['why'].replace('could not read: ', '')}"[:200],
                 "kind": "note", "area": "Documents", "due": "", "next": "Install the readers, or scan it again, then run ./securax lifeos docs.",
                 "from": SOURCE, "vital": False, "score": 1.0}]
    area, word, impact = AREA[kind], WORD[kind], IMPACT.get(kind, 1)
    out = []

    def add(rule, title, due, nxt, days, imp=impact, vital=False):
        out.append({"id": _id(rel, rule), "t": title[:200], "kind": "issue", "area": area, "due": due, "next": nxt[:200],
                    "from": SOURCE, "vital": vital, "score": float(imp * _urgency(days))})

    dates = [(r, dt.date.fromisoformat(d["date"])) for d in row["dates"] for r in [d["role"]]]
    soon = sorted((d, r) for r, d in dates if 0 <= (d - now).days <= WINDOW)
    future = [d for r, d in dates if d >= now]
    past = sorted(d for r, d in dates if d < now and r in ("expiry", "premium"))
    if soon:
        d, role = soon[0]
        due = max(now, d - dt.timedelta(days=LEAD)).isoformat()
        if role == "premium":
            add("due", f"Pay the {word} premium ({stem}) before {_fmt(d)}", due, f"Pay it, or set up auto-pay, before {_fmt(d)}.", (d - now).days)
        elif role == "maturity":
            add("due", f"Plan for the {word} maturing ({stem}) on {_fmt(d)}", due, "Decide where the money goes before it lands.", (d - now).days)
        else:
            add("due", f"Renew {word} ({stem}) before {_fmt(d)}", due, f"Compare and renew it before {_fmt(d)}; keep the new copy here.", (d - now).days)
    elif past and not future:
        d = past[-1]
        add("lapsed", f"LAPSED? {word} ({stem}) ended or fell due on {_fmt(d)}", now.isoformat(),
            "Check today whether it is still in force; renew or replace it, and drop the new copy here.", (d - now).days, vital=True)
    in30 = (now + dt.timedelta(days=30)).isoformat()
    if kind in NOMINEE_KINDS and row["nominee"] == "absent":
        add("nominee-absent", f"Add a nominee: {word} ({stem}) has none", in30,
            "Ask the insurer, bank or fund for the nomination form, or add one in its app.", None, imp=3)
    elif kind == "insurance" and row["nominee"] == "unknown":
        add("nominee-unknown", f"Check the nominee on {word} ({stem})", in30,
            "Look at the policy schedule or the insurer's app; add a nominee if there is none.", None, imp=3)
    return out


def mark_vital(items: list[dict]) -> list[dict]:
    """The top 20% of issues by score are vital (at least one), and anything lapsed."""
    issues = sorted((x for x in items if x["kind"] == "issue"), key=lambda x: (-x["score"], x["due"] or "9999", x["id"]))
    for x in issues[:max(1, math.ceil(len(issues) * 0.2))]:
        x["vital"] = True
    return items


def scan(folder: pathlib.Path, now: dt.date | None = None, run=None, which=None) -> tuple[list[dict], list[dict]]:
    """(register rows, inbox items) for every document under folder."""
    now = now or today()
    rows, items = [], []
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not any(s.startswith(".") for s in p.relative_to(folder).parts)
                   and p.suffix.lower() in READABLE)
    for p in files:
        row, _text = read_doc(p, folder, run, which)
        rows.append(row)
        items += items_for(row, now)
    return rows, mark_vital(items)


def papers(rows: list[dict]) -> dict:
    """The guided list with what is in, and the figures summed: the Life OS shows it as "Your papers"."""
    have = {}
    for r in rows:
        if r.get("readable"):
            have[r["kind"]] = have.get(r["kind"], 0) + 1
    checklist = [{"key": k, "name": n, "why": w, "where": wh, "have": sum(have.get(x, 0) for x in kinds)} for k, kinds, n, w, wh in CATALOG]
    tot = {}
    for r in rows:
        for f, v in (r.get("figures") or {}).items():
            if f in ("money_in", "money_out", "tds_total"):
                tot[f] = tot.get(f, 0) + v
            elif f in ("gross_income", "taxable_income", "tax_paid"):
                tot[f] = max(tot.get(f, 0), v)          # the latest Form 16 is the largest; two copies are not two salaries
            else:
                tot[f] = tot.get(f, 0) + v
    if tot.get("gross_income") and tot.get("money_out"):
        tot["saving_rate_pct"] = round(100 * (1 - tot["money_out"] / tot["gross_income"]))
    return {"checklist": checklist, "figures": tot, "read": today().isoformat(), "folder": _rel(DOCS)}


def paper_items(pp: dict, now: dt.date) -> list[dict]:
    """One action per paper not yet in, the first three vital: they unlock everything else. Gone once the paper is in."""
    out, due = [], (now + dt.timedelta(days=3)).isoformat()
    for i, c in enumerate(x for x in pp["checklist"] if not x["have"]):
        out.append({"id": "ld-paper-" + c["key"], "t": f"Drop in: {c['name']}"[:200], "kind": "action", "area": "Papers", "due": due,
                    "next": f"Get it {c['where']}; save it in {pp['folder']}/ and run ./securax lifeos docs."[:200],
                    "from": SOURCE, "vital": i < 3, "score": 2.0})
    return out


# -- writing ---------------------------------------------------------------------------------------------------------------------

def _private_dir(d: pathlib.Path) -> None:
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        d.chmod(0o700)
    except OSError:
        pass


def _write_private(path: pathlib.Path, data: str | bytes) -> None:
    """Write atomically, readable by the owner only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data.encode("utf-8") if isinstance(data, str) else data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    path.chmod(0o600)


def merge(items: list[dict], out: pathlib.Path) -> tuple[dict, list[str]]:
    """The new import file, and the ids resolved this time: other sources' items stay, docs items are replaced."""
    try:
        old = json.loads(out.read_text("utf-8"))
        if not isinstance(old, dict):
            old = {}
    except (OSError, ValueError):
        old = {}
    olditems = [x for x in old.get("items", []) if isinstance(x, dict)]
    keep = [x for x in olditems if x.get("from") != SOURCE]
    now_ids = {x["id"] for x in items}
    gone = [x["id"] for x in olditems if x.get("from") == SOURCE and x.get("id") not in now_ids]
    resolved = [r for r in old.get("resolved", []) if isinstance(r, str) and r not in now_ids]
    resolved = list(dict.fromkeys(resolved + gone))[-RESOLVED_KEEP:]
    new = dict(old)
    new.setdefault("about", "Notes waiting for the Guiding Map Inbox (./securax lifeos). Private: never committed.")
    new["items"] = keep + items
    new["resolved"] = resolved
    return new, gone


def _ics_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def _fold(line: str) -> str:
    """Fold at 75 octets (RFC 5545), never inside a UTF-8 character."""
    out, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > (75 if not out else 74):
            out.append(cur)
            cur, size = "", 0
        cur += ch
        size += n
    out.append(cur)
    return "\r\n ".join(out)


def ics(items: list[dict], stamp: dt.datetime | None = None) -> str:
    """One all-day event per dated issue, each with reminders a week and a day before."""
    stamp = (stamp or dt.datetime.now(dt.timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//SecuRAX//Life OS documents//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    for x in items:
        if x["kind"] != "issue" or not x.get("due"):
            continue
        d = dt.date.fromisoformat(x["due"])
        lines += ["BEGIN:VEVENT", f"UID:{x['id']}", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{d + dt.timedelta(days=1):%Y%m%d}", "SUMMARY:" + _ics_text(x["t"]),
                  "DESCRIPTION:" + _ics_text(x["next"]), "TRANSP:TRANSPARENT"]
        for trig in ("-P7D", "-P1D"):
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + _ics_text(x["t"]), f"TRIGGER:{trig}", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "".join(_fold(ln) + "\r\n" for ln in lines)


def write_all(rows: list[dict], items: list[dict], out: pathlib.Path | None = None, life: pathlib.Path | None = None) -> list[str]:
    """Write the three files; return the ids resolved."""
    out, life = out or OUT, life or LIFE
    _private_dir(life)
    pp = papers(rows)
    new, gone = merge(items + paper_items(pp, today()), out)
    new["papers"] = pp
    _write_private(out, json.dumps(new, ensure_ascii=False, indent=1))
    reg = {"about": "Your documents, as ./securax lifeos docs read them. Numbers masked; no names. Private: never committed.",
           "read": today().isoformat(), "documents": rows}
    _write_private(life / "docs-register.json", json.dumps(reg, ensure_ascii=False, indent=1))
    _write_private(life / "docs-alarms.ics", ics(items))
    return gone


# -- the command -----------------------------------------------------------------------------------------------------------------

def _rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def guide(folder: pathlib.Path) -> int:
    """The guided list in the terminal: what is in, what to get next, and where."""
    rows = scan(folder)[0] if folder.is_dir() else []
    pp = papers(rows)
    print(f"Your papers ({sum(1 for c in pp['checklist'] if c['have'])} of {len(pp['checklist'])} in). Drop each into {_rel(folder)}/,"
          " any format, any name; then run ./securax lifeos docs.")
    for c in pp["checklist"]:
        print(f"  {'✔' if c['have'] else '·'} {c['name']}" + ("" if c["have"] else f"\n      for {c['why']}; get it {c['where']}"))
    if pp["figures"]:
        print("Read from them so far: " + ", ".join(f"{k.replace('_', ' ')} {v:,}" for k, v in pp["figures"].items()))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "docs":
        argv = argv[1:]
    elif argv and argv[0] == "papers":
        return guide(DOCS)
    if any(a in ("-h", "--help", "help") for a in argv):
        print(__doc__)
        return 0
    dry, as_json = "--dry-run" in argv, "--json" in argv
    rest = [a for a in argv if not a.startswith("--")]
    unknown = [a for a in argv if a.startswith("--") and a not in ("--dry-run", "--json")]
    if unknown:
        print(f"Unknown option {unknown[0]}.\n{__doc__}")
        return 2
    folder = pathlib.Path(" ".join(rest)).expanduser() if rest else DOCS
    if not folder.is_dir():
        if rest:
            print(f"No folder {folder}. Give a folder that holds your documents, or leave it out to use {_rel(DOCS)}/.")
            return 1
        if dry:
            print(f"{_rel(folder)}/ does not exist yet; without --dry-run it is made for you (readable by you only).")
            return 0
        _private_dir(folder.parent)
        _private_dir(folder)
        print(f"Made {_rel(folder)}/ (readable by you only).")
        return guide(folder)
    rows, items = scan(folder)
    if as_json:
        print(json.dumps({"documents": rows, "items": items}, ensure_ascii=False, indent=1))
    if not rows:
        if not as_json:
            print(f"No papers in {_rel(folder)}/ yet. Run ./securax lifeos papers for the list of what to drop in.")
        return 0
    gone = [] if dry else write_all(rows, items)
    if as_json:
        return 0
    bad = [r for r in rows if not r["readable"]]
    issues = sorted((x for x in items if x["kind"] == "issue"), key=lambda x: (not x["vital"], -x["score"], x["due"]))
    print(("Would read" if dry else "Read") + f" {len(rows) - len(bad)} document(s); {len(bad)} could not be read.")
    for why in sorted({r["why"] for r in bad}):
        print(f"  {sum(1 for r in bad if r['why'] == why)} × {why}")
    print(f"{len(issues)} issue(s)" + (" to add:" if dry else ":"))
    for x in issues:
        print(f"  {'★ ' if x['vital'] else '  '}{x['t']}" + (f" (due {x['due']})" if x["due"] else ""))
    if dry:
        print("Nothing written (--dry-run).")
        return 0
    if gone:
        print(f"{len(gone)} earlier item(s) are no longer found; the Life OS will tick them off.")
    print("Open the Guiding Map: they are in the Inbox. Calendar reminders: " + _rel(LIFE / "docs-alarms.ics")
          + " (open it with your calendar app).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
