#!/usr/bin/env python3
"""The estate's autopilot: it learns from its own failures, drills itself, and sees trouble days ahead (doc 92).

    ./securax autopilot              one screen: what failed and was learned, which drills ran and which come next, what is
                                     forecast to run out, and when
    ./securax autopilot learn        (hourly routine) every routine that newly fails gets a postmortem draft in vault/postmortems
                                     and an alert; one that keeps failing (3 times in 7 days) is escalated with the command
                                     that starts a fix; one that recovers says so once
    ./securax autopilot drill        (nightly routine) runs the 2 drills that most need it: never run, longest ago, failed last
                                     time, or most critical. A recovery that got much slower than usual is flagged
    ./securax autopilot forecast     (hourly routine) records disk space, backup headroom, the AI allowance and answer latency,
                                     and warns when a trend crosses its limit within 7 days

How it decides, said plainly:
- Drills: score = days since the drill last ran (capped at 90; never run counts as 100) x 2 for a critical scenario x 3 if it
  failed last time. The highest two run. Over a few weeks every drill runs, and the risky ones run most.
- Slower recovery: a drill that took more than 1.5 times its usual (median) time, and at least 2 minutes more, is flagged.
- Forecasts: the trend is the Theil-Sen slope (the median of all pairwise slopes), so one odd reading cannot fool it. A
  forecast needs 6 readings over 2 days; until then it says it is still learning.
Nothing here changes your data, keys or code: it drafts, measures and tells you; a person approves every fix. Everything it
keeps is bounded (doc 80). Standard library only. Exit codes: 0 nothing needs you, 1 something does, 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "governance"))
HISTORY = ROOT / "routines" / ".history.json"
JOBS = ROOT / "routines" / "jobs.json"
KEEP_SAMPLES = 5000
DRILLS_PER_NIGHT = int(os.environ.get("AUTOPILOT_DRILLS", "2") or 2)
EXTRA_DRILLS = {                       # checks that are drills too, beyond the continuity scenarios
    "honesty": {"title": "The AI still refuses to guess", "cmd": ["ai", "honesty"], "critical": False},
    "resilience": {"title": "Every machine combination is still covered", "cmd": ["resilience"], "critical": True},
}
LIMITS = {                             # metric: (limit, "below" or "above" is the bad side, what to say, the fix)
    "disk_free_gb": (5.0, "below", "free disk space falls under 5 GB", "./securax storage --auto"),
    "backup_headroom_gb": (0.0, "below", "the backups that retention keeps no longer fit on the disk", "./securax storage --auto, or a bigger disk"),
    "ai_month_used_pct": (100.0, "above", "this month's AI allowance runs out", "./securax ai budget (the local model keeps answering)"),
    "latency_p95_s": (30.0, "above", "answers take longer than the 30-second target", "./securax doctor, then ./securax keys for a faster model"),
}


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def state_dir() -> pathlib.Path:
    d = home() / "autopilot"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: pathlib.Path, data) -> None:
    path.write_text(json.dumps(data, indent=1), "utf-8")


def notify(msg: str, title: str = "SecuRAX autopilot") -> None:
    try:
        subprocess.run([sys.executable, str(ROOT / "governance" / "notify.py"), "send", msg, "--title", title],
                       capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pass


def securax(*args: str, timeout: int = 1800) -> tuple[int, str]:
    p = subprocess.run(["bash", str(ROOT / "securax"), *args], capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "SECURAX_NO_OPEN": "1"}, stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout + p.stderr)[-1500:]


# ============================================================================================================ learn
def _kinds() -> dict:
    try:
        return {j["id"]: j.get("kind", "guard") for j in json.loads(JOBS.read_text("utf-8"))}
    except (OSError, ValueError, KeyError):
        return {}


def learn(history: dict | None = None, now: float | None = None, say=print, alert=notify, draft=None) -> dict:
    """Turn routine failures into postmortem drafts, escalations and recoveries. Returns what it did."""
    now = now or time.time()
    history = _load(HISTORY, {}) if history is None else history
    seen_p = state_dir() / "learned.json"
    seen = _load(seen_p, {})
    kinds = _kinds()
    did = {"new": [], "recurring": [], "recovered": []}
    for job, runs in sorted(history.items()):
        if not runs or kinds.get(job, "guard") in ("report", "nudge") or job.startswith("autopilot-"):
            continue                    # a report that finds things is doing its job; a reminder is not a check; never itself
        last = runs[-1]
        rec = seen.get(job)
        if last.get("code", 0) == 0:
            if rec and rec.get("open"):
                rec["open"] = False
                did["recovered"].append(job)
                alert(f"Routine {job} is green again after {rec.get('count', 1)} failure(s).")
            continue
        week = [r for r in runs if r.get("code", 0) != 0 and _age_days(r.get("t", ""), now) <= 7]
        tail = (last.get("tail") or "").strip().splitlines()[-1:] or [""]
        if not rec or not rec.get("open"):
            path = (draft or _draft)(job, last.get("code"), tail[0])
            seen[job] = {"open": True, "first": last.get("t"), "count": 1, "postmortem": str(path), "escalated": False}
            did["new"].append(job)
            alert(f"Routine {job} failed (exit {last.get('code')}): {tail[0][:160]}. A postmortem draft is ready: {path}")
            continue
        if last.get("t") != rec.get("last_t"):
            rec["count"] = rec.get("count", 1) + 1
        rec["last_t"] = last.get("t")
        if len(week) >= 3 and not rec.get("escalated"):
            rec["escalated"] = True
            did["recurring"].append(job)
            alert(f"Routine {job} keeps failing ({len(week)} times in 7 days). To start a fix you approve: "
                  f"./securax autobuild \"routine {job} keeps failing: {tail[0][:120]}\"")
    _save(seen_p, seen)
    if did["new"] or did["recurring"] or did["recovered"]:
        say(f"learned: {len(did['new'])} new failure(s), {len(did['recurring'])} recurring, {len(did['recovered'])} recovered")
    return did


def _age_days(stamp: str, now: float) -> float:
    try:
        return (now - dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M").timestamp()) / 86400
    except ValueError:
        return 1e9


def _draft(job: str, code, line: str) -> pathlib.Path:
    import postmortem
    p = postmortem.new(f"Routine {job} failed", "sev3")
    with p.open("a", encoding="utf-8") as fh:
        fh.write(f"\n<!-- drafted by ./securax autopilot learn -->\nThe routine `{job}` exited {code}. Its last line: `{line[:200]}`\n"
                 f"See its history: ./securax routines list, and run it by hand to read all of it.\n")
    return p


# ============================================================================================================ drill
def _drill_log() -> pathlib.Path:
    return state_dir() / "drills.jsonl"


def drill_history() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    import continuity
    for path in (continuity.drills_path(), _drill_log()):
        try:
            for line in path.read_text("utf-8").splitlines():
                r = json.loads(line)
                out.setdefault(r["id"], []).append(r)
        except (OSError, ValueError, KeyError):
            continue
    return out


def candidates() -> list[dict]:
    import continuity
    out, kinds = [], set()
    for s in continuity.load():
        if s.get("drill") and s["drill"] not in kinds:                   # one scenario per drill kind (three share a restore)
            kinds.add(s["drill"])
            out.append({"id": s["id"], "title": s["title"], "critical": s.get("rpo_min", 1e9) <= 1440 or s.get("rto_min", 1e9) <= 120,
                        "scenario": True})
    out += [{"id": k, "title": v["title"], "critical": v["critical"], "scenario": False} for k, v in EXTRA_DRILLS.items()]
    return out


def score(c: dict, hist: list[dict], now: float) -> float:
    if not hist:
        return 100.0 * (2 if c["critical"] else 1)
    last = hist[-1]
    try:
        age = (now - dt.datetime.fromisoformat(last["when"]).timestamp()) / 86400
    except (KeyError, ValueError):
        age = 90.0
    return min(age, 90.0) * (2 if c["critical"] else 1) * (3 if not last.get("ok") else 1)


def pick(now: float | None = None, n: int = DRILLS_PER_NIGHT, hist: dict | None = None) -> list[dict]:
    now = now or time.time()
    hist = drill_history() if hist is None else hist
    return sorted(candidates(), key=lambda c: -score(c, hist.get(c["id"], []), now))[:n]


def slower(minutes: float, past: list[dict]) -> bool:
    ok = [r["minutes"] for r in past if r.get("ok") and isinstance(r.get("minutes"), (int, float))]
    if len(ok) < 3:
        return False
    med = statistics.median(ok)
    return minutes > 1.5 * med and minutes - med >= 2


def drill(say=print, alert=notify, runner=None, now: float | None = None) -> int:
    import continuity
    now = now or time.time()
    hist = drill_history()
    bad = 0
    for c in pick(now, hist=hist):
        past = hist.get(c["id"], [])
        t0 = time.time()
        if runner:
            ok, note = runner(c)
        elif c["scenario"]:
            rc = continuity.drill(c["id"], say=lambda *_: None)
            ok, note = rc == 0, ""
        else:
            rc, out = securax(*EXTRA_DRILLS[c["id"]]["cmd"])
            ok, note = rc == 0, out.strip().splitlines()[-1:] or [""]
            note = note[0][:200]
        minutes = round((time.time() - t0) / 60, 2)
        if not c["scenario"] or runner:
            with _drill_log().open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"id": c["id"], "when": dt.datetime.now().isoformat(timespec="seconds"), "ok": ok,
                                     "minutes": minutes, "note": note}) + "\n")
        _trim(_drill_log(), 2000)
        slow = ok and slower(minutes, past)
        say(("✔ " if ok and not slow else "✗ ") + f"drill {c['id']}: {c['title']} - {'passed' if ok else 'FAILED'} in {minutes} min"
            + (" (much slower than usual)" if slow else ""))
        if not ok or slow:
            bad += 1
            alert(f"Nightly drill {c['id']} {'FAILED' if not ok else 'passed but much slower than usual'}. "
                  f"See: ./securax continuity show {c['id']}" if c["scenario"] else f"Nightly drill {c['id']} FAILED: {note}")
    return 1 if bad else 0


def _trim(path: pathlib.Path, keep: int) -> None:
    try:
        lines = path.read_text("utf-8").splitlines()
        if len(lines) > keep:
            path.write_text("\n".join(lines[-keep:]) + "\n", "utf-8")
    except OSError:
        pass


# ============================================================================================================ forecast
def _samples_path() -> pathlib.Path:
    return state_dir() / "metrics.jsonl"


def _get(url: str, timeout: float = 5):
    key = os.environ.get("SECURAX_GATEWAY_KEY", "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"} if key else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:                  # noqa: S310 (the estate's own gateway)
            return json.loads(r.read())
    except (OSError, ValueError, urllib.error.HTTPError):
        return None


def measure(gw: str = "http://localhost:8080") -> dict:
    """The readings, now. A reading that cannot be taken is left out (never guessed)."""
    out = {}
    du = shutil.disk_usage(home() if home().exists() else ROOT)
    out["disk_free_gb"] = round(du.free / 1e9, 2)
    try:
        import continuity
        import ransomguard
        b = ransomguard.pick(continuity.backup_dir())
        if b:
            kept = 7 + 4 + 3                                                       # what retention keeps (doc 88)
            out["backup_headroom_gb"] = round((du.free - kept * b.stat().st_size) / 1e9, 2)
    except Exception:  # noqa: BLE001 (a reading that cannot be taken is left out)
        pass
    bud = _get(gw.rstrip("/") + "/v1/budget")
    if isinstance(bud, dict):
        pct = [r["month_used"] / r["month_limit"] * 100 for r in bud.get("callers", []) if r.get("month_limit")]
        if pct:
            out["ai_month_used_pct"] = round(max(pct), 1)
    lat = _get(gw.rstrip("/") + "/v1/latency")
    if isinstance(lat, dict) and lat.get("samples"):
        out["latency_p95_s"] = round(float(lat.get("p95_ms") or 0) / 1000, 2)
    return out


def record(readings: dict, now: float | None = None) -> None:
    now = now or time.time()
    with _samples_path().open("a", encoding="utf-8") as fh:
        for k, v in readings.items():
            fh.write(json.dumps({"at": int(now), "m": k, "v": v}) + "\n")
    _trim(_samples_path(), KEEP_SAMPLES)


def theil_sen(points: list[tuple[float, float]]) -> float:
    slopes = [(y2 - y1) / (x2 - x1) for i, (x1, y1) in enumerate(points) for x2, y2 in points[i + 1:] if x2 != x1]
    return statistics.median(slopes) if slopes else 0.0


def predict(samples: list[dict], now: float | None = None) -> list[dict]:
    now = now or time.time()
    out = []
    for m, (limit, side, what, fix) in LIMITS.items():
        pts = sorted((s["at"], s["v"]) for s in samples if s["m"] == m and now - s["at"] <= 14 * 86400)
        if len(pts) < 6 or pts[-1][0] - pts[0][0] < 2 * 86400:
            out.append({"metric": m, "state": "learning", "what": what})
            continue
        if len(pts) > 300:                                                         # thin, so the pairwise median stays cheap
            pts = pts[:: len(pts) // 300 + 1]
        slope = theil_sen(pts) * 86400                                             # per day
        current = statistics.median(v for _, v in pts[-3:])
        breached = current < limit if side == "below" else current > limit
        toward = slope < 0 if side == "below" else slope > 0
        days = None if breached or not toward or slope == 0 else (limit - current) / slope
        state = "now" if breached else ("soon" if days is not None and days <= 7 else ("watch" if days is not None and days <= 30 else "ok"))
        out.append({"metric": m, "state": state, "current": round(current, 2), "per_day": round(slope, 3),
                    "days": None if days is None else round(days, 1), "what": what, "fix": fix})
    return out


def forecast(say=print, alert=notify, readings: dict | None = None, now: float | None = None) -> int:
    now = now or time.time()
    record(measure() if readings is None else readings, now)
    p = _samples_path()
    samples = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]
    res = predict(samples, now)
    told_p = state_dir() / "forecast-told.json"
    told = _load(told_p, {})
    urgent = [r for r in res if r["state"] in ("now", "soon")]
    for r in urgent:
        key = f"{r['metric']}:{r['state']}"
        if now - told.get(key, 0) > 86400:                                         # once a day per warning, at most
            when = "now" if r["state"] == "now" else f"in about {r['days']} days"
            alert(f"Ahead of time: {r['what']} {when}. Fix: {r['fix']}")
            told[key] = now
    _save(told_p, told)
    for r in res:
        if r["state"] == "learning":
            continue
        say(f"  {'✗' if r['state'] in ('now', 'soon') else ('·' if r['state'] == 'watch' else '✔')} {r['metric']}: {r['current']} "
            f"({r['per_day']:+}/day)" + (f": {r['what']} {'now' if r['state'] == 'now' else 'in about ' + str(r['days']) + ' days'}"
                                         if r["state"] in ("now", "soon", "watch") else ""))
    return 1 if urgent else 0


# ============================================================================================================ status
def status(say=print) -> int:
    seen = _load(state_dir() / "learned.json", {})
    open_ = {k: v for k, v in seen.items() if v.get("open")}
    say("AUTOPILOT · what the estate learned, drilled and foresees by itself\n")
    say(f"Failures being learned from: {len(open_)}")
    for job, v in sorted(open_.items()):
        say(f"  ✗ {job} (since {v.get('first')}, {v.get('count', 1)} time(s)){'  · escalated' if v.get('escalated') else ''}  {v.get('postmortem', '')}")
    hist, now = drill_history(), time.time()
    say("\nDrills (next ones first):")
    for c in sorted(candidates(), key=lambda c: -score(c, hist.get(c["id"], []), now)):
        h = hist.get(c["id"], [])
        last = f"last {h[-1].get('when', '')[:10]} {'passed' if h[-1].get('ok') else 'FAILED'}" if h else "never run"
        say(f"  {'✔' if h and h[-1].get('ok') else '·'} {c['id']:<14} {last}")
    p = _samples_path()
    samples = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()] if p.exists() else []
    say("\nForecasts:")
    for r in predict(samples):
        if r["state"] == "learning":
            say(f"  · {r['metric']}: still learning (needs 6 readings over 2 days)")
        else:
            say(f"  {'✗' if r['state'] in ('now', 'soon') else '✔'} {r['metric']}: {r['current']} ({r['per_day']:+}/day)"
                + (f" - {r['what']} in about {r['days']} days" if r.get("days") is not None else ""))
    return 1 if open_ else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="autopilot", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="status", choices=["status", "learn", "drill", "forecast"])
    a = ap.parse_args(argv)
    if a.cmd == "learn":
        did = learn()
        return 1 if did["new"] or did["recurring"] else 0
    if a.cmd == "drill":
        return drill()
    if a.cmd == "forecast":
        return forecast()
    return status()


if __name__ == "__main__":
    sys.exit(main())
