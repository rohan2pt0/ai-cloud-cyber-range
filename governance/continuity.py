#!/usr/bin/env python3
"""The estate's crisis and continuity plan, measured (doc 84).

    ./securax continuity                 every scenario: its RTO and RPO targets, what they really are today, and the next fix
    ./securax continuity show ID         the steps, in order, for one scenario (read it during the crisis)
    ./securax continuity drill ID        run that scenario's safe drill, time it, and record the result
    ./securax continuity mirror          copy the code off GitHub: a git bundle in the backup folders, and a push to MIRROR_REMOTES
    ./securax continuity --json          the same as the first, for the cockpit

The scenarios live in governance/continuity.json. RPO (how much may be lost) is measured from the newest backup, off-site copy or
code bundle. RTO (how long it may be down) is measured by the last drill: a scenario never drilled reads "not proven". A drill
never changes your data. The mirror routine runs daily. Standard library only. Exit codes: 0 all within target, 1 not, 2 bad usage.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAN = ROOT / "governance" / "continuity.json"
ENVF = ROOT / "local" / "compose" / ".env"


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def env(key: str, default: str = "") -> str:
    if os.environ.get(key):
        return os.environ[key]
    try:
        for line in ENVF.read_text("utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return default


def load(path: pathlib.Path = PLAN) -> list[dict]:
    return json.loads(path.read_text("utf-8"))["scenarios"]


def backup_dir() -> pathlib.Path:
    return pathlib.Path(env("SECURAX_BACKUP_DIR") or ROOT / "backups").expanduser()


def newest(folder: pathlib.Path | None, patterns: tuple[str, ...]) -> pathlib.Path | None:
    if not folder or not folder.is_dir():
        return None
    files = [f for p in patterns for f in folder.glob(p) if f.is_file()]
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def rpo_minutes(source: str, now: float | None = None) -> float | None:
    """How much would be lost right now, in minutes; None when nothing protects it."""
    now = now or time.time()
    if source == "none":
        return 0.0
    if source == "backup":
        f = newest(backup_dir(), ("securax-*.tar.gz", "securax-*.tar.gz.gpg"))
    elif source == "offsite":
        off = env("SECURAX_OFFSITE_DIR")
        f = newest(pathlib.Path(off).expanduser() if off else None, ("securax-*.tar.gz.gpg",))
    elif source == "repo":
        marker = backup_dir() / "repo-latest.head"
        head = git("rev-parse", "HEAD")[1]
        if marker.exists() and marker.read_text().strip() == head:
            return 0.0                                          # the bundle holds every commit there is
        f = backup_dir() / "repo-latest.bundle"
        f = f if f.exists() else None
    else:
        return None
    return None if f is None else (now - f.stat().st_mtime) / 60


def drills_path() -> pathlib.Path:
    return home() / "continuity" / "drills.jsonl"


def last_drills() -> dict[str, dict]:
    out = {}
    try:
        for line in drills_path().read_text("utf-8").splitlines():
            r = json.loads(line)
            out[r["id"]] = r
    except (OSError, ValueError):
        pass
    return out


def status(scenarios: list[dict] | None = None, now: float | None = None) -> list[dict]:
    scenarios = scenarios or load()
    drills, rows = last_drills(), []
    for s in scenarios:
        rpo = rpo_minutes(s["rpo_source"], now)
        d = drills.get(s["id"])
        rto_ok = d is not None and d.get("ok") and d.get("minutes", 1e9) <= s["rto_min"] if s.get("drill") else True
        rpo_ok = rpo is not None and rpo <= s["rpo_min"] if s["rpo_source"] != "none" else True
        fix = ("" if rpo_ok else "./securax continuity mirror" if s["rpo_source"] == "repo" else "./securax backup offsite" if s["rpo_source"] == "offsite"
               else "./securax backup")
        if not fix and not rto_ok:
            fix = f"./securax continuity drill {s['id']}"
        rows.append({"id": s["id"], "title": s["title"], "rpo_source": s["rpo_source"], "rto_min": s["rto_min"], "rpo_min": s["rpo_min"], "rpo_now": None if rpo is None else round(rpo),
                     "drilled": d.get("when") if d else None, "rto_ok": bool(rto_ok), "rpo_ok": bool(rpo_ok), "ok": bool(rto_ok and rpo_ok), "fix": fix})
    return rows


def _span(minutes: float | None) -> str:
    if minutes is None:
        return "nothing protects it"
    return f"{minutes:.0f} min" if minutes < 120 else f"{minutes / 60:.0f} h" if minutes < 2880 else f"{minutes / 1440:.0f} days"


# ---------------------------------------------------------------------------------------------------- mirror and drills
def mirror(say=print) -> int:
    """A git bundle of every branch in the backup folder (and the off-site folder), then a push to each MIRROR_REMOTES entry."""
    dest = backup_dir()
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / "repo-latest.bundle.tmp"
    rc = subprocess.run(["git", "-C", str(ROOT), "bundle", "create", str(tmp), "--all"], capture_output=True, text=True)
    if rc.returncode or subprocess.run(["git", "bundle", "verify", str(tmp)], capture_output=True, cwd=ROOT).returncode:
        say("✗ could not write a verified code bundle: " + (rc.stderr or "")[-300:])
        tmp.unlink(missing_ok=True)
        return 1
    tmp.replace(dest / "repo-latest.bundle")
    (dest / "repo-latest.head").write_text(git("rev-parse", "HEAD")[1] + "\n")
    say(f"✔ code bundle (every branch, verified): {dest / 'repo-latest.bundle'}")
    off = env("SECURAX_OFFSITE_DIR")
    if off and pathlib.Path(off).expanduser().is_dir():
        o = pathlib.Path(off).expanduser()
        (o / "repo-latest.bundle").write_bytes((dest / "repo-latest.bundle").read_bytes())
        say(f"✔ copied to the off-site folder: {o}")
    bad = 0
    for remote in [r.strip() for r in env("MIRROR_REMOTES").split(",") if r.strip()]:
        p = subprocess.run(["git", "-C", str(ROOT), "push", "--quiet", remote, "--all"], capture_output=True, text=True, timeout=300)
        subprocess.run(["git", "-C", str(ROOT), "push", "--quiet", remote, "--tags"], capture_output=True, text=True, timeout=300)
        if p.returncode:
            bad += 1
            say(f"✗ mirror {remote}: {(p.stderr or '').strip()[-200:]}")
        else:
            say(f"✔ mirrored to {remote}")
    if not env("MIRROR_REMOTES"):
        say("  (no second git host yet: add MIRROR_REMOTES=<git URL> to local/compose/.env, e.g. a free GitLab or Codeberg repository)")
    return 1 if bad else 0


def _securax(*args: str, timeout: int = 900) -> tuple[int, str]:
    p = subprocess.run(["bash", str(ROOT / "securax"), *args], capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "SECURAX_NO_OPEN": "1"})
    return p.returncode, (p.stdout + p.stderr)[-1500:]


def run_drill(kind: str) -> tuple[bool, str]:
    if kind == "rollback-check":
        rc, out = _securax("rollback", "--check")
        return rc == 0, out
    if kind == "repo-bundle":
        f = backup_dir() / "repo-latest.bundle"
        if not f.exists() and mirror(say=lambda *_: None):
            return False, "could not write the bundle"
        with tempfile.TemporaryDirectory() as d:
            c = subprocess.run(["git", "clone", "--quiet", str(f), str(pathlib.Path(d) / "repo")], capture_output=True, text=True)
            if c.returncode:
                return False, c.stderr[-500:]
            fs = subprocess.run(["git", "-C", str(pathlib.Path(d) / "repo"), "fsck", "--no-progress"], capture_output=True, text=True)
            ok = fs.returncode == 0 and (pathlib.Path(d) / "repo" / "securax").exists()
            return ok, "the bundle clones into a whole, working checkout" if ok else fs.stderr[-500:]
    if kind == "backup-drill":
        rc, out = _securax("backup", "drill")
        return rc == 0, out
    if kind == "models":
        rc, out = _securax("models", timeout=300)
        return rc == 0, out
    if kind == "storage":
        rc, out = _securax("storage", "--no-record", timeout=300)
        return rc == 0, out
    if kind == "passwords":
        rc, out = _securax("passwords", "status", timeout=60)
        return rc == 0, out
    return False, f"no drill called {kind}"


def drill(sid: str, scenarios: list[dict] | None = None, runner=run_drill, say=print) -> int:
    s = next((x for x in (scenarios or load()) if x["id"] == sid), None)
    if not s:
        say(f"No scenario called {sid}. See them with:  ./securax continuity")
        return 2
    if not s.get("drill"):
        say(f"{s['title']}: no safe automatic drill (it would mean really doing it). Walk through the steps instead:  ./securax continuity show {sid}")
        return 0
    t0 = time.time()
    ok, out = runner(s["drill"])
    minutes = (time.time() - t0) / 60
    rec = {"id": sid, "when": dt.datetime.now().isoformat(timespec="seconds"), "ok": ok, "minutes": round(minutes, 2), "note": out.strip()[-300:]}
    drills_path().parent.mkdir(parents=True, exist_ok=True)
    with drills_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    say(("✔ " if ok else "✗ ") + f"drill {sid}: {'passed' if ok else 'FAILED'} in {minutes:.1f} min (target: back within {s['rto_min']} min)")
    if not ok:
        say("  " + out.strip()[-600:])
    return 0 if ok else 1


# ---------------------------------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "status"
    if cmd in ("status", "--json"):
        rows = status()
        if "--json" in argv:
            print(json.dumps({"scenarios": rows, "ok": all(r["ok"] for r in rows)}, indent=1))
            return 0
        print("CONTINUITY · each crisis, how long it may stop you (RTO) and how much it may lose (RPO): the target, and today\n")
        for r in rows:
            mark = "✔" if r["ok"] else "✗"
            rpo = "" if r["rpo_source"] == "none" else f" · RPO now {_span(r['rpo_now'])} (target {_span(r['rpo_min'])})"
            print(f"  {mark} {r['title']}")
            print(f"      RTO target {_span(r['rto_min'])}{'' if r['rto_ok'] else ' · not proven by a drill yet'}{rpo}" + (f"\n      fix: {r['fix']}" if r["fix"] else ""))
        print("\nThe steps for one:  ./securax continuity show ID   (IDs: " + ", ".join(r["id"] for r in rows) + ")")
        return 0 if all(r["ok"] for r in rows) else 1
    if cmd == "show" and len(argv) > 1:
        s = next((x for x in load() if x["id"] == argv[1]), None)
        if not s:
            print(f"No scenario called {argv[1]}.")
            return 2
        print(f"{s['title'].upper()}\nYou notice it when: {s['notice']}\nBack within {_span(s['rto_min'])}; lose at most {_span(s['rpo_min'])}.\n")
        for i, step in enumerate(s["steps"], 1):
            print(f"  {i}. {step}")
        return 0
    if cmd == "drill" and len(argv) > 1:
        return drill(argv[1])
    if cmd == "mirror":
        return mirror()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
