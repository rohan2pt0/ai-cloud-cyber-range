#!/usr/bin/env python3
"""A task brief that a weaker model can act on: what to do, where it lives, what bites, and what "done" means (doc 83).

    ./securax brief "fix the sync token check"           print the brief (paste it into OpenCode, ChatGPT, Gemini or any chat AI)
    ./securax brief "…" --files                          only the likely files, one per line (autobuild hands these to the agent)
    ./securax brief "…" --json

Models fail on the same three things: they edit the wrong file, they miss the rule that broke last time, and they stop before the
repo's own checks pass. So the brief carries a map of the files this task most likely touches (ranked by the task's words against
each tracked file's path and its own first line of description), the lessons from LESSONS.md that share its words, and the exact
checks for the kinds of files involved. It never lists vault/, .env or generated files. Standard library only; reads git ls-files.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ALIASES = pathlib.Path(__file__).resolve().parent / "brief.json"
NEVER = ("vault/", "local/compose/.env", "portal/cockpit", "portal/navigator", "portal/setup.json", "website/docs/", "guiding-map/index.html")
TEXT = {".py", ".sh", ".js", ".html", ".md", ".json", ".yml", ".yaml", ".toml", ".conf", ".css", ""}
STOP = set("""a an and are as at be by can do does for from has have how i in into is it its make me my of on or so that the this to
up use was we what when with without you your add fix new change update make sure please should would could also all any each every""".split())
# what "done" means, by the kind of file the task touches (AGENTS.md section 3)
CHECKS = [
    (r"^guiding-map/(ops\.js|index\.html|hub\.html|sw\.js)", "Life OS: `cd guiding-map && node build.js && npm test` (every file must pass), then "
     "`python3 guiding-map/tests/ui_audit.py OUT` (0 page errors, 0 contrast failures, both themes)"),
    (r"^securax$", "CLI: `bash -n securax`; a new command gets a line in `./securax help`; never end a branch or loop with a bare `[ … ] &&`"),
    (r"^apps/llm-gateway/", "Gateway: `python3 -m pytest -q apps/llm-gateway`; never weaken a rail"),
    (r"^apps/estate-sync/", "Sync: `python3 -m pytest -q apps/estate-sync` (auth stays fail-closed; the merge stays commutative)"),
    (r"^docs/|^mkdocs\.yml", "Docs: `mkdocs build --strict`; a new doc goes in the mkdocs.yml nav; set its light in docs/status.yml, then `python3 docs/sync_status.py`"),
    (r"^features\.json$", "Features: `python3 tools/features_sync.py`"),
    (r"^local/compose/", "Compose: `docker compose -f local/compose/docker-compose.yml config -q`; pin every image to a version"),
    (r"^\.github/workflows/", "Workflows: `python3 -m pytest -q lifecycle/tests/test_workflows_parse.py` (an invalid workflow runs nothing and looks green)"),
]
ALWAYS = ["`ruff check .` and `python3 -m pytest -q` (or `./securax verify`, what CI enforces)",
          "`git add -A`, then `python3 -m lifecycle.fitness` (untracked files are invisible to it)",
          "a line in CHANGELOG.md under [Unreleased]; `python3 tools/readme_sync.py`",
          "re-read your own diff as a reviewer before you call it done"]


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z0-9]+", text.lower()) if w not in STOP and len(w) > 2}


def tracked() -> list[str]:
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    return [f for f in r.stdout.splitlines() if not f.startswith(NEVER) and pathlib.Path(f).suffix in TEXT and "/tests/" not in f
            and not f.startswith("vendor/") and not f.endswith("__init__.py")]


def aliased(task: str) -> list[str]:
    """Files named by the words people use for each part (lifecycle/brief.json), in the order they appear there."""
    t = " " + re.sub(r"[^a-z0-9 -]+", " ", task.lower()) + " "
    try:
        table = json.loads(ALIASES.read_text("utf-8"))["aliases"]
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for keys, paths in table.items():
        if any(f" {k} " in t or f" {k}s " in t for k in keys.split("|")):
            out += [p for p in paths if p not in out]
    return out


def _body_words(path: str) -> set[str]:
    try:
        return words((ROOT / path).read_text("utf-8", "ignore")[:6000])
    except OSError:
        return set()


def describe(path: str) -> str:
    """The file's own first line of description: a docstring, a leading comment, or a markdown title."""
    try:
        head = (ROOT / path).read_text("utf-8", "ignore")[:1500]
    except OSError:
        return ""
    for pat in (r'^\s*(?:#![^\n]*\n)?\s*"""(.+?)(?:\n|""")', r"^\s*(?:#![^\n]*\n)?\s*(?:#|//)\s*(.+)", r"^#\s+(.+)", r"<title>(.+?)</title>"):
        m = re.search(pat, head, re.S if pat.startswith('^\\s*(?:#![^\\n]*\\n)?\\s*"""') else re.M)
        if m:
            return m.group(1).strip().splitlines()[0][:160]
    return ""


