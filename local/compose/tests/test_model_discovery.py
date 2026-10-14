"""model_discovery: retired model names are replaced by a live one; offline/rejected keys never corrupt .env."""
import importlib.util
import io
import json
import pathlib
import urllib.error

import pytest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("md", HERE.parent / "model_discovery.py")
md = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md)
CAT = json.loads((HERE.parent.parent.parent / "plugins" / "catalog.json").read_text())


@pytest.fixture(autouse=True)
def _no_test_hook(monkeypatch):
    # The sandbox exports SECURAX_DISCOVERY_REWRITE for the whole process tree; unit tests must not inherit it.
    monkeypatch.delenv("SECURAX_DISCOVERY_REWRITE", raising=False)


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_for(payloads: dict, fail=None):
    def _open(req, timeout=0):
        url = req.full_url
        if fail:
            raise fail
        for host, body in payloads.items():
            if host in url:
                return Resp(json.dumps(body).encode())
        raise urllib.error.URLError("no route")
    return _open


def test_retired_default_is_replaced_by_best_live_model():
    env = {"GROQ_API_KEY": "gsk_x", "GEMINI_API_KEY": "AIza_x"}
    live = {"groq.com": {"data": [{"id": "llama-3.1-8b-instant"}, {"id": "openai/gpt-oss-120b"}, {"id": "whisper-large-v3"}]},
            "googleapis.com": {"models": [{"name": "models/gemini-9.1-flash", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/gemini-9.2-flash-preview", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/gemini-9.0-flash", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/embedding-001", "supportedGenerationMethods": ["embedContent"]}]}}
    res = {r["id"]: r for r in md.check(CAT, env, opener_for(live))}
    assert res["gemini"]["status"] == "replaced" and res["gemini"]["new"] == "gemini/gemini-9.1-flash"   # newest stable, not preview
    assert res["groq"]["status"] in ("ok", "replaced")


def test_live_current_model_is_left_alone_and_user_override_respected():
    cur = next(p for p in CAT["providers"] if p["id"] == "openai")["model"].split("/", 1)[1]
    env = {"OPENAI_API_KEY": "sk-x"}
    res = md.check(CAT, env, opener_for({"openai.com": {"data": [{"id": cur}, {"id": "gpt-99-mini"}]}}))
    assert res[0]["status"] == "ok"
    env["OPENAI_MODEL"] = "openai/retired-model"
    res = md.check(CAT, env, opener_for({"openai.com": {"data": [{"id": cur}, {"id": "gpt-99-mini"}]}}))
    assert res[0]["status"] == "replaced" and res[0]["new"] == "openai/gpt-99-mini"


def test_offline_and_rejected_key_change_nothing(tmp_path):
    env = {"OPENAI_API_KEY": "sk-x"}
    assert md.check(CAT, env, opener_for({}, fail=urllib.error.URLError("offline")))[0]["status"] == "unreachable"
    err = urllib.error.HTTPError("u", 401, "no", {}, None)
    assert md.check(CAT, env, opener_for({}, fail=err))[0]["status"] == "key-rejected"
    f = tmp_path / ".env"
    f.write_text("OPENAI_API_KEY=sk-x\n")
    assert md.check(CAT, md.parse_env_file(str(f)), opener_for({}, fail=urllib.error.URLError("offline")))[0]["status"] == "unreachable"
    assert f.read_text() == "OPENAI_API_KEY=sk-x\n"            # .env untouched


def test_no_keys_means_no_calls():
    assert md.check(CAT, {}, opener_for({}, fail=AssertionError("must not call the network"))) == []


def test_set_env_value_replaces_or_appends(tmp_path):
    f = tmp_path / ".env"
    f.write_text("A=1\nGROQ_MODEL=old\n")
    md.set_env_value(str(f), "GROQ_MODEL", "new")
    md.set_env_value(str(f), "NEWKEY", "v")
    assert f.read_text() == "A=1\nGROQ_MODEL=new\nNEWKEY=v\n"


def test_every_discoverable_provider_has_a_recipe_and_a_default():
    for p in CAT["providers"]:
        d = p.get("discover")
        if d:
            assert d["kind"] in ("openai", "gemini", "anthropic") and d["url"].startswith("https://") and d["prefer"]
            assert p["model"].startswith(d["prefix"]), p["id"]


def test_unreachable_says_why_and_no_match_lists_live_models():
    env = {"OPENAI_API_KEY": "sk-x"}
    r = md.check(CAT, env, opener_for({}, fail=urllib.error.HTTPError("u", 503, "down", {}, None)))[0]
    assert r["status"] == "unreachable" and "503" in r["detail"]
    r = md.check(CAT, env, opener_for({"openai.com": {"data": [{"id": "zzz-1"}, {"id": "zzz-2"}]}}))[0]
    assert r["status"] == "no-match" and r["live"] == ["zzz-1", "zzz-2"]


def test_deepseek_default_is_the_current_v4_model_and_legacy_name_is_only_a_fallback():
    p = next(p for p in CAT["providers"] if p["id"] == "deepseek")
    assert p["model"] == "deepseek/deepseek-v4-flash"
    env = {"DEEPSEEK_API_KEY": "sk-x"}
    r = md.check(CAT, env, opener_for({"deepseek.com": {"data": [{"id": "deepseek-chat"}]}}))[0]
    assert r["status"] == "replaced" and r["new"] == "deepseek/deepseek-chat"      # old accounts keep working until the alias dies
    r = md.check(CAT, env, opener_for({"deepseek.com": {"data": [{"id": "deepseek-v4-flash"}, {"id": "deepseek-v4-pro"}]}}))[0]
    assert r["status"] == "ok"


def test_xai_answers_a_wrong_key_with_400_and_that_is_reported_as_a_rejected_key():
    env = {"XAI_API_KEY": "xai-wrong"}
    err = urllib.error.HTTPError("u", 400, "Incorrect API key provided", {}, None)
    assert md.check(CAT, env, opener_for({}, fail=err))[0]["status"] == "key-rejected"
    # ...but a 400 from a provider that uses 401 for bad keys is still just 'unreachable'
    assert md.check(CAT, {"OPENAI_API_KEY": "sk-x"}, opener_for({}, fail=err))[0]["status"] == "unreachable"
