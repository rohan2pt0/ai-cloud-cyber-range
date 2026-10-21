#!/usr/bin/env python3
"""Keep ransomware from poisoning the backups, and prove a restore really works (doc 88).

    ./securax backup                 runs `check` first: when the data looks encrypted, the backup is kept but named -SUSPECT,
                                     nothing old is deleted, nothing goes off-site, and you get an alert (exit 3)
    python3 governance/ransomguard.py check [--json]       is the data on this machine readable, and are the canary files intact?
    python3 governance/ransomguard.py pick DIR [DIR...]    the newest backup that is NOT suspect (what `restore latest` uses)
    python3 governance/ransomguard.py prune DIR --keep N [--weeks W] [--months M]
                                     keep the newest N, plus the newest of each of the last W weeks and M months; never the
                                     newest clean one; at most 3 suspect files
    python3 governance/ransomguard.py verify FOLDER [--json]
                                     the restore twin: an unpacked backup is opened file by file (databases checked with SQLite's
                                     own integrity check, the vault parsed, the canary compared) without touching your live data

Why: a backup routine that keeps "the newest 7" copies will, a week after ransomware encrypts your files, hold only encrypted
copies. Replication and sync copy the damage too. So every backup is checked before it may replace an older one.

Two signals, either one is enough:
- canary files: small files with fixed text, planted in vault/ and ~/.securax. Ransomware encrypts them with everything else.
- the vault's own files: JSON must parse, text must be text, workbooks and PDFs must start the way they always do. Known ransom
  notes and ransomware file endings are flagged by name.
Standard library only. Exit codes: 0 clean, 1 a check failed (verify), 2 bad usage, 3 suspect.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import sqlite3
import sys
import tarfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANARY_NAME = ".securax-canary.txt"
CANARY_TEXT = ("SecuRAX canary file. Do not edit or delete it.\n"
               "If this text is unreadable, something encrypted your files: run  ./securax continuity show data-lost\n")
MAGIC = {".xlsx": b"PK\x03\x04", ".docx": b"PK\x03\x04", ".pptx": b"PK\x03\x04", ".zip": b"PK\x03\x04", ".pdf": b"%PDF",
         ".png": b"\x89PNG", ".jpg": b"\xff\xd8", ".jpeg": b"\xff\xd8", ".gz": b"\x1f\x8b", ".tgz": b"\x1f\x8b"}
TEXT = {".json", ".jsonl", ".md", ".txt", ".csv", ".yml", ".yaml", ".ics", ".html", ".log"}
NOTE = re.compile(r"decrypt|ransom|(recover|restore|how[_ -]?to).*(files|data)", re.I)
ENDINGS = {".locked", ".encrypted", ".crypt", ".crypted", ".lockbit", ".akira", ".ryk", ".wncry", ".locky", ".cerber"}
SUSPECT_TAG = "-SUSPECT"
STAMP = re.compile(r"securax-(\d{8})-(\d{6})")
MAX_SUSPECT = 3
DB = re.compile(r"\.(db|sqlite3?)(-wal|-shm|-journal)?$")
MAX_FILES = 20000                      # a scan stops here: a vault is small; this bounds the time on a huge folder


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def canary_files(root: pathlib.Path = ROOT) -> dict[str, pathlib.Path]:
    """Where the canaries live, by a name that does not change when the checkout moves (vault/ of THIS root, and ~/.securax)."""
    return {"vault": root / "vault" / CANARY_NAME, "home": home() / CANARY_NAME}


def plant(root: pathlib.Path = ROOT, again: bool = False) -> list[str]:
    """Write each canary that is not there. A canary whose TEXT changed is left alone (that is the evidence); `again` rewrites
    it too, after you have checked that it was a false alarm."""
    made = []
    for f in canary_files(root).values():
        if f.exists() and not again:
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(CANARY_TEXT, "utf-8")
        made.append(str(f))
    return made


def canary_ok(f: pathlib.Path) -> bool:
    try:
        return f.read_text("utf-8") == CANARY_TEXT
    except (OSError, UnicodeDecodeError):
        return False


# --------------------------------------------------------------------------------------------------------- file checks
def readable(f: pathlib.Path) -> bool | None:
    """True when the file looks like what its name says, False when it does not, None when we cannot tell (unknown type).
    The question is "was it encrypted?", not "is it perfect": a text file that is merely malformed, saved with a byte-order mark,
    in UTF-16 or in a Windows code page still reads as text. Encrypted bytes read as none of those."""
    ext = f.suffix.lower()
    try:
        if ext in MAGIC:
            with f.open("rb") as fh:
                head = fh.read(8)
            return head.startswith(MAGIC[ext]) or f.stat().st_size == 0
        if ext in TEXT:
            with f.open("rb") as fh:
                raw = fh.read(65536)
            return looks_like_text(raw)
    except OSError:
        return False
    return None


def looks_like_text(raw: bytes) -> bool:
    if not raw or raw.startswith((b"\xff\xfe", b"\xfe\xff")):          # empty, or UTF-16 (Excel's "Unicode text")
        return True
    try:
        raw.decode("utf-8-sig")
        return b"\x00" not in raw
    except UnicodeDecodeError as exc:
        if exc.start >= len(raw) - 3:                                     # a character cut by the 64 KB read
            return b"\x00" not in raw
    if b"\x00" in raw:
        return False
    txt = raw.decode("cp1252", errors="replace")                         # Excel's default CSV on Windows
    good = sum(ch.isprintable() or ch in "\r\n\t" for ch in txt)
    return good >= 0.95 * len(txt) and "\ufffd" not in txt


def scan(folders: list[pathlib.Path], canaries: list[pathlib.Path] | None = None) -> dict:
    checked, bad, notes, odd, n = 0, [], [], [], 0
    for d in folders:
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            n += 1
            if n > MAX_FILES:
                break
            if not f.is_file() or f.name == CANARY_NAME or f.name.startswith(("~$", ".~lock.")):
                continue                                    # Office and LibreOffice lock files are not documents
            if NOTE.search(f.name):
                notes.append(str(f))
            if f.suffix.lower() in ENDINGS:
                odd.append(str(f))
            r = readable(f)
            if r is None:
                continue
            checked += 1
            if not r:
                bad.append(str(f))
    canaries = canaries or []
    changed = [str(c) for c in canaries if c.exists() and not canary_ok(c)]
    gone = [str(c) for c in canaries if not c.exists()]
    damaged = len(bad) >= 3 and len(bad) >= 0.25 * checked
    # Names prove nothing alone (a postmortem called "Tabletop ransomware", an advisory about it, an old file.locked): a note or an
    # ending counts only next to content that changed. A canary whose text changed, many unreadable files, or many files renamed
    # to a ransomware ending count alone. A canary that is simply missing is planted again (a new checkout, a deleted folder).
    content = bool(changed or bad)
    reasons = []
    if changed:
        reasons.append(f"{len(changed)} canary file(s) no longer hold their text")
    if damaged:
        reasons.append(f"{len(bad)} of {checked} files no longer open as what they are")
    if len(odd) >= 3 or (odd and content):
        reasons.append(f"{len(odd)} file(s) renamed to a ransomware ending")
    if notes and content:
        reasons.append(f"{len(notes)} file(s) named like a ransom note")
    return {"suspect": bool(reasons), "reasons": reasons, "checked": checked, "unreadable": bad[:20],
            "canaries": len(canaries), "canaries_lost": changed + gone, "notes": notes[:10], "endings": odd[:10]}


def check(root: pathlib.Path = ROOT) -> dict:
    cans = list(canary_files(root).values())
    res = scan([root / "vault"], cans)
    if not res["suspect"]:
        plant(root)                         # a canary that is simply missing (a new checkout, a deleted folder) comes back
    return res


# ------------------------------------------------------------------------------------------------------- backup files
def backups(*dirs: pathlib.Path) -> list[pathlib.Path]:
    """Every backup in these folders, newest first (by the time in its name, the file time when there is none)."""
    out = [f for d in dirs if d and d.is_dir() for f in d.glob("securax-*.tar.gz*")
           if f.is_file() and (f.name.endswith(".tar.gz") or f.name.endswith(".tar.gz.gpg"))]
    return sorted(out, key=when, reverse=True)


def when(f: pathlib.Path) -> float:
    m = STAMP.search(f.name)
    if m:
        try:
            return dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").timestamp()
        except ValueError:
            pass
    return f.stat().st_mtime


def suspect(f: pathlib.Path) -> bool:
    return SUSPECT_TAG in f.name


def pick(*dirs: pathlib.Path, encrypted_only: bool = False) -> pathlib.Path | None:
    for f in backups(*dirs):
        if not suspect(f) and (f.name.endswith(".gpg") or not encrypted_only):
            return f
    return None


def to_keep(files: list[pathlib.Path], keep: int, weeks: int = 4, months: int = 3) -> set[pathlib.Path]:
    clean = [f for f in sorted(files, key=when, reverse=True) if not suspect(f)]
    kept = set(clean[:max(keep, 1)])
    seen_w, seen_m = set(), set()
    for f in clean:
        d = dt.datetime.fromtimestamp(when(f))
        w, m = d.isocalendar()[:2], (d.year, d.month)
        if w not in seen_w and len(seen_w) < weeks:
            seen_w.add(w)
            kept.add(f)
        if m not in seen_m and len(seen_m) < months:
            seen_m.add(m)
            kept.add(f)
    kept.update(sorted((f for f in files if suspect(f)), key=when, reverse=True)[:MAX_SUSPECT])
    return kept


def prune(folder: pathlib.Path, keep: int, weeks: int = 4, months: int = 3, encrypted_only: bool = False,
          suspects_only: bool = False) -> list[str]:
    """Delete what retention does not keep. With suspects_only (a suspect run), only suspect copies beyond the newest few go:
    a run of false alarms cannot fill the disk, and no clean copy is touched."""
    files = [f for f in backups(folder) if f.name.endswith(".gpg") or not encrypted_only]
    kept = to_keep(files, keep, weeks, months) if not suspects_only else {f for f in files if not suspect(f)} | to_keep(files, 1, 0, 0)
    gone = []
    for f in files:
        if f not in kept:
            f.unlink(missing_ok=True)
            gone.append(f.name)
    return gone


# ------------------------------------------------------------------------------------------------------------ the twin
def verify(folder: pathlib.Path) -> dict:
    """Open an unpacked backup the way a restore would, in a scratch folder: every volume and the vault unpack, every
    database passes SQLite's integrity check, the vault's files open, the canary is intact. Live data is never touched."""
    res = {"ok": True, "volumes": 0, "databases": 0, "db_bad": [], "problems": []}
    with tempfile.TemporaryDirectory(prefix="securax-twin-", dir=folder) as tmp:      # beside the unpacked backup, not in /tmp
        twin = pathlib.Path(tmp)
        for t in sorted(folder.glob("*.tgz")):
            dest = twin / t.stem
            dest.mkdir()
            whole = t.name == "vault.tgz"                       # the vault is small: open all of it; a volume: its databases only
            try:
                with tarfile.open(t) as tf:
                    for m in tf:                                 # reading every member proves the whole archive is intact
                        if not m.isfile() or not (whole or DB.search(m.name)):
                            continue
                        if m.name.startswith("/") or ".." in pathlib.PurePosixPath(m.name).parts:
                            raise tarfile.TarError(f"unsafe member {m.name}")
                        out = dest / m.name
                        out.parent.mkdir(parents=True, exist_ok=True)
                        with tf.extractfile(m) as src, out.open("wb") as fh:
                            shutil.copyfileobj(src, fh)
            except (tarfile.TarError, OSError, EOFError) as exc:
                res["problems"].append(f"{t.name} does not unpack: {exc}")
                continue
            res["volumes"] += t.name.startswith("vol-")
            for db in (p for p in dest.rglob("*") if p.is_file() and p.suffix in {".db", ".sqlite", ".sqlite3"}):
                res["databases"] += 1
                try:
                    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as con:
                        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                            res["db_bad"].append(db.name)
                except sqlite3.DatabaseError:
                    res["db_bad"].append(db.name)
            if not whole:
                shutil.rmtree(dest, ignore_errors=True)          # one volume's databases on disk at a time
        vault = twin / "vault" / "vault"
        cans = [vault / CANARY_NAME] if (vault / CANARY_NAME).exists() else []
        res["scan"] = scan([vault], cans)
    if res["db_bad"]:
        res["problems"].append(f"{len(res['db_bad'])} database(s) fail their integrity check: {', '.join(res['db_bad'][:5])}")
    if res["scan"]["suspect"]:
        res["problems"].append("the backed-up vault itself looks encrypted: " + "; ".join(res["scan"]["reasons"]))
    if not (folder / "env").exists():
        res["problems"].append("no .env in the backup (your keys would not come back)")
    res["ok"] = not res["problems"]
    return res


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ransomguard", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check")
    c.add_argument("--json", action="store_true")
    p = sub.add_parser("pick")
    p.add_argument("dirs", nargs="+")
    p.add_argument("--encrypted", action="store_true")
    r = sub.add_parser("prune")
    r.add_argument("dir")
    r.add_argument("--keep", type=int, default=7)
    r.add_argument("--weeks", type=int, default=4)
    r.add_argument("--months", type=int, default=3)
    r.add_argument("--encrypted", action="store_true")
    r.add_argument("--suspects-only", action="store_true")
    sub.add_parser("replant")
    v = sub.add_parser("verify")
    v.add_argument("dir")
    v.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        res = check()
        if a.json:
            print(json.dumps(res))
        elif res["suspect"]:
            print("✗ RANSOMWARE SUSPECTED: " + "; ".join(res["reasons"]))
            print("  (A false alarm? Open the files below yourself. Only if they are fine:  ./securax backup clear-alarm)")
            for f in (res["canaries_lost"] + res["notes"] + res["endings"] + res["unreadable"])[:8]:
                print("    " + f)
        else:
            print(f"✔ data looks normal: {res['checked']} files open as what they are, {res['canaries']} canary file(s) intact")
        return 3 if res["suspect"] else 0
    if a.cmd == "pick":
        f = pick(*(pathlib.Path(d).expanduser() for d in a.dirs), encrypted_only=a.encrypted)
        if f:
            print(f)
        return 0 if f else 1
    if a.cmd == "prune":
        for name in prune(pathlib.Path(a.dir).expanduser(), a.keep, a.weeks, a.months, a.encrypted, a.suspects_only):
            print(f"  removed old backup {name}")
        return 0
    if a.cmd == "replant":
        for f in plant(again=True):
            print(f"  ✔ canary rewritten: {f}")
        print("Only do this after checking your files yourself: the next backup is guarded again from here.")
        return 0
    if a.cmd == "verify":
        res = verify(pathlib.Path(a.dir))
        if a.json:
            print(json.dumps(res))
        else:
            for line in res["problems"]:
                print("  ✗ " + line)
            if res["ok"]:
                print(f"  ✔ restore twin: {res['volumes']} data volume(s) unpack, {res['databases']} database(s) pass SQLite's integrity "
                      f"check, {res['scan']['checked']} vault file(s) open, canary {'intact' if res['scan']['canaries'] else 'not in this backup yet'}")
        return 0 if res["ok"] else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
