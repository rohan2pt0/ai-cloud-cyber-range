#!/usr/bin/env python3
"""Where SecuRAX keeps its files, how fast they grow, and when the disk runs out — in plain words.

    ./securax storage                 report: sizes, free space, growth, forecast, what to do
    ./securax storage --json          the same for machines (the cockpit uses it)
    ./securax storage --tidy [--yes]  show (or, with --yes, do) the SAFE clean-ups: dangling images, old build cache

What lives where (nothing else grows):
  Docker volumes   the databases, chats, workflows, models (the Ollama model store is usually the biggest)   -> HOT: keep on a fast disk
  ./backups        one archive per `./securax backup`; the newest $BACKUP_KEEP (default 7) are kept          -> WARM: copy off the machine (3-2-1)
  ~/.securax       incident cases, offline threat-data snapshots, sprout secrets, history                   -> small
  Docker images    pinned third-party images + the ones built here; old versions pile up after updates     -> reclaimable by `--tidy`
  container logs   rotate by themselves (10 MB x 3 per container, set in the compose file)                   -> bounded
History is appended at most every 12 hours; the forecast needs 3 samples over at least 2 days and says "collecting data" until then.
It never deletes volumes or backups. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
HOME = pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")
PROJECT_PREFIXES = ("vulnbank-range_", "vulnbank-range-")
UNIT = {"b": 1, "kb": 1e3, "mb": 1e6, "gb": 1e9, "tb": 1e12}


def parse_size(s: str) -> int:
    m = re.match(r"\s*([\d.]+)\s*([a-zA-Z]*)", s or "")
    if not m:
        return 0
    return round(float(m.group(1)) * UNIT.get(m.group(2).lower() or "b", 1))


def human(n: float) -> str:
    for u in ("B", "kB", "MB", "GB", "TB"):
        if abs(n) < 1000 or u == "TB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1000
    return str(n)


def dir_size(p: pathlib.Path, skip: tuple[str, ...] = ("node_modules", ".git")) -> int:
    total = 0
    if not p.exists():
        return 0
    for root, dirs, files in os.walk(p, onerror=lambda e: None):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def docker_json(*args: str, timeout: int = 25):
    try:
        r = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def env_value(root: pathlib.Path, key: str) -> str:
    """A value from local/compose/.env (the file `securax` itself reads), or ''."""
    try:
        for ln in (root / "local" / "compose" / ".env").read_text("utf-8").splitlines():
            if ln.startswith(key + "="):
                return ln.split("=", 1)[1].strip().strip("'\"")
    except OSError:
        pass
    return ""


def measure(root: pathlib.Path = ROOT, backups: pathlib.Path | None = None, now: float | None = None) -> dict:
    now = now or time.time()
    out: dict = {"ts": int(now), "docker": False}
    backups = backups or pathlib.Path(os.environ.get("SECURAX_BACKUP_DIR") or env_value(root, "SECURAX_BACKUP_DIR") or root / "backups")
    files = sorted(backups.glob("securax-*.tar.gz*"), key=lambda f: f.stat().st_mtime, reverse=True) if backups.exists() else []
    out["backups"] = {"dir": str(backups), "count": len(files), "bytes": sum(f.stat().st_size for f in files),
                      "newest_age_days": round((now - files[0].stat().st_mtime) / 86400, 1) if files else None}
    out["home"] = {"dir": str(HOME), "bytes": dir_size(HOME)}
    out["repo"] = {"dir": str(root), "bytes": dir_size(root)}
    du = shutil.disk_usage(str(HOME if HOME.exists() else root))
    out["disk"] = {"path": str(HOME if HOME.exists() else root), "total": du.total, "free": du.free, "free_pct": round(du.free / du.total * 100, 1)}
    txt = docker_json("system", "df", "--format", "{{json .}}")
    if txt:
        out["docker"] = True
        rows = {}
        for ln in txt.splitlines():
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            rows[d["Type"]] = {"bytes": parse_size(d["Size"]), "reclaimable_bytes": parse_size(d["Reclaimable"].split(" ")[0])}
        out["docker_usage"] = rows
        vol = docker_json("system", "df", "-v", "--format", "json", timeout=40)
        vols = []
        try:
            for v in (json.loads(vol).get("Volumes") or []) if vol else []:
                if v.get("Name", "").startswith(PROJECT_PREFIXES):
                    vols.append({"name": v["Name"], "bytes": parse_size(v.get("Size", ""))})
        except ValueError:
            pass
        out["volumes"] = sorted(vols, key=lambda v: -v["bytes"])
    out["estate_bytes"] = (out["backups"]["bytes"] + out["home"]["bytes"] + sum(v["bytes"] for v in out.get("volumes", []))
                           + out.get("docker_usage", {}).get("Images", {}).get("bytes", 0))
    return out


# ------------------------------------------------------------------------------------------------------------------ history
def history_path() -> pathlib.Path:
    return HOME / "storage-history.jsonl"


def record(m: dict, min_gap_s: int = 12 * 3600, path: pathlib.Path | None = None) -> bool:
    path = path or history_path()
    rows = load_history(path)
    if rows and m["ts"] - rows[-1]["ts"] < min_gap_s:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": m["ts"], "estate": m["estate_bytes"], "free": m["disk"]["free"], "backups": m["backups"]["bytes"]}) + "\n")
    return True


def load_history(path: pathlib.Path | None = None) -> list[dict]:
    path = path or history_path()
    out = []
    if path.exists():
        for ln in path.read_text("utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    return out[-90:]


def forecast(rows: list[dict], free: int) -> dict:
    """Days until the disk is full if the estate keeps growing at its recent rate. Least-squares slope of estate bytes over time."""
    if len(rows) < 3 or rows[-1]["ts"] - rows[0]["ts"] < 2 * 86400:
        return {"state": "collecting", "days": None, "bytes_per_day": None}
    xs = [(r["ts"] - rows[0]["ts"]) / 86400 for r in rows]
    ys = [r["estate"] for r in rows]
    n = len(rows)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
    if slope <= 1e6:                                   # under 1 MB/day: effectively flat
        return {"state": "flat", "days": None, "bytes_per_day": int(max(slope, 0))}
    return {"state": "growing", "days": round(free / slope, 0), "bytes_per_day": int(slope)}


def advice(m: dict, fc: dict) -> list[str]:
    out = []
    pct = m["disk"]["free_pct"]
    if pct < 10:
        out.append(f"URGENT: only {pct}% of the disk is free. Run `./securax storage --tidy --yes`, then move ./backups to another disk (set SECURAX_BACKUP_DIR).")
    elif pct < 20:
        out.append(f"{pct}% of the disk is free: plan a clean-up (`./securax storage --tidy`) and an off-machine copy of ./backups.")
    if fc.get("state") == "growing" and fc["days"] is not None and fc["days"] < 60:
        out.append(f"At the current growth (~{human(fc['bytes_per_day'])}/day) the disk is full in about {int(fc['days'])} days.")
    rec = m.get("docker_usage", {}).get("Images", {}).get("reclaimable_bytes", 0) + m.get("docker_usage", {}).get("Build Cache", {}).get("reclaimable_bytes", 0)
    if rec > 3e9:
        out.append(f"{human(rec)} of old Docker images/build cache can be reclaimed safely: `./securax storage --tidy --yes`.")
    big = [v for v in m.get("volumes", []) if v["bytes"] > 5e9]
    for v in big[:2]:
        out.append(f"{v['name']} is {human(v['bytes'])}: if it is the model store, keep one or two models (`docker exec <ollama> ollama rm <model>`).")
    if m["backups"]["count"] and m["backups"]["bytes"] > 5e9:
        out.append(f"Backups use {human(m['backups']['bytes'])}: lower BACKUP_KEEP in local/compose/.env or point SECURAX_BACKUP_DIR at a bigger disk.")
    if m["backups"]["count"] == 0:
        out.append("No backup yet: `./securax backup` (then copy it off this machine: one copy on the laptop is not a backup).")
    if not out:
        out.append("Nothing needs doing: space is healthy and growth is bounded (logs rotate; only backups and models grow, and backups are capped).")
    return out


def tidy(yes: bool) -> list[str]:
    done = []
    steps = [("dangling images", ["image", "prune", "-f"]), ("build cache older than 7 days", ["builder", "prune", "-f", "--filter", "until=168h"])]
    for label, args in steps:
        if not yes:
            done.append(f"would remove: {label}   (add --yes to do it)")
            continue
        out = docker_json(*args, timeout=300)
        m = re.search(r"Total reclaimed space:\s*(.+)", out or "")
        done.append(f"removed {label}: reclaimed {m.group(1) if m else 'nothing'}")
    return done


def report(m: dict, fc: dict) -> str:
    lines = [f"Disk: {human(m['disk']['free'])} free of {human(m['disk']['total'])} ({m['disk']['free_pct']}% free)  — {m['disk']['path']}"]
    lines.append(f"SecuRAX uses about {human(m['estate_bytes'])}:")
    lines.append(f"  backups   {human(m['backups']['bytes']):>9}  {m['backups']['count']} file(s) in {m['backups']['dir']}"
                 + (f", newest {m['backups']['newest_age_days']} days old" if m['backups']['newest_age_days'] is not None else ""))
    lines.append(f"  ~/.securax{human(m['home']['bytes']):>9}  incident cases, offline threat data, history")
    if m["docker"]:
        for k in ("Images", "Local Volumes", "Build Cache"):
            d = m.get("docker_usage", {}).get(k)
            if d:
                lines.append(f"  {k.lower():<10}{human(d['bytes']):>9}  ({human(d['reclaimable_bytes'])} reclaimable)")
        for v in m.get("volumes", [])[:5]:
            lines.append(f"    volume {v['name'].split('_', 1)[-1]:<22}{human(v['bytes']):>9}")
    else:
        lines.append("  (Docker is not running, so images and volumes are not counted)")
    fs = {"collecting": "forecast: collecting data (needs 3 readings over 2+ days — run this or `./securax up` daily)",
          "flat": "forecast: growth is flat — no risk of running out soon",
          "growing": f"forecast: growing ~{human(fc.get('bytes_per_day') or 0)}/day → disk full in about {int(fc['days']) if fc.get('days') is not None else '?'} days"}[fc["state"]]
    lines.append(fs)
    lines.append("What to do:")
    lines += ["  • " + a for a in advice(m, fc)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tidy", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args(argv)
    m = measure()
    if not a.no_record:
        record(m)
    fc = forecast(load_history(), m["disk"]["free"])
    if a.tidy:
        print("\n".join(tidy(a.yes)))
        return 0
    if a.json:
        print(json.dumps({"measure": m, "forecast": fc, "advice": advice(m, fc)}, indent=2))
    else:
        print(report(m, fc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
