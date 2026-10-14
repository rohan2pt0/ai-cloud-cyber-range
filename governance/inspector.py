#!/usr/bin/env python3
"""Look inside third-party software BEFORE you trust it: a static, sandboxed behavioural report, and what CHANGED between two versions.

    ./securax inspect PATH                 a folder, an npm tarball (.tgz) or any file: what can it do, where does it talk, does it run things at install
    ./securax inspect npm:name@1.2.3       fetch the package (no install scripts are run) and inspect it
    ./securax inspect --diff OLD NEW       what NEW can do that OLD could not (the supply-chain attack signature): new network, new programs run,
                                           new install hooks, new hard-coded addresses, new binaries
    ./securax inspect --watch              check every pinned third-party package in integrations/rea/watchlist.json against the registry; when a newer
                                           version exists, inspect both and report the drift (exit 2 = a human should look)
    ./securax inspect --watch --schedule weekly|off      let your own crontab do that every week (opt-in; nothing leaves the machine but registry lookups)
    ./securax inspect --build              build the sandbox image (once; needs Docker and internet)
    ./securax inspect --selftest           prove the sandbox really has no network, a read-only disk and no privileges

The engine is REA ("Reverse Engineer Anything", MIT, github.com/morluto/rea, npm rea-agents), pinned to one version by lockfile with integrity hashes and
installed WITHOUT install scripts. It only ever runs inside a container with NO network, a READ-ONLY root, NO capabilities, a non-root user and hard
limits; the target is mounted read-only; REA's JavaScript analysis parses code as inert text and never executes it. Dynamic analysis (running the target)
is deliberately NOT offered here. Without Docker/the image the built-in checks still run, and the report says so.

Honest limits: this is STATIC triage by heuristics. It finds the usual shapes of trouble (an install hook that runs a program, a library that suddenly
opens network connections, a hard-coded IP, an encoded blob handed to eval); it does not prove software safe, and native code (binaries) is only
fingerprinted, because disassembly needs Hopper / Ghidra / IDA, which are not in the sandbox image. Use it to decide where to look, not as a verdict
you can show an auditor on its own.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
REA_DIR = ROOT / "integrations" / "rea"
REA_VERSION = "6.5.0"
IMAGE = f"securax-rea:{REA_VERSION}"
WATCHLIST = REA_DIR / "watchlist.json"
HOME = pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")
CRON_TAG = "# securax-inspect-watch"
# Everything REA runs under. NO network, read-only root, no capabilities, non-root, bounded memory/processes/time.
SANDBOX = ["--network", "none", "--read-only", "--tmpfs", "/tmp:rw,size=256m", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "--pids-limit", "256", "--memory", "2g", "--cpus", "2"]
MAX_FILES, MAX_BYTES, MAX_TEXT = 20000, 500 * 1024 * 1024, 5 * 1024 * 1024
HIGH, MEDIUM, INFO = 3, 2, 1
SEVERITY = {HIGH: "HIGH", MEDIUM: "MEDIUM", INFO: "info"}

NET = {"net", "http", "https", "http2", "dgram", "tls", "dns", "ws", "websocket", "axios", "node-fetch", "got", "undici", "request", "superagent",
       "needle", "socket.io-client", "xmlhttprequest", "cross-fetch", "isomorphic-fetch", "playwright-core", "puppeteer"}
EXEC = {"child_process", "cross-spawn", "execa", "shelljs", "node-pty", "@lydell/node-pty", "spawn-sync", "foreground-child"}
FS = {"fs", "fs-extra", "graceful-fs", "fs/promises", "rimraf", "del"}
ENV = {"os"}
DYN = {"vm", "vm2", "isolated-vm"}
NATIVE = {"ffi-napi", "koffi", "node-gyp-build", "bindings", "node-addon-api", "prebuild-install", "node-pre-gyp"}
HOOKS = ("preinstall", "install", "postinstall", "prepare", "preuninstall", "postuninstall")
BENIGN_HOSTS = ("registry.npmjs.org", "github.com", "raw.githubusercontent.com", "nodejs.org", "npmjs.com", "www.w3.org", "json-schema.org", "example.com",
                "localhost", "127.0.0.1", "opensource.org", "creativecommons.org", "mozilla.org", "developer.mozilla.org", "stackoverflow.com", "w3.org",
                "schemas.xmlsoap.org", "xmlns.com", "purl.org", "apache.org", "gnu.org", "eslint.org", "tc39.es", "ecma-international.org")
URL_RE = re.compile(r"""https?://[^\s'"`)<>\\]+""")
IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
B64_RE = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")
MOD_RE = re.compile(r"""(?:require\s*\(\s*|from\s+|import\s+|import\s*\(\s*)['"]([^'"\n]+)['"]""")
HOSTOPT_RE = re.compile(r"""\b(?:hostname|host)\s*:\s*['"]([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)['"]""")
COMPUTED_RE = re.compile(r"""(?:\brequire|\bimport)\s*\(\s*(?!['"`])[A-Za-z_$(]""")
EVAL_RE = re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(|(?<![\w.])Function\s*\(\s*['\"`]")
ENV_RE = re.compile(r"\bprocess\.env\b")
TEXT_EXT = {".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".sh", ".py", ".ps1", ".bat", ".cmd", ".rb", ".pl", ".php"}
BIN_EXT = {".node", ".so", ".dll", ".dylib", ".exe", ".bin", ".class", ".jar", ".wasm"}
MAGIC = {b"\x7fELF": "ELF executable/library", b"MZ": "Windows PE", b"\xcf\xfa\xed\xfe": "Mach-O", b"\xce\xfa\xed\xfe": "Mach-O", b"\xca\xfe\xba\xbe": "Mach-O universal / Java class",
         b"\x00asm": "WebAssembly"}


# ───────────────────────────────────────────── getting the target onto disk, safely ─────────────────────────────────────────────
def safe_extract(archive: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    """Unpack a tar/tgz without trusting it: no absolute paths, no '..', no links or devices, bounded size and count. Returns the folder to inspect."""
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    with tarfile.open(archive) as tf:
        members = tf.getmembers()
        if len(members) > MAX_FILES:
            raise ValueError(f"archive has {len(members)} entries (limit {MAX_FILES})")
        base = dest.resolve()
        for m in members:
            target = (dest / m.name).resolve()
            if not str(target).startswith(str(base) + os.sep) and target != base:
                raise ValueError(f"unsafe path in archive: {m.name}")
            if m.issym() or m.islnk() or m.isdev() or m.isfifo():
                continue                                                     # links and devices are never extracted
            total += max(m.size, 0)
            if total > MAX_BYTES:
                raise ValueError("archive expands beyond the size limit")
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(m)
                with open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
    tops = [p for p in dest.iterdir()]
    return tops[0] if len(tops) == 1 and tops[0].is_dir() else dest           # npm tarballs wrap everything in package/


def tree_digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    if path.is_file():
        h.update(path.read_bytes())
        return h.hexdigest()
    for p in sorted(x for x in path.rglob("*") if x.is_file() and not x.is_symlink()):
        h.update(str(p.relative_to(path)).encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def resolve(target: str, work: pathlib.Path) -> tuple[pathlib.Path, str, str]:
    """-> (folder or file to inspect, label, kind)."""
    if target.startswith("npm:"):
        if not shutil.which("npm"):
            raise SystemExit("npm is needed to fetch an npm package:  sudo apt install nodejs npm")
        r = subprocess.run(["npm", "pack", target[4:], "--ignore-scripts", "--silent", "--pack-destination", str(work)], capture_output=True, text=True, timeout=300)
        if r.returncode:
            raise SystemExit(f"could not fetch {target}: {r.stderr.strip()[-300:]}")
        tgz = work / r.stdout.strip().splitlines()[-1]
        return safe_extract(tgz, work / "x"), target[4:], "npm package"
    p = pathlib.Path(target).expanduser()
    if not p.exists():
        raise SystemExit(f"{target}: no such file or folder")
    if p.is_dir():
        return p, p.name or str(p), "folder"
    if tarfile.is_tarfile(p):
        return safe_extract(p, work / "x"), p.name, "archive"
    return p, p.name, "file"


# ───────────────────────────────────────────── the built-in static checks (always run) ─────────────────────────────────────────────
def scan_tree(path: pathlib.Path) -> dict:
    """Facts read straight from the files: install hooks, URLs and IPs, encoded blobs, eval, environment use, embedded binaries."""
    out = {"files": 0, "hooks": {}, "urls": set(), "ips": set(), "eval": 0, "env": 0, "base64_blobs": 0, "binaries": [], "package": {}, "mods": set(), "computed": 0}
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file() and not p.is_symlink())
    for p in files[:MAX_FILES]:
        out["files"] += 1
        rel = p.name if path.is_file() else str(p.relative_to(path))
        try:
            head = p.open("rb").read(8)
        except OSError:
            continue
        kind = next((v for k, v in MAGIC.items() if head.startswith(k)), None)
        if kind and not rel.endswith((".js", ".json", ".md", ".txt")):
            out["binaries"].append({"path": rel, "type": kind})
        elif p.suffix.lower() in BIN_EXT and kind is None and p.suffix.lower() in {".node", ".so", ".dll", ".dylib", ".exe"}:
            out["binaries"].append({"path": rel, "type": p.suffix.lower() + " file"})
        if p.name == "package.json" and p.parent == (path if path.is_dir() else p.parent):
            try:
                pj = json.loads(p.read_text("utf-8", "replace"))
                out["package"] = {"name": pj.get("name"), "version": pj.get("version")}
                out["hooks"] = {k: v for k, v in (pj.get("scripts") or {}).items() if k in HOOKS}
            except ValueError:
                pass
        if p.suffix.lower() not in TEXT_EXT and not (kind is None and p.stat().st_size < 4096 and p.suffix == ""):
            continue
        if p.stat().st_size > MAX_TEXT:
            continue
        txt = p.read_text("utf-8", "replace")
        for u in URL_RE.findall(txt):
            host = re.sub(r"^https?://", "", u).split("/")[0].split(":")[0].lower()
            if not host.endswith(BENIGN_HOSTS) and "." in host:
                out["urls"].add(u.rstrip(".,;"))
        for ip in IP_RE.findall(txt):
            if ip not in ("127.0.0.1", "0.0.0.0", "255.255.255.255", "255.255.255.0", "1.0.0.0", "0.0.0.1") and not ip.startswith(("0.", "127.")) and not p.name.endswith("package.json"):
                out["ips"].add(ip)
        if p.suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx"}:
            out["mods"].update(re.sub(r"^node:", "", m) for m in MOD_RE.findall(txt) if not m.startswith((".", "/")))
            out["computed"] += len(COMPUTED_RE.findall(txt))
        for h in HOSTOPT_RE.findall(txt):
            if not h.lower().endswith(BENIGN_HOSTS) and not re.fullmatch(r"\d+(?:\.\d+){3}", h):
                out["urls"].add("host:" + h)
        out["eval"] += len(EVAL_RE.findall(txt))
        out["env"] += len(ENV_RE.findall(txt))
        out["base64_blobs"] += len(B64_RE.findall(re.sub(r"sourceMappingURL=data:[^\s]+", "", txt)))
    out["urls"], out["ips"], out["mods"] = sorted(out["urls"]), sorted(out["ips"]), sorted(out["mods"])
    return out


def strings_scan(path: pathlib.Path) -> dict:
    """For a file the JavaScript engine cannot read (a native binary, an installer): printable strings -> URLs and IPs, plus a fingerprint."""
    data = path.read_bytes()[:50 * 1024 * 1024]
    txt = "\n".join(m.decode("ascii", "replace") for m in re.findall(rb"[\x20-\x7e]{6,}", data))
    urls = sorted({u.rstrip(".,;") for u in URL_RE.findall(txt) if not re.sub(r"^https?://", "", u).split("/")[0].lower().endswith(BENIGN_HOSTS)})
    ips = sorted(ip for ip in set(IP_RE.findall(txt)) if not ip.startswith(("0.", "127.", "255.")))
    kind = next((v for k, v in MAGIC.items() if data.startswith(k)), "unknown file type")
    return {"type": kind, "urls": urls[:50], "ips": ips[:50]}


# ───────────────────────────────────────────── the REA engine (sandboxed) ─────────────────────────────────────────────
def docker_ready() -> bool:
    return bool(shutil.which("docker")) and subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def image_present() -> bool:
    return docker_ready() and subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode == 0


def build_image() -> int:
    if not docker_ready():
        print("Docker is not running. Start Docker Desktop (Windows: with WSL integration), then run this again.")
        return 1
    print(f"Building the sandbox image {IMAGE} (REA {REA_VERSION}, from a lockfile with integrity hashes, no install scripts). Needs internet once.")
    return subprocess.run(["docker", "build", "-t", IMAGE, str(REA_DIR)]).returncode


def run_rea(target: pathlib.Path, timeout: int = 300) -> dict:
    """Run REA's static JavaScript analysis on `target` inside the sandbox. Returns the evidence record, or {} with an error note."""
    mount = target if target.is_dir() else target.parent
    inside = "/target" if target.is_dir() else f"/target/{target.name}"
    cmd = ["docker", "run", "--rm", *SANDBOX, "-v", f"{mount}:/target:ro", IMAGE, "analyze-javascript-application", inside, "--format", "json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"REA timed out after {timeout}s"}
    last: dict = {}
    for ln in r.stdout.splitlines():
        ln = ln.strip()
        if ln.startswith("{") and not ln.startswith('{"rea_progress"'):
            try:
                last = json.loads(ln)
            except ValueError:
                continue
    if "normalized_result" not in last:
        return {"error": (last.get("message") or r.stderr.strip()[-300:] or f"REA exit {r.returncode}")[:300]}
    return last


def parse_evidence(ev: dict) -> dict:
    """Pull what matters out of REA's evidence graph: imported modules (static, dynamic, computed), URLs/routes, the package identity."""
    nr = ev.get("normalized_result", {})
    mods: set[str] = set()
    computed: list[str] = []
    endpoints: set[str] = set()
    pkg: dict = {}
    for n in nr.get("graph", {}).get("nodes", []):
        kind, key = n.get("kind"), str(n.get("identity", {}).get("key", ""))
        if kind == "javascript-module":
            m = re.match(r"^(?:require|static-import|dynamic-import|external):(.+)$", key)
            if not m:
                continue
            spec = m.group(1)
            if key.startswith("dynamic-import:") and not any(o.get("properties", {}).get("specifier") for o in n.get("observations", [])):
                computed.append(spec)
            elif not spec.startswith(("./", "../", "import(")):
                mods.add(re.sub(r"^node:", "", spec))
        elif kind == "endpoint":
            try:
                v = json.loads(key)
                if isinstance(v, list) and len(v) > 1:
                    endpoints.add(str(v[1]))
            except ValueError:
                pass
            for o in n.get("observations", []):
                if o.get("properties", {}).get("value"):
                    endpoints.add(str(o["properties"]["value"]))
        elif kind == "package":
            for o in n.get("observations", []):
                pr = o.get("properties", {})
                if pr.get("name"):
                    pkg = {"name": pr.get("name"), "version": pr.get("version")}
    return {"modules": sorted(mods), "computed_imports": computed, "endpoints": sorted(endpoints), "package": pkg,
            "evidence_id": ev.get("evidence_id"), "limitations": nr.get("limitations", [])[:3]}


def capabilities(mods: list[str]) -> dict[str, list[str]]:
    def base(m: str) -> str:
        return m if m.startswith("@") else m.split("/")[0] if m.split("/")[0] in NET | EXEC | ENV | DYN | NATIVE else m
    cap: dict[str, list[str]] = {"network": [], "run_programs": [], "files": [], "environment": [], "dynamic_code": [], "native": []}
    for m in mods:
        for key, group in (("network", NET), ("run_programs", EXEC), ("files", FS), ("environment", ENV), ("dynamic_code", DYN), ("native", NATIVE)):
            if m in group or base(m) in group:
                cap[key].append(m)
    return cap


# ───────────────────────────────────────────── the report ─────────────────────────────────────────────
def build_report(target: str, use_rea: bool = True) -> dict:
    with tempfile.TemporaryDirectory(prefix="securax-inspect-") as td:
        work = pathlib.Path(td)
        path, label, kind = resolve(target, work)
        facts = scan_tree(path) if path.is_dir() else {"files": 1, "hooks": {}, "urls": [], "ips": [], "eval": 0, "env": 0, "base64_blobs": 0, "binaries": [], "package": {}, "mods": [], "computed": 0}
        rep: dict = {"target": label, "kind": kind, "sha256": tree_digest(path), "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "files": facts["files"], "engine": {"name": "built-in checks only", "note": ""}, "modules": facts["mods"], "endpoints": [], "computed_imports": ["(computed)"] * facts["computed"],
                     "package": facts["package"], "hooks": facts["hooks"], "urls": facts["urls"], "ips": facts["ips"], "eval_calls": facts["eval"],
                     "env_reads": facts["env"], "encoded_blobs": facts["base64_blobs"], "binaries": facts["binaries"], "limits": []}
        if path.is_file():
            s = strings_scan(path)
            rep["urls"], rep["ips"] = s["urls"], s["ips"]
            rep["binaries"] = [{"path": path.name, "type": s["type"]}] if s["type"] != "unknown file type" else []
            rep["limits"].append("a single file is fingerprinted (type, hash, strings); disassembly needs Hopper / Ghidra / IDA, which are not in the sandbox image")
        elif use_rea and image_present():
            ev = run_rea(path)
            if "error" in ev:
                rep["engine"]["note"] = "REA could not analyse this: " + ev["error"]
            else:
                p = parse_evidence(ev)
                rep["engine"] = {"name": "REA", "version": REA_VERSION, "image": IMAGE, "evidence_id": p["evidence_id"], "sandbox": "no network, read-only root, no capabilities, non-root"}
                rep["modules"], rep["computed_imports"] = p["modules"], p["computed_imports"]
                rep["endpoints"] = sorted({e for e in p["endpoints"] if re.match(r"^(https?|wss?)://", e)} | set(rep["urls"]))
                rep["package"] = p["package"] or rep["package"]
                rep["limits"] += p["limitations"]
        elif use_rea:
            rep["engine"]["note"] = "the REA sandbox image is not built (./securax inspect --build): imports were read with simple pattern matching instead"
    rep["capabilities"] = capabilities(rep["modules"])
    if rep["env_reads"]:
        rep["capabilities"]["environment"] = sorted(set(rep["capabilities"]["environment"]) | {"process.env"})
    if rep["eval_calls"] or rep["computed_imports"]:
        rep["capabilities"]["dynamic_code"] = sorted(set(rep["capabilities"]["dynamic_code"]) | ({"eval / new Function"} if rep["eval_calls"] else set()) | ({"computed import()"} if rep["computed_imports"] else set()))
    rep["limits"].append("static triage by heuristics: it shows where to look, it does not prove software safe")
    rep["flags"] = flags_for(rep)
    rep["verdict"] = verdict(rep["flags"])
    return rep


def flags_for(r: dict) -> list[dict]:
    f: list[dict] = []
    cap = r["capabilities"]

    def add(sev: int, code: str, text: str) -> None:
        f.append({"severity": SEVERITY[sev], "code": code, "text": text})
    net, ex, dyn = bool(cap["network"]), bool(cap["run_programs"]), bool(cap["dynamic_code"])
    if r["hooks"]:
        runs = ", ".join(f"{k}: {v}" for k, v in r["hooks"].items())
        add(HIGH if (net or ex or r["ips"]) else MEDIUM, "INSTALL_HOOK", f"runs code the moment it is installed ({runs}); npm install scripts are the usual way a malicious package gets in (many legitimate tools have one too: read it, then decide)")
    if net and ex and cap["environment"]:
        add(HIGH, "NET_EXEC_ENV", "can read your environment, open network connections AND run programs: the combination of a stealer")
    if r["ips"] and (net or ex):
        add(HIGH, "HARD_IP", f"talks to or contains a hard-coded address ({', '.join(r['ips'][:3])}): legitimate libraries use names, not raw IPs")
    if r["encoded_blobs"] and dyn:
        add(HIGH, "ENCODED_EVAL", "decodes a large encoded blob and runs it (eval / Function / computed import): the classic way to hide behaviour")
    elif r["encoded_blobs"] or r["eval_calls"]:
        add(MEDIUM, "ENCODED_OR_EVAL", "contains eval / new Function or large encoded blobs, which hide what the code really does")
    if r["computed_imports"]:
        add(MEDIUM, "COMPUTED_IMPORT", "loads modules whose name is computed at run time, so what it imports cannot be read from the code")
    if r["binaries"]:
        add(MEDIUM, "BINARY", f"ships native code ({', '.join(b['path'] for b in r['binaries'][:3])}): only fingerprinted here, not disassembled")
    ext = [u for u in r["urls"] if not u.startswith(("http://localhost", "https://localhost"))]
    if ext and (net or ex):
        add(INFO, "ENDPOINTS", f"mentions {len(ext)} external address(es): {', '.join(ext[:3])}")
    if net:
        add(INFO, "CAP_NETWORK", "can open network connections (" + ", ".join(cap["network"]) + ")")
    if ex:
        add(INFO, "CAP_EXEC", "can run other programs (" + ", ".join(cap["run_programs"]) + ")")
    return f


def verdict(flags: list[dict]) -> str:
    sev = {x["severity"] for x in flags}
    return "BLOCK" if "HIGH" in sev else "REVIEW" if "MEDIUM" in sev else "OK"


def diff_reports(old: dict, new: dict) -> dict:
    """What NEW can do that OLD could not. A library that grows network or exec access in a patch release is the supply-chain attack signature."""
    d: list[dict] = []

    def add(sev: int, code: str, text: str) -> None:
        d.append({"severity": SEVERITY[sev], "code": code, "text": text})
    for key, label, sev in (("network", "open network connections", MEDIUM), ("run_programs", "run other programs", HIGH), ("dynamic_code", "run dynamically built code", MEDIUM),
                            ("native", "load native code", MEDIUM)):
        gained = sorted(set(new["capabilities"][key]) - set(old["capabilities"][key]))
        if gained:
            add(sev, f"NEW_{key.upper()}", f"the new version can now {label} ({', '.join(gained)}) and the old one could not" if not old["capabilities"][key]
                else f"the new version added to what it can do to {label}: {', '.join(gained)}")
    for h in sorted(set(new["hooks"]) - set(old["hooks"])):
        add(HIGH, "NEW_INSTALL_HOOK", f"a new install-time script appeared ({h}: {new['hooks'][h]})")
    for k in sorted(set(new["hooks"]) & set(old["hooks"])):
        if new["hooks"][k] != old["hooks"][k]:
            add(HIGH, "CHANGED_INSTALL_HOOK", f"the install-time script {k} changed")
    ips = sorted(set(new["ips"]) - set(old["ips"]))
    if ips:
        add(HIGH, "NEW_IP", f"new hard-coded address(es): {', '.join(ips)}")
    urls = sorted(set(new["urls"]) - set(old["urls"]))
    if urls:
        add(MEDIUM, "NEW_URL", f"new external address(es): {', '.join(urls[:5])}")
    bins = sorted({b["path"] for b in new["binaries"]} - {b["path"] for b in old["binaries"]})
    if bins:
        add(MEDIUM, "NEW_BINARY", f"new native file(s): {', '.join(bins[:5])}")
    if new["encoded_blobs"] > old["encoded_blobs"] or new["eval_calls"] > old["eval_calls"]:
        add(MEDIUM, "MORE_OBFUSCATION", "more eval / encoded content than before")
    gone = sorted(set(old["capabilities"]["network"]) - set(new["capabilities"]["network"]))
    if gone:
        add(INFO, "LESS_NETWORK", f"no longer uses: {', '.join(gone)}")
    return {"old": {"target": old["target"], "sha256": old["sha256"], "verdict": old["verdict"]}, "new": {"target": new["target"], "sha256": new["sha256"], "verdict": new["verdict"]},
            "changes": d, "verdict": verdict(d), "new_report": new}


# ───────────────────────────────────────────── output ─────────────────────────────────────────────
def render(r: dict) -> str:
    pk = r["package"] or {}
    name = f"{pk.get('name')}@{pk.get('version')}" if pk.get("name") else r["target"]
    eng = r["engine"]
    out = [f"INSPECT  {name}   ({r['kind']}, {r['files']} files, sha256 {r['sha256'][:12]}...)",
           "engine   : " + (f"REA {eng['version']} in a sandbox (no network, read-only disk, no privileges); evidence {str(eng.get('evidence_id', ''))[:16]}..." if eng["name"] == "REA"
                            else "built-in checks only" + (f" - {eng['note']}" if eng.get("note") else "")), ""]
    out.append({"OK": "VERDICT  : OK  - nothing alarming in what can be read statically", "REVIEW": "VERDICT  : REVIEW  - something a person should look at before trusting this",
                "BLOCK": "VERDICT  : BLOCK  - do not install or run this until a person has looked"}[r["verdict"]])
    labels = {"network": "talk over the network", "run_programs": "run other programs", "files": "read/write files", "environment": "read your environment", "dynamic_code": "run dynamically built code", "native": "load native code"}
    caps = [f"{labels[k]}: {', '.join(v)}" for k, v in r["capabilities"].items() if v]
    out += ["", "What it can do (read from the code):"] + (["   - " + c for c in caps] or ["   - nothing beyond plain computation was found"])
    if r["flags"]:
        out += ["", "Worth knowing:"] + [f"   [{x['severity']}] {x['text']}" for x in sorted(r["flags"], key=lambda x: {"HIGH": 0, "MEDIUM": 1, "info": 2}[x["severity"]])]
    if r["endpoints"] or r["urls"]:
        out += ["", "Addresses seen: " + ", ".join(sorted(set(r["endpoints"]) | set(r["urls"]))[:8])]
    out += ["", "Limits: " + "; ".join(dict.fromkeys(r["limits"]))]
    return "\n".join(out)


def render_diff(d: dict) -> str:
    out = [f"DRIFT  {d['old']['target']}  ->  {d['new']['target']}   (sha256 {d['old']['sha256'][:8]}... -> {d['new']['sha256'][:8]}...)", ""]
    out.append({"OK": "VERDICT : OK  - the new version can do nothing the old one could not", "REVIEW": "VERDICT : REVIEW  - the new version can do more than the old one: look before upgrading",
                "BLOCK": "VERDICT : BLOCK  - the new version gained powers typical of a compromised package: do not upgrade until a person has looked"}[d["verdict"]])
    out += [""] + ([f"   [{x['severity']}] {x['text']}" for x in sorted(d["changes"], key=lambda x: {"HIGH": 0, "MEDIUM": 1, "info": 2}[x["severity"]])] or ["   no change in what it can do"])
    return "\n".join(out)


def save(rep: dict, name: str) -> pathlib.Path:
    d = HOME / "inspect"
    d.mkdir(parents=True, exist_ok=True)
    p = d / (re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80] + "-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    p.write_text(json.dumps(rep, indent=2), "utf-8")
    p.chmod(0o600)
    return p


# ───────────────────────────────────────────── the autonomous watch ─────────────────────────────────────────────
def vkey(v: str) -> tuple:
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-+]", v)[:4])


def latest_version(name: str) -> str | None:
    if not shutil.which("npm"):
        return None
    r = subprocess.run(["npm", "view", name, "version"], capture_output=True, text=True, timeout=60)
    return r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else None


def watch(ci: bool = False) -> int:
    wl = json.loads(WATCHLIST.read_text("utf-8"))
    worst, summary = 0, []
    for e in wl["packages"]:
        name, pinned = e["name"], e["pinned"]
        lat = latest_version(name)
        row = {"package": name, "pinned": pinned, "latest": lat, "why": e.get("why", "")}
        if lat is None:
            row["status"] = "could not reach the registry (offline?)"
        elif vkey(lat) <= vkey(pinned):
            row["status"] = "up to date"
        else:
            try:
                old, new = build_report(f"npm:{name}@{pinned}"), build_report(f"npm:{name}@{lat}")
                dr = diff_reports(old, new)
                row.update(status=f"newer version {lat}: " + dr["verdict"], verdict=dr["verdict"], changes=[c["text"] for c in dr["changes"] if c["severity"] != "info"],
                           report=str(save(dr, f"{name}-{pinned}-to-{lat}")))
                worst = max(worst, {"OK": 0, "REVIEW": 1, "BLOCK": 2}[dr["verdict"]])
            except (SystemExit, ValueError, OSError) as ex:
                row["status"] = f"could not inspect: {ex}"
        summary.append(row)
    print(json.dumps(summary, indent=2) if ci else "\n".join(
        f"  {r['package']:<16} pinned {r['pinned']:<10} latest {str(r['latest']):<10} {r['status']}" + ("".join(f"\n      - {c}" for c in r.get('changes', [])) if r.get("changes") else "") for r in summary))
    return 2 if worst else 0


def schedule(mode: str) -> int:
    if not shutil.which("crontab"):
        print("crontab is not available here (WSL: sudo apt-get install -y cron && sudo service cron start).")
        return 1
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = [ln for ln in (cur.stdout if cur.returncode == 0 else "").splitlines() if CRON_TAG not in ln]
    if mode == "status":
        mine = [ln for ln in (cur.stdout if cur.returncode == 0 else "").splitlines() if CRON_TAG in ln]
        print("\n".join(mine) if mine else "no weekly watch scheduled.")
        return 0
    if mode == "weekly":
        lines.append(f"17 6 * * 1 bash {ROOT / 'securax'} inspect --watch >> {HOME / 'inspect-watch.log'} 2>&1 {CRON_TAG}")
    p = subprocess.run(["crontab", "-"], input="\n".join(lines) + ("\n" if lines else ""), text=True)
    print("weekly watch scheduled (Mondays 06:17; log: ~/.securax/inspect-watch.log). Undo: ./securax inspect --watch --schedule off" if mode == "weekly" else "weekly watch removed.")
    return p.returncode


def selftest() -> int:
    """Prove the sandbox is a sandbox: no network, no writes to the image, no privileges."""
    if not image_present():
        print(f"the sandbox image {IMAGE} is not built: ./securax inspect --build")
        return 1
    js = ("const net=require('net'),fs=require('fs');let res={};"
          "res.write_blocked=(()=>{try{fs.writeFileSync('/opt/rea/x','1');return false}catch(e){return true}})();"
          "res.uid=process.getuid();"
          "const s=net.connect({host:'1.1.1.1',port:443,timeout:2000});"
          "s.on('connect',()=>{res.network_blocked=false;console.log(JSON.stringify(res));process.exit(0)});"
          "s.on('error',()=>{res.network_blocked=true;console.log(JSON.stringify(res));process.exit(0)});"
          "s.on('timeout',()=>{res.network_blocked=true;console.log(JSON.stringify(res));process.exit(0)});")
    r = subprocess.run(["docker", "run", "--rm", *SANDBOX, "--entrypoint", "node", IMAGE, "-e", js], capture_output=True, text=True, timeout=60)
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        print("selftest could not run:", (r.stderr or r.stdout)[-300:])
        return 1
    ok = res.get("network_blocked") and res.get("write_blocked") and res.get("uid") != 0
    print(f"sandbox: network {'BLOCKED' if res.get('network_blocked') else 'OPEN (!)'}, disk {'read-only' if res.get('write_blocked') else 'WRITABLE (!)'}, runs as uid {res.get('uid')} (not root)  ->  {'OK' if ok else 'NOT SAFE'}")
    return 0 if ok else 1


def mcp_command(project: pathlib.Path) -> list[str]:
    """The command an agent (OpenCode) runs to talk to REA over MCP: the same sandbox, plus the project mounted READ-ONLY at /work."""
    return ["docker", "run", "-i", "--rm", *SANDBOX, "-v", f"{project}:/work:ro", IMAGE, "--mcp"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sandboxed static inspection of third-party software.")
    ap.add_argument("target", nargs="?")
    ap.add_argument("--diff", nargs=2, metavar=("OLD", "NEW"))
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--schedule", choices=["weekly", "off", "status"])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ci", action="store_true", help="watch: machine-readable output")
    ap.add_argument("--no-rea", action="store_true", help="built-in checks only")
    ap.add_argument("--strict", action="store_true", help="exit 1 on REVIEW, 2 on BLOCK")
    a = ap.parse_args(argv)
    if a.build:
        return build_image()
    if a.selftest:
        return selftest()
    if a.schedule:
        return schedule(a.schedule)
    if a.watch:
        return watch(a.ci)
    if a.diff:
        d = diff_reports(build_report(a.diff[0], not a.no_rea), build_report(a.diff[1], not a.no_rea))
        print(json.dumps(d, indent=2) if a.json else render_diff(d))
        if not a.json:
            print(f"\nreport saved: {save(d, 'diff-' + d['new']['target'])}")
        return {"OK": 0, "REVIEW": 1, "BLOCK": 2}[d["verdict"]] if a.strict else 0
    if not a.target:
        ap.error("give a folder, a .tgz, a file, or npm:name@version")
    rep = build_report(a.target, not a.no_rea)
    print(json.dumps(rep, indent=2) if a.json else render(rep))
    if not a.json:
        print(f"\nreport saved: {save(rep, rep['target'])}")
    return {"OK": 0, "REVIEW": 1, "BLOCK": 2}[rep["verdict"]] if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
