#!/usr/bin/env python3
"""The estate's crisis and continuity plan, measured (doc 84).

    ./securax continuity                 every scenario: its RTO and RPO targets, what they really are today, and the next fix
    ./securax continuity show ID         the steps, in order, for one scenario (read it during the crisis)
    ./securax continuity drill ID        run that scenario's safe drill, time it, and record the result
    ./securax continuity tabletop [ID]   a structured tabletop exercise (ransomware, compromise, node-lost): each inject is a question;
                                         what this machine can prove is checked, the rest you answer; writes an after-action report
                                         (--answers=yyn... for scripts)
    ./securax continuity mirror          copy the code off GitHub: a git bundle in the backup folders, and a push to MIRROR_REMOTES
    ./securax continuity mirror setup    a second git host (a private GitLab project) in three steps, with its own write-only-there key
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
    files = [f for p in patterns for f in folder.glob(p) if f.is_file() and "-SUSPECT" not in f.name]   # suspect copies protect nothing
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def git(*args: str, repo: pathlib.Path = ROOT) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def rpo_minutes(source: str, now: float | None = None, repo: pathlib.Path = ROOT) -> float | None:
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
        head = git("rev-parse", "HEAD", repo=repo)[1]
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
def mirror(say=print, repo: pathlib.Path = ROOT) -> int:
    """A git bundle of every branch in the backup folder (and the off-site folder), then a push to each MIRROR_REMOTES entry."""
    if git("rev-parse", "--is-shallow-repository", repo=repo)[1] == "true":
        # a shallow checkout lacks the older commits, so its bundle would not clone: refuse rather than keep a broken copy
        say("✗ this checkout is shallow (only recent history), so a bundle of it would not restore. Get the whole history once:")
        say("    git fetch --unshallow        then run this again")
        return 1
    dest = backup_dir()
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / "repo-latest.bundle.tmp"
    rc = subprocess.run(["git", "-C", str(repo), "bundle", "create", str(tmp), "--all"], capture_output=True, text=True)
    if rc.returncode or subprocess.run(["git", "bundle", "verify", str(tmp)], capture_output=True, cwd=repo).returncode:
        say("✗ could not write a verified code bundle: " + (rc.stderr or "")[-300:])
        tmp.unlink(missing_ok=True)
        return 1
    tmp.replace(dest / "repo-latest.bundle")
    (dest / "repo-latest.head").write_text(git("rev-parse", "HEAD", repo=repo)[1] + "\n")
    say(f"✔ code bundle (every branch, verified): {dest / 'repo-latest.bundle'}")
    off = env("SECURAX_OFFSITE_DIR")
    if off and pathlib.Path(off).expanduser().is_dir():
        o = pathlib.Path(off).expanduser()
        (o / "repo-latest.bundle").write_bytes((dest / "repo-latest.bundle").read_bytes())
        say(f"✔ copied to the off-site folder: {o}")
    bad = 0
    for remote in [r.strip() for r in env("MIRROR_REMOTES").split(",") if r.strip()]:
        p = subprocess.run(["git", "-C", str(repo), "push", "--quiet", remote, "--all"], capture_output=True, text=True, timeout=300, env=_git_env())
        subprocess.run(["git", "-C", str(repo), "push", "--quiet", remote, "--tags"], capture_output=True, text=True, timeout=300, env=_git_env())
        if p.returncode:
            bad += 1
            say(f"✗ mirror {remote}: {(p.stderr or '').strip()[-200:]}")
        else:
            say(f"✔ mirrored to {remote}")
    if not env("MIRROR_REMOTES"):
        say("  (no second git host yet: ./securax continuity mirror setup  walks you through a free private GitLab copy)")
    return 1 if bad else 0


def mirror_key() -> pathlib.Path:
    """The SSH key that may push to the mirror and nowhere else (a GitLab deploy key on that one project)."""
    return home() / "continuity" / "mirror_ed25519"


def _git_env() -> dict:
    k = mirror_key()
    if not k.exists():
        return dict(os.environ)
    return {**os.environ, "GIT_SSH_COMMAND": f"ssh -i '{k}' -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"}


def set_env(key: str, value: str, path: pathlib.Path | None = None) -> None:
    """Write KEY=value into local/compose/.env (replacing an old line), keeping the file readable only by you."""
    path = path or ENVF
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    lines = [x for x in lines if not x.startswith(key + "=")] + [f"{key}={value}"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", "utf-8")
    path.chmod(0o600)


def mirror_setup(url: str = "", say=print, repo: pathlib.Path = ROOT) -> int:
    """No address: make the key and print the steps. With the address GitLab shows: prove the key can push, save it, mirror now."""
    k = mirror_key()
    if not url and not k.exists():
        k.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "securax-mirror", "-f", str(k)], capture_output=True, text=True)
            err = r.stderr.strip()[-200:] if r.returncode else ""
        except FileNotFoundError:
            err = "ssh-keygen is not installed (Ubuntu: sudo apt install openssh-client)"
        if err:
            say("✗ could not make the mirror key: " + err)
            return 1
    if not url:
        say("A SECOND HOME FOR THE CODE, so a GitHub outage or a lost account costs nothing. Free, about five minutes, once.\n")
        say("  1. On gitlab.com (you can sign in with Google): New project > Create blank project. Visibility: Private.")
        say("     Untick 'Initialize repository with a README'. Create.")
        say("  2. In that project: Settings > Repository > Deploy keys > Add new key. Paste this, and tick 'Grant write permissions':\n")
        say("     " + k.with_suffix(".pub").read_text().strip() + "\n")
        say("  3. On the project page: Code > Clone with SSH > copy. Then run this, pasting the address after 'setup':")
        say("     ./securax continuity mirror setup <the address you copied>\n")
        say("The key can push to that one project only; it is not your GitLab password, and it stays in ~/.securax.")
        return 0
    if url.startswith(("http://", "https://")) and "@" not in url:
        say("✗ that is the HTTPS address; copy the one under 'Clone with SSH' (it starts with git@).")
        return 2
    p = subprocess.run(["git", "-C", str(repo), "ls-remote", url], capture_output=True, text=True, timeout=60, env=_git_env())
    if p.returncode:
        say("✗ the mirror refused the key: " + (p.stderr or "").strip()[-200:])
        say("  Check step 2 (the deploy key is added, with 'Grant write permissions' ticked), then run this again.")
        return 1
    have = [r.strip() for r in env("MIRROR_REMOTES").split(",") if r.strip()]
    set_env("MIRROR_REMOTES", ",".join(have + ([] if url in have else [url])))
    os.environ["MIRROR_REMOTES"] = ",".join(have + ([] if url in have else [url]))
    say(f"✔ saved: {url} (the daily code-mirror routine pushes to it from now on)")
    return mirror(say=say, repo=repo)


def _securax(*args: str, timeout: int = 900) -> tuple[int, str]:
    p = subprocess.run(["bash", str(ROOT / "securax"), *args], capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "SECURAX_NO_OPEN": "1"})
    return p.returncode, (p.stdout + p.stderr)[-1500:]


def run_drill(kind: str, repo: pathlib.Path = ROOT) -> tuple[bool, str]:
    if kind == "rollback-check":
        rc, out = _securax("rollback", "--check")
        return rc == 0, out
    if kind == "repo-bundle":
        f = backup_dir() / "repo-latest.bundle"
        if not f.exists() and mirror(say=lambda *_: None, repo=repo):
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


# ---------------------------------------------------------------------------------------------------- tabletop exercises
TABLETOPS = ROOT / "governance" / "tabletops.json"
KEEP_REPORTS = 20                                         # after-action reports kept per machine (bounded, doc 80)


def exercises(path: pathlib.Path = TABLETOPS) -> list[dict]:
    return json.loads(path.read_text("utf-8"))["exercises"]


def _age_days(f: pathlib.Path | None, now: float) -> float | None:
    return None if f is None else (now - f.stat().st_mtime) / 86400


def _clean(folder: pathlib.Path | None, encrypted: bool = False) -> list[pathlib.Path]:
    if not folder or not folder.is_dir():
        return []
    fs = [f for f in folder.glob("securax-*.tar.gz*") if f.is_file() and "-SUSPECT" not in f.name
          and (f.name.endswith(".gpg") or not encrypted)]
    return sorted(fs, key=lambda f: f.stat().st_mtime, reverse=True)


def tabletop_check(name: str, now: float | None = None) -> tuple[bool | None, str]:
    """What this machine can prove for one inject: True, False, or None (only you can answer)."""
    now = now or time.time()
    off = env("SECURAX_OFFSITE_DIR")
    offd = pathlib.Path(off).expanduser() if off else None
    if name == "alerts":
        on = [k for k in ("SECURAX_NOTIFY_NTFY", "SECURAX_NOTIFY_WEBHOOK", "ALERT_WEBHOOK") if env(k)]
        return bool(on), ("alerts go to: " + ", ".join(on)) if on else "no alert channel is set"
    if name == "depth":
        cl = _clean(backup_dir())
        if not cl:
            return False, "no clean backup on this machine"
        newest_d, oldest_d = _age_days(cl[0], now), _age_days(cl[-1], now)
        ok = newest_d <= 2 and oldest_d >= 6
        return ok, f"{len(cl)} clean backup(s), newest {newest_d:.1f} days old, oldest {oldest_d:.1f} days old" + (
            "" if ok else " (needs one from the last 2 days AND one at least a week old)")
    if name == "encrypted":
        k = env("SECURAX_BACKUP_KEYFILE")
        ok = bool(k) and pathlib.Path(k).expanduser().is_file()
        return ok, "backups are encrypted with a key you were made to save elsewhere" if ok else "backups are not encrypted"
    if name in ("offsite", "offsite_offline"):
        cl = _clean(offd, encrypted=True)
        age = _age_days(cl[0], now) if cl else None
        site_ok = age is not None and age <= 2
        detail = f"off-site copy {age:.1f} days old" if age is not None else "no off-site copy"
        if name == "offsite":
            return site_ok, detail
        log = home() / "continuity" / "offline.log"
        txt = log.read_text("utf-8", errors="replace").strip() if log.exists() else ""
        last = txt.splitlines()[-1][:20] if txt else ""
        try:
            off_age = (now - dt.datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()) / 86400
        except ValueError:
            off_age = None
        detail += f"; offline copy {off_age:.0f} days old" if off_age is not None else "; no offline copy recorded"
        return site_ok and off_age is not None and off_age <= 35, detail
    if name == "drilled":
        d = last_drills().get("data-lost")
        if not d:
            return False, "the restore was never drilled"
        try:
            age = (now - dt.datetime.fromisoformat(d["when"]).timestamp()) / 86400
        except (KeyError, ValueError):
            age = 1e9
        ok = bool(d.get("ok")) and age <= 100
        return ok, f"last drill {'passed' if d.get('ok') else 'FAILED'} {age:.0f} days ago in {d.get('minutes', 0):.1f} min"
    if name == "allowance":
        day, month = env("AI_BUDGET_DAY_TOKENS", "0"), env("AI_BUDGET_MONTH_TOKENS", "0")
        ok = any(v.strip().isdigit() and int(v) > 0 for v in (day, month))
        return (True, f"capped at {day} tokens a day, {month} a month") if ok else (None, "no token cap is set in .env")
    if name == "known_good":
        f = home() / "known-good.jsonl"
        n = len(f.read_text("utf-8").splitlines()) if f.exists() else 0
        return n > 0, f"{n} known working version(s) recorded" if n else "no working version recorded yet (./securax up records one)"
    if name == "peers":
        n = len([x for x in env("SYNC_PEERS").split(",") if x.strip()])
        return n > 0, f"syncs with {n} other node(s)" if n else "syncs with no other node"
    if name == "sync":
        n = len([x for x in env("SYNC_PEERS").split(",") if x.strip()])
        return None, f"this node syncs with {n} other node(s)"
    if name == "mirror":
        bundle = (backup_dir() / "repo-latest.bundle").exists()
        remotes = [r for r in env("MIRROR_REMOTES").split(",") if r.strip()]
        ok = bundle and bool(remotes)
        return ok, ("a code bundle " + ("exists" if bundle else "is missing") + f" and {len(remotes)} mirror host(s) are set")
    if name == "killswitch":                    # doc 105, G11: one command stops AI, with no restart
        compose = (ROOT / "local" / "compose" / "docker-compose.yml").read_text("utf-8")
        ok = (ROOT / "local" / "compose" / "controls").is_dir() and "AI_CONTROL_FILE" in compose and "./controls:" in compose
        return ok, "the AI stop switch is mounted in the gateway (./securax ai stop all)" if ok else "the AI stop switch is missing"
    if name == "ai_clock":                      # the clocks an AI data leak usually starts are loaded
        have = {f.stem for f in (ROOT / "governance" / "regulators").glob("*.json")}
        need = {"cert-in", "dpdp"}
        return need <= have, "loaded: " + ", ".join(sorted(need & have)) + ("" if need <= have else "; missing: " + ", ".join(sorted(need - have)))
    if name == "replicas":
        return None, "only Cloudflare knows how many machines serve your address (./securax online status shows it)"
    return None, ""


def tabletop(eid: str, answers: str | None = None, ask=None, say=print, now: float | None = None) -> int:
    """Walk one exercise inject by inject. A check this machine can prove decides; otherwise you answer y or n.
    Writes an after-action report (what held, each gap and its fix) and returns 1 when there is any gap."""
    ex = next((x for x in exercises() if x["id"] == eid), None)
    if not ex:
        say(f"No exercise called {eid}. The exercises: " + ", ".join(x["id"] for x in exercises()))
        return 2
    feed = iter((answers or "").replace(",", ""))
    interactive = answers is None and sys.stdin.isatty()
    ask = ask or (lambda q: input(q))
    say(f"TABLETOP · {ex['title']}\n{ex['story']}\n")
    rows, t0 = [], time.time()
    for i, inj in enumerate(ex["injects"], 1):
        say(f"[{inj['at']} · {inj['phase']}] {inj['event']}")
        held, how = None, ""
        if inj.get("check"):
            held, how = tabletop_check(inj["check"], now)
        if held is None:
            if interactive:
                a = ask(f"  {inj['ask']} [y/n] ").strip().lower()[:1]
            else:
                a = next(feed, "")
            held = a == "y"
            how = (how + "; " if how else "") + {"y": "you answered yes", "n": "you answered no"}.get(a, "not answered")
        else:
            say(f"  {inj['ask']}")
            how = "checked on this machine: " + how
        say(("  ✔ " if held else "  ✗ ") + how)
        if not held:
            say(f"    the plan expects: {inj['expect']}\n    fix: {inj['fix']}")
        rows.append({"n": i, "at": inj["at"], "phase": inj["phase"], "ask": inj["ask"], "held": held, "how": how,
                     "expect": inj["expect"], "fix": inj["fix"]})
    gaps = [r for r in rows if not r["held"]]
    rec = {"id": eid, "when": dt.datetime.now().isoformat(timespec="seconds"), "injects": len(rows), "gaps": len(gaps),
           "minutes": round((time.time() - t0) / 60, 1)}
    out = home() / "continuity" / "tabletops"
    out.mkdir(parents=True, exist_ok=True)
    report = out / f"{eid}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    report.write_text(after_action(ex, rows, rec), "utf-8")
    for old in sorted(out.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[KEEP_REPORTS:]:
        old.unlink()
    with (home() / "continuity" / "tabletops.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**rec, "report": str(report)}) + "\n")
    say(f"\n{len(rows) - len(gaps)} of {len(rows)} held. " + ("Ready." if not gaps else f"{len(gaps)} gap(s) to close, each with its fix in the report."))
    say(f"After-action report: {report}")
    return 0 if not gaps else 1


def after_action(ex: dict, rows: list[dict], rec: dict) -> str:
    lines = [f"# After-action report: {ex['title']}", "", f"- Exercise: `{ex['id']}` (scenario `{ex.get('scenario', '')}`)",
             f"- Run: {rec['when']}, {rec['minutes']} min", f"- Result: {rec['injects'] - rec['gaps']} of {rec['injects']} held", "",
             "## What happened, and what held", "", "| # | When | Phase | Question | Held | How we know |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['n']} | {r['at']} | {r['phase']} | {r['ask']} | {'yes' if r['held'] else '**no**'} | {r['how']} |" for r in rows]
    lines += ["", "## Gaps and fixes", ""]
    lines += [f"- [ ] {r['fix']} (inject {r['n']}: {r['expect']})" for r in rows if not r["held"]] or ["- none"]
    lines += ["", "Turn each gap into an action with an owner and a date:  ./securax postmortem new \"Tabletop " + ex["id"] + "\"", ""]
    return "\n".join(lines)


def last_tabletops() -> dict[str, dict]:
    f = home() / "continuity" / "tabletops.jsonl"
    out = {}
    if f.exists():
        for line in f.read_text("utf-8").splitlines():
            try:
                r = json.loads(line)
                out[r["id"]] = r
            except (ValueError, KeyError):
                continue
    return out


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
        tt = last_tabletops()
        print("Tabletop exercises (talk it through, the machine checks what it can):  ./securax continuity tabletop ID")
        for x in exercises():
            r = tt.get(x["id"])
            print(f"  {'·' if not r else ('✔' if not r['gaps'] else '✗')} {x['id']:<11} {x['title']}"
                  + (f"  (last {r['when'][:10]}: {r['gaps']} gap(s))" if r else "  (never run)"))
        return 0 if all(r["ok"] for r in rows) else 1
    if cmd == "tabletop":
        if len(argv) < 2:
            for x in exercises():
                print(f"  {x['id']:<11} {x['title']}  ({len(x['injects'])} injects)")
            print("Run one:  ./securax continuity tabletop ransomware")
            return 0
        ans = next((a.split("=", 1)[1] for a in argv[2:] if a.startswith("--answers=")), None)
        return tabletop(argv[1], answers=ans)
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
    if cmd == "mirror" and argv[1:2] == ["setup"]:
        return mirror_setup(" ".join(argv[2:]).strip())
    if cmd == "mirror":
        return mirror()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
