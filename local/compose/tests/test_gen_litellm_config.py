"""Tests for the plugin-catalog -> LiteLLM config generator (gen_litellm_config.py).

No Docker and no network: we feed the generator a fake .env dict and assert the emitted YAML
enables exactly the right providers, routes the default correctly, and always stays valid YAML.
"""
import importlib.util
import pathlib

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
    assert doc["litellm_settings"]["fallbacks"] == [{"bank-assistant": ["bank-assistant-local"]}]


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
