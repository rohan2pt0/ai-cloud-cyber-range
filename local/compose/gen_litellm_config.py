#!/usr/bin/env python3
"""Generate litellm-config.generated.yaml from the SecuRAX plugin catalog + your .env.

The catalog (plugins/catalog.json) is the single source of truth for provider plugins.
A provider is ENABLED when every API key it needs is present (non-empty) in the env.
Only enabled providers are written into the router config, so Chat lists exactly the
models you can actually use — all still routed through the security gateway.

RESILIENCE MODEL (the "degradation ladder")
  * Every enabled provider gets its OWN alias with exactly ONE deployment. (Two deployments under
    one name would be randomly load-balanced — a slow local model would answer half your requests
    even when a fast cloud model is healthy.)
  * `chains` in the catalog (bank-assistant, builder) are ordered ladders. The first enabled rung
    answers; the rest become LiteLLM `fallbacks`. Every chain ends in `local`, which is always on,
    so an answer is possible even with zero keys and zero internet.
  * Cloud rungs get a short timeout so a hung provider fails over in seconds; the local rung gets a
    long one because CPU inference is slow but sure.

Pure standard library (no PyYAML): the output YAML is simple and regular, emitted by hand.
The generator reads ONLY the env mapping it is handed (no hidden os.environ reads), so output is
deterministic and tests are hermetic. `main()` builds that mapping from the process env + .env file.

Usage:
  python3 gen_litellm_config.py --status                 # show enabled/disabled providers + chains
  python3 gen_litellm_config.py --write                  # (re)write litellm-config.generated.yaml
  python3 gen_litellm_config.py --write --env-file .env  # read keys from a specific .env
Model override: set <ID>_MODEL in the env (e.g. OPENAI_MODEL=openai/gpt-4o, LOCAL_MODEL=qwen2.5:3b)
to change a provider's model without editing the catalog.
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CATALOG = os.path.join(REPO, "plugins", "catalog.json")
BASELINE_OUT = os.path.join(HERE, "litellm-config.yaml")            # tracked reference; never touched by `up`
OUT = os.path.join(HERE, "litellm-config.generated.yaml")           # what the router mounts; git-ignored, per machine

CLOUD_TIMEOUT = 40     # seconds: a hung cloud provider should fail over fast
LOCAL_TIMEOUT = 300    # seconds: CPU inference is slow but sure


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


def env_lookup(env: dict, key: str) -> str:
    return (env.get(key) or "").strip()


def is_enabled(p: dict, env: dict, baseline: bool = False) -> bool:
    if p.get("always"):
        return True
    if baseline:
        # the shipped committed config is deterministic: only the default provider (Gemini)
        # plus always-on local — never influenced by whatever env this runs in.
        return bool(p.get("default"))
    needs = p.get("env", [])
    if not needs:
        return True
    return all(env_lookup(env, k) for k in needs)


def model_for(p: dict, env: dict, baseline: bool = False) -> str:
    """Catalog default, overridable with <ID>_MODEL (e.g. GROK_MODEL=xai/grok-3, LOCAL_MODEL=qwen2.5:3b).
    Local (Ollama) models accept a bare tag ('qwen2.5:3b') and get the required `ollama/` prefix."""
    override = "" if baseline else env_lookup(env, p["id"].upper() + "_MODEL")
    model = override or p.get("model", "")
    if p.get("local") and model and not model.startswith("ollama/"):
        model = "ollama/" + model
    return model


def internal_api_base(url: str, env: dict, baseline: bool = False) -> str:
    """With internal TLS on (`./securax tls internal on`) the local model is reached over HTTPS through its sidecar, by its internal name."""
    if not baseline and env_lookup(env, "TLS_INTERNAL") == "1" and url.rstrip("/") == "http://ollama:11434":
        return "https://ollama.securax.internal:8443"
    return url


def install_id(env: dict) -> str:
    """A stable, non-secret id for THIS install (8 hex chars of a hash of the router key): sent as the session id some providers ask coding agents to identify with."""
    import hashlib
    return hashlib.sha256((env_lookup(env, "LITELLM_MASTER_KEY") or "securax").encode()).hexdigest()[:8]


def provider_params(p: dict, env: dict, baseline: bool = False) -> dict:
    """litellm_params for one provider (everything except model_name)."""
    params: dict[str, object] = {"model": model_for(p, env, baseline)}
    if p.get("local"):
        # Ollama-style local model: literal api_base, no key. Its env entries are only on/off gate
        # flags (e.g. ENABLE_LOCAL_CODER), never an api_key.
        params["api_base"] = internal_api_base(p["api_base"], env, baseline)
        params["timeout"] = LOCAL_TIMEOUT
        return params
    params["timeout"] = CLOUD_TIMEOUT
    if p.get("region_env"):
        # AWS Bedrock authenticates with the AWS key pair + region — NOT an api_key.
        params["aws_access_key_id"] = "os.environ/AWS_ACCESS_KEY_ID"
        params["aws_secret_access_key"] = "os.environ/AWS_SECRET_ACCESS_KEY"
        params["aws_region_name"] = f"os.environ/{p['region_env']}"
        return params
    keys = [k for k in p.get("env", []) if not k.endswith("_API_BASE")]
    if keys:
        params["api_key"] = f"os.environ/{keys[0]}"
    if p.get("needs_base"):
        params["api_base"] = "os.environ/AZURE_API_BASE"
    elif p.get("api_base"):
        params["api_base"] = p["api_base"]                       # an OpenAI-compatible endpoint that is not the vendor default (e.g. OpenCode Go)
    if p.get("headers"):
        params["extra_headers"] = {k: v.replace("{install}", install_id(env)) for k, v in p["headers"].items()}
    return params


def check_key(catalog: dict, provider_id: str, key: str) -> str:
    """Soft sanity check for a pasted API key (never blocks; the wizard just warns).

    Returns "ok", "other:<id>:<label>" when the key's prefix clearly belongs to a DIFFERENT provider
    (e.g. an OpenRouter `sk-or-` key pasted under ElevenLabs), or "prefix:<expected>" when the provider
    has a well-known prefix this key does not start with. Ambiguous prefixes (`sk-` is shared by
    OpenAI and DeepSeek) are never reported as "other".
    """
    key = key.strip()
    by_id = {p["id"]: p for p in catalog.get("providers", [])}
    want = by_id.get(provider_id, {}).get("key_prefix", "")
    matches = [(len(p["key_prefix"]), p["id"]) for p in by_id.values()
               if p.get("key_prefix") and key.startswith(p["key_prefix"])]
    if matches:
        best = max(n for n, _ in matches)
        winners = [pid for n, pid in matches if n == best]
        if provider_id in winners:
            return "ok"
        if len(winners) == 1 and winners[0] != provider_id:
            return f"other:{winners[0]}:{by_id[winners[0]]['label']}"
    if want and not key.startswith(want):
        return f"prefix:{want}"
    return "ok"


def enabled_llm_ids(catalog: dict, env: dict, baseline: bool = False) -> list[str]:
    return [p["id"] for p in catalog.get("providers", [])
            if p.get("kind") == "llm" and is_enabled(p, env, baseline)]


def live_chain(chain_ids: list[str], enabled: set[str]) -> list[str]:
    """The rungs of a chain that are actually enabled, in ladder order."""
    return [i for i in chain_ids if i in enabled]


def _emit_params(lines: list[str], params: dict) -> None:
    for k, v in params.items():
        lines.append(f"      {k}: {json.dumps(v) if isinstance(v, dict) else v}")


def generate(catalog: dict, env: dict, baseline: bool = False) -> str:
    providers = catalog.get("providers", [])
    by_id = {p["id"]: p for p in providers}
    enabled = set(enabled_llm_ids(catalog, env, baseline))
    chains = {k: v for k, v in catalog.get("chains", {}).items() if not k.startswith("_")}

    lines: list[str] = [
        "# AUTO-GENERATED from plugins/catalog.json by gen_litellm_config.py — do NOT hand-edit.",
        "# Re-run `./securax providers` (or this script with --write) after adding/removing a key.",
        "# The gateway is the SECURITY PEP; this is the FinOps/RESILIENCE PEP (fallback ladders).",
        "# One deployment per alias (no random shuffle); chains + fallbacks give the degradation ladder.",
        "model_list:",
        "  # ---- each enabled provider, selectable by its own alias ----",
    ]
    for p in providers:
        if p["id"] not in enabled:
            continue
        lines += [f"  - model_name: {p['alias']}", "    litellm_params:"]
        _emit_params(lines, provider_params(p, env, baseline))

    lines.append("  # ---- degradation ladders: the first enabled rung answers; the rest are fallbacks ----")
    fallbacks: list[dict] = []
    for chain_name, ids in chains.items():
        live = live_chain(ids, enabled)
        if not live:
            continue  # unreachable while 'local' ends every chain (enforced by tests)
        head = by_id[live[0]]
        lines += [f"  - model_name: {chain_name}", "    litellm_params:"]
        _emit_params(lines, provider_params(head, env, baseline))
        if len(live) > 1:
            fallbacks.append({chain_name: [by_id[i]["alias"] for i in live[1:]]})

    lines += [
        "",
        "litellm_settings:",
        "  num_retries: 1",
        "  request_timeout: 120",
        f"  fallbacks: {json.dumps(fallbacks)}",
        "  drop_params: true",
        "  json_logs: true",
        "",
        "router_settings:",
        "  routing_strategy: simple-shuffle",
        "  # a deployment that fails twice is cooled down briefly so requests go straight to the next rung",
        "  allowed_fails: 2",
        "  cooldown_time: 30",
        "",
        "general_settings:",
        "  master_key: os.environ/LITELLM_MASTER_KEY",
        "  max_budget: 25",
        "  budget_duration: 30d",
        "",
    ]
    return "\n".join(lines)


def status(catalog: dict, env: dict, baseline: bool = False) -> list[tuple[str, str, bool]]:
    return [(p["id"], p["label"], is_enabled(p, env, baseline)) for p in catalog.get("providers", [])]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the LiteLLM router config from the plugin catalog.")
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"))
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--out", default=None, help="default: litellm-config.generated.yaml (or litellm-config.yaml with --baseline)")
    ap.add_argument("--write", action="store_true", help="write the config file")
    ap.add_argument("--status", action="store_true", help="print provider enable/disable status + chains")
    ap.add_argument("--check-key", metavar="PROVIDER_ID",
                    help="read an API key on STDIN and report whether it looks like PROVIDER_ID's key")
    ap.add_argument("--baseline", action="store_true",
                    help="generate the shipped baseline (default provider on, ignore local keys)")
    args = ap.parse_args(argv)

    catalog = load_catalog(args.catalog)
    if args.check_key:
        import sys
        print(check_key(catalog, args.check_key, sys.stdin.read()))   # key via stdin: never in argv/ps
        return 0
    # Process env wins over the .env file (same precedence Docker Compose uses for interpolation).
    env: dict[str, str] = {} if args.baseline else {**parse_env_file(args.env_file), **os.environ}

    if args.status or not args.write:
        for pid, label, on in status(catalog, env, args.baseline):
            print(f"  [{'ON ' if on else 'off'}] {pid:<11} {label}")
        enabled = set(enabled_llm_ids(catalog, env, args.baseline))
        by_id = {p["id"]: p for p in catalog["providers"]}
        for name, ids in catalog.get("chains", {}).items():
            if name.startswith("_"):
                continue
            rungs = " → ".join(by_id[i]["alias"] for i in live_chain(ids, enabled))
            print(f"  chain {name:<15} {rungs}")
        if not args.write:
            return 0

    out = args.out or (BASELINE_OUT if args.baseline else OUT)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(generate(catalog, env, baseline=args.baseline))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
