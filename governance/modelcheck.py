#!/usr/bin/env python3
"""Model supply chain (doc 105, gap G4; OWASP LLM03 and LLM04): a local model runs only if its digest is one you approved.

    ./securax ai check                       every model in the local Ollama against its approved digest: OK, CHANGED or UNLISTED
    ./securax ai check --approve NAME --reason "..."
                                             approve the digest NAME has now (kept private in vault/model-digests.json, with who,
                                             when and why); the shipped defaults are approved in governance/model-registry.yaml
    ./securax ai check --scan PATH           look inside weight files (.ckpt .pt .pth .bin .pkl, also zipped) for pickle code that
                                             would run on load (os, subprocess, eval and the like); prefer .safetensors or GGUF

A digest is the sha256 of the model's manifest, the same value the Ollama registry serves; `ollama list` shows its first 12
characters as the ID. A model whose tag now points at different weights reads CHANGED, even under a familiar name: a re-pushed
tag is exactly how poisoned weights would arrive. Standard library only (the registry needs PyYAML, which the estate uses).
Exit codes: 0 every model approved and every scanned file clean, 1 otherwise, 2 usage.
"""
from __future__ import annotations

import datetime as dt
import getpass
import io
import json
import os
import pathlib
import pickletools
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "governance" / "model-registry.yaml"
PICKLE_EXT = {".ckpt", ".pt", ".pth", ".bin", ".pkl", ".pickle"}
# modules whose functions run code or touch the system when a pickle names them (the picklescan danger list, reduced)
DANGER = {"os", "posix", "nt", "subprocess", "sys", "socket", "shutil", "runpy", "importlib", "webbrowser", "pty",
          "builtins.eval", "builtins.exec", "builtins.compile", "builtins.open", "builtins.__import__", "builtins.getattr",
          "__builtin__.eval", "__builtin__.exec", "__builtin__.open"}


def vault() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_VAULT_DIR") or ROOT / "vault")


def approved(registry: pathlib.Path = REGISTRY) -> dict[str, dict]:
    """NAME -> {digest, by, why}: the shipped defaults, then the owner's own approvals (which win)."""
    import yaml
    out = {k: {"digest": v, "by": "governance/model-registry.yaml", "why": "shipped default"}
           for k, v in ((yaml.safe_load(registry.read_text("utf-8")) or {}).get("digests") or {}).items()}
    mine = vault() / "model-digests.json"
    if mine.exists():
        out.update(json.loads(mine.read_text("utf-8")))
    return out


def parse_list(text: str) -> list[dict]:
    """`ollama list` output -> [{name, id}] (the ID is the digest's first 12 hex characters)."""
    rows = []
    for line in text.splitlines():
        m = re.match(r"^(\S+)\s+([0-9a-f]{12})\b", line.strip())
        if m:
            rows.append({"name": m.group(1), "id": m.group(2)})
    return rows


def _norm(name: str) -> str:
    return name if ":" in name else name + ":latest"


def check(local: list[dict], ok: dict[str, dict]) -> list[dict]:
    res = []
    known = {_norm(k): v for k, v in ok.items()}
    for m in local:
        want = known.get(_norm(m["name"]))
        if not want:
            res.append({**m, "state": "unlisted", "why": f"approve it after checking where it came from: ./securax ai check --approve {m['name']} --reason \"...\""})
        elif not want["digest"].startswith(m["id"]):
            res.append({**m, "state": "changed", "why": f"approved {want['digest'][:12]} ({want['by']}); the weights under this name are not the ones approved"})
        else:
            res.append({**m, "state": "ok", "why": want["why"]})
    return res


def approve(name: str, local: list[dict], reason: str, by: str = "") -> dict:
    hit = next((m for m in local if _norm(m["name"]) == _norm(name)), None)
    if not hit:
        raise ValueError(f"{name} is not in the local Ollama; pull it first")
    if not reason.strip():
        raise ValueError("a reason is required: where the model came from and why it is trusted")
    path = vault() / "model-digests.json"
    data = json.loads(path.read_text("utf-8")) if path.exists() else {}
    data[_norm(name)] = {"digest": hit["id"], "by": by or getpass.getuser(), "why": reason.strip(),
                         "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1), "utf-8")
    os.chmod(path, 0o600)
    return data[_norm(name)]


def _globals(data: bytes) -> list[str]:
    """Every module.name a pickle stream imports (GLOBAL and STACK_GLOBAL), without running it."""
    found, strings = [], []
    try:
        for op, arg, _pos in pickletools.genops(io.BytesIO(data)):
            if op.name == "GLOBAL":
                found.append(str(arg).replace(" ", "."))
            elif op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE", "BINUNICODE8"):
                strings.append(str(arg))
            elif op.name == "STACK_GLOBAL" and len(strings) >= 2:
                found.append(f"{strings[-2]}.{strings[-1]}")
    except Exception:  # noqa: BLE001  (a truncated or odd stream still reports what it found)
        pass
    return found


def scan_file(path: pathlib.Path) -> list[str]:
    """The dangerous imports inside one weight file (zipped PyTorch files hold their pickles as */data.pkl)."""
    blobs = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            blobs = [z.read(n) for n in z.namelist() if n.endswith(".pkl")]
    else:
        blobs = [path.read_bytes()]
    bad = []
    for b in blobs:
        for g in _globals(b):
            mod = g.split(".")[0]
            if g in DANGER or mod in DANGER:
                bad.append(g)
    return sorted(set(bad))


def scan(target: pathlib.Path) -> list[dict]:
    files = [target] if target.is_file() else sorted(p for p in target.rglob("*") if p.suffix.lower() in PICKLE_EXT)
    return [{"file": str(f), "bad": scan_file(f)} for f in files]


def main(argv: list[str]) -> int:
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if "--scan" in argv:
        i = argv.index("--scan")
        if i + 1 >= len(argv):
            print("usage: ./securax ai check --scan PATH", file=sys.stderr)
            return 2
        res = scan(pathlib.Path(argv[i + 1]))
        for r in res:
            print(("  ✗ " + r["file"] + ": runs code on load: " + ", ".join(r["bad"])) if r["bad"] else "  ✔ " + r["file"])
        if not res:
            print("  no pickle-format weight files found")
        return 1 if any(r["bad"] for r in res) else 0
    local = parse_list(sys.stdin.read())
    if "--approve" in argv:
        i = argv.index("--approve")
        name = argv[i + 1] if i + 1 < len(argv) else ""
        reason = argv[argv.index("--reason") + 1] if "--reason" in argv and argv.index("--reason") + 1 < len(argv) else ""
        try:
            rec = approve(name, local, reason)
        except ValueError as e:
            print(f"✗ {e}", file=sys.stderr)
            return 2
        print(f"✔ {name} approved at {rec['digest']} (private, vault/model-digests.json)")
        return 0
    if not local:
        print("No local models found (is the estate up? ./securax up)")
        return 1
    res = check(local, approved())
    icon = {"ok": "✔ OK", "changed": "✗ CHANGED", "unlisted": "· UNLISTED"}
    print("Local models against their approved digests (doc 105, G4):")
    for r in res:
        print(f"  {icon[r['state']]:<11} {r['name']:<28} {r['id']}   {r['why']}")
    return 0 if all(r["state"] == "ok" for r in res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
