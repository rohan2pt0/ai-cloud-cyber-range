"""The OpenCode terminal agent is pointed at the SecuRAX gateway and nothing else: the config it gets must close every side door."""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import gen_litellm_config as gen  # noqa: E402
import gen_opencode_config as oc  # noqa: E402

ROOT = HERE.parent.parent


def _cfg(env=None, url="http://localhost:8080"):
    return oc.build(gen.load_catalog(gen.CATALOG), env or {"GEMINI_API_KEY": "g", "OPENCODE_GO_API_KEY": "k"}, url)


def test_opencode_can_only_reach_the_gateway():
    c = _cfg()
    assert c["enabled_providers"] == ["securax"]                        # its other built-in providers are off: no side door around the guardrails
    assert list(c["provider"]) == ["securax"] and c["provider"]["securax"]["npm"] == "@ai-sdk/openai-compatible"
    assert c["provider"]["securax"]["options"]["baseURL"] == "http://localhost:8080/v1"


def test_the_config_holds_no_secret_the_key_is_read_from_the_environment_at_run_time():
    txt = json.dumps(_cfg({"GEMINI_API_KEY": "AIza-secret", "OPENCODE_GO_API_KEY": "ocgo-secret", "LITELLM_MASTER_KEY": "master-secret"}))
    assert "secret" not in txt.replace("{env:SECURAX_GATEWAY_KEY}", "") and "{env:SECURAX_GATEWAY_KEY}" in txt


def test_safe_defaults_for_a_regulated_user():
    c = _cfg()
    assert c["autoupdate"] is False and c["share"] == "disabled"         # no unreviewed code arrives by itself; no public conversation links
    assert c["permission"] == {"edit": "ask", "bash": "ask"}             # OpenCode's own default is to allow everything


def test_the_build_ladder_is_the_default_model_and_the_models_are_the_estates_aliases():
    c = _cfg()
    assert c["model"] == "securax/builder" and c["small_model"] == "securax/builder"
    models = c["provider"]["securax"]["models"]
    assert {"builder", "opencodego", "opencodego-glm", "bank-assistant-local"} <= set(models)
    assert not {"bank-assistant", "twin"} & set(models)                  # a coding agent never gets a Chat chain (personal data)
    assert all(m["limit"]["context"] > 0 for m in models.values())
    assert models["bank-assistant-local"]["limit"]["context"] < models["builder"]["limit"]["context"]   # the small local model gets a small window


def test_no_provider_is_offered_that_has_no_key():
    models = _cfg({"GEMINI_API_KEY": "g"})["provider"]["securax"]["models"]
    assert "opencodego" not in models and "bank-assistant-gemini" in models


def test_cli_writes_the_file_where_asked(tmp_path):
    out = tmp_path / "x" / "opencode.json"
    r = subprocess.run([sys.executable, str(HERE / "gen_opencode_config.py"), "--env-file", str(tmp_path / "none"), "--base-url", "https://localhost", "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and json.loads(out.read_text())["provider"]["securax"]["options"]["baseURL"] == "https://localhost/v1"


def test_the_launcher_without_opencode_installed_gives_a_pinned_npm_install_not_a_curl_to_shell():
    r = subprocess.run(["bash", str(ROOT / "securax"), "opencode"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "HOME": str(ROOT)})
    out = r.stdout + r.stderr
    assert r.returncode == 1 and "npm install -g opencode-ai@" in out and "| bash" not in out and "| sh" not in out


def test_check_reports_the_build_chain_only(capsys, tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENCODE_GO_API_KEY=x\nGROQ_API_KEY=gsk_x\nDEEPSEEK_API_KEY=sk-x\n")
    assert oc.main(["--env-file", str(env), "--check"]) == 0
    out = capsys.readouterr().out
    assert "default model: securax/builder" in out and "none (as it should be)" in out
    chain = next(ln for ln in out.splitlines() if ln.startswith("Build chain"))
    assert chain.index("groq") < chain.index("deepseek") and chain.rstrip().endswith("bank-assistant-local")


def test_the_strong_chain_is_offered_and_the_build_rules_ride_with_every_session():
    cat = gen.load_catalog(gen.CATALOG)
    env = {"OPENCODE_GO_API_KEY": "sk-go"}
    c = oc.build(cat, env, "http://localhost:8080")
    models = c["provider"]["securax"]["models"]
    assert {"builder", "strong", "opencodego-pro", "opencodego-kimi"} <= set(models) and c["model"] == "securax/builder"
    assert oc.build(cat, env, "http://localhost:8080", strong=True)["model"] == "securax/strong"
    assert [pathlib.Path(i).name for i in c["instructions"]] == ["BUILD-CONTRACT.md", "LESSONS.md"] and all(pathlib.Path(i).exists() for i in c["instructions"])
    assert oc.check(cat, env, c) == 0                                       # strong is a coding chain, not a Chat chain
