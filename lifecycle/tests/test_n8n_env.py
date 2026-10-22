"""n8n 2 blocks workflows from reading the environment unless N8N_BLOCK_ENV_ACCESS_IN_NODE is false. The estate turns that
back on because the shipped templates read GATEWAY_URL; this keeps the trade safe: while workflows can read n8n's
environment, nothing secret may be in it, and the templates read only the variables listed here."""
import json
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "local" / "compose"
TEMPLATES = sorted((ROOT / "integrations" / "n8n").glob("*.json"))
ALLOWED = {"GATEWAY_URL"}
SECRET = re.compile(r"KEY|TOKEN|SECRET|PASS|CREDENTIAL|PRIVATE", re.I)


class _Loader(yaml.SafeLoader):
    """Compose's own tags (!override, !reset) carry the plain value underneath."""


def _plain(loader, node):
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node, deep=True)
    return loader.construct_scalar(node)


for _tag in ("!override", "!reset"):
    _Loader.add_constructor(_tag, _plain)


def _env(file: str) -> dict:
    svc = (yaml.load((COMPOSE / file).read_text("utf-8"), Loader=_Loader).get("services") or {}).get("n8n") or {}
    env = svc.get("environment") or {}
    return env if isinstance(env, dict) else dict(e.split("=", 1) for e in env)


def test_no_secret_sits_in_n8n_s_environment_while_workflows_can_read_it():
    env = {**_env("docker-compose.yml"), **_env("tls-internal.yml")}
    assert env.get("N8N_BLOCK_ENV_ACCESS_IN_NODE") == "false"
    leaked = sorted(k for k in env if SECRET.search(k))
    assert not leaked, f"move these out of n8n's environment into n8n credentials: {leaked}"


def test_the_templates_read_only_the_listed_variables():
    assert TEMPLATES
    for t in TEMPLATES:
        json.loads(t.read_text("utf-8"))
        used = set(re.findall(r"\$env\.([A-Za-z_][A-Za-z0-9_]*)", t.read_text("utf-8")))
        assert used <= ALLOWED, f"{t.name} reads {sorted(used - ALLOWED)}; add a non-secret name to ALLOWED or use a credential"
