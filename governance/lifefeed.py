#!/usr/bin/env python3
"""LIFEFEED — what the estate already knows, handed to the Guiding Map so you never type it.

Writes portal/estate-feed.json (served same-origin at /portal/estate-feed.json next to the cockpit). The Guiding Map's Today screen
shows up to four lines from it under "From your estate". Sources, all read-only and local:
  * the cockpit snapshot (portal/cockpit.json): the most urgent red items, with the command that fixes each;
  * the certification planner (learning/certs.py + ~/.securax/certs-state.json): the certification you are on and its exam-by date;
  * the backup folder: how old the newest backup is, and whether it is encrypted.
Nothing personal is added: no amounts, no names, no keys. Runs automatically after every cockpit refresh (so after `./securax up`).

    ./securax lifefeed [--out portal/estate-feed.json] [--print]
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "portal" / "estate-feed.json"
COCKPIT = ROOT / "portal" / "cockpit.json"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def read_env(path: pathlib.Path = ROOT / "local" / "compose" / ".env") -> dict:
    out = {}
    try:
        for line in path.read_text("utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def cockpit_items(path: pathlib.Path = COCKPIT, limit: int = 2) -> list[dict]:
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    reds = [m for m in data.get("metrics", []) if m.get("status") == "red"]
    reds.sort(key=lambda m: (not m.get("urgent"), -int(m.get("importance") or 0)))
    items = [{"icon": "⚠", "level": "act", "src": "cockpit", "id": m.get("id", ""), "text": f"{m.get('label')}: {m.get('action') or m.get('why')}", "cmd": m.get("cmd", "")}
             for m in reds[:limit]]
    if not reds and data.get("metrics"):
        items.append({"icon": "✔", "level": "ok", "src": "cockpit", "text": "Estate healthy: nothing red on the cockpit", "cmd": ""})
    return items


def certs_item(today: dt.date | None = None) -> dict | None:
    try:
        cp = _load("securax_certs_feed", "learning/certs.py")
        d, st = cp.load(), cp.load_state()
        passed = {k for k, v in st.items() if v == "passed"}
        p = cp.plan(d, 30, 500000, today or dt.date.today(), passed=passed, route="per-course")
    except Exception:  # noqa: BLE001 - a planner problem must never blank the feed
        return None
    row = next((r for r in p["rows"] if r["id"] != "practice"), None)
    if not row:
        return {"icon": "\U0001f393", "level": "ok", "src": "certs", "text": "Every planned certification is marked passed", "cmd": "./securax certs plan --with-optional"}
    status = st.get(row["id"], "not started")
    return {"icon": "\U0001f393", "level": "info", "src": "certs",
            "text": f"Certification now: {row['name']} ({status}); planned exam by {row['exam_by']}", "cmd": "./securax certs next"}


def backup_item(env: dict, now: float | None = None) -> dict:
    now = now or time.time()
    d = pathlib.Path(env.get("SECURAX_BACKUP_DIR") or os.environ.get("SECURAX_BACKUP_DIR") or ROOT / "backups")
    files = sorted((f for f in d.glob("securax-*.tar.gz*") if f.is_file()), key=lambda f: f.stat().st_mtime, reverse=True) if d.is_dir() else []
    if not files:
        return {"icon": "\U0001f4be", "level": "act", "src": "backup", "text": "No estate backup yet", "cmd": "./securax backup"}
    age = int((now - files[0].stat().st_mtime) // 86400)
    enc = files[0].name.endswith(".gpg")
    lvl = "act" if age > 7 or not enc else "ok"
    text = f"Newest backup is {age} day{'s' if age != 1 else ''} old, {'encrypted' if enc else 'NOT encrypted'}"
    return {"icon": "\U0001f4be", "level": lvl, "src": "backup", "text": text, "cmd": "" if lvl == "ok" else ("./securax protect" if not enc else "./securax backup")}


def build(now: float | None = None, env: dict | None = None, cockpit: pathlib.Path = COCKPIT, today: dt.date | None = None) -> dict:
    env = read_env() if env is None else env
    items = cockpit_items(cockpit)
    c = certs_item(today)
    if c:
        items.append(c)
    if not any("backup" in (i.get("id") or "") for i in items):             # the cockpit already said it: never say the same thing twice
        items.append(backup_item(env, now))
    items.sort(key=lambda i: {"act": 0, "info": 1, "ok": 2}.get(i["level"], 3))
    return {"generated": dt.datetime.fromtimestamp(now or time.time()).isoformat(timespec="minutes"), "items": items[:4]}


def write(out: pathlib.Path = OUT, **kw) -> dict:
    data = build(**kw)
    out.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix=f".{out.name}.", dir=out.parent)       # unique per writer: two refreshes at once cannot share a temp file
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=1, ensure_ascii=False))
    os.chmod(tmp, 0o644)
    os.replace(tmp, out)                                                      # atomic: the app never reads a half-written file
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)
    data = write(pathlib.Path(a.out))
    if a.print:
        print(json.dumps(data, indent=1, ensure_ascii=False))
    else:
        print(f"Estate feed written: {a.out} ({len(data['items'])} line(s) for the Guiding Map's Today screen)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
