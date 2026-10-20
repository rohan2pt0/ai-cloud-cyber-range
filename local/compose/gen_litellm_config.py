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
import re

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


def private_base(url: str) -> bool:
    """True for an Ollama URL on a machine you own: loopback, private LAN, Tailscale (100.64.0.0/10) or a *.ts.net name. A rung with this
    URL counts as zone 'local' for data residency, so a public address must never pass (it would carry Red-tier data off your machines)."""
    import ipaddress
    from urllib.parse import urlparse
    try:
        u = urlparse(url.strip())
        host = (u.hostname or "").lower()
        if u.scheme not in ("http", "https") or not host:
            return False
        if host == "localhost" or host.endswith(".ts.net"):
            return True
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private or ip in ipaddress.ip_network("100.64.0.0/10")
    except ValueError:
        return False


def is_enabled(p: dict, env: dict, baseline: bool = False) -> bool:
    if p.get("always"):
        return True
    if p.get("private_base_only") and not baseline and not private_base(env_lookup(env, p["api_base_env"])):
        return False
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


def reasoning_for(p: dict, env: dict, baseline: bool = False) -> str:
    """Optional reasoning cap (<ID>_REASONING=low etc.), applied only where the catalog has checked that LiteLLM maps it to LESS
    thinking for the provider's current model. Anything else returns "" so the request is exactly as before."""
    level = "" if baseline else env_lookup(env, p["id"].upper() + "_REASONING").lower()
    cap = p.get("reasoning") or {}
    if not level or not cap or level not in cap.get("levels", []):
        return ""
    return level if re.search(cap.get("model", "$^"), model_for(p, env, baseline)) else ""


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
    if reasoning_for(p, env, baseline):
        params["reasoning_effort"] = reasoning_for(p, env, baseline)
    if p.get("local"):
        # Ollama-style local model: literal api_base, no key. Its env entries are only on/off gate
        # flags (e.g. ENABLE_LOCAL_CODER), never an api_key.
        params["api_base"] = env_lookup(env, p["api_base_env"]) if p.get("api_base_env") else internal_api_base(p["api_base"], env, baseline)
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
    elif p.get("api_base_env"):
        params["api_base"] = f"os.environ/{p['api_base_env']}"            # an endpoint that is per account (e.g. E2E TIR), kept in .env
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
        # Providers that read the SAME key variable (openrouter + openrouter_pro) are one key, not an ambiguity.
        if len({(by_id[w].get("env") or [w])[0] for w in winners}) == 1:
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


EDITABLE_CHAINS = ("builder", "strong")   # the coding chains; Chat chains (bank-assistant, twin) carry personal data: their order is reviewed code, never a .env switch


def chain_override(catalog: dict, env: dict, name: str) -> list[str] | None:
    """CHAIN_<NAME>=a,b,c in .env replaces the catalog order of an editable chain (`./securax providers chain`). Unknown ids are
    dropped, NON-llm entries are dropped, and 'local' is always kept as the last rung, so an edit can never remove the floor."""
    raw = env_lookup(env, "CHAIN_" + name.upper().replace("-", "_"))
    if name not in EDITABLE_CHAINS or not raw:
        return None
    llm = {p["id"] for p in catalog.get("providers", []) if p.get("kind") == "llm"}
    ids = [i.strip() for i in raw.split(",") if i.strip() in llm and i.strip() != "local"]
    return list(dict.fromkeys(ids)) + ["local"]


def edit_chain(catalog: dict, env: dict, name: str, action: str, pid: str = "", before: str = "") -> tuple[str, str | None]:
    """(plain-English message, new CHAIN_<NAME> value or None on refusal). Never lets an edit remove 'local' or touch a Chat chain."""
    if name not in EDITABLE_CHAINS:
        return f"Only the coding chains can be reordered here ({', '.join(EDITABLE_CHAINS)}); Chat chains carry personal data, so their order is reviewed code.", None
    llm = {p["id"] for p in catalog.get("providers", []) if p.get("kind") == "llm"}
    cur = chains_for(catalog, env)[name]
    if action == "reset":
        return f"The {name} chain is back to the shipped order.", ""
    if pid not in llm:
        return f"unknown provider id '{pid}'. Valid: {', '.join(sorted(llm))}", None
    if pid == "local":
        return "local is always the last rung of every chain; it cannot be moved or removed.", None
    rest = [i for i in cur if i != pid]
    if action == "remove":
        return f"Removed {pid} from the {name} chain.", ",".join(i for i in rest if i != "local")
    if action == "add":
        if before and before not in rest:
            return f"'{before}' is not in the {name} chain.", None
        at = rest.index(before) if before else rest.index("local")
        new = rest[:at] + [pid] + rest[at:]
        return f"Added {pid} to the {name} chain" + (f" before {before}." if before else " (just before local)."), ",".join(i for i in new if i != "local")
    return f"unknown action '{action}' (add, remove, reset)", None


