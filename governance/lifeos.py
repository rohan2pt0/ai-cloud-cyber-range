#!/usr/bin/env python3
"""Bring notes you keep elsewhere into the Life OS Inbox, where each one becomes a decision (doc 84).

    ./securax lifeos import keep [FILE]   a Google Takeout export of Keep (the .zip, or its folder). No file: the newest
                                          takeout-*.zip in Downloads, Documents or Desktop (the Windows ones too)
    ./securax lifeos status               how many imported notes are waiting for the Guiding Map to pick them up

Google Keep has no API for personal accounts, so the way out is Google Takeout (takeout.google.com > Keep > Export). Each unticked
checklist line becomes an action to decide (its note's title becomes the area); each plain note becomes a note; ticked lines and
notes in the bin are left out. The result goes to portal/inbox-import.json, which the Guiding Map merges into the Inbox the next time
it opens (each note once, by id). That file stays on this machine (git-ignored). Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "portal" / "inbox-import.json"
HOME = pathlib.Path.home()


def find_takeout() -> pathlib.Path | None:
    dirs = [HOME / d for d in ("Downloads", "Documents", "Desktop")] + [p for p in pathlib.Path("/mnt/c/Users").glob("*/Downloads")] if pathlib.Path("/mnt/c/Users").exists() else [HOME / d for d in ("Downloads", "Documents", "Desktop")]
    files = [f for d in dirs if d.is_dir() for f in d.glob("takeout-*.zip")]
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def _notes(src: pathlib.Path):
    """(name, parsed note) for every Keep note JSON in a Takeout zip or folder."""
    if src.is_file() and zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if "/Keep/" in "/" + n and n.endswith(".json"):
                    try:
                        yield n, json.loads(z.read(n).decode("utf-8"))
                    except (ValueError, UnicodeDecodeError):
                        continue
    elif src.is_dir():
        for f in sorted(src.rglob("*.json")):
            if "Keep" in f.parts:
                try:
                    yield str(f), json.loads(f.read_text("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    continue


def _id(*parts: str) -> str:
    return "keep-" + hashlib.sha1("\x1f".join(parts).encode()).hexdigest()[:16]


def convert(src: pathlib.Path) -> list[dict]:
    items = []
    for name, n in _notes(src):
        if not isinstance(n, dict) or n.get("isTrashed"):
            continue
        title = (n.get("title") or "").strip()
        labels = ", ".join(x.get("name", "") for x in n.get("labels", []) if isinstance(x, dict) and x.get("name"))
        area = title or labels or "Google Keep"
        lines = n.get("listContent") or []
        if lines:
            for ln in lines:
                text = (ln.get("text") or "").strip() if isinstance(ln, dict) else ""
                if text and not ln.get("isChecked"):
                    items.append({"id": _id(name, text), "t": text[:500], "kind": "action", "area": area[:80], "from": "keep"})
            continue
        body = (n.get("textContent") or "").strip()
        if title or body:
            text = (title + (": " if title and body else "") + body)[:500]
            items.append({"id": _id(name, text), "t": text, "kind": "note", "area": (labels or "Google Keep")[:80], "from": "keep"})
    return items


def write(items: list[dict], out: pathlib.Path = OUT) -> tuple[int, int]:
    """(added, total): merged with what is already waiting, each note once."""
    try:
        whole = json.loads(out.read_text("utf-8"))
        whole = whole if isinstance(whole, dict) else {}
    except (OSError, ValueError):
        whole = {}
    old = whole.get("items", [])
    have = {x["id"] for x in old}
    new = [x for x in items if x["id"] not in have]
    out.parent.mkdir(parents=True, exist_ok=True)
    whole.update({"about": "Notes waiting for the Guiding Map Inbox (./securax lifeos). Private: never committed.", "items": old + new})
    out.write_text(json.dumps(whole, ensure_ascii=False, indent=1), "utf-8")        # other keys (such as "resolved") stay
    try:
        out.chmod(0o600)
    except OSError:
        pass
    return len(new), len(old) + len(new)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:2] == ["import", "workbook"] or argv[:1] in (["docs"], ["papers"], ["readers"]):     # the life workbooks and private documents (doc 104)
        import importlib.util
        rel = "governance/lifebook.py" if argv[0] == "import" else "governance/lifedocs.py"
        spec = importlib.util.spec_from_file_location("securax_" + pathlib.Path(rel).stem, ROOT / rel)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.main(argv[2:] if argv[0] == "import" else argv if argv[0] in ("papers", "readers") else argv[1:])
    if argv[:2] == ["import", "keep"]:
        src = pathlib.Path(" ".join(argv[2:])).expanduser() if argv[2:] else find_takeout()
        if not src or not src.exists():
            print("No Google Keep export found. Get one: takeout.google.com > Deselect all > Keep > Export, download the .zip to Downloads,")
            print("then run this again (it finds the newest takeout-*.zip by itself).")
            return 1
        items = convert(src)
        if not items:
            print(f"{src.name} holds no Keep notes (is it a Keep export?).")
            return 1
        added, total = write(items)
        acts = sum(1 for x in items if x["kind"] == "action")
        print(f"✔ {len(items)} from Keep ({acts} unticked list lines as actions to decide, {len(items) - acts} notes); {added} new.")
        print("  Open the Guiding Map: they appear in the Inbox, where each one gets a next step and a date (or stays a note).")
        return 0
    if argv[:1] == ["status"]:
        try:
            n = len(json.loads(OUT.read_text("utf-8")).get("items", []))
        except (OSError, ValueError):
            n = 0
        print(f"{n} imported note(s) waiting in {OUT.relative_to(ROOT)} (the Guiding Map takes each one once).")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
