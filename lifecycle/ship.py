#!/usr/bin/env python3
"""Ship: the pull-request loop that Claude Code used to run for you, run by SecuRAX itself (doc 98).
Open the pull request, watch CI, and when it goes red, gather the failing logs into a brief and let autobuild fix it
(one validated push per round). When every check is green and nothing conflicts, merge it and reset your branch.

    ./securax ship check                 can this machine run the loop? (git, a GitHub token, OpenCode, the open models)
    ./securax ship login                 save a GitHub token, privately (vault/github-token, 0600)
    ./securax ship pr [--title T] [--body-file F]    push this branch and open its pull request (the repo's template)
    ./securax ship status [PR]           every check on the pull request's latest commit, in one view
    ./securax ship watch [PR] [--fix N] [--merge] [--once] [--interval S] [--timeout M]
                                         wait for CI; on red write the failure brief (and with --fix let autobuild fix it,
                                         at most N rounds); on green with --merge, squash-merge and reset the branch
    ./securax ship watch --all --once --fix 2 --merge
                                         one pass over every pull request this machine opened (the pr-watch routine)

Rules it keeps, the same as the estate's: it never skips, disables or weakens a test (autobuild's gate and diffcheck
refuse that); it pushes one fix per round, because every push restarts the 40-minute sandbox; it merges only when
every check passed and GitHub says the PR is mergeable; it rewrites no history except resetting its own branch after
the merge. Your token never prints and stays in vault/. Standard library only; its only network calls go to the GitHub
API and to git's own remote. Exit codes: 0 ok or merged, 1 CI red, blocked or not set up yet, 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = os.environ.get("GITHUB_API", "https://api.github.com")
OK = {"success", "skipped", "neutral"}
BAD = {"failure", "timed_out", "cancelled", "action_required", "startup_failure", "stale"}


class ShipError(Exception):
    pass


# ------------------------------------------------------------------------------------------------ where things are
def vault() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_VAULT_DIR") or ROOT / "vault")


def state_file() -> pathlib.Path:
    return vault() / "ship" / "state.json"


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise ShipError(f"git {' '.join(args)} failed: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout.strip()


def slug() -> str:
    """owner/repo: SECURAX_REPO, else brand.env REPO_SLUG, else the origin remote."""
    if os.environ.get("SECURAX_REPO"):
        return os.environ["SECURAX_REPO"]
    be = ROOT / "brand.env"
    if be.exists():
        m = re.search(r"^REPO_SLUG=(\S+)", be.read_text("utf-8"), re.M)
        if m:
            return m.group(1)
    url = git("remote", "get-url", "origin", check=False)
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
    if not m:
        raise ShipError("cannot tell which GitHub repository this is: set SECURAX_REPO=owner/repo")
    return m.group(1)


def token() -> str | None:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t.strip()
    f = vault() / "github-token"
    return f.read_text("utf-8").strip() if f.exists() else None


# ------------------------------------------------------------------------------------------------ the GitHub API
def api(method: str, path: str, data: dict | None = None, raw: bool = False, tries: int = 3):
    tok = token()
    if not tok:
        raise ShipError("no GitHub token: run ./securax ship login")
    url = path if path.startswith("http") else API + path
    body = json.dumps(data).encode() if data is not None else None
    for i in range(tries):
        req = urllib.request.Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "securax-ship", **({"Content-Type": "application/json"} if body else {})})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = r.read()
                return payload.decode("utf-8", "replace") if raw else (json.loads(payload) if payload else {})
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 405, 409, 422):
                msg = e.read().decode("utf-8", "replace")[:300]
                hint = {401: "the token is wrong or expired (./securax ship login)",
                        403: "the token lacks a permission (Contents, Pull requests: read and write; Actions, Checks: read)",
                        404: "not found, or the token cannot see this repository"}.get(e.code, msg)
                raise ShipError(f"GitHub said {e.code} for {method} {path}: {hint}") from None
            if i == tries - 1:
                raise ShipError(f"GitHub said {e.code} for {method} {path} after {tries} tries") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if i == tries - 1:
                raise ShipError(f"cannot reach GitHub ({e}); check the connection and try again") from None
        time.sleep(2 * 2 ** i)   # 2, 4 seconds: the network retry rule the estate uses everywhere


# ------------------------------------------------------------------------------------------------ the state of a PR
def classify(runs: list[dict]) -> dict:
    """Pending, red or green, from the check runs on one commit. No runs at all is pending, never green."""
    pending = [r["name"] for r in runs if r.get("status") != "completed"]
    red = [r for r in runs if r.get("status") == "completed" and r.get("conclusion") in BAD]
    state = "pending" if pending or not runs else ("red" if red else "green")
    return {"state": state, "pending": pending, "red": [{"name": r["name"], "id": r["id"], "url": r.get("html_url", "")} for r in red],
            "total": len(runs)}


def pr_state(n: int) -> dict:
    s = slug()
    pr = api("GET", f"/repos/{s}/pulls/{n}")
    runs = api("GET", f"/repos/{s}/commits/{pr['head']['sha']}/check-runs?per_page=100").get("check_runs", [])
    return {"pr": pr, "checks": classify(runs), "sha": pr["head"]["sha"], "mergeable": pr.get("mergeable_state"), "merged": pr.get("merged"),
            "open": pr.get("state") == "open", "branch": pr["head"]["ref"], "base": pr["base"]["ref"]}


def _clean_log(text: str, keep: int = 120) -> str:
    lines = [re.sub(r"^\d{4}-\d\d-\d\dT[\d:.]+Z\s?", "", ln) for ln in text.splitlines()]
    lines = [re.sub(r"\x1b\[[0-9;]*m", "", ln) for ln in lines]
    hits = [ln for ln in lines if re.search(r"(?i)\b(error|failed|failure|assert|traceback|✘|exit code [1-9])", ln)]
    tail = lines[-keep:]
    return "\n".join((hits[-40:] + ["", "... last lines ..."] if hits else []) + tail)


def brief(n: int, st: dict, logs: dict[str, str], attempt: int) -> pathlib.Path:
    """The failure brief: what is red, the telling lines of each log, the lessons and the rules. Private, in vault/."""
    lessons = (ROOT / "LESSONS.md").read_text("utf-8").splitlines()[-12:] if (ROOT / "LESSONS.md").exists() else []
    out = [f"# CI is red on pull request #{n} (commit {st['sha'][:7]}, round {attempt})", "",
           "Make it green by fixing the cause. Never skip, disable or weaken a test, a rail or a check (BUILD-CONTRACT.md).",
           "If the failure is not this change's (it is red on the base branch too, or names a service the diff does not touch),",
           "write that down in one line and change nothing.", "", "## Failing checks", ""]
    out += [f"- {r['name']}: {r['url']}" for r in st["checks"]["red"]]
    for name, text in logs.items():
        out += ["", f"## {name}: the telling lines", "", "```", _clean_log(text), "```"]
    out += ["", "## Recent lessons (LESSONS.md)", ""] + lessons
    p = vault() / "ship" / f"pr{n}-round{attempt}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", "utf-8")
    os.chmod(p, 0o600)
    return p


def failing_logs(st: dict) -> dict[str, str]:
    logs = {}
    for r in st["checks"]["red"][:4]:
        try:
            logs[r["name"]] = api("GET", f"/repos/{slug()}/actions/jobs/{r['id']}/logs", raw=True)
        except ShipError as e:
            logs[r["name"]] = f"(log not available: {e})"
    return logs


# ------------------------------------------------------------------------------------------------ remembering PRs
def remember(n: int, branch: str) -> None:
    f = state_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    d = json.loads(f.read_text("utf-8")) if f.exists() else {}
    d[str(n)] = {"branch": branch, "at": dt.datetime.now().isoformat(timespec="seconds"), "rounds": d.get(str(n), {}).get("rounds", 0)}
    f.write_text(json.dumps(d, indent=1), "utf-8")


def tracked() -> dict:
    f = state_file()
    return json.loads(f.read_text("utf-8")) if f.exists() else {}


def forget(n: int) -> None:
    d = tracked()
    if d.pop(str(n), None) is not None:
        state_file().write_text(json.dumps(d, indent=1), "utf-8")


def tell(msg: str) -> None:
    """The phone, if the andon cord is set up; never fails the loop."""
    try:
        subprocess.run([str(ROOT / "securax"), "notify", "send", msg, "--title", "SecuRAX ship"], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass


# ------------------------------------------------------------------------------------------------ the actions
def body_from_template(title: str) -> str:
    """The repository's pull-request template, its sections filled from the commits; never its instructions."""
    tpl = next((p for p in (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md", ROOT / ".github" / "pull_request_template.md") if p.exists()), None)
    base = git("merge-base", "HEAD", "origin/main", check=False) or "origin/main"
    log = git("log", "--format=- %s", f"{base}..HEAD", check=False) or f"- {title}"
    if not tpl:
        return f"## What & why\n{log}\n\n## How to test\n`./securax verify`\n\nAssisted-by: SecuRAX open models\n"
    out = []
    for line in tpl.read_text("utf-8").splitlines():
        if line.strip().startswith("<!--"):
            continue
        out.append(line)
        if line.startswith("## What"):
            out.append(log)
        elif line.startswith("## How to test"):
            out.append("```bash\n./securax verify\n```")
    return "\n".join(out).strip() + "\n\nAssisted-by: SecuRAX open models\n"


def open_pr(title: str | None, body_file: str | None) -> int:
    br = git("rev-parse", "--abbrev-ref", "HEAD")
    if br in ("main", "master", "HEAD"):
        raise ShipError("you are on main: make a branch first (git checkout -b my-change)")
    if git("status", "--porcelain"):
        raise ShipError("you have uncommitted changes: commit them first (then ./securax verify)")
    title = title or git("log", "-1", "--format=%s")
    body = pathlib.Path(body_file).read_text("utf-8") if body_file else body_from_template(title)
    for i in range(4):   # push, retrying a network failure: 2, 4, 8 seconds
        r = subprocess.run(["git", "-C", str(ROOT), "push", "-u", "origin", br], capture_output=True, text=True)
        if not r.returncode:
            break
        if i == 3 or "rejected" in r.stderr:
            raise ShipError(f"git push failed: {r.stderr.strip()[:300]}")
        time.sleep(2 * 2 ** i)
    s = slug()
    existing = api("GET", f"/repos/{s}/pulls?head={s.split('/')[0]}:{br}&state=open")
    if existing:
        n = existing[0]["number"]
        print(f"✔ pull request #{n} already open for {br}: {existing[0]['html_url']}")
    else:
        pr = api("POST", f"/repos/{s}/pulls", {"title": title, "head": br, "base": "main", "body": body})
        n = pr["number"]
        print(f"✔ opened pull request #{n}: {pr['html_url']}")
    remember(n, br)
    print(f"  Next: ./securax ship watch {n} --fix 2 --merge   (or leave it to the pr-watch routine)")
    return n


def fix_round(n: int, st: dict, attempt: int) -> bool:
    """One autobuild round on the PR's branch, fed the brief. Pushes only when autobuild's gate went green."""
    b = brief(n, st, failing_logs(st), attempt)
    br = st["branch"]
    if git("rev-parse", "--abbrev-ref", "HEAD") != br:
        if git("status", "--porcelain"):
            raise ShipError(f"cannot switch to {br}: this checkout has uncommitted changes")
        git("fetch", "-q", "origin", br)
        git("checkout", "-q", br)
    git("pull", "-q", "--ff-only", "origin", br)
    task = f"CI is red on pull request #{n}. Read the failure brief at {b} and fix the cause so every check passes."
    before = git("rev-parse", "HEAD")
    r = subprocess.run([str(ROOT / "securax"), "autobuild", task, "--tries", "3"], cwd=ROOT)
    fixed = git("rev-parse", "--abbrev-ref", "HEAD")
    if r.returncode or fixed == br:
        git("checkout", "-q", br, check=False)
        print(f"✘ autobuild could not make it green (brief: {b}); this needs a person or the strong models: ./securax opencode --strong")
        return False
    git("checkout", "-q", br)
    git("merge", "-q", "--ff-only", fixed)     # autobuild's green commit lands on the PR branch as a fast-forward
    git("branch", "-q", "-D", fixed)
    if git("rev-parse", "HEAD") == before:
        return False
    git("push", "-q", "origin", br)
    print(f"✔ round {attempt}: a green fix is pushed to {br}; CI runs again")
    return True


def merge(n: int, st: dict) -> None:
    s = slug()
    api("PUT", f"/repos/{s}/pulls/{n}/merge", {"merge_method": "squash", "sha": st["sha"], "commit_title": f"{st['pr']['title']} (#{n})"})
    print(f"✔ merged #{n} into {st['base']}")
    forget(n)
    # Reset the working branch onto the new base, as the estate's own rule says: a merged PR is finished, never reused.
    if git("rev-parse", "--abbrev-ref", "HEAD", check=False) == st["branch"] and not git("status", "--porcelain", check=False):
        git("fetch", "-q", "origin", st["base"])
        git("checkout", "-q", "-B", st["branch"], f"origin/{st['base']}")
        git("push", "-q", "-u", "--force-with-lease", "origin", st["branch"], check=False)   # -u: track its own remote branch, not the base
        print(f"  {st['branch']} now starts from the new {st['base']}")
    tell(f"Merged #{n}: {st['pr']['title']}")


def watch(n: int, fix: int, do_merge: bool, once: bool, interval: int, timeout_min: int) -> int:
    deadline, said = time.time() + timeout_min * 60, None
    rounds = tracked().get(str(n), {}).get("rounds", 0)
    while True:
        st = pr_state(n)
        if st["merged"] or not st["open"]:
            print(f"#{n} is {'merged' if st['merged'] else 'closed'}: nothing to do")
            forget(n)
            return 0
        c = st["checks"]
        line = f"#{n} {st['sha'][:7]}: {c['state']}" + (f" ({len(c['pending'])} still running)" if c["pending"] else "") + \
               (f", red: {', '.join(r['name'] for r in c['red'])}" if c["red"] else "") + f", GitHub says {st['mergeable']}"
        if line != said:
            print(line)
            said = line
        if st["mergeable"] == "dirty":
            print("✘ it conflicts with the base: merge it locally (git fetch origin main && git merge origin/main), run ./securax verify, push")
            tell(f"#{n} has a merge conflict")
            return 1
        if c["state"] == "red" and not c["pending"]:
            if rounds < fix:
                rounds += 1
                d = tracked()
                d.setdefault(str(n), {"branch": st["branch"]})["rounds"] = rounds
                state_file().parent.mkdir(parents=True, exist_ok=True)
                state_file().write_text(json.dumps(d, indent=1), "utf-8")
                if fix_round(n, st, rounds):
                    if once:
                        return 0          # a green fix is pushed; the next pass sees its CI
                    said = None
                    time.sleep(interval)
                    continue
            b = brief(n, st, failing_logs(st), rounds or 1)
            print(f"✘ CI is red. The failure brief: {b}")
            tell(f"#{n} is red: {', '.join(r['name'] for r in c['red'])}. Brief in vault/ship.")
            return 1
        if c["state"] == "green":
            if do_merge and st["mergeable"] in ("clean", "unstable", "has_hooks"):
                merge(n, st)
                return 0
            print(f"✔ #{n} is green" + ("" if do_merge else ": merge it when you are ready (or add --merge)"))
            return 0
        if once or time.time() > deadline:
            return 0 if once else 1
        time.sleep(interval)


def check(say=print) -> int:
    rows = []

    def row(ok: bool, what: str, fix: str = "") -> None:
        rows.append(ok)
        say(f"  {'✔' if ok else '✘'} {what}" + ("" if ok else f"\n      fix: {fix}"))
    say("Can this machine build SecuRAX without Claude Code? (doc 98)\n")
    row(bool(shutil.which("git")), "git is installed", "install git")
    inside = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-dir"], capture_output=True).returncode == 0
    row(inside, "this folder is a git checkout", "clone the repository, then run this inside it")
    try:
        s = slug()
        row(True, f"the repository is {s}")
    except ShipError as e:
        row(False, "the repository is known", str(e))
        s = None
    t = token()
    row(bool(t), "a GitHub token is saved", "./securax ship login   (a fine-grained token: Contents and Pull requests read and write; Actions and Checks read)")
    if t and s:
        try:
            me = api("GET", "/user")
            repo = api("GET", f"/repos/{s}")
            row(bool(repo.get("permissions", {}).get("push")), f"the token works (signed in as {me.get('login')}) and can push to {s}",
                "give the token write access to this repository")
        except ShipError as e:
            row(False, "the token works", str(e))
    row(bool(shutil.which("opencode")), "OpenCode is installed (the coding agent)", "npm install -g opencode-ai@1.19.0   (doc 42)")
    envf = ROOT / "local" / "compose" / ".env"
    has_key = envf.exists() and re.search(r"^OPENCODE_GO_API_KEY=\S+", envf.read_text("utf-8"), re.M)
    row(bool(has_key), "the open models are paid for (OpenCode Go key)", "./securax providers add opencodego   (doc 83), then ./securax up")
    row(bool(shutil.which("aider")) or bool(shutil.which("opencode")), "an agent autobuild can drive", "./securax build --setup, or install OpenCode")
    ok = all(rows)
    say("\n" + ("✔ Ready: ./securax ship pr, then ./securax ship watch N --fix 2 --merge" if ok else
               f"✘ {rows.count(False)} thing(s) to set up first; each fix is above."))
    return 0 if ok else 1


def login() -> int:
    print("Paste a GitHub fine-grained token for this repository (it is not shown, and is kept in vault/github-token, 0600).")
    print("Permissions: Contents read and write, Pull requests read and write, Actions read, Checks read.")
    t = getpass.getpass("token: ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{20,255}", t):
        print("That does not look like a GitHub token.", file=sys.stderr)
        return 2
    f = vault() / "github-token"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(t + "\n", "utf-8")
    os.chmod(f, 0o600)
    try:
        print(f"✔ saved; signed in as {api('GET', '/user').get('login')}")
        return 0
    except ShipError as e:
        print(f"saved, but it did not work yet: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax ship", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="check", choices=["check", "login", "pr", "status", "watch"])
    ap.add_argument("pr", nargs="?", type=int)
    ap.add_argument("--title")
    ap.add_argument("--body-file")
    ap.add_argument("--fix", type=int, default=0)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--timeout", type=int, default=120)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            return check()
        if a.cmd == "login":
            return login()
        if a.cmd == "pr":
            open_pr(a.title, a.body_file)
            return 0
        prs = [int(k) for k in tracked()] if a.all else ([a.pr] if a.pr else [int(k) for k in tracked()][-1:])
        if not prs:
            print("No pull request to look at: ./securax ship pr opens one, or name it: ./securax ship watch 123")
            return 0 if a.all else 2
        rc = 0
        for n in prs:
            if a.cmd == "status":
                st = pr_state(n)
                c = st["checks"]
                print(f"#{n} {st['pr']['title']}\n  {c['state']}: {c['total']} check(s), {len(c['pending'])} running, {len(c['red'])} red; GitHub says {st['mergeable']}")
                for r in c["red"]:
                    print(f"  ✘ {r['name']}: {r['url']}")
            else:
                rc = max(rc, watch(n, a.fix, a.merge, a.once, max(15, a.interval), a.timeout))
        return rc
    except ShipError as e:
        print(f"✘ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
