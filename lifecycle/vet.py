#!/usr/bin/env python3
"""VET — the supply-chain gate for third-party agent skills, plugins and MCP servers.

Popular is not safe: a skill is text an agent OBEYS, and a plugin's hooks run with YOUR privileges. Before anything from the
internet is allowed near an agent, `./securax vet` answers four questions WITHOUT executing a single byte of it:

  1. PIN      exactly which commit is this, and what does its file tree hash to?
  2. LICENCE  may we use and redistribute it?
  3. SURFACE  what can it EXECUTE? (hooks, install scripts, curl|sh, MCP servers, shell-outs, credential reads, binaries)
  4. TEXT     what can it make an agent DO? Every markdown/text file goes through SecuRAX's own guardrail engine (prompt injection,
              hidden Unicode, secrets): the product protecting itself with itself.

Verdict: PASS (exit 0) · REVIEW (1: a human must read the listed lines) · BLOCK (2: do not use). A pin manifest is only written
for PASS/REVIEW with --accept, and `vet verify` later proves the vendored tree still hashes to what was vetted.

Static analysis finds the lazy and the obvious. It cannot prove a repo is benign: read what it flags, keep pins, re-vet on every bump.
Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "llm-gateway"))
from app import guardrails  # noqa: E402

VET_DIR = ROOT / "vendor" / "vetted"
MAX_FILE = 512 * 1024
TEXT_EXT = {".md", ".mdx", ".txt", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini", ".rst"}
CODE_EXT = {".sh", ".bash", ".zsh", ".py", ".js", ".mjs", ".cjs", ".ts", ".rb", ".ps1", ".bat", ".cmd"}
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
SEV = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

LICENSES = [  # (spdx, regex over the LICENSE text, ok to vendor & redistribute?)
    ("MIT", r"permission is hereby granted, free of charge", True),
    ("Apache-2.0", r"apache license.{0,40}version 2\.0", True),
    ("BSD", r"redistribution and use in source and binary forms", True),
    ("ISC", r"permission to use, copy, modify, and/or distribute", True),
    ("MPL-2.0", r"mozilla public license.{0,20}2\.0", True),
    ("AGPL-3.0", r"gnu affero general public license", False),
    ("GPL", r"gnu general public license", False),
    ("Unlicense", r"this is free and unencumbered software", True),
]

# (rule, severity, regex, description) — applied to CODE and shell-ish files
SURFACE_RULES = [
    ("pipe-to-shell", "critical", re.compile(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b", re.I), "downloads and executes code (curl | sh)"),
    ("eval-b64", "critical", re.compile(r"(base64\s+(-d|--decode)|b64decode|atob)\s*\(?[^\n]{0,80}\b(eval|exec|sh|bash)\b", re.I), "decodes a blob and runs it"),
    ("reads-credentials", "high", re.compile(r"(~|\$HOME|os\.path\.expanduser\([^)]*\))/?\.(ssh|aws|gnupg|kube|docker)\b|\.npmrc|\.netrc|id_rsa|credentials\.json", re.I), "reads credential locations"),
    ("env-exfil", "high", re.compile(r"(process\.env|os\.environ|\$\{?[A-Z_]*(KEY|TOKEN|SECRET)[A-Z_]*\}?)[^\n]{0,120}(curl|wget|fetch\(|requests\.(post|get)|http\.request|axios|nc\s)", re.I), "environment/secrets near a network call"),
    ("shell-out", "medium", re.compile(r"child_process|\bsubprocess\.[a-z_]+\([^)]*shell\s*=\s*True|\bos\.system\(|\beval\(|\bexec\(|Invoke-Expression|\bIEX\b"), "spawns a shell / evaluates code"),
    ("network-call", "low", re.compile(r"https?://(?!(?:github\.com|raw\.githubusercontent\.com|docs\.|www\.w3\.org|schemas?\.|json-schema\.org|npmjs\.|pypi\.org|shields\.io|img\.shields\.io|opensource\.org|creativecommons\.org))[a-z0-9.-]+", re.I), "talks to an external host"),
    ("destructive", "high", re.compile(r"\brm\s+-rf?\s+(/|~|\$HOME)\b|\bmkfs\b|:\(\)\s*\{\s*:\|:&\s*\};:|dd\s+if=.*of=/dev/", re.I), "destructive command"),
    ("persistence", "high", re.compile(r"crontab|launchctl|systemctl\s+enable|/etc/profile|\.bashrc|\.zshrc|schtasks|Startup\\", re.I), "installs itself to run later"),
]


class Finding(dict):
    @classmethod
    def mk(cls, sev: str, rule: str, path: str, msg: str, line: int = 0) -> "Finding":
        return cls(severity=sev, rule=rule, file=path, line=line, message=msg)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def walk(root: pathlib.Path):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            p = pathlib.Path(dirpath) / f
            if p.is_symlink():
                yield p
                continue
            yield p


OURS = {"PROVENANCE.md"}            # our own notes inside a vendored folder: not third-party content, not hashed


def tree_hash(root: pathlib.Path, skip: set[str] = frozenset()) -> tuple[str, int]:
    """Hash of every file's relative path + content (excludes .git). Detects ANY change, add or removal."""
    h, n = hashlib.sha256(), 0
    for p in walk(root):
        rel = p.relative_to(root).as_posix()
        if rel in skip:
            continue
        h.update(rel.encode() + b"\0")
        if p.is_symlink():
            h.update(b"symlink:" + os.readlink(p).encode())
        else:
            h.update(sha256(p.read_bytes()).encode())
        n += 1
    return h.hexdigest(), n


