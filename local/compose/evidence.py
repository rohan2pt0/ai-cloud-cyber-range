#!/usr/bin/env python3
"""Build an auditor-friendly evidence pack from what the running estate already records.

Contents (no prompts, no completions, no secrets):  what is running (versions, images, readiness), which AI providers
are enabled (ids only), the guardrail posture, an aggregate of gateway decisions (counts by decision / stage / rule /
model — never message text), the latest backup, the latest sandbox result, and SHA-256 checksums of the pack itself.
`./securax evidence` collects the raw outputs and calls this.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
import platform
import re
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def summarize_audit(lines) -> dict:
    """Count gateway audit decisions. Only enumerated fields are read; free text (finding detail, errors) is dropped."""
    dec, stage, rule, model = (collections.Counter() for _ in range(4))
    n = 0
    first = last = ""
    for ln in lines:
        m = re.search(r"\{.*\}", ln)
        if not m:
            continue
        try:
            ev = json.loads(m.group(0))
        except ValueError:
            continue
        if not isinstance(ev, dict) or "decision" not in ev:
            continue
        n += 1
        dec[str(ev.get("decision"))] += 1
        if ev.get("stage"):
            stage[str(ev["stage"])] += 1
        if ev.get("model"):
            model[str(ev["model"])] += 1
        for f in ev.get("findings") or []:
            if isinstance(f, dict) and f.get("rule"):
                rule[str(f["rule"])] += 1
        ts = str(ev.get("ts", ""))
        first, last = (first or ts), (ts or last)
    return {"events": n, "first": first, "last": last, "decisions": dict(dec), "blocked_at_stage": dict(stage),
            "rules_triggered": dict(rule), "models_used": dict(model)}


def read(path: str, default: str = "") -> str:
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return default


def parse_env_file(path: str) -> dict:
    out = {}
    for line in read(path).splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def build(raw_dir: str, env_file: str, root: str = ROOT) -> tuple[dict, str]:
    env = parse_env_file(env_file)
    cat = json.loads(read(os.path.join(root, "plugins", "catalog.json"), "{}") or "{}")
    enabled = [p["id"] for p in cat.get("providers", []) if p.get("kind") == "llm" and p.get("env")
               and all(env.get(k) for k in p["env"][:1])] if cat else []
    gen = os.path.join(root, "local", "compose", "litellm-config.generated.yaml")
    sandbox = {}
    try:
        sandbox = json.loads(read(os.path.join(root, "sandbox", "out", "results.json"), "{}") or "{}")
    except ValueError:
        pass
    backups = sorted(f for f in os.listdir(os.path.join(root, "backups"))) if os.path.isdir(os.path.join(root, "backups")) else []
    data = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product_version": read(os.path.join(root, "VERSION")).strip(),
        "git_commit": read(os.path.join(raw_dir, "git_commit")).strip(),
        "host": {"os": platform.platform(), "python": platform.python_version()},
        "docker": read(os.path.join(raw_dir, "docker_version")).strip(),
        "readiness": read(os.path.join(raw_dir, "readyz")).strip() or "unknown (estate not running)",
        "gateway_version": read(os.path.join(raw_dir, "gateway_version")).strip(),
        "containers": [ln for ln in read(os.path.join(raw_dir, "compose_ps")).splitlines() if ln.strip()],
        "ai_providers_enabled": enabled,
        "detector_llama_guard": "ON" if env.get("LLAMA_GUARD_URL") else "OFF (built-in rails enforce)",
        "router_config_sha256": hashlib.sha256(read(gen).encode()).hexdigest() if os.path.exists(gen) else "n/a",
        "decisions": summarize_audit(read(os.path.join(raw_dir, "gateway_log")).splitlines()),
        "latest_backup": backups[-1] if backups else "none",
        "sandbox_last_run": {"journeys": {j.get("name"): ("PASS" if j.get("passed") else "FAIL") for j in sandbox.get("journeys", [])}}
        if isinstance(sandbox, dict) and sandbox.get("journeys") else "not run on this machine",
    }
    d = data["decisions"]
    md = io.StringIO()
    md.write(f"# SecuRAX evidence pack — {data['generated_utc']}\n\n")
    md.write(f"- Product version **{data['product_version']}**, commit `{data['git_commit']}`, gateway reports `{data['gateway_version']}`\n")
    md.write(f"- Readiness: **{data['readiness']}**; Llama Guard detector: **{data['detector_llama_guard']}**\n")
    md.write(f"- AI providers enabled (key present): {', '.join(enabled) or 'none (private local model only)'}\n")
    md.write(f"- Router config SHA-256: `{data['router_config_sha256']}`\n- Latest backup file: {data['latest_backup']}\n")
    md.write(f"- Docker: {data['docker'] or 'n/a'}\n\n## Guardrail decisions (aggregate; no message content)\n")
    md.write(f"Events: {d['events']} ({d['first']} → {d['last']})\n\n")
    for title, key in (("Decisions", "decisions"), ("Blocked at stage", "blocked_at_stage"),
                       ("Rules triggered", "rules_triggered"), ("Models used", "models_used")):
        md.write(f"**{title}:** " + (", ".join(f"{k}={v}" for k, v in d[key].items()) or "none") + "\n\n")
    md.write("## Containers\n```\n" + "\n".join(data["containers"]) + "\n```\n\n")
    md.write("## Control mapping\nSee `docs/securax/04-COMPLIANCE-MAP.md` (RBI CSF / FREE-AI, CERT-In, DPDP, SEBI CSCRF, PCI DSS, NIST CSF, ISO 27001/42001).\n")
    md.write("\n_This pack is generated from the running estate. It contains no prompts, completions or API keys. "
             "It supports, and does not replace, your compliance team's assessment._\n")
    return data, md.getvalue()


def write_pack(out: str, data: dict, report: str) -> None:
    files = {"evidence.json": json.dumps(data, indent=2).encode(), "evidence.md": report.encode()}
    files["SHA256SUMS"] = "".join(f"{hashlib.sha256(v).hexdigest()}  {k}\n" for k, v in files.items()).encode()
    with tarfile.open(out, "w:gz") as t:
        for name, blob in files.items():
            ti = tarfile.TarInfo(name)
            ti.size, ti.mtime, ti.mode = len(blob), int(time.time()), 0o600
            t.addfile(ti, io.BytesIO(blob))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    data, report = build(a.dir, a.env_file)
    write_pack(a.out, data, report)
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
