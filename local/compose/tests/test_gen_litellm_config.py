"""Tests for the plugin-catalog -> LiteLLM config generator (gen_litellm_config.py).

No Docker and no network: we feed the generator a fake .env dict and assert the emitted YAML
enables exactly the right providers, routes the default correctly, and always stays valid YAML.
"""
import importlib.util
import pathlib
import re

import yaml

HERE = pathlib.Path(__file__).resolve().parent
GEN_PATH = HERE.parent / "gen_litellm_config.py"
CATALOG = HERE.parent.parent.parent / "plugins" / "catalog.json"

spec = importlib.util.spec_from_file_location("gen_litellm_config", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _catalog():
    return gen.load_catalog(str(CATALOG))


def test_catalog_parses_and_has_required_fields():
    cat = _catalog()
    assert cat.get("providers"), "catalog has providers"
    ids = [p["id"] for p in cat["providers"]]
    # the providers the user asked for are all present
    for need in ("openai", "deepseek", "azure", "mistral", "grok", "perplexity", "bedrock", "elevenlabs"):
        assert need in ids, f"{need} missing from catalog"
    for p in cat["providers"]:
        assert "id" in p and "label" in p and "kind" in p
        assert isinstance(p.get("env", []), list)
        if p["kind"] == "llm":
            assert p.get("alias") and p.get("model"), f"{p['id']} llm needs alias+model"


def test_baseline_is_deterministic_and_gemini_default(monkeypatch):
    # Even with cloud keys in the real env, --baseline must ignore them.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-be-ignored")
    cat = _catalog()
    out = gen.generate(cat, {}, baseline=True)
    doc = yaml.safe_load(out)               # must be valid YAML
    names = [m["model_name"] for m in doc["model_list"]]
    assert "bank-assistant" in names and "bank-assistant-local" in names
    assert "openai" not in names            # baseline ignores env keys
    # default routes to Gemini first, with a local fallback entry
    assert any("gemini" in str(m["litellm_params"].get("model", "")) for m in doc["model_list"])
    assert {"bank-assistant": ["bank-assistant-local"]} in doc["litellm_settings"]["fallbacks"]


def test_enabled_providers_appear_disabled_dont():
    cat = _catalog()
    env = {"GEMINI_API_KEY": "g", "OPENAI_API_KEY": "o", "DEEPSEEK_API_KEY": "d"}
    out = gen.generate(cat, env)
    doc = yaml.safe_load(out)
    names = [m["model_name"] for m in doc["model_list"]]
    assert "openai" in names and "deepseek" in names
    assert "mistral" not in names and "grok" not in names     # no key => not listed
    # api_key is referenced via os.environ, never the literal key value
    blob = out
    assert "os.environ/OPENAI_API_KEY" in blob
    assert "sk-" not in blob and "\no\n" not in blob


def test_model_override():
    cat = _catalog()
    env = {"OPENAI_API_KEY": "o", "OPENAI_MODEL": "openai/gpt-4o"}
    out = gen.generate(cat, env)
    doc = yaml.safe_load(out)
    openai = [m for m in doc["model_list"] if m["model_name"] == "openai"][0]
    assert openai["litellm_params"]["model"] == "openai/gpt-4o"


def test_azure_needs_key_and_base():
    cat = _catalog()
    assert gen.is_enabled(next(p for p in cat["providers"] if p["id"] == "azure"),
                          {"AZURE_API_KEY": "k"}) is False           # base missing
    assert gen.is_enabled(next(p for p in cat["providers"] if p["id"] == "azure"),
                          {"AZURE_API_KEY": "k", "AZURE_API_BASE": "https://x"}) is True


def test_bedrock_carries_region_param():
    cat = _catalog()
    env = {"AWS_ACCESS_KEY_ID": "a", "AWS_SECRET_ACCESS_KEY": "b", "AWS_REGION": "us-east-1"}
    out = gen.generate(cat, env)
    doc = yaml.safe_load(out)
    bedrock = [m for m in doc["model_list"] if m["model_name"] == "bedrock"][0]
    assert bedrock["litellm_params"]["aws_region_name"] == "os.environ/AWS_REGION"
    # Bedrock authenticates with the AWS key pair, never a bogus api_key
    assert "api_key" not in bedrock["litellm_params"]
    assert bedrock["litellm_params"]["aws_access_key_id"] == "os.environ/AWS_ACCESS_KEY_ID"


def test_local_always_on_even_with_empty_env():
    cat = _catalog()
    out = gen.generate(cat, {})
    doc = yaml.safe_load(out)
    assert "bank-assistant-local" in [m["model_name"] for m in doc["model_list"]]


def test_local_coder_uses_api_base_not_key():
    cat = _catalog()
    # disabled without the flag
    out0 = gen.generate(cat, {})
    assert "coder" not in [m["model_name"] for m in yaml.safe_load(out0)["model_list"]]
    # enabled with the flag -> literal api_base, NO api_key (it's an Ollama model)
    out = gen.generate(cat, {"ENABLE_LOCAL_CODER": "1"})
    coder = [m for m in yaml.safe_load(out)["model_list"] if m["model_name"] == "coder"][0]
    assert coder["litellm_params"]["api_base"] == "http://ollama:11434"
    assert "api_key" not in coder["litellm_params"]
    assert coder["litellm_params"]["model"].startswith("ollama/")
    # CODER_MODEL override works
    out2 = gen.generate(cat, {"ENABLE_LOCAL_CODER": "1", "CODER_MODEL": "ollama/qwen2.5-coder:14b"})
    coder2 = [m for m in yaml.safe_load(out2)["model_list"] if m["model_name"] == "coder"][0]
    assert coder2["litellm_params"]["model"] == "ollama/qwen2.5-coder:14b"


def test_tts_and_compute_never_in_model_list():
    cat = _catalog()
    env = {"ELEVENLABS_API_KEY": "e", "REMOTE_OLLAMA_BASE": "http://x:11434"}
    out = gen.generate(cat, env)
    doc = yaml.safe_load(out)
    names = [m["model_name"] for m in doc["model_list"]]
    assert "elevenlabs" not in names and "compute" not in names   # not chat models


# ───────────────────── resilience invariants (the degradation ladder) ─────────────────────
COMPOSE = HERE.parent / "docker-compose.yml"


def _all_enabled_env(cat):
    return {k: "x" for p in cat["providers"] for k in p.get("env", [])}


def _scenarios(cat):
    return [({}, True), ({}, False), (_all_enabled_env(cat), False),
            ({"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q"}, False)]


def _fallback_map(doc):
    return {k: v for d in doc["litellm_settings"]["fallbacks"] for k, v in d.items()}


def test_every_alias_is_a_single_deployment():
    # Two deployments under one name are RANDOMLY load-balanced (simple-shuffle): a slow local model
    # would answer half the traffic even while a fast cloud model is healthy. Local is a fallback.
    cat = _catalog()
    for env, baseline in _scenarios(cat):
        names = [m["model_name"] for m in yaml.safe_load(gen.generate(cat, env, baseline))["model_list"]]
        assert len(names) == len(set(names)), f"duplicate model_name in {env or 'empty'}/{baseline}"


def test_chains_end_in_local_and_use_real_providers():
    cat = _catalog()
    ids = {p["id"] for p in cat["providers"]}
    chains = {k: v for k, v in cat["chains"].items() if not k.startswith("_")}
    assert "bank-assistant" in chains and "builder" in chains
    for name, rungs in chains.items():
        assert rungs[-1] == "local", f"chain {name} must end in the always-on local model"
        assert all(r in ids for r in rungs), f"chain {name} references an unknown provider"


def test_every_fallback_alias_exists_in_model_list():
    # A fallback pointing at a missing alias makes LiteLLM error at the worst possible moment.
    cat = _catalog()
    for env, baseline in _scenarios(cat):
        doc = yaml.safe_load(gen.generate(cat, env, baseline))
        names = {m["model_name"] for m in doc["model_list"]}
        for head, tails in _fallback_map(doc).items():
            assert head in names
            assert all(t in names for t in tails), f"{head} falls back to a missing alias"


def test_zero_keys_still_yields_an_answerable_ladder():
    # Worst case: no keys, no internet. Chat must still have a model that can answer (local).
    cat = _catalog()
    doc = yaml.safe_load(gen.generate(cat, {}))
    by_name = {m["model_name"]: m["litellm_params"] for m in doc["model_list"]}
    for chain in ("bank-assistant", "builder"):
        assert by_name[chain]["model"].startswith("ollama/"), f"{chain} must fall to local with no keys"
    assert "bank-assistant-local" in by_name


def test_ladder_is_free_first_and_ordered():
    cat = _catalog()
    env = {"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q", "OPENROUTER_API_KEY": "o", "OPENAI_API_KEY": "x"}
    fb = _fallback_map(yaml.safe_load(gen.generate(cat, env)))
    assert fb["bank-assistant"] == ["groq", "openrouter", "bank-assistant-local"]
    assert "openai" not in fb["bank-assistant"], "a paid provider must never be in the default chat chain"
    assert fb["builder"] == ["groq", "openrouter", "bank-assistant-local"]   # no deepseek key -> gemini heads it


def test_builder_prefers_cheap_deepseek_then_free_then_local():
    cat = _catalog()
    env = {"DEEPSEEK_API_KEY": "d", "GEMINI_API_KEY": "g", "ENABLE_LOCAL_CODER": "1"}
    doc = yaml.safe_load(gen.generate(cat, env))
    head = [m for m in doc["model_list"] if m["model_name"] == "builder"][0]["litellm_params"]
    assert head["model"].startswith("deepseek/")
    assert _fallback_map(doc)["builder"] == ["bank-assistant-gemini", "coder", "bank-assistant-local"]


def test_local_model_override_gets_ollama_prefix_and_baseline_ignores_it():
    cat = _catalog()
    doc = yaml.safe_load(gen.generate(cat, {"LOCAL_MODEL": "qwen2.5:3b"}))
    local = [m for m in doc["model_list"] if m["model_name"] == "bank-assistant-local"][0]
    assert local["litellm_params"]["model"] == "ollama/qwen2.5:3b"
    base = yaml.safe_load(gen.generate(cat, {"LOCAL_MODEL": "qwen2.5:3b"}, baseline=True))
    local_b = [m for m in base["model_list"] if m["model_name"] == "bank-assistant-local"][0]
    assert local_b["litellm_params"]["model"] == "ollama/qwen2.5:1.5b"   # baseline is deterministic


def test_cloud_fails_over_fast_local_waits_long():
    cat = _catalog()
    doc = yaml.safe_load(gen.generate(cat, {"GROQ_API_KEY": "q"}))
    by_name = {m["model_name"]: m["litellm_params"] for m in doc["model_list"]}
    assert by_name["groq"]["timeout"] == gen.CLOUD_TIMEOUT
    assert by_name["bank-assistant-local"]["timeout"] == gen.LOCAL_TIMEOUT
    assert gen.CLOUD_TIMEOUT < gen.LOCAL_TIMEOUT


def test_litellm_container_receives_every_env_var_the_config_references():
    # THE bug class that made every paid provider fail with an auth error: the generated config
    # referenced os.environ/OPENAI_API_KEY but docker-compose never passed it into the litellm
    # container. Fully-enabled config => every referenced var must be wired through compose.
    cat = _catalog()
    compose = yaml.safe_load(COMPOSE.read_text())
    passed = set(compose["services"]["litellm"]["environment"])
    refs = set(re.findall(r"os\.environ/([A-Z0-9_]+)", gen.generate(cat, _all_enabled_env(cat))))
    missing = refs - passed
    assert not missing, f"litellm container is not given: {sorted(missing)}"


# ───────────────────────── key-paste sanity check (soft warnings) ─────────────────────────
def test_check_key_flags_a_key_pasted_under_the_wrong_provider():
    # Real incident: an OpenRouter key (sk-or-v1-…) was pasted into the ElevenLabs slot.
    cat = _catalog()
    assert gen.check_key(cat, "elevenlabs", "sk-or-v1-abcdef").startswith("other:openrouter:")
    assert gen.check_key(cat, "openrouter", "sk-or-v1-abcdef") == "ok"
    assert gen.check_key(cat, "anthropic", "sk-ant-api03-xyz") == "ok"
    assert gen.check_key(cat, "openai", "sk-ant-api03-xyz").startswith("other:anthropic:")


def test_check_key_never_calls_ambiguous_prefixes_wrong():
    cat = _catalog()
    # `sk-` is shared by OpenAI and DeepSeek: a plain sk- key must not be reported as the other one.
    assert gen.check_key(cat, "deepseek", "sk-abc123") == "ok"
    assert gen.check_key(cat, "openai", "sk-abc123") == "ok"
    assert gen.check_key(cat, "openai", "sk-proj-abc123") == "ok"


def test_check_key_warns_on_unexpected_prefix_but_stays_quiet_without_a_known_one():
    cat = _catalog()
    # a UUID-looking value is not an xAI key (those start with xai-)
    assert gen.check_key(cat, "grok", "00000000-0000-4000-8000-000000000000") == "prefix:xai-"
    # providers with no well-known prefix are never second-guessed
    assert gen.check_key(cat, "mistral", "whatever-format") == "ok"
    assert gen.check_key(cat, "azure", "0123456789abcdef") == "ok"
    assert gen.check_key(cat, "nope", "x") == "ok"


def test_env_example_ships_llama_guard_OFF():
    # Real incident: .env.example once shipped LLAMA_GUARD_URL=http://ollama:11434 with no model pulled,
    # so (fail-closed) EVERY request was blocked. The optional detector must stay opt-in.
    ex = (HERE.parent / ".env.example").read_text()
    m = re.search(r"(?m)^LLAMA_GUARD_URL=(.*)$", ex)
    assert m, "LLAMA_GUARD_URL line missing from .env.example"
    assert m.group(1).strip() == "", "LLAMA_GUARD_URL must default to empty (detector opt-in)"


def test_open_webui_defaults_to_the_free_ladder_and_has_no_random_arena_model():
    # Screenshots showed "Arena Model" (a random-model picker) selected, and DEFAULT_MODELS was ignored on
    # existing installs because Open WebUI persists first-run config. Keep the stack's config authoritative.
    env = yaml.safe_load(COMPOSE.read_text())["services"]["open-webui"]["environment"]
    assert env["DEFAULT_MODELS"].endswith("bank-assistant}")            # ${DEFAULT_MODELS:-bank-assistant}
    assert str(env["ENABLE_PERSISTENT_CONFIG"]).lower() == "false"
    assert str(env["ENABLE_EVALUATION_ARENA_MODELS"]).lower() == "false"


def test_nothing_starts_against_a_router_that_is_still_booting():
    # Found by the sandbox: `./securax up` returned while LiteLLM was still booting, so the gateway was
    # "healthy" yet every chat 502'd and Chat listed half the models. Pin the readiness-gated start order.
    svc = yaml.safe_load(COMPOSE.read_text())["services"]
    assert "readiness" in " ".join(svc["litellm"]["healthcheck"]["test"])
    assert "/readyz" in " ".join(svc["gateway"]["healthcheck"]["test"])
    assert svc["gateway"]["depends_on"]["litellm"]["condition"] == "service_healthy"
    assert svc["open-webui"]["depends_on"]["gateway"]["condition"] == "service_healthy"


def test_router_never_phones_huggingface():
    # Found by the sandbox: LiteLLM fetched a tokenizer from huggingface.co on every request. A sovereign,
    # offline-first estate must not make that outbound call (and offline it cost seconds of retries).
    env = yaml.safe_load(COMPOSE.read_text())["services"]["litellm"]["environment"]
    assert str(env["HF_HUB_OFFLINE"]) == "1" and str(env["TRANSFORMERS_OFFLINE"]) == "1"


REPO = HERE.parent.parent.parent


def test_generated_router_config_is_never_a_tracked_file():
    # Found on a real Windows laptop: `up` rewrote the TRACKED litellm-config.yaml, so the next `git pull`
    # failed ("local changes would be overwritten"). The per-machine file must be git-ignored and be what
    # the router mounts; the tracked baseline must stay untouched by `up`.
    assert gen.OUT.endswith("litellm-config.generated.yaml") and gen.OUT != gen.BASELINE_OUT
    mounts = yaml.safe_load(COMPOSE.read_text())["services"]["litellm"]["volumes"]
    assert any(m.startswith("./litellm-config.generated.yaml:") for m in mounts)
    assert "local/compose/litellm-config.generated.yaml" in (REPO / ".gitignore").read_text()


def test_shell_entrypoints_stay_lf_and_windows_has_a_launcher():
    # Found on Windows: `./securax` can't run in PowerShell, and a CRLF checkout breaks the script.
    attrs = (REPO / ".gitattributes").read_text()
    assert "* text=auto eol=lf" in attrs and "*.bat text eol=crlf" in attrs
    assert "wsl" in (REPO / "securax.cmd").read_text()
    for bat in ("START-HERE-Windows.bat", "STOP-Windows.bat"):
        assert "securax.cmd" in (REPO / bat).read_text(), f"{bat} must go through the WSL launcher"


def test_windows_install_path_is_scripted_and_documented():
    # The one-paste installer + quickstart are what a non-technical Windows user follows blindly.
    import subprocess
    sh = REPO / "local" / "scripts" / "wsl-setup.sh"
    assert subprocess.run(["bash", "-n", str(sh)]).returncode == 0
    txt = sh.read_text()
    assert "docker info" in txt and "WSL integration" in txt and ".env" in txt
    qs = (REPO / "WINDOWS-QUICKSTART.md").read_text()
    assert "wsl-setup.sh" in qs and "./securax keys" in qs and ".wslconfig" in qs
    assert "~/securax" in (REPO / "securax.cmd").read_text()


def test_cli_has_keys_size_preflight_and_elastic_helpers():
    cli = (REPO / "securax").read_text()
    for needle in ("\n  keys)", "\n  size)", "\n  preflight)", "autosize()", "docker_res()", "LOCAL_MODEL_PIN"):
        assert needle in cli, needle


# ───────────────────────────── OpenCode Go: flat-rate open models, build ladder only ─────────────────────────────
def test_opencode_go_heads_the_build_ladder_and_is_never_in_chat():
    cat = _catalog()
    env = {"OPENCODE_GO_API_KEY": "k", "DEEPSEEK_API_KEY": "d", "GEMINI_API_KEY": "g"}
    doc = yaml.safe_load(gen.generate(cat, env))
    head = [m for m in doc["model_list"] if m["model_name"] == "builder"][0]["litellm_params"]
    assert head["model"] == "openai/deepseek-v4.1-flash" and head["api_base"] == "https://opencode.ai/inference/go/v1"
    fb = _fallback_map(doc)
    assert fb["builder"][:3] == ["opencodego-glm", "deepseek", "bank-assistant-gemini"]
    assert "opencodego" not in fb["bank-assistant"] and "opencodego-glm" not in fb["bank-assistant"], "Chat carries personal data and Go is sold for coding agents"
    assert [m for m in doc["model_list"] if m["model_name"] == "bank-assistant"][0]["litellm_params"]["model"].startswith("gemini/")


def test_opencode_go_sends_the_key_from_the_environment_and_identifies_itself():
    doc = yaml.safe_load(gen.generate(_catalog(), {"OPENCODE_GO_API_KEY": "k", "LITELLM_MASTER_KEY": "m"}))
    p = [m for m in doc["model_list"] if m["model_name"] == "opencodego"][0]["litellm_params"]
    assert p["api_key"] == "os.environ/OPENCODE_GO_API_KEY" and "k" not in str(p["api_base"])
    assert p["extra_headers"]["User-Agent"] == "securax-gateway"
    assert p["extra_headers"]["x-opencode-session"].startswith("securax-") and len(p["extra_headers"]["x-opencode-session"]) == len("securax-") + 8
    assert "m" != p["extra_headers"]["x-opencode-session"][8:]                       # the router key itself never leaves in a header


def test_opencode_go_is_off_without_its_key_and_both_models_share_one_key():
    cat = _catalog()
    assert not {"opencodego", "opencodego_glm"} & set(gen.enabled_llm_ids(cat, {}))
    assert {"opencodego", "opencodego_glm"} <= set(gen.enabled_llm_ids(cat, {"OPENCODE_GO_API_KEY": "k"}))


def test_opencode_go_discovery_recipe_prefers_the_flash_models_and_skips_non_chat_ones():
    by = {p["id"]: p for p in _catalog()["providers"]}
    assert by["opencodego"]["discover"]["url"] == "https://opencode.ai/inference/go/v1/models"
    import re
    prefer = by["opencodego"]["discover"]["prefer"]
    assert re.search(prefer[0], "deepseek-v4.1-flash") and re.search(_catalog()["_discover_exclude"], "deepseek-v4-flash-vision-exp", re.I)