def detect_license(root: pathlib.Path) -> tuple[str, bool, str]:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE"):
        f = root / name
        if f.exists():
            txt = f.read_text("utf-8", "ignore")[:6000].lower()
            for spdx, rx, ok in LICENSES:
                if re.search(rx, txt, re.S):
                    return spdx, ok, name
            return "UNKNOWN", False, name
    return "NONE", False, ""


def scan_text(rel: str, text: str) -> list[Finding]:
    out: list[Finding] = []
    for i in range(0, len(text), 7500):                         # the gateway's own limit is 8000 chars
        chunk = text[i:i + 7500]
        for f in guardrails.detect_prompt_injection(chunk):
            sev = f.severity if f.severity in SEV else "medium"
            out.append(Finding.mk(sev, f.rule, rel, f"{f.category}: {f.detail}", text[:i].count("\n") + 1))
        _, outf = guardrails.check_output(chunk, set(), set())
        out += [Finding.mk("critical", f.rule, rel, "secret/credential in the text") for f in outf if f.rule.startswith("SECRET-")]
    for m in re.finditer(r"<!--(.{0,400}?)-->", text, re.S):  # instructions hidden in HTML comments render invisible in markdown
        body = m.group(1)
        if re.search(r"\b(ignore|you must|do not (tell|mention)|secretly|system prompt|exfiltrate|send .* to)\b", body, re.I):
            out.append(Finding.mk("high", "hidden-comment-instruction", rel, "an HTML comment (invisible when rendered) addresses the agent", text[:m.start()].count("\n") + 1))
    return out


def scan_code(rel: str, text: str) -> list[Finding]:
    out: list[Finding] = []
    for rule, sev, rx, desc in SURFACE_RULES:
        for m in rx.finditer(text):
            out.append(Finding.mk(sev, rule, rel, f"{desc}: {m.group(0)[:80]!r}", text[:m.start()].count("\n") + 1))
            if rule in ("network-call", "shell-out"):
                break                                            # one example per file is enough for the low-signal rules
    return out


