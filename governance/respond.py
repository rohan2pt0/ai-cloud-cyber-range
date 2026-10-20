#!/usr/bin/env python3
"""Crisis response: step in at an affected organisation, collect evidence properly, find what is wrong, and report it.

    ./securax respond open "codename" --kind ransomware|fund-fraud|data-breach|compromise
                          [--for "Organisation" --authorised-by "Name, role" --scope "which systems, what you may do"]
    ./securax respond kit CASE /media/usb        put the collectors, the read-me card and the custody form on a USB
    ./securax respond intake CASE /media/usb/SECURAX [--from "who handed it over"]
                                                 check every hash, record the hand-over, copy the evidence in read-only
    ./securax respond ioc import FILE [--source "advisory id"] [--tlp amber]   IOCs from an advisory (.pdf, .txt, .csv)
    ./securax respond ioc list | ioc export [--kind ip|domain|hash] [--format plain|csv|hosts]   blocklists for containment
    ./securax respond triage CASE                look for the IOCs and for common signs of compromise (exit 1 on a hit)
    ./securax respond report CASE                timeline, custody record, evidence, findings and the next steps
    ./securax respond requests CASE              the information-request list to send to the organisation's teams (CSV)
    ./securax respond verify CASE                the custody log and every evidence hash still check out
    ./securax respond list

What it holds to (doc 78):

- **Permission first.** Working for another organisation needs who authorised it and the scope, recorded before any kit.
- **Order of volatility** (RFC 3227) in the collectors: memory and running state before disks and logs.
- **Chain of custody.** Every step (kit made, collected, handed over, received, copied, analysed) is an entry in a
  hash-chained log. Editing or deleting an entry is detected by `verify`. Each evidence folder carries the SHA-256 of every
  file, checked on intake and again on every `verify`.
- **Nothing private leaves the vault.** Cases live in vault/respond/, IOCs in vault/intel/iocs/ (never in git). An IOC file
  keeps the TLP of its source, and every report and export says it.

It helps a responder; it does not replace one. Findings are leads to check, not conclusions. Standard library only; PDFs
need `pdftotext` (Ubuntu: sudo apt install poppler-utils).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import ipaddress
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VAULT = ROOT / "vault"
CASES = VAULT / "respond"
IOCS = VAULT / "intel" / "iocs"
KIT = ROOT / "governance" / "respond_kit"
KINDS = ("ransomware", "fund-fraud", "data-breach", "compromise")
TLPS = ("clear", "white", "green", "amber", "amber+strict", "red")

_s = importlib.util.spec_from_file_location("securax_incident", ROOT / "governance" / "incident.py")
incident = importlib.util.module_from_spec(_s)
_s.loader.exec_module(incident)


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# ───────────────────────────────────────────── cases and custody ─────────────────────────────────────────────
def case_dir(cid: str, root: pathlib.Path | None = None) -> pathlib.Path:
    d = (root or CASES) / cid
    if not (d / "custody.jsonl").exists():
        raise KeyError(f"No case {cid}. See them with:  ./securax respond list")
    return d


def custody(d: pathlib.Path):
    return incident.Case(d / "custody.jsonl")


def open_case(name: str, kind: str, org: str = "", authorised_by: str = "", scope: str = "", root: pathlib.Path | None = None,
              at: dt.datetime | None = None) -> str:
    if kind not in KINDS:
        raise ValueError(f"--kind must be one of: {', '.join(KINDS)}")
    if org and not (authorised_by.strip() and scope.strip()):
        raise ValueError("Working for another organisation needs --authorised-by \"name, role\" and --scope \"systems and actions\" first.")
    t = at or now()
    cid = t.strftime("IR-%Y%m%d-") + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:24]
    d = (root or CASES) / cid
    d.mkdir(parents=True, exist_ok=False)
    os.chmod(d, 0o700)
    (d / "evidence").mkdir()
    custody(d).append("open", {"name": name, "kind": kind, "for": org or "own estate", "authorised_by": authorised_by, "scope": scope}, at=t)
    return cid


def _sha(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_kit(cid: str, dest: pathlib.Path, root: pathlib.Path | None = None) -> pathlib.Path:
    d = case_dir(cid, root)
    out = dest / "SECURAX"
    (out / "tools").mkdir(parents=True, exist_ok=True)
    (out / "evidence").mkdir(exist_ok=True)
    files = {"collect.sh": "collect.sh", "collect.ps1": "collect.ps1", "README-FIRST.txt": "README-FIRST.txt",
             "CUSTODY-FORM.csv": "CUSTODY-FORM.csv", "tools-README.txt": "tools/README.txt"}
    for src, dst in files.items():
        shutil.copy2(KIT / src, out / dst)
    (out / "CASE_ID").write_text(cid + "\n")
    os.chmod(out / "collect.sh", 0o755)
    custody(d).append("kit_prepared", {"where": str(out), "collectors": {k: _sha(KIT / k) for k in ("collect.sh", "collect.ps1")}})
    return out


def check_manifest(folder: pathlib.Path) -> dict:
    """Every file listed matches its hash, and no file is missing or unlisted (collector.json and the manifest aside)."""
    man = folder / "MANIFEST.sha256"
    listed, bad, missing = {}, [], []
    for ln in man.read_text("utf-8", "ignore").splitlines():
        if ln.strip():
            h, _, rel = ln.strip().partition("  ")
            listed[rel.strip().replace("\\", "/").removeprefix("./")] = h.lower()
    for rel, h in listed.items():
        p = folder / rel
        if not p.is_file():
            missing.append(rel)
        elif _sha(p) != h:
            bad.append(rel)
    present = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} - {"MANIFEST.sha256", "collector.json"}
    extra = sorted(present - set(listed))
    return {"files": len(listed), "altered": bad, "missing": missing, "unlisted": extra, "ok": not (bad or missing or extra),
            "manifest_sha256": _sha(man)}


def _read_only(path: pathlib.Path) -> None:
    for p in [path, *path.rglob("*")]:
        mode = p.stat().st_mode
        p.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def intake(cid: str, src: pathlib.Path, handed_by: str = "", root: pathlib.Path | None = None) -> list[dict]:
    d = case_dir(cid, root)
    base = src / "evidence" if (src / "evidence").is_dir() else src
    out = []
    for folder in sorted(p for p in base.iterdir() if p.is_dir() and (p / "MANIFEST.sha256").exists()):
        target = d / "evidence" / folder.name
        if target.exists():
            out.append({"folder": folder.name, "skipped": "already taken in"})
            continue
        res = check_manifest(folder)
        meta = {}
        try:
            meta = json.loads((folder / "collector.json").read_text("utf-8-sig"))
        except (OSError, ValueError):
            pass
        shutil.copytree(folder, target)
        _read_only(target)
        rec = {"folder": folder.name, "host": meta.get("host", ""), "collected_by": meta.get("collected_by", ""),
               "collected_utc": meta.get("started_utc", ""), "handed_by": handed_by, **res}
        custody(d).append("received", rec)
        out.append(rec)
    if not out:
        raise ValueError(f"No evidence folders (with MANIFEST.sha256) under {base}")
    return out


# ───────────────────────────────────────────── IOCs ─────────────────────────────────────────────
DEFANG = [(re.compile(r"\[\.\]|\(\.\)|\{\.\}|\[dot\]", re.I), "."), (re.compile(r"\[:\]"), ":"), (re.compile(r"\bhxxp", re.I), "http"),
          (re.compile(r"\[@\]|\[at\]", re.I), "@")]
_NUM = r"\.?\d{1,3}(?!\d|\s*(?:\[\.\]|\.)\d)"          # a last octet, never the start of the next address
IP_ITEM = re.compile(r"(?<![\d.])(\d{1,3}(?:\[\.\]|\.)\d{1,3}(?:\[\.\]|\.)\d{1,3}(?:\[\.\]|\.)\d{1,3})((?:\s*(?:[-–]\s*" + _NUM + r"|,\s*" + _NUM
                     + r"(?:\s*[-–]\s*" + _NUM + r")?))*)")
DOMAIN_DEFANGED = re.compile(r"\b((?:[a-z0-9-]+(?:\[\.\]|\(\.\))+)+[a-z]{2,24})\b", re.I)
HASH = re.compile(r"(?<![0-9a-f])([0-9a-f]{64}|[0-9a-f]{40}|[0-9a-f]{32})(?![0-9a-f])", re.I)
WINDOWS_OWN = {"cmd.exe", "powershell.exe", "pwsh.exe", "rundll32.exe", "regsvr32.exe", "wmic.exe", "mshta.exe", "svchost.exe", "explorer.exe",
               "conhost.exe", "schtasks.exe", "certutil.exe", "bitsadmin.exe", "cscript.exe", "wscript.exe", "msiexec.exe"}   # names, not indicators
FILE_NEAR_HASH = re.compile(r"([\w.\-]+\.(?:jsp|jspx|war|php|aspx?|py|sh|ps1|bat|vbs|js|exe|dll|so|elf|bin|dat|tar|zip|jar))\b", re.I)


def refang(s: str) -> str:
    for rx, sub in DEFANG:
        s = rx.sub(sub, s)
    return s


def _hashes(text: str) -> set[str]:
    """Hashes, including the ones a PDF table wraps over two lines (the halves are the next two hex runs in reading order)."""
    runs = re.findall(r"(?<![0-9a-z])[0-9a-f]{8,64}(?![0-9a-z])", text, re.I)
    out, i = set(), 0
    while i < len(runs):
        a = runs[i]
        if len(a) in (32, 40, 64):
            out.add(a.lower())
        elif i + 1 < len(runs) and len(runs[i + 1]) not in (32, 40, 64) and len(a) + len(runs[i + 1]) in (32, 40, 64):
            out.add((a + runs[i + 1]).lower())
            i += 1
        i += 1
    return out


def _expand(base: str, tail: str) -> list[str]:
    a, b, c, last = (int(x) for x in base.split("."))
    out, cur = {last}, last
    for m in re.finditer(r"[-–]\s*\.?(\d{1,3})|,\s*\.?(\d{1,3})", tail):
        if m.group(1):                                              # a range from the previous number
            hi = int(m.group(1))
            out.update(range(cur, min(hi, 255) + 1))
            cur = hi
        else:
            cur = int(m.group(2))
            out.add(cur)
    return [f"{a}.{b}.{c}.{x}" for x in sorted(out) if 0 <= x <= 255]


def extract_iocs(text: str) -> dict:
    """IPs (with advisory-style ranges), domains and URLs written defanged, hashes, and file names next to a hash."""
    ips: set[str] = set()
    for m in IP_ITEM.finditer(text):
        base = m.group(1).replace("[.]", ".")
        try:
            ipaddress.IPv4Address(base)
        except ValueError:
            continue
        if "[.]" in m.group(1) or m.group(2):                       # advisories defang real indicators; plain ones are prose
            ips.update(_expand(base, m.group(2) or ""))
    doms = {refang(m.group(1)).lower() for m in DOMAIN_DEFANGED.finditer(text)}
    hashes = _hashes(text)
    files = set()
    for ln in text.splitlines():
        if HASH.search(ln) or re.match(r"^\s*\d{1,3}\s", ln):      # a table row: number, file name, hash
            files.update(f for f in FILE_NEAR_HASH.findall(ln) if f.lower() not in WINDOWS_OWN and not f.lower().endswith((".com", ".org", ".net")))
    doms -= {d for d in doms if re.fullmatch(r"\d+(\.\d+)*", d)}
    return {"ip": sorted(ips, key=lambda x: tuple(int(p) for p in x.split("."))), "domain": sorted(doms), "hash": sorted(hashes),
            "file": sorted(files)}


def pdf_text(path: pathlib.Path) -> str:
    if not shutil.which("pdftotext"):
        raise ValueError("Reading a PDF needs pdftotext (Ubuntu/WSL: sudo apt install poppler-utils). Or save the IOC pages as .txt.")
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout


def ioc_import(path: pathlib.Path, source: str = "", tlp: str = "amber", store: pathlib.Path | None = None) -> pathlib.Path:
    if tlp.lower() not in TLPS:
        raise ValueError(f"--tlp must be one of: {', '.join(TLPS)}")
    text = pdf_text(path) if path.suffix.lower() == ".pdf" else path.read_text("utf-8", "ignore")
    found = extract_iocs(text)
    if not any(found.values()):
        raise ValueError(f"{path.name}: no indicators found (IPs and domains must be written defanged, like 203[.]0[.]113[.]9)")
    name = re.sub(r"[^a-z0-9]+", "-", (source or path.stem).lower()).strip("-")[:60]
    out = (store or IOCS) / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": source or path.name, "tlp": tlp.lower(), "imported": now().isoformat(timespec="seconds"),
                               "file_sha256": _sha(path), **found}, indent=1))
    os.chmod(out, 0o600)
    return out


def ioc_load(store: pathlib.Path | None = None) -> dict:
    """{kind: {value: [source, ...]}} over every imported IOC file, plus the highest TLP among them."""
    merged = {"ip": {}, "domain": {}, "hash": {}, "file": {}}
    tlp = "clear"
    for f in sorted((store or IOCS).glob("*.json")) if (store or IOCS).exists() else []:
        try:
            d = json.loads(f.read_text("utf-8"))
        except ValueError:
            continue
        if TLPS.index(d.get("tlp", "amber")) > TLPS.index(tlp):
            tlp = d.get("tlp", "amber")
        for k in merged:
            for v in d.get(k, []):
                merged[k].setdefault(v, []).append(d.get("source", f.stem))
    merged["tlp"] = tlp
    return merged


# ───────────────────────────────────────────── triage ─────────────────────────────────────────────
AI_APIS = ("api.openai.com", "api.anthropic.com", "api.deepseek.com", "dashscope.aliyuncs.com", "generativelanguage.googleapis.com",
           "api.mistral.ai", "openrouter.ai", "api.groq.com", "api.together.xyz")
ODD_PATHS = re.compile(r"\\(?:AppData\\Local\\Temp|Windows\\Temp|Users\\Public|PerfLogs|ProgramData\\[^\\\"]+\.exe)\\?|(?:^|\s)/(?:tmp|var/tmp|dev/shm)/\S+", re.I)


def _texts(folder: pathlib.Path):
    for p in folder.rglob("*"):
        if not p.is_file() or p.stat().st_size > 50_000_000 or p.suffix.lower() in (".evtx", ".raw", ".lime", ".mem", ".tgz", ".zip", ".gz"):
            continue
        b = p.read_bytes()
        if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
            yield p, b.decode("utf-16", "ignore")                   # reg export and some Windows tools write UTF-16
        elif b"\0" not in b[:4096]:
            yield p, b.decode("utf-8", "ignore")


def triage(cid: str, root: pathlib.Path | None = None, store: pathlib.Path | None = None) -> list[dict]:
    d = case_dir(cid, root)
    iocs = ioc_load(store)
    hits: list[dict] = []
    seen = set()

    def hit(sev, what, where, value, why):
        k = (what, where, value)
        if k not in seen:
            seen.add(k)
            hits.append({"severity": sev, "what": what, "where": where, "value": value, "why": why})

    for ev in sorted(p for p in (d / "evidence").iterdir() if p.is_dir()):
        for p, text in _texts(ev):
            rel = f"{ev.name}/{p.relative_to(ev).as_posix()}"
            low = text.lower()
            for ip in set(re.findall(r"(?<![\d.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\d.])", text)) & set(iocs["ip"]):
                hit("critical", "known-bad IP address", rel, ip, "listed by " + ", ".join(iocs["ip"][ip]))
            for dom, src in iocs["domain"].items():
                if dom in low:
                    hit("critical", "known-bad domain", rel, dom, "listed by " + ", ".join(src))
            for h in set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", low)) & set(iocs["hash"]):
                hit("critical", "known-bad file hash", rel, h, "listed by " + ", ".join(iocs["hash"][h]))
            for fn, src in iocs["file"].items():
                if re.search(r"(?<![\w.-])" + re.escape(fn.lower()) + r"(?![\w.-])", low):
                    hit("high", "file name from an advisory", rel, fn, "listed by " + ", ".join(src) + " (names can collide: check the hash)")
            if p.name in ("processes.csv", "processes.txt", "connections-with-process.csv", "process-tree.txt"):
                for m in ODD_PATHS.finditer(text):
                    hit("medium", "program running from a temp or public folder", rel, m.group(0).strip()[:120], "malware often runs from writable folders")
            if p.name == "deleted-but-running.txt" and text.strip():
                hit("high", "program running after its file was deleted", rel, text.strip().splitlines()[0][:120], "a classic sign of an implant on Linux")
            if p.name == "startup-folders.csv":
                for row in csv.DictReader(io.StringIO(text)):
                    if re.search(r"\.(exe|bat|cmd|vbs|js|ps1|hta|scr)$", row.get("Name", ""), re.I):
                        hit("medium", "program or script in a startup folder", rel, row.get("Name", ""), "runs at every log-on")
            if p.name in ("dns-cache.txt", "connections-with-process.csv", "journal-3-days.txt"):
                for api in AI_APIS:
                    if api in low:
                        hit("medium", "AI service contacted from this machine", rel, api, "expected on a laptop, unusual on a server: attackers use AI services to drive attacks")
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    hits.sort(key=lambda h: (order[h["severity"]], h["what"], h["where"]))
    (d / "triage.json").write_text(json.dumps({"tlp": iocs["tlp"], "at": now().isoformat(timespec="seconds"), "hits": hits}, indent=1))
    custody(d).append("analysed", {"tool": "respond triage", "hits": len(hits), "ioc_sources_tlp": iocs["tlp"],
                                   "ioc_counts": {k: len(v) for k, v in iocs.items() if k != "tlp"}})
    return hits


# ───────────────────────────────────────────── requests, report, verify ─────────────────────────────────────────────
REQUESTS = [  # (workstream, source, what to ask for, period, fields) — a generic pattern for any affected organisation
    ("Timeline", "Incident management", "What was seen, when, by whom; actions so far and who took them", "From first sign to now", "Date-time with time zone, event, system, team"),
    ("Architecture", "IT operations", "Network, DC/DR and data-flow diagrams for the affected systems; recent changes", "Current, plus changes in the last 30 days", "Diagram, change ID, implementer, approver"),
    ("Identity", "Active Directory / PAM / IdP", "Admin and user log-ons, privileged sessions, shared accounts, permission changes", "Two weeks before detection onward", "Account, source IP or host, time, action, approval"),
    ("Endpoints and servers", "Affected hosts", "Collector output from each affected host (this kit), EDR alerts and quarantine", "Detection window and before", "Host, folder, manifest hash"),
    ("Network", "Firewall / VPN / proxy / IDS / WAF / DNS", "Allowed and blocked connections, VPN sessions, DNS queries, WAF events", "Two weeks before detection onward", "Time, source, destination, port, action, user"),
    ("Applications and APIs", "Application owners", "Application, API gateway and web server logs; API keys and service accounts in use", "Detection window and before", "Request ID, client, endpoint, status, identity"),
    ("Logging gaps", "SOC / SIEM", "Which logs exist, retention, and any gaps, deletions or disabled logging", "Retention period", "Source, retention, first and last event, gaps"),
    ("Backups", "Backup team", "Backups and snapshots available, last good copy, any deletion or encryption of backups", "Last 90 days", "Item, time, location, verified (yes/no)"),
]
REQUESTS_BY_KIND = {
    "fund-fraud": [("Transactions", "Core banking / payment switch / aggregator", "All transfers in the window, suspect and legitimate, with approvals and reconciliation", "Detection window and before", "Reference (UTR), amount, beneficiary, time, status, maker and checker"),
                   ("Beneficiaries", "Core banking / payment platform", "Beneficiary creation, change and approval history for the suspect beneficiaries", "Last 3 months", "Beneficiary, account, created by, approved by, time"),
                   ("Payment integrations", "Integration / middleware owners", "Message and API logs to banks, aggregators and payment rails; credential and certificate changes", "Detection window and before", "Message ID, time, status, identity, certificate (never private keys)")],
    "ransomware": [("Encryption scope", "IT operations", "Which hosts and shares are encrypted, ransom notes, file extensions, first encrypted time", "Detection window", "Host, share, note file, first-seen time"),
                   ("Exfiltration", "Network / proxy / cloud storage", "Large outbound transfers and uploads to file-sharing or cloud storage", "Two weeks before encryption", "Time, source, destination, bytes")],
    "data-breach": [("Data affected", "Data owners / DPO", "What data, how many people, where it was stored, who could reach it", "Detection window", "Dataset, records, sensitivity, location"),
                    ("Exposure", "Application / cloud owners", "Public buckets, open databases or dashboards, and their access logs", "Last 90 days", "Resource, exposure, access log")],
}


def requests_csv(cid: str, root: pathlib.Path | None = None) -> pathlib.Path:
    d = case_dir(cid, root)
    kind = custody(d).events()[0]["data"]["kind"]
    out = d / "information-requests.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["#", "workstream", "system or team", "what we need", "period", "fields or format", "status", "notes"])
        for i, r in enumerate(REQUESTS + REQUESTS_BY_KIND.get(kind, []), 1):
            w.writerow([i, *r, "requested", ""])
    custody(d).append("note", {"text": "information-request list written", "file": out.name})
    return out


def verify(cid: str, root: pathlib.Path | None = None) -> list[str]:
    d = case_dir(cid, root)
    problems = custody(d).verify()
    for ev in sorted(p for p in (d / "evidence").iterdir() if p.is_dir()):
        r = check_manifest(ev)
        if not r["ok"]:
            problems.append(f"evidence {ev.name}: altered {r['altered'][:3]}, missing {r['missing'][:3]}, unlisted {r['unlisted'][:3]}")
    return problems


def _step(kind: str, d: dict) -> str:
    if kind == "open":
        return f"case opened ({d['kind']}) for {d['for']}"
    if kind == "kit_prepared":
        return f"kit written to {d['where']}"
    if kind == "received":
        return (f"{d['folder']} from {d.get('host') or '?'} (collected by {d.get('collected_by') or '?'}; handed over by {d.get('handed_by') or '?'}): "
                f"{d['files']} files, {'hashes verified' if d['ok'] else 'HASH PROBLEMS'}")
    if kind == "analysed":
        return f"triage: {d['hits']} lead(s)"
    return d.get("text") or json.dumps(d)[:120]


def report(cid: str, root: pathlib.Path | None = None) -> pathlib.Path:
    d = case_dir(cid, root)
    ev = custody(d).events()
    o = ev[0]["data"]
    tri = json.loads((d / "triage.json").read_text()) if (d / "triage.json").exists() else {"hits": [], "tlp": "clear"}
    problems = verify(cid, root)
    tlp = tri.get("tlp", "clear").upper()
    L = [f"# Incident response report: {o['name']} ({cid})", "", f"**TLP:{tlp}** (the highest marking among the IOC sources used). "
         "Share it only as that marking allows.", "", "| | |", "|---|---|", f"| Kind | {o['kind']} |", f"| For | {o['for']} |",
         f"| Authorised by | {o.get('authorised_by') or 'own estate'} |", f"| Scope | {o.get('scope') or 'own estate'} |",
         f"| Opened | {ev[0]['ts']} |", f"| Integrity | {'custody log and every evidence hash verify' if not problems else 'PROBLEMS: ' + '; '.join(problems)} |", ""]
    L += ["## Chain of custody", "", "| # | time (UTC) | by | step | detail |", "|---|---|---|---|---|"]
    for e in ev:
        det = e["data"]
        txt = _step(e["kind"], det)
        L.append(f"| {e['seq']} | {e['ts']} | {e['actor']} | {e['kind']} | {txt} |")
    L += ["", "## Leads from triage", ""]
    if tri["hits"]:
        L += ["| severity | what | where | value | why |", "|---|---|---|---|---|"]
        L += [f"| {h['severity']} | {h['what']} | `{h['where']}` | `{h['value']}` | {h['why']} |" for h in tri["hits"]]
    else:
        L.append("No IOC matched and no common sign was found. That is not proof of a clean system: check what was not collected.")
    L += ["", "## Next steps", "",
          "1. **Contain:** block the matched addresses and domains (`./securax respond ioc export --format csv`); disable accounts and rotate every "
          "secret that was on an affected system; isolate affected hosts without switching them off.",
          "2. **Preserve:** keep the original USB and the vault copy; make working copies for analysis; never analyse the original.",
          "3. **Analyse:** review each lead above; extend collection to every host that talked to a matched address.",
          "4. **Eradicate and recover:** rebuild from known-good images or verified backups; patch the entry point; reset credentials.",
          "5. **Report:** CERT-In within 6 hours of noticing (and any sector regulator): `./securax incident open ... --regulators cert-in,...`.",
          "6. **Harden:** fix what let it happen (MFA, patching, logging, egress limits, maker-checker on money movement).", "",
          "_Leads are pointers for a responder to check, not findings of fact. Generated by `./securax respond report`._"]
    out = d / "report.md"
    out.write_text("\n".join(L) + "\n")
    return out


# ───────────────────────────────────────────── command line ─────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="./securax respond", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("open")
    p.add_argument("name")
    p.add_argument("--kind", default="compromise")
    p.add_argument("--for", dest="org", default="")
    p.add_argument("--authorised-by", default="")
    p.add_argument("--scope", default="")
    p = sub.add_parser("kit")
    p.add_argument("case")
    p.add_argument("dest")
    p = sub.add_parser("intake")
    p.add_argument("case")
    p.add_argument("src")
    p.add_argument("--from", dest="handed_by", default="")
    p = sub.add_parser("ioc")
    p.add_argument("action", choices=["import", "list", "export"])
    p.add_argument("file", nargs="?")
    p.add_argument("--source", default="")
    p.add_argument("--tlp", default="amber")
    p.add_argument("--kind", default="")
    p.add_argument("--format", default="plain", choices=["plain", "csv", "hosts"])
    for name in ("triage", "report", "requests", "verify"):
        sub.add_parser(name).add_argument("case")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "open":
            cid = open_case(a.name, a.kind, a.org, a.authorised_by, a.scope)
            print(f"✔ case {cid} opened (custody log started).\n  Next:  ./securax respond kit {cid} /media/<your-usb>     (Windows: the USB's drive, e.g. E:/)")
        elif a.cmd == "kit":
            out = make_kit(a.case, pathlib.Path(a.dest))
            print(f"✔ responder kit written to {out}\n  Optional tools (memory, full triage): see {out / 'tools' / 'README.txt'}\n  On site: follow {out / 'README-FIRST.txt'}")
        elif a.cmd == "intake":
            for r in intake(a.case, pathlib.Path(a.src), a.handed_by):
                if "skipped" in r:
                    print(f"  · {r['folder']}: {r['skipped']}")
                else:
                    print(f"  {'✔' if r['ok'] else '✗'} {r['folder']}: {r['files']} files, " + ("every hash matches" if r["ok"] else
                          f"PROBLEM: altered {len(r['altered'])}, missing {len(r['missing'])}, unlisted {len(r['unlisted'])} (kept and flagged)"))
            print(f"  Next:  ./securax respond triage {a.case}")
        elif a.cmd == "ioc":
            if a.action == "import":
                if not a.file:
                    print("Name the advisory:  ./securax respond ioc import advisory.pdf --source \"advisory id\" --tlp amber")
                    return 2
                out = ioc_import(pathlib.Path(a.file).expanduser(), a.source, a.tlp)
                d = json.loads(out.read_text())
                print(f"✔ TLP:{d['tlp'].upper()} · {len(d['ip'])} IPs, {len(d['domain'])} domains, {len(d['hash'])} hashes, {len(d['file'])} file names "
                      f"from {pathlib.Path(a.file).name}\n  Kept privately in vault/intel/iocs/{out.name} (never in git). Check the counts against the advisory.")
            else:
                io_ = ioc_load()
                kinds = [a.kind] if a.kind else ["ip", "domain", "hash", "file"]
                if a.action == "list":
                    print(f"Imported IOCs (highest marking TLP:{io_['tlp'].upper()}): " + ", ".join(f"{len(io_[k])} {k}" for k in ("ip", "domain", "hash", "file")))
                    return 0
                print(f"# TLP:{io_['tlp'].upper()}: share only as that marking allows", file=sys.stderr)
                for k in kinds:
                    for v in io_[k]:
                        if a.format == "hosts" and k == "domain":
                            print(f"0.0.0.0 {v}")
                        elif a.format == "csv":
                            print(f"{k},{v},{'|'.join(io_[k][v])}")
                        elif a.format == "plain":
                            print(v)
        elif a.cmd == "triage":
            hits = triage(a.case)
            if not hits:
                print("No IOC matched and no common sign was found (check what was not collected).")
            for h in hits[:40]:
                print(f"  {h['severity']:<8} {h['what']:<44} {h['value'][:50]:<50} {h['where']}")
            print(f"  {len(hits)} lead(s). Report:  ./securax respond report {a.case}")
            return 1 if hits else 0
        elif a.cmd == "report":
            print(f"✔ {report(a.case)}")
        elif a.cmd == "requests":
            print(f"✔ {requests_csv(a.case)}  (open it in Excel; send each row to the team named)")
        elif a.cmd == "verify":
            probs = verify(a.case)
            print("✔ the custody log and every evidence hash verify" if not probs else "\n".join("✗ " + x for x in probs))
            return 1 if probs else 0
        elif a.cmd == "list":
            rows = sorted(CASES.glob("*/custody.jsonl")) if CASES.exists() else []
            if not rows:
                print("No response cases yet.  Start one:  ./securax respond open \"codename\" --kind ransomware")
            for f in rows:
                o = incident.Case(f).events()[0]
                print(f"  {f.parent.name:<36} {o['data']['kind']:<12} for {o['data']['for']}")
        else:
            print(__doc__)
        return 0
    except (KeyError, ValueError, FileExistsError, FileNotFoundError) as e:
        print(str(e).strip("'\""))
        return 1


if __name__ == "__main__":
    sys.exit(main())