def pick_coder(catalog: dict, visible_mb: int) -> dict:
    """The local coding model for a machine whose Docker sees `visible_mb` of memory: the first catalog tier whose RAM floor is met AND
    whose runtime need (file x runtime_factor) still leaves reserve_mb for the rest of the estate. Returns model, need_mb, why, stepped_from."""
    coder = next(p for p in catalog["providers"] if p["id"] == "coder")
    sz = coder["sizing"]
    wanted = None
    for t in sz["tiers"]:
        need = int(t["size_gb"] * 1024 * sz["runtime_factor"])
        if visible_mb < t["min_mb"]:
            continue
        wanted = wanted or t["model"]
        if visible_mb - need >= sz["reserve_mb"] or t is sz["tiers"][-1]:
            return {"model": t["model"], "need_mb": need, "why": t["why"],
                    "stepped_from": wanted if wanted != t["model"] else ""}
    t = sz["tiers"][-1]
    return {"model": t["model"], "need_mb": int(t["size_gb"] * 1024 * sz["runtime_factor"]), "why": t["why"], "stepped_from": ""}


def chains_for(catalog: dict, env: dict, baseline: bool = False) -> dict[str, list[str]]:
    """The ladders to generate: the catalog's, with any CHAIN_<NAME> override from .env (never in the shipped baseline)."""
    chains = {k: list(v) for k, v in catalog.get("chains", {}).items() if not k.startswith("_")}
    if not baseline:
        for name in chains:
            ov = chain_override(catalog, env, name)
            if ov:
                chains[name] = ov
    return chains


def _emit_params(lines: list[str], params: dict) -> None:
    for k, v in params.items():
        lines.append(f"      {k}: {json.dumps(v) if isinstance(v, dict) else v}")


def generate(catalog: dict, env: dict, baseline: bool = False) -> str:
    providers = catalog.get("providers", [])
    by_id = {p["id"]: p for p in providers}
    enabled = set(enabled_llm_ids(catalog, env, baseline))
    chains = chains_for(catalog, env, baseline)

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
        "  # Fail over instead of retrying what cannot succeed now: a rate limit (free tiers), a timeout, a bad key or a",
        "  # rejected request goes straight to the next rung; only a provider's own 5xx gets one more try on the same rung.",
        "  retry_policy: {RateLimitErrorRetries: 0, TimeoutErrorRetries: 0, AuthenticationErrorRetries: 0, BadRequestErrorRetries: 0, ContentPolicyViolationErrorRetries: 0, InternalServerErrorRetries: 1}",
        "  # Cool a rung down fast when it is clearly unavailable (a bad key at once, a rate limit or timeout on the 2nd hit),",
        "  # so the next requests skip it for a minute instead of paying the same failure again.",
        "  allowed_fails_policy: {AuthenticationErrorAllowedFails: 0, RateLimitErrorAllowedFails: 1, TimeoutErrorAllowedFails: 1}",
        "  allowed_fails: 2",
        "  cooldown_time: 60",
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
    ap.add_argument("--pick-coder", type=int, metavar="VISIBLE_MB", help="print '<model> <need_mb> [<model it stepped down from>]' for this much memory")
    ap.add_argument("--chain-edit", nargs=4, metavar=("CHAIN", "ACTION", "ID", "BEFORE"),
                    help="print the new CHAIN_<NAME> value for add|remove|reset (used by `./securax providers chain`)")
    ap.add_argument("--status", action="store_true", help="print provider enable/disable status + chains")
    ap.add_argument("--check-key", metavar="PROVIDER_ID",
                    help="read an API key on STDIN and report whether it looks like PROVIDER_ID's key")
    ap.add_argument("--baseline", action="store_true",
                    help="generate the shipped baseline (default provider on, ignore local keys)")
    args = ap.parse_args(argv)

    catalog = load_catalog(args.catalog)
    if args.pick_coder is not None:
        r = pick_coder(catalog, args.pick_coder)
        print(f"{r['model']} {r['need_mb']} {r['stepped_from']}".rstrip())
        return 0
    if args.chain_edit:
        import sys
        msg, value = edit_chain(catalog, {**parse_env_file(args.env_file), **os.environ}, *args.chain_edit)
        if value is None:
            print(msg, file=sys.stderr)
            return 1
        print(msg, file=sys.stderr)
        print(value)
        return 0
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
        for name, ids in chains_for(catalog, env, args.baseline).items():
            rungs = " → ".join(by_id[i]["alias"] for i in live_chain(ids, enabled))
            print(f"  chain {name:<15} {rungs}" + ("   (your order, CHAIN_" + name.upper() + " in .env)" if chain_override(catalog, env, name) and not args.baseline else ""))
        if not args.write:
            return 0

    out = args.out or (BASELINE_OUT if args.baseline else OUT)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(generate(catalog, env, baseline=args.baseline))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