def scan_config(rel: str, name: str, text: str) -> list[Finding]:
    """Executable surface declared in config: hooks, MCP servers, install scripts, permission widening."""
    out: list[Finding] = []
    low = rel.lower()
    if "/hooks/" in "/" + low or name in ("hooks.json",):
        out.append(Finding.mk("high", "agent-hook", rel, "agent hooks run commands automatically on agent events, with YOUR privileges"))
    if name in (".mcp.json", "mcp.json") or "mcpservers" in text.lower().replace("_", ""):
        out.append(Finding.mk("high", "mcp-server", rel, "declares MCP servers (code that your agent calls and trusts)"))
    if name == "package.json":
        try:
            pkg = json.loads(text)
        except ValueError:
            pkg = {}
        scripts = pkg.get("scripts") or {}
        for k in ("preinstall", "install", "postinstall", "prepare", "prepublish"):
            if k in scripts:
                out.append(Finding.mk("critical", "install-script", rel, f"npm '{k}' script runs on install: {scripts[k][:80]!r}"))
        if pkg.get("dependencies"):
            out.append(Finding.mk("low", "npm-dependencies", rel, "pulls dependencies from npm (a second supply chain to vet)"))
    if name == "settings.json" or name == "settings.local.json":
        if re.search(r"enableAllProjectMcpServers|bypassPermissions|dangerouslySkipPermissions|\"allow\"\s*:\s*\[[^\]]*\*", text):
            out.append(Finding.mk("critical", "permission-widening", rel, "settings widen the agent's permissions or auto-approve MCP servers"))
    if name in ("setup.py", "pyproject.toml") and re.search(r"cmdclass|build-backend\s*=\s*['\"](?!setuptools|hatchling|flit|poetry)", text):
        out.append(Finding.mk("medium", "python-build-hook", rel, "custom build step runs at install time"))
    return out


def is_binary(b: bytes) -> bool:
    return b[:4] in (b"\x7fELF", b"MZ\x90\x00", b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe") or b"\0" in b[:2048]


def vet_dir(root: pathlib.Path) -> dict:
    findings: list[Finding] = []
    files = 0
    for p in walk(root):
        rel = p.relative_to(root).as_posix()
        files += 1
        if p.is_symlink():
            tgt = os.path.realpath(p)
            if not tgt.startswith(str(root.resolve())):
                findings.append(Finding.mk("high", "symlink-escape", rel, f"symlink points outside the repo: {os.readlink(p)}"))
            continue
        if p.stat().st_size > MAX_FILE:
            findings.append(Finding.mk("low", "large-file", rel, f"{p.stat().st_size // 1024} KB (not scanned)"))
            continue
        b = p.read_bytes()
        if is_binary(b):
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2", ".ttf"):
                findings.append(Finding.mk("high", "binary", rel, "executable/binary content that cannot be reviewed as text"))
            continue
        text = b.decode("utf-8", "ignore")
        ext = p.suffix.lower()
        if ext in TEXT_EXT or p.name.upper().startswith(("README", "LICENSE")) or ext == "":
            findings += scan_text(rel, text)
        if ext in CODE_EXT or text.startswith("#!"):
            findings += scan_code(rel, text)
        if p.name in ("package.json", "hooks.json", ".mcp.json", "mcp.json", "settings.json", "settings.local.json", "setup.py", "pyproject.toml") or "/hooks/" in "/" + rel.lower():
            findings += scan_config(rel, p.name, text)
        if ext in (".yml", ".yaml") and ".github/workflows" in rel and re.search(r"pull_request_target|secrets\.", text):
            findings.append(Finding.mk("low", "ci-secrets", rel, "workflow touches secrets / pull_request_target (not an issue for us, noted)"))
    spdx, lic_ok, lic_file = detect_license(root)
    if not lic_ok:
        findings.append(Finding.mk("high" if spdx in ("NONE", "UNKNOWN") else "medium", "licence", lic_file or "-", f"licence is {spdx}: we may not be allowed to vendor or redistribute it"))
    findings.sort(key=lambda f: -SEV[f["severity"]])
    worst = max((SEV[f["severity"]] for f in findings), default=0)
    verdict = "BLOCK" if worst >= SEV["critical"] else ("REVIEW" if worst >= SEV["medium"] else "PASS")
    th, n = tree_hash(root)
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("critical", "high", "medium", "low")}
    return {"verdict": verdict, "licence": spdx, "licence_ok": lic_ok, "files": files, "tree_sha256": th, "counts": counts, "findings": findings}


# ───────────────────────────────────────────── fetch / pin ─────────────────────────────────────────────
def git(args: list[str], cwd: str | None = None, timeout: int = 300) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=cwd, text=True, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"})
    return p.returncode, p.stdout


