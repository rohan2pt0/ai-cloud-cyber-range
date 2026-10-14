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
Standard library only.
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

LOCAL_LIMIT = {"context": 32768, "output": 4096}
CLOUD_LIMIT = {"context": 128000, "output": 16384}


def build(catalog: dict, env: dict, base_url: str) -> dict:
    enabled = set(gen.enabled_llm_ids(catalog, env))
    by_id = {p["id"]: p for p in catalog["providers"]}
    models: dict[str, dict] = {}

    def add(alias: str, label: str, local: bool) -> None:
        models[alias] = {"name": label, "limit": dict(LOCAL_LIMIT if local else CLOUD_LIMIT)}
    chains = {k: v for k, v in catalog.get("chains", {}).items() if not k.startswith("_")}
    for name in ("builder", "bank-assistant"):
        if name in chains and gen.live_chain(chains[name], enabled):
            add(name, "Build ladder (OpenCode Go > DeepSeek > free tiers > local)" if name == "builder" else "Chat ladder (free tiers > local)", False)
    for pid in sorted(enabled, key=lambda i: list(by_id).index(i)):
        p = by_id[pid]
        add(p["alias"], p["label"], bool(p.get("local")))
    return {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "share": "disabled",
        "enabled_providers": ["securax"],
        "model": "securax/builder" if "builder" in models else "securax/" + next(iter(models)),
        "small_model": "securax/builder" if "builder" in models else "securax/" + next(iter(models)),   # titles etc. also stay on the build ladder
        "permission": {"edit": "ask", "bash": "ask"},
        "provider": {"securax": {"npm": "@ai-sdk/openai-compatible", "name": "SecuRAX (guarded gateway)",
                                 "options": {"baseURL": base_url.rstrip("/") + "/v1", "apiKey": "{env:SECURAX_GATEWAY_KEY}"},
                                 "models": models}},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the OpenCode config that routes through the SecuRAX gateway.")
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"))
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    env = {**gen.parse_env_file(a.env_file), **os.environ}
    cfg = build(gen.load_catalog(gen.CATALOG), env, a.base_url)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2) + "\n", "utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
