"""SecuRAX Routines — sovereign scheduled tasks (the local 'Claude Routines' equivalent).

Claude's Routines run your prompts on a schedule. The estate's sovereign version runs your
estate's own commands/agents on a schedule — a morning brief, a weekly intel pull, a scheduled
web-research job — on YOUR box, free, offline. It is deliberately lighter than n8n (which is the
visual/webhook automation plane): this is code-first, one config file, auditable, and driven by
plain cron on your machine.

How it runs: a single real cron line invokes `./securax routines run` every minute (or every 5);
this module reads `routines/jobs.json`, works out which jobs are due, de-dupes against a per-job
last-run state file, and executes them. All effectful I/O (the clock, the command runner) is
injected, so the whole thing is unit-tested offline with zero side effects.

Config (routines/jobs.json): a list of jobs, each:
  { "id": "morning-brief", "cron": "45 7 * * 1-5", "command": ["./securax", "doctor"],
    "description": "...", "enabled": true }
`cron` is standard 5-field (minute hour day-of-month month day-of-week), supporting
*, */n, a-b, a-b/n and comma lists. `command` is an argv list (no shell, so no injection).
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JOBS = Path(__file__).resolve().parent / "jobs.json"
DEFAULT_STATE = Path(__file__).resolve().parent / ".state.json"
DEFAULT_HISTORY = Path(__file__).resolve().parent / ".history.json"     # per-job run history, for `routines prune` (local, gitignored)
DEFAULT_OFF = Path(__file__).resolve().parent / ".off.json"             # jobs you switched off with `routines off ID` (local, gitignored)
DEFAULT_ON = Path(__file__).resolve().parent / ".on.json"               # jobs shipped off that you switched on with `routines on ID` (same)
KINDS = ("guard", "report", "nudge")      # guard: silence is success; report: should find things; nudge: a reminder to you

# field ranges for minute hour day-of-month month day-of-week
_FIELD_BOUNDS = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]  # dow: 0 and 7 both = Sunday


def _parse_field(spec: str, lo: int, hi: int) -> set[int]:
    """Expand one cron field into the set of matching integers. Raises ValueError on garbage."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty cron field part in '{spec}'")
        step = 1
        if "/" in part:
            base, step_s = part.split("/", 1)
            step = int(step_s)
            if step <= 0:
                raise ValueError(f"step must be positive in '{part}'")
        else:
            base = part
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            a, b = base.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(base)
        if start > end or start < lo or end > hi:
            raise ValueError(f"cron field '{part}' out of range [{lo},{hi}]")
        out.update(range(start, end + 1, step))
    return out


def cron_matches(expr: str, t: time.struct_time) -> bool:
    """True if the 5-field cron expression matches the given local time."""
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"cron must have 5 fields, got {len(fields)}: '{expr}'")
    minute, hour, dom, month, dow = fields
    sets = [
        _parse_field(minute, *_FIELD_BOUNDS[0]),
        _parse_field(hour, *_FIELD_BOUNDS[1]),
        _parse_field(dom, *_FIELD_BOUNDS[2]),
        _parse_field(month, *_FIELD_BOUNDS[3]),
        # day-of-week: accept 0-7 (both 0 and 7 mean Sunday), anywhere in a list/range, then fold.
        {d % 7 for d in _parse_field(dow, *_FIELD_BOUNDS[4])},
    ]
    now_dow = (t.tm_wday + 1) % 7  # python Mon=0..Sun=6 -> cron Sun=0..Sat=6
    if t.tm_min not in sets[0] or t.tm_hour not in sets[1] or t.tm_mon not in sets[3]:
        return False
    # cron semantics: when BOTH dom and dow are restricted, a match on EITHER fires.
    dom_restricted = dom.strip() != "*"
    dow_restricted = dow.strip() != "*"
    dom_ok = t.tm_mday in sets[2]
    dow_ok = now_dow in sets[4]
    if dom_restricted and dow_restricted:
        return dom_ok or dow_ok
    return dom_ok and dow_ok


@dataclass
class Job:
    id: str
    cron: str
    command: list
    description: str = ""
    enabled: bool = True
    kind: str = "guard"                   # unknown jobs count as guards, so prune never suggests removing one by mistake
    once: bool = False                    # a routine that messages a person: on several machines, only one runs it (doc 91)


def parse_jobs(path: Optional[Path] = None) -> tuple[list[Job], list[str]]:
    """Tolerant parse: return (valid jobs, per-job error messages). One malformed entry never
    discards the healthy ones — critical so a single hand-edit typo can't silently stop EVERY
    scheduled routine. `load_jobs` is the strict wrapper used where surfacing errors is wanted."""
    p = Path(path) if path else DEFAULT_JOBS
    try:
        data = json.loads(p.read_text()) if p.exists() else []
    except Exception as exc:  # noqa: BLE001
        return [], [f"jobs file is not valid JSON: {str(exc)[:120]}"]
    if not isinstance(data, list):
        return [], ["jobs file must be a JSON list of jobs"]
    jobs: list[Job] = []
    errors: list[str] = []
    seen: set[str] = set()
    for i, raw in enumerate(data):
        try:
            jid = raw["id"]
            if jid in seen:
                raise ValueError(f"duplicate job id '{jid}'")
            cmd = raw["command"]
            if not isinstance(cmd, list) or not cmd:
                raise ValueError("command must be a non-empty argv list (no shell)")
            cron_matches(raw["cron"], time.localtime())  # validate the expression up front
            seen.add(jid)
            kind = raw.get("kind", "guard")
            if kind not in KINDS:
                raise ValueError(f"kind must be one of {', '.join(KINDS)}")
            jobs.append(Job(jid, raw["cron"], cmd, raw.get("description", ""), (raw.get("enabled", True) or jid in switched_on()) and jid not in switched_off(), kind,
                            bool(raw.get("once", False))))
        except Exception as exc:  # noqa: BLE001
            ident = raw.get("id", "?") if isinstance(raw, dict) else "?"
            errors.append(f"job #{i} ({ident}): {exc}")
    return jobs, errors