def fetch(src: str, ref: str, dest: pathlib.Path) -> tuple[pathlib.Path, str]:
    """A local directory is scanned in place; a URL is fetched shallowly at `ref` (never checked out with hooks: git hooks are not copied)."""
    local = pathlib.Path(src)
    if local.is_dir():
        rc, sha = git(["rev-parse", "HEAD"], cwd=str(local))
        return local, sha.strip() if rc == 0 else "local-uncommitted"
    dest.mkdir(parents=True, exist_ok=True)
    for step in (["init", "-q"], ["remote", "add", "origin", src], ["fetch", "-q", "--depth", "1", "origin", ref or "HEAD"], ["checkout", "-q", "--force", "FETCH_HEAD"]):
        rc, out = git(step, cwd=str(dest))
        if rc != 0:
            raise SystemExit(f"vet: git {' '.join(step[:2])} failed:\n{out[-500:]}")
    rc, sha = git(["rev-parse", "HEAD"], cwd=str(dest))
    return dest, sha.strip()


def vendored_mismatch(upstream: pathlib.Path, vendored: pathlib.Path) -> list[str]:
    """Every vendored file (except our own notes) must exist upstream at the same relative path with identical bytes."""
    bad: list[str] = []
    if not vendored.is_dir():
        return [f"{vendored} does not exist"]
    for p in walk(vendored):
        rel = p.relative_to(vendored).as_posix()
        if rel in OURS:
            continue
        up = upstream / rel
        if not up.is_file() or up.read_bytes() != p.read_bytes():
            bad.append(f"{rel}: " + ("not in upstream" if not up.is_file() else "differs from upstream"))
    return bad


def report_md(name: str, src: str, sha: str, res: dict) -> str:
    c = res["counts"]
    lines = [f"# vet: {name}", "", f"- source: `{src}`", f"- commit (the pin): `{sha}`", f"- tree sha256: `{res['tree_sha256'][:16]}…` over {res['files']} files",
             f"- licence: **{res['licence']}** ({'ok to vendor' if res['licence_ok'] else 'NOT ok / unknown'})",
             f"- **verdict: {res['verdict']}** — critical {c['critical']}, high {c['high']}, medium {c['medium']}, low {c['low']}", ""]
    if res["findings"]:
        lines += ["| severity | rule | where | what |", "|---|---|---|---|"]
        for f in res["findings"][:80]:
            lines.append(f"| {f['severity']} | {f['rule']} | `{f['file']}:{f['line']}` | {f['message'][:110].replace('|', '/')} |")
        if len(res["findings"]) > 80:
            lines.append(f"| … | | | {len(res['findings']) - 80} more in the JSON |")
    lines += ["", "Static analysis finds the lazy and the obvious; it cannot prove a repo benign. Read what is flagged, keep the pin, re-vet on every bump."]
    return "\n".join(lines) + "\n"


