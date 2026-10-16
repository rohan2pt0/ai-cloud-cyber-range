"""Phones over Tailscale (doc 58): one address carries the app, the gateway and sync; shared keys are not flagged."""
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
CONF = (ROOT / "local/compose/guiding-map.conf").read_text()


def test_app_server_forwards_gateway_and_sync_on_the_same_origin():
    for path, upstream in (("/v1/", "gateway:8080"), ("= /healthz", "gateway:8080"), ("/sync", "estate-sync:8089")):
        block = CONF.split(f"location {path} {{", 1)[1].split("}", 1)[0]
        assert upstream in block, path
        # through a variable + resolver: nginx still starts while that service is stopped
        assert re.search(r"proxy_pass \$\w+;", block), path
    assert "resolver 127.0.0.11" in CONF


def test_sync_location_carries_websocket_upgrade():
    block = CONF.split("location /sync {", 1)[1].split("}", 1)[0]
    assert "proxy_set_header Upgrade $http_upgrade" in block and "proxy_http_version 1.1" in block


def _check(provider, key):
    gen = ROOT / "local/compose/gen_litellm_config.py"
    return subprocess.run(["python3", str(gen), "--check-key", provider], input=key, capture_output=True, text=True).stdout.strip()


def test_shared_key_providers_are_not_flagged_as_wrong():
    assert _check("openrouter_pro", "sk-or-v1-abc") == "ok"
    assert _check("groq_qwen", "gsk_abc") == "ok"
    assert _check("elevenlabs", "sk-or-v1-abc").startswith("other:openrouter")   # a real mix-up is still caught


def test_consent_fields_ask_for_yes_not_a_paste():
    s = (ROOT / "securax").read_text()
    assert "*_OK) printf '  %s (type yes to accept" in s
    cat = json.loads((ROOT / "plugins/catalog.json").read_text())
    ok_envs = {e for p in cat["providers"] for e in p.get("env", []) if e.endswith("_OK")}
    assert ok_envs, "expected at least one consent field"


def test_placeholder_gateway_key_is_replaced_on_up():
    s = (ROOT / "securax").read_text()
    assert '[ "$(ev LITELLM_MASTER_KEY)" = "sk-range-change-me" ]' in s and "secrets.token_hex(24)" in s


def test_command_center_teaches_tailscale_not_an_open_wifi_port():
    hub = (ROOT / "guiding-map/hub.html").read_text()
    assert "./securax phones" in hub
    # BIND_HOST=0.0.0.0 may only appear as the thing NOT to do
    for line in hub.splitlines():
        if "BIND_HOST=0.0.0.0" in line:
            assert "never" in line.lower() or "never" in hub[max(0, hub.index(line) - 200):hub.index(line)].lower()
