#!/usr/bin/env python3
"""Write an OpenCode (https://opencode.ai, the open-source terminal coding agent) config that sends EVERY model call through the SecuRAX gateway.

    ./securax opencode            (the CLI writes this file and launches OpenCode with OPENCODE_CONFIG pointing at it)

Why through the gateway: OpenCode on its own talks straight to whichever providers you give it. Pointed at the gateway instead, its prompts get
the same guardrails (PII / secrets / injection), audit lines, data-residency rules and the build ladder (OpenCode Go -> DeepSeek -> free tiers ->
your local model) as everything else in the estate, and you hold ONE set of keys (in .env), not one per tool.

The file holds no secret: the key is read from the environment at run time (`{env:SECURAX_GATEWAY_KEY}`). Settings that matter for a regulated user:
  * enabled_providers: ["securax"]   OpenCode can ONLY reach the gateway (its other built-in providers are off, so no side door around the guardrails)
  * autoupdate false                 no unreviewed code arrives by itself; upgrade on purpose
  * share "disabled"                 `/share` (publishing a conversation to a public link) is switched off entirely
  * permission edit/bash "ask"       it asks before changing a file or running a command (its default is to allow everything)
  * instructions                     the build contract and the lessons ride with every session (OpenCode reads AGENTS.md by itself)
Models: the build ladder ('builder', cheap and fast) by default; `--strong` starts on the strong chain (the strongest open models, for
the hard work the router sends there). Both are offered in OpenCode's model picker either way. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_litellm_config as gen  # noqa: E402

CODING_CHAINS = ("builder", "strong")      # the only chains a coding agent may use: Chat chains can carry personal data
INSTRUCTIONS = ["BUILD-CONTRACT.md", "LESSONS.md"]
LOCAL_LIMIT = {"context": 16384, "output": 4096}      # = the ollama container's OLLAMA_CONTEXT_LENGTH default (docker-compose.yml)
CLOUD_LIMIT = {"context": 128000, "output": 16384}


def build(catalog: dict, env: dict, base_url: str, rea_project: str | None = None, strong: bool = False) -> dict:
    enabled = set(gen.enabled_llm_ids(catalog, env))
    by_id = {p["id"]: p for p in catalog["providers"]}
    models: dict[str, dict] = {}

    local_limit = {**LOCAL_LIMIT, "context": int(str(env.get("OLLAMA_CONTEXT_LENGTH") or LOCAL_LIMIT["context"]))}   # .env can change it

    def add(alias: str, label: str, local: bool) -> None:
        models[alias] = {"name": label, "limit": dict(local_limit if local else CLOUD_LIMIT)}
    chains = gen.chains_for(catalog, env)
    # Only the coding ladders: a coding agent never gets a Chat chain (bank-assistant, twin), which can carry personal data.
    for name, label in (("builder", "Build ladder"), ("strong", "Strong open models")):
        if name in chains and gen.live_chain(chains[name], enabled):
            add(name, label + " (" + " > ".join(by_id[i]["alias"] for i in gen.live_chain(chains[name], enabled)) + ")", False)
    for pid in sorted(enabled, key=lambda i: list(by_id).index(i)):
        p = by_id[pid]
        add(p["alias"], p["label"], bool(p.get("local")))
    cfg = {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "share": "disabled",
        "enabled_providers": ["securax"],
        "model": "securax/strong" if strong and "strong" in models else "securax/builder" if "builder" in models else "securax/" + next(iter(models)),
        "small_model": "securax/builder" if "builder" in models else "securax/" + next(iter(models)),   # titles etc. also stay on the build ladder
        "permission": {"edit": "ask", "bash": "ask"},
        "instructions": [str(HERE.parent.parent / n) for n in INSTRUCTIONS],       # absolute: the config file lives outside the repo
        "provider": {"securax": {"npm": "@ai-sdk/openai-compatible", "name": "SecuRAX (guarded gateway)",
                                 "options": {"baseURL": base_url.rstrip("/") + "/v1", "apiKey": "{env:SECURAX_GATEWAY_KEY}"},
                                 "models": models}},
    }
    if rea_project:
        # REA (Reverse Engineer Anything) as an MCP server for the agent, but ONLY inside its sandbox container: no network, read-only disk, no
        # privileges, the project mounted read-only. OpenCode has no per-call approval for MCP tools, so the container is the control.
        import importlib.util
        spec = importlib.util.spec_from_file_location("securax_inspector", HERE.parent.parent / "governance" / "inspector.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cfg["mcp"] = {"rea": {"type": "local", "command": mod.mcp_command(pathlib.Path(rea_project).resolve()), "enabled": True, "timeout": 60000}}
    return cfg


def check(catalog: dict, env: dict, cfg: dict) -> int:
    """Plain-English report for `./securax opencode --check`. Exit 1 if OpenCode would not default to the build ladder or could pick a Chat chain."""
    by_id = {p["id"]: p for p in catalog["providers"]}
    enabled = set(gen.enabled_llm_ids(catalog, env))
    chains = gen.chains_for(catalog, env)
    rungs = [by_id[i]["alias"] for i in gen.live_chain(chains.get("builder", []), enabled)]
    models = cfg["provider"]["securax"]["models"]
    chat = sorted(set(models) & {k for k in chains if k not in CODING_CHAINS})
    print(f"OpenCode default model: {cfg['model']}  (titles and summaries: {cfg['small_model']})")
    print("Build chain, in order: " + (" → ".join(rungs) or "(nothing enabled)") + ("   (your order, CHAIN_BUILDER in .env)" if gen.chain_override(catalog, env, "builder") else ""))
    print("Chat chains offered to OpenCode: " + (", ".join(chat) if chat else "none (as it should be)"))
    strong = [by_id[i]["alias"] for i in gen.live_chain(chains.get("strong", []), enabled)]
    print("Strong chain (./securax opencode --strong): " + (" → ".join(strong) or "(nothing enabled)"))
    ok = cfg["model"] in ("securax/builder", "securax/strong") and not chat
    print("✔ OpenCode uses the coding chains only." if ok else "✗ OpenCode is NOT limited to the coding chains.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the OpenCode config that routes through the SecuRAX gateway.")
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"))
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--out", help="where to write the config (not needed with --check)")
    ap.add_argument("--check", action="store_true", help="say which chain OpenCode uses and its live rungs; write nothing")
    ap.add_argument("--rea-project", default=None, help="also give the agent REA over MCP, sandboxed, with this folder mounted read-only")
    ap.add_argument("--strong", action="store_true", help="start on the strong chain (the strongest open models)")
    ap.add_argument("--strong-ready", action="store_true", help="exit 0 when the strong chain has a cloud rung (a key is set); write nothing")
    a = ap.parse_args(argv)
    env = {**gen.parse_env_file(a.env_file), **os.environ}
    catalog = gen.load_catalog(gen.CATALOG)
    if a.strong_ready:
        live = gen.live_chain(gen.chains_for(catalog, env).get("strong", []), set(gen.enabled_llm_ids(catalog, env)))
        return 0 if [i for i in live if i not in ("home", "coder", "local")] else 1
    cfg = build(catalog, env, a.base_url, a.rea_project, a.strong)
    if a.check:
        return check(catalog, env, cfg)
    if not a.out:
        ap.error("--out is required unless --check is given")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2) + "\n", "utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