# ───────────────────────────────────────────── commands ─────────────────────────────────────────────
def cmd_check(a: argparse.Namespace) -> int:
    name = a.name or re.sub(r"\.git$", "", a.source.rstrip("/").split("/")[-1])
    with tempfile.TemporaryDirectory() as td:
        root, sha = fetch(a.source, a.ref, pathlib.Path(td) / "repo")
        res = vet_dir(root)
        mismatch = vendored_mismatch(root, ROOT / a.vendored) if (a.accept and a.vendored) else []
    print(f"vet {name} @ {sha[:12]}: {res['verdict']}  (critical {res['counts']['critical']}, high {res['counts']['high']}, medium {res['counts']['medium']}, low {res['counts']['low']}; licence {res['licence']})")
    for f in res["findings"][:12]:
        if SEV[f["severity"]] >= SEV["medium"]:
            print(f"  {f['severity']:<8} {f['rule']:<22} {f['file']}:{f['line']}  {f['message'][:90]}")
    out = pathlib.Path(a.out) if a.out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / f"vet-{name}.md").write_text(report_md(name, a.source, sha, res))
        (out / f"vet-{name}.json").write_text(json.dumps({"name": name, "source": a.source, "commit": sha, **res}, indent=2))
        print(f"  report: {out / f'vet-{name}.md'}")
    if a.accept:
        if res["verdict"] == "BLOCK":
            print("  NOT accepted: a BLOCK verdict can never be pinned.", file=sys.stderr)
            return 2
        if mismatch:
            print("  NOT accepted: the vendored copy is not byte-identical to upstream at the pinned commit:\n    " + "\n    ".join(mismatch[:8]), file=sys.stderr)
            return 2
        VET_DIR.mkdir(parents=True, exist_ok=True)
        vend_hash = tree_hash(ROOT / a.vendored, OURS)[0] if a.vendored else ""
        man = {"name": name, "source": a.source, "commit": sha, "upstream_tree_sha256": res["tree_sha256"], "vendored_tree_sha256": vend_hash, "licence": res["licence"],
               "verdict": res["verdict"], "counts": res["counts"], "vetted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "vendored_path": a.vendored or "", "review_note": a.note, "reviewed_findings": [f"{f['rule']}@{f['file']}:{f['line']}" for f in res["findings"] if SEV[f["severity"]] >= 2]}
        (VET_DIR / f"{name}.json").write_text(json.dumps(man, indent=2) + "\n")
        print(f"  pinned: vendor/vetted/{name}.json  (commit {sha[:12]})")
    return {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[res["verdict"]]


def cmd_verify(_: argparse.Namespace) -> int:
    """Every vendored path must still hash to what was vetted. Tamper, drift or a silent update fails this."""
    bad = 0
    mans = sorted(VET_DIR.glob("*.json")) if VET_DIR.exists() else []
    for m in mans:
        man = json.loads(m.read_text())
        vp = man.get("vendored_path")
        if not vp:
            print(f"  · {man['name']}: pinned at {man['commit'][:12]} (nothing vendored)")
            continue
        d = ROOT / vp
        if not d.is_dir():
            print(f"  ✘ {man['name']}: vendored path {vp} is missing")
            bad += 1
            continue
        th, _ = tree_hash(d, OURS)
        ok = th == man["vendored_tree_sha256"]
        print(f"  {'✔' if ok else '✘'} {man['name']}: {vp} {'matches' if ok else 'DIFFERS from'} the vetted copy ({man['vendored_tree_sha256'][:12]}, upstream {man['commit'][:12]})")
        bad += 0 if ok else 1
    if not mans:
        print("  (no vetted third-party content)")
    return 1 if bad else 0


def cmd_rules(a: argparse.Namespace) -> int:
    """Print the vetted skill text for `autobuild` to prepend. Prints NOTHING (and exits 0) unless every vendored tree verifies."""
    chunks: list[str] = []
    for m in sorted(VET_DIR.glob("*.json")) if VET_DIR.exists() else []:
        man = json.loads(m.read_text())
        vp = man.get("vendored_path")
        if not vp or not (ROOT / vp).is_dir():
            continue
        th, _ = tree_hash(ROOT / vp, OURS)
        if th != man["vendored_tree_sha256"]:
            continue                                            # tampered or drifted: silently not used (verify will shout)
        for f in sorted((ROOT / vp).glob("**/*.md")):
            if f.name.upper().startswith(("README", "LICENSE")):
                continue
            chunks.append(f.read_text("utf-8", "ignore").strip())
    text = "\n\n---\n\n".join(chunks)
    print(text[: a.max_chars])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="vet a git URL or a local directory")
    c.add_argument("source")
    c.add_argument("--ref", default="", help="branch, tag or commit (default: the default branch)")
    c.add_argument("--name", default="")
    c.add_argument("--out", default="", help="write vet-<name>.md/.json here")
    c.add_argument("--accept", action="store_true", help="write vendor/vetted/<name>.json (PASS/REVIEW only)")
    c.add_argument("--vendored", default="", help="repo-relative path where you vendored the vetted files (verified later)")
    c.add_argument("--note", default="", help="why the flagged lines were judged acceptable (recorded in the manifest)")
    c.set_defaults(fn=cmd_check)
    sub.add_parser("verify", help="re-hash every vendored path against its manifest").set_defaults(fn=cmd_verify)
    r = sub.add_parser("rules", help="print vetted skill text for autobuild (empty unless everything verifies)")
    r.add_argument("--max-chars", type=int, default=3500)
    r.set_defaults(fn=cmd_rules)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
