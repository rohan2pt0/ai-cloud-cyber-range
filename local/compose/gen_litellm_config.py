#!/usr/bin/env python3
"""Generate litellm-config.yaml from the SecuRAX plugin catalog + your .env.

The catalog (plugins/catalog.json) is the single source of truth for provider plugins.
A provider is ENABLED when every API key it needs is present (non-empty) in the env.
Only enabled providers are written into the router config, so Chat lists exactly the
models you can actually use — all still routed through the security gateway.

Pure standard library (no PyYAML): the output YAML is simple and regular, emitted by hand.

Usage:
  python3 gen_litellm_config.py --status                 # show enabled/disabled providers
  python3 gen_litellm_config.py --write                  # (re)write litellm-config.yaml
  python3 gen_litellm_config.py --write --env-file .env  # read keys from a specific .env
Model override: set <ID>_MODEL in the env (e.g. OPENAI_MODEL=openai/gpt-4o) to change a
provider's model without editing the catalog. Azure/Bedrock also read their own extras.
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CATALOG = os.path.join(REPO, "plugins", "catalog.json")
OUT = os.path.join(HERE, "litellm-config.yaml")


def load_catalog(path: str = CATALOG) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_env_file(path: str) -> dict:
    """Minimal KEY=VALUE .env parser (ignores comments/blank lines, strips quotes)."""
    env: dict[str, str] = {}
    if not path or not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def env_lookup(env_file: dict, key: str) -> str:
    """Prefer the real process environment, fall back to the parsed .env file."""
    val = os.environ.get(key)
    if val is None:
        val = env_file.get(key, "")
    return (val or "").strip()


def is_enabled(p: dict, env_file: dict, baseline: bool = False) -> bool:
    if p.get("always"):
        return True
    if baseline:
        # the shipped committed config is deterministic: only the default provider (Gemini)
        # plus always-on local — never influenced by whatever env this runs in.
        return bool(p.get("default"))
    needs = p.get("env", [])
    if not needs:
        return True
    return all(env_lookup(env_file, k) for k in needs)


def model_for(p: dict, env_file: dict) -> str:
    """Catalog default, overridable with <ID>_MODEL (e.g. GROK_MODEL=xai/grok-3)."""
    override = env_lookup(env_file, p["id"].upper() + "_MODEL")
    return override or p.get("model", "")


def _emit_params(lines: list[str], params: dict) -> None:
    for k, v in params.items():
        lines.append(f"      {k}: {v}")


def generate(catalog: dict, env_file: dict, baseline: bool = False) -> str:
    providers = catalog.get("providers", [])
    by_id = {p["id"]: p for p in providers}
    gemini_on = is_enabled(by_id["gemini"], env_file, baseline) if "gemini" in by_id else False

    lines: list[str] = [
        "# AUTO-GENERATED from plugins/catalog.json by gen_litellm_config.py — do NOT hand-edit.",
        "# Re-run `./securax providers` (or this script with --write) after adding/removing a key.",
        "# The gateway is the SECURITY PEP; this is the FinOps PEP (cost control + fallback).",
        "model_list:",
        "  # ---- default the app calls: fast cloud Gemini when its key is set, else sovereign local ----",
        "  - model_name: bank-assistant",
        "    litellm_params:",
    ]
    if gemini_on:
        _emit_params(lines, {"model": model_for(by_id["gemini"], env_file),
                             "api_key": "os.environ/GEMINI_API_KEY"})
        # local fallback entry under the same alias
        lines += ["  - model_name: bank-assistant", "    litellm_params:"]
        _emit_params(lines, {"model": by_id["local"]["model"], "api_base": by_id["local"]["api_base"]})
    else:
        _emit_params(lines, {"model": by_id["local"]["model"], "api_base": by_id["local"]["api_base"]})

    # explicit sovereign-local alias (always present)
    lines += ["  - model_name: bank-assistant-local", "    litellm_params:"]
    _emit_params(lines, {"model": by_id["local"]["model"], "api_base": by_id["local"]["api_base"]})

    # every other ENABLED llm provider, selectable by its own alias
    for p in providers:
        if p.get("kind") != "llm" or p["id"] in ("gemini", "local"):
            continue
        if not is_enabled(p, env_file, baseline):
            continue
        params: dict[str, str] = {"model": model_for(p, env_file)}
        if p.get("local"):
            # Ollama-style local model: literal api_base, no API key. Its env entries are just
            # on/off gate flags (e.g. ENABLE_LOCAL_CODER), never an api_key.
            params["api_base"] = p["api_base"]
        else:
            # first API key env -> api_key; azure/bedrock carry extras
            keys = [k for k in p.get("env", []) if not k.endswith("_API_BASE")]
            if keys:
                params["api_key"] = f"os.environ/{keys[0]}"
            if p.get("needs_base"):
                params["api_base"] = "os.environ/AZURE_API_BASE"
            if p.get("region_env"):
                params["aws_region_name"] = f"os.environ/{p['region_env']}"
        lines += [f"  - model_name: {p['alias']}", "    litellm_params:"]
        _emit_params(lines, params)

    lines += [
        "",
        "litellm_settings:",
        "  num_retries: 1",
        "  request_timeout: 120",
        '  fallbacks: [{"bank-assistant": ["bank-assistant-local"]}]',
        "  drop_params: true",
        "  json_logs: true",
        "",
        "router_settings:",
        "  routing_strategy: simple-shuffle",
        "",
        "general_settings:",
        "  master_key: os.environ/LITELLM_MASTER_KEY",
        "  max_budget: 25",
        "  budget_duration: 30d",
        "",
    ]
    return "\n".join(lines)


def status(catalog: dict, env_file: dict) -> list[tuple[str, str, bool]]:
    rows = []
    for p in catalog.get("providers", []):
        rows.append((p["id"], p["label"], is_enabled(p, env_file)))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate litellm-config.yaml from the plugin catalog.")
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"))
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--write", action="store_true", help="write the config file")
    ap.add_argument("--status", action="store_true", help="print provider enable/disable status")
    ap.add_argument("--baseline", action="store_true",
                    help="generate the shipped baseline (default provider on, ignore local keys)")
    args = ap.parse_args(argv)

    catalog = load_catalog(args.catalog)
    env_file = {} if args.baseline else parse_env_file(args.env_file)

    if args.status or not args.write:
        for pid, label, on in status(catalog, env_file):
            mark = "ON " if on else "off"
            print(f"  [{mark}] {pid:<11} {label}")
        if not args.write:
            return 0

    cfg = generate(catalog, env_file, baseline=args.baseline)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(cfg)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
