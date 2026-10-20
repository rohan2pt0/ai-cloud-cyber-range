#!/usr/bin/env python3
"""Go back to a version that worked, at any time, in one command (doc 82).

    ./securax rollback --list            every version that ran healthy on THIS machine, newest first
    ./securax rollback                   go back to the newest working version older than the one running now
    ./securax rollback N | COMMIT | vX.Y.Z   go back to that one (N from --list)
    ./securax rollback N --with-data     ... and also restore the data backup taken while that version was running
    ./securax rollback --latest          come forward again to the newest version
    ./securax rollback --status          where you are now, and whether you are pinned to an older version
    ./securax rollback --check           can every recorded version still be restored? (the weekly routine; changes nothing)

How it is safe:
- Working versions are recorded only when the estate really came up healthy (`up`, `update`). Each one is also pinned with a
  git ref (refs/securax/good/...), so it cannot be lost even if the published history changes.
- Before going back: unsaved code edits are put aside with `git stash` (named, recoverable), the running data is backed up,
  and the version you are leaving is pinned (refs/securax/before-rollback/...), so you can always come forward again.
- After going back the estate is restarted and must answer its health check. If it does not, you are returned to where you
  were, automatically.
- An older version stays put: the nightly update only runs on the main branch, so it never undoes a rollback by itself.
  `--latest` brings you back to main.
The record keeps the newest 50 versions (bounded, like everything else, doc 80). Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEEP = 50
MIN_GAP_S = 6 * 3600                 # the same version is recorded again at most every 6 hours


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def ledger_path() -> pathlib.Path:
    return home() / "known-good.jsonl"


def git(*args: str, root: pathlib.Path = ROOT, check: bool = False) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()[:300]}")
    return p.returncode, p.stdout.strip()


def newest_backup(root: pathlib.Path = ROOT) -> str | None:
    d = pathlib.Path(os.environ.get("SECURAX_BACKUP_DIR") or root / "backups")
    files = sorted(d.glob("securax-*.tar.gz*"), key=lambda f: f.stat().st_mtime, reverse=True) if d.exists() else []
    return str(files[0]) if files else None


def load(path: pathlib.Path | None = None) -> list[dict]:
    p = path or ledger_path()
    if not p.exists():
        return []
    out = []
    for ln in p.read_text("utf-8").splitlines():
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def record(reason: str, root: pathlib.Path = ROOT, path: pathlib.Path | None = None, now: float | None = None) -> dict | None:
    """Note that the estate is healthy on the current commit. Returns the entry, or None when nothing new was recorded."""
    now = now or time.time()
    rc, commit = git("rev-parse", "HEAD", root=root)
    if rc:
        return None
    rows = load(path)
    last = next((r for r in reversed(rows) if r["commit"] == commit), None)
    if last and now - last["ts"] < MIN_GAP_S:
        return None
    version = (root / "VERSION").read_text().strip() if (root / "VERSION").exists() else "?"
    dirty = bool(git("status", "--porcelain", "--untracked-files=no", root=root)[1])
    entry = {"ts": int(now), "when": dt.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M"), "commit": commit, "version": version,
             "branch": git("rev-parse", "--abbrev-ref", "HEAD", root=root)[1], "reason": reason, "local_edits": dirty,
             "backup": newest_backup(root)}
    git("update-ref", f"refs/securax/good/{int(now)}", commit, root=root)        # this version can never be garbage-collected
    rows.append(entry)
    rows = rows[-KEEP:]
    p = path or ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows), "utf-8")
    tmp.replace(p)
    keep = {f"refs/securax/good/{r['ts']}" for r in rows}
    for ref in git("for-each-ref", "--format=%(refname)", "refs/securax/good/", root=root)[1].splitlines():
        if ref and ref not in keep:
            git("update-ref", "-d", ref, root=root)                               # bounded: the pins follow the record
    return entry


def distinct(rows: list[dict]) -> list[dict]:
    """Newest first, one entry per commit (its newest record)."""
    seen, out = set(), []
    for r in reversed(rows):
        if r["commit"] not in seen:
            seen.add(r["commit"])
            out.append(r)
    return out


def resolve(target: str | None, rows: list[dict], root: pathlib.Path = ROOT) -> dict:
    cands = distinct(rows)
    head = git("rev-parse", "HEAD", root=root)[1]
    if not cands:
        raise ValueError("No working version recorded yet. One is recorded each time `./securax up` brings the estate up healthy.")
    if target is None:
        older = [r for r in cands if r["commit"] != head]
        if not older:
            raise ValueError("The version running now is the only working version recorded on this machine.")
        return older[0]
    if target.isdigit():
        i = int(target)
        if not 1 <= i <= len(cands):
            raise ValueError(f"Pick 1 to {len(cands)} (see ./securax rollback --list).")
        return cands[i - 1]
    rc, commit = git("rev-parse", "--verify", "--quiet", target + "^{commit}", root=root)
    if rc:
        raise ValueError(f"{target} is not a version this checkout knows (a number from --list, a commit or a tag like v0.2.0).")
    known = next((r for r in cands if r["commit"] == commit), None)
    return known or {"commit": commit, "version": "?", "when": "never recorded as working here", "backup": None, "unrecorded": True}


def check(rows: list[dict], root: pathlib.Path = ROOT) -> list[str]:
    """Every recorded version still exists in git, and every recorded backup is still on disk. Changes nothing."""
    out = []
    for r in distinct(rows):
        if git("cat-file", "-e", r["commit"] + "^{commit}", root=root)[0]:
            out.append(f"{r['when']} {r['commit'][:9]}: the code of this version is missing from this checkout")
        if r.get("backup") and not pathlib.Path(r["backup"]).exists():
            out.append(f"{r['when']} {r['commit'][:9]}: its data backup {r['backup']} is gone (the code can still be restored)")
    return out


def securax(*args: str, root: pathlib.Path = ROOT, timeout: int = 1800) -> tuple[int, str]:
    env = {**os.environ, "SECURAX_NO_OPEN": "1"}
    p = subprocess.run(["bash", str(root / "securax"), *args], capture_output=True, text=True, timeout=timeout, env=env)
    return p.returncode, (p.stdout + p.stderr)[-2000:]


def healthy(root: pathlib.Path = ROOT, run=securax) -> bool:
    return run("ready", root=root, timeout=60)[0] == 0


def go(target: dict, with_data: bool = False, root: pathlib.Path = ROOT, run=securax, ready=healthy, say=print) -> int:
    """Move the checkout to target['commit'] and restart; on failure, return to where we were. Returns an exit code."""
    head = git("rev-parse", "HEAD", root=root)[1]
    branch = git("rev-parse", "--abbrev-ref", "HEAD", root=root)[1]               # "HEAD" when already on a pinned version
    if target["commit"] == head and not with_data:
        say("You are already on that version.")
        return 0
    stamp = int(time.time())
    if git("status", "--porcelain", root=root)[1]:
        git("stash", "push", "--include-untracked", "-m", f"securax-rollback-{stamp}", root=root, check=True)
        say(f"  • your unsaved code edits are kept aside as git stash 'securax-rollback-{stamp}' (get them back: git stash pop)")
    git("update-ref", f"refs/securax/before-rollback/{stamp}", head, root=root)
    if ready(root=root, run=run):
        rc, out = run("backup", root=root)
        say("  • data backed up first: " + (out.strip().splitlines()[-1] if rc == 0 and out.strip() else "could not take a backup (" + out[-200:] + ")"))
    say(f"  • going to {target['commit'][:9]} (version {target.get('version', '?')}, worked {target.get('when', '?')})")
    git("checkout", "--quiet", "--detach", target["commit"], root=root, check=True)
    if with_data:
        if not target.get("backup") or not pathlib.Path(target["backup"]).exists():
            say("  ✗ no data backup was recorded for that version (or the file is gone): the code was moved, the data was not")
        else:
            rc, out = run("restore", target["backup"], "--yes", root=root)
            say("  • data restored from " + target["backup"] if rc == 0 else "  ✗ data restore failed: " + out[-300:])
    run("down", root=root)
    rc, out = run("up", root=root)
    if rc == 0 and ready(root=root, run=run):
        say(f"✔ The estate is running version {target.get('version', '?')} ({target['commit'][:9]}) and is healthy.")
        say("  The nightly update leaves it here. To come forward again:  ./securax rollback --latest")
        record("rollback", root=root)
        return 0
    say("✗ That version did not start healthy. Returning to where you were…")
    git("checkout", "--quiet", branch if branch != "HEAD" else head, root=root)
    run("down", root=root)
    run("up", root=root)
    say("  Back on the version you started from." if ready(root=root, run=run) else "  The estate is still not healthy: run ./securax doctor")
    return 3


def latest(root: pathlib.Path = ROOT, run=securax, ready=healthy, say=print) -> int:
    git("checkout", "--quiet", "main", root=root, check=True)
    rc, out = git("pull", "--ff-only", "--quiet", root=root)
    if rc:
        say("  (could not reach the newest code online; using the main branch already here)")
    run("down", root=root)
    rc, out = run("up", root=root)
    ok = rc == 0 and ready(root=root, run=run)
    say(f"✔ Back on the newest version ({git('rev-parse', '--short', 'HEAD', root=root)[1]}) and healthy." if ok else "✗ The newest version did not start healthy: ./securax rollback  takes you back again.")
    if ok:
        record("latest", root=root)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="./securax rollback", description=__doc__.split("\n\n")[0])
    ap.add_argument("target", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--with-data", action="store_true")
    ap.add_argument("--yes", action="store_true", help="do not ask before going back")
    ap.add_argument("--record", metavar="REASON", help=argparse.SUPPRESS)        # called by `up` and `update` when the estate is healthy
    a = ap.parse_args(argv)
    try:
        rows = load()
        if a.record:
            record(a.record)
            return 0
        if a.list:
            c = distinct(rows)
            head = git("rev-parse", "HEAD")[1]
            if not c:
                print("No working version recorded yet: one is recorded each time `./securax up` brings the estate up healthy.")
            for i, r in enumerate(c, 1):
                print(f"  {i:>2}. {r['when']}  v{r['version']:<8} {r['commit'][:9]}  {r['reason']:<9}"
                      + ("  backup: " + pathlib.Path(r["backup"]).name if r.get("backup") else "  (no backup then)") + ("   ← running now" if r["commit"] == head else ""))
            return 0
        if a.status:
            head = git("rev-parse", "HEAD")[1]
            branch = git("rev-parse", "--abbrev-ref", "HEAD")[1]
            c = distinct(rows)
            print(f"Running {head[:9]} on " + ("main (follows updates)" if branch == "main" else "an older, pinned version (the nightly update leaves it alone)" if branch == "HEAD" else f"branch {branch}"))
            print(f"Working versions recorded: {len(c)}" + (f"; newest {c[0]['when']} ({c[0]['commit'][:9]})" if c else ""))
            return 0
        if a.check:
            probs = check(rows)
            print("✔ every recorded working version can be restored" if not probs else "\n".join("✗ " + p for p in probs))
            return 1 if probs else 0
        if a.latest:
            return latest()
        t = resolve(a.target, rows)
        print(f"Go back to {t['commit'][:9]} (version {t.get('version', '?')}, worked {t.get('when', '?')})" + (" and restore its data backup" if a.with_data else "") + "?")
        if t.get("unrecorded"):
            print("  ⚠ this version was never recorded as working on this machine")
        if not a.yes:
            if not sys.stdin.isatty():
                print("  (add --yes to go ahead without a question)")
                return 2
            if input("  Type yes to continue: ").strip().lower() != "yes":
                print("  Nothing changed.")
                return 0
        return go(t, a.with_data)
    except (ValueError, RuntimeError) as e:
        print(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