def switched_off(path: Optional[Path] = None) -> set:
    try:
        return set(json.loads(Path(path or DEFAULT_OFF).read_text()))
    except Exception:  # noqa: BLE001 - no file (the usual case) or an unreadable one: nothing is off
        return set()


def switched_on(path: Optional[Path] = None) -> set:
    try:
        return set(json.loads(Path(path or DEFAULT_ON).read_text()))
    except Exception:  # noqa: BLE001 - no file: nothing switched on beyond what jobs.json ships
        return set()


def set_off(job_id: str, off: bool, path: Optional[Path] = None, on_path: Optional[Path] = None) -> None:
    """Off wins over everything; on also covers a job that ships switched off (enabled: false), which used to stay off silently."""
    p, cur = Path(path or DEFAULT_OFF), switched_off(path)
    cur = (cur | {job_id}) if off else (cur - {job_id})
    p.write_text(json.dumps(sorted(cur)))
    q, on = Path(on_path or DEFAULT_ON), switched_on(on_path)
    on = (on - {job_id}) if off else (on | {job_id})
    q.write_text(json.dumps(sorted(on)))


FINDING = re.compile(r"✗|⚠|\bFAIL|\bWARN|\berror\b|\bred\b|\bamber\b", re.I)


def record_run(job_id: str, code: int, output: str, stamp: str, path: Optional[Path] = None, keep: int = 40) -> None:
    """Append one run to the history: when, the exit code, and whether the output found anything."""
    p = Path(path or DEFAULT_HISTORY)
    try:
        hist = json.loads(p.read_text()) if p.exists() else {}
    except Exception:  # noqa: BLE001 - a damaged history is rebuilt, never fatal to the scheduler
        hist = {}
    hist.setdefault(job_id, []).append({"t": stamp, "code": code, "found": bool(FINDING.search(output or ""))})
    hist[job_id] = hist[job_id][-keep:]
    p.write_text(json.dumps(hist))


def load_jobs(path: Optional[Path] = None) -> list[Job]:
    """Strict load: raises if ANY job is invalid (used by the CLI `list`/validation and tests)."""
    jobs, errors = parse_jobs(path)
    if errors:
        raise ValueError("; ".join(errors))
    return jobs


def due_jobs(jobs: list[Job], now: time.struct_time,
             last_run: Optional[dict] = None) -> list[Job]:
    """Jobs that match `now` and have not already run in this same minute (de-dup)."""
    last_run = last_run or {}
    stamp = time.strftime("%Y-%m-%dT%H:%M", now)
    out = []
    for j in jobs:
        if not j.enabled:
            continue
        if cron_matches(j.cron, now) and last_run.get(j.id) != stamp:
            out.append(j)
    return out


def _is_leader() -> bool:
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("resilience", ROOT / "governance" / "resilience.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return bool(mod.is_leader())
    except Exception:  # noqa: BLE001 (fail open: a duplicate reminder is better than none)
        return True


def _default_runner(cmd: list) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_due(now: Optional[time.struct_time] = None, *,
            jobs_path: Optional[Path] = None, state_path: Optional[Path] = None,
            runner: Callable[[list], tuple] = _default_runner,
            read_state: Optional[Callable[[], dict]] = None,
            write_state: Optional[Callable[[dict], None]] = None,
            leader: Optional[Callable[[], bool]] = None) -> list[dict]:
    """Run every due job once; record the run so the same minute never double-fires. Returns a
    per-job result list. All I/O is injectable, so tests run with no clock/disk/subprocess."""
    now = now or time.localtime()
    sp = Path(state_path) if state_path else DEFAULT_STATE

    def _read() -> dict:
        try:
            return json.loads(sp.read_text()) if sp.exists() else {}
        except Exception:  # noqa: BLE001
            return {}

    def _write(state: dict) -> None:
        sp.write_text(json.dumps(state, indent=2))

    real = read_state is None                     # tests inject state; only a real run writes the history
    read_state = read_state or _read
    write_state = write_state or _write
    state = read_state()
    stamp = time.strftime("%Y-%m-%dT%H:%M", now)
    jobs, errors = parse_jobs(jobs_path)          # tolerant: a bad job can't stop the healthy ones
    results = [{"id": "(config)", "error": e} for e in errors]
    ran_any = False
    lead: Optional[bool] = None
    for j in due_jobs(jobs, now, state):
        if j.once:                                # one machine of several sends it; any doubt and this one does
            if lead is None:
                lead = (leader or _is_leader)()
            if not lead:
                results.append({"id": j.id, "skipped": "another machine of yours runs this one", "exit_code": 0})
                state[j.id] = stamp
                continue
        try:
            code, output = runner(j.command)
        except Exception as exc:  # noqa: BLE001 — a job crash must not kill the scheduler
            code, output = 1, f"runner error: {str(exc)[:200]}"
        state[j.id] = stamp
        ran_any = True
        if real:
            try:
                record_run(j.id, code, output, stamp, sp.with_name(".history.json"))
            except OSError:
                pass
        results.append({"id": j.id, "cron": j.cron, "ran_at": stamp,
                        "exit_code": code, "output_tail": (output or "")[-400:]})
    if ran_any:
        write_state(state)
    return results