def rank(task: str, files: list[str] | None = None, top: int = 8) -> list[tuple[str, str, float]]:
    want = words(task)
    named = set(re.findall(r"[\w./-]+\.\w+|\b[a-z][\w-]+/[\w./-]+", task))
    alias = aliased(task)
    code = {".py", ".js", ".html", ""}
    out = []
    for f in files if files is not None else tracked():
        parts = words(f.replace("/", " ").replace("_", " ").replace("-", " ").replace(".", " "))
        desc = describe(f)
        score = 3.0 * len(want & parts) + 1.5 * len(want & words(desc)) + (10.0 if any(n in f for n in named) else 0.0)
        hit = next((i for i, a in enumerate(alias) if f == a or (a.endswith("/") and f.startswith(a))), None)
        if hit is not None:
            score += 12.0 - hit
        if score:
            score += 0.4 * min(len(want & _body_words(f)), 5) + (0.5 if pathlib.Path(f).suffix in code else 0.0)
            out.append((f, desc, score - 0.001 * f.count("/")))
    return sorted(out, key=lambda x: -x[2])[:top]


def lessons(task: str, top: int = 5) -> list[str]:
    want = words(task)
    try:
        lines = [x[2:].strip() for x in (ROOT / "LESSONS.md").read_text("utf-8").splitlines() if x.startswith("- ")]
    except OSError:
        return []
    scored = sorted(((len(want & words(x)), i, x) for i, x in enumerate(lines)), key=lambda t: (-t[0], -t[1]))
    return [x for s, _, x in scored if s][:top]


def checks(files: list[str]) -> list[str]:
    seen = []
    for rx, what in CHECKS:
        if any(re.search(rx, f) for f in files) and what not in seen:
            seen.append(what)
    return seen + ALWAYS


def build(task: str) -> dict:
    files = rank(task)
    return {"task": task, "files": [{"path": f, "what": d} for f, d, _ in files], "lessons": lessons(task), "checks": checks([f for f, _, _ in files])}


def markdown(b: dict) -> str:
    out = [f"# Task\n{b['task']}\n", "# How to work (in this order)",
           "1. Read the files below that matter, and AGENTS.md. Say in three lines which files you will change and which test proves it.",
           "2. Write or extend the test first, and see it fail for the right reason.",
           "3. Make the smallest change that passes it. Match the surrounding code: names, comments, plain words.",
           "4. Run every check in \"Done means\". Fix what fails; never skip, weaken or fake a check.",
           "5. Re-read the diff as a strict reviewer, then report what changed, what you ran, and what you could not verify.\n",
           "# Where it most likely lives"]
    out += [f"- `{f['path']}`" + (f": {f['what']}" if f["what"] else "") for f in b["files"]] or ["- (no file matched: start from AGENTS.md section 2)"]
    if b["lessons"]:
        out += ["\n# Lessons that apply (from LESSONS.md)"] + [f"- {x}" for x in b["lessons"]]
    out += ["\n# Done means"] + [f"- {x}" for x in b["checks"]]
    out += ["\n# Never", "- commit anything from vault/ or .env; name a real person, employer or document; print a placeholder a user must guess",
            "- add a dependency or a network call without saying why; leave a generated file out of date"]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    flags = {a for a in argv if a.startswith("--")}
    task = " ".join(a for a in argv if not a.startswith("--")).strip()
    if not task:
        print(__doc__)
        return 2
    b = build(task)
    if "--files" in flags:
        print("\n".join(f["path"] for f in b["files"]))
    elif "--json" in flags:
        print(json.dumps(b, indent=1))
    else:
        print(markdown(b), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
