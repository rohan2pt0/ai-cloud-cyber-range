"""`./securax gateway-auth`: keys are generated once, only hashes are stored, privileged roles cannot be handed to a machine."""
import base64
import importlib.util
import json
import pathlib
import stat

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("gwauth", REPO / "governance" / "gateway_auth.py")
ga = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ga)
idn = ga._identity()


def envfile(tmp_path):
    p = tmp_path / ".env"
    p.write_text("LITELLM_MASTER_KEY=sk-range-dev\n")
    return p


def test_a_key_is_shown_once_and_only_its_hash_is_stored(tmp_path):
    p = envfile(tmp_path)
    key = ga.add_key(p, "n8n", ["service"], expires="2999-01-01")
    raw = p.read_text()
    assert key.startswith("sk-sx-") and key not in raw.split(ga.KEYVAR)[1].split("\n")[0]
    stored = ga.load_keys(ga.read_env(p))
    assert stored[0]["sha256"] == idn.hash_key(key) and stored[0]["expires"] == "2999-01-01"
    assert stat.S_IMODE(p.stat().st_mode) == 0o600


def test_the_stored_list_is_exactly_what_the_gateway_loads(tmp_path):
    p = envfile(tmp_path)
    key = ga.add_key(p, "n8n", ["service"])
    cfg = idn.Config.from_env({"AUTH_MODE": "required", "GATEWAY_API_KEYS_B64": ga.read_env(p)[ga.KEYVAR]})
    assert idn.verify_api_key(key, cfg).subject == "key:n8n"


def test_machines_cannot_hold_mfa_roles_or_unknown_roles(tmp_path):
    p = envfile(tmp_path)
    for roles in (["admin"], ["auditor"], ["wizard"]):
        with pytest.raises(SystemExit):
            ga.add_key(p, "x", roles)


def test_revoke_and_rotate(tmp_path):
    p = envfile(tmp_path)
    old = ga.add_key(p, "ops", ["service"])
    new = ga.add_key(p, "ops", ["service"])                     # same name replaces: the old hash is gone
    keys = ga.load_keys(ga.read_env(p))
    assert len(keys) == 1 and keys[0]["sha256"] == idn.hash_key(new) != idn.hash_key(old)
    assert ga.main(["--env-file", str(p), "key", "revoke", "ops"]) == 0
    assert ga.load_keys(ga.read_env(p)) == []
    assert ga.main(["--env-file", str(p), "key", "revoke", "ops"]) == 1


def test_enable_turns_auth_on_and_creates_the_keys_the_estate_needs(tmp_path, capsys):
    p = envfile(tmp_path)
    assert ga.main(["--env-file", str(p), "enable"]) == 0
    env = ga.read_env(p)
    assert env["AUTH_MODE"] == "required" and env["WEBUI_GATEWAY_KEY"].startswith("sk-sx-") and env["GATEWAY_API_KEY"].startswith("sk-sx-")
    assert {k["id"] for k in ga.load_keys(env)} == {"openwebui", "securax-cli"}
    cfg = idn.Config.from_env({"AUTH_MODE": "required", "GATEWAY_API_KEYS_B64": env[ga.KEYVAR]})
    assert idn.verify_api_key(env["WEBUI_GATEWAY_KEY"], cfg) and idn.verify_api_key(env["GATEWAY_API_KEY"], cfg)
    ga.main(["--env-file", str(p), "enable"])                   # idempotent: does not rotate working keys
    assert ga.read_env(p)["WEBUI_GATEWAY_KEY"] == env["WEBUI_GATEWAY_KEY"]
    ga.main(["--env-file", str(p), "disable"])
    assert ga.read_env(p)["AUTH_MODE"] == "off"


def test_status_warns_about_open_gateway_missing_idp_and_non_expiring_keys(tmp_path, capsys):
    p = envfile(tmp_path)
    ga.main(["--env-file", str(p), "status"])
    assert "accepts anyone" in capsys.readouterr().out
    ga.main(["--env-file", str(p), "enable"])
    capsys.readouterr()
    ga.main(["--env-file", str(p), "status"])
    out = capsys.readouterr().out
    assert "no OIDC provider yet" in out and "no expiry" in out


def test_encoded_list_survives_a_round_trip_with_awkward_characters(tmp_path):
    p = envfile(tmp_path)
    ga.save_keys(p, [{"id": "a'b\"c$d", "sha256": "0" * 64, "roles": ["service"]}])
    assert ga.load_keys(ga.read_env(p))[0]["id"] == "a'b\"c$d"
    assert json.loads(base64.b64decode(ga.read_env(p)[ga.KEYVAR]))[0]["roles"] == ["service"]
